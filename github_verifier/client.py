"""
GitHub REST API client.

Features:
  • Rate-limit detection via X-RateLimit-* headers with automatic wait
  • Exponential-backoff retries on 5xx and timeouts
  • Transparent pagination up to a configurable max
  • Token is never logged or included in exceptions
"""
from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Any

import httpx

from .config import GitHubConfig, settings
from .exceptions import (
    AuthenticationError,
    GitHubAPIError,
    InvalidUsernameError,
    RateLimitError,
)

logger = logging.getLogger(__name__)

# GitHub username rules: 1-39 chars, alphanumeric or hyphen,
# cannot start/end with hyphen, no consecutive hyphens.
_USERNAME_RE = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$")


def parse_github_target(raw: str) -> tuple[str, str | None]:
    """
    Parse a GitHub username, profile URL, or repository URL.
    Returns (username, repo_name or None).

    Examples:
      • "octocat" -> ("octocat", None)
      • "@octocat" -> ("octocat", None)
      • "https://github.com/octocat" -> ("octocat", None)
      • "https://github.com/octocat/Spoon-Knife" -> ("octocat", "Spoon-Knife")
    """
    raw = raw.strip().rstrip("/")
    repo_name: str | None = None

    if raw.startswith(("http://", "https://")):
        parts = raw.split("github.com/")
        if len(parts) == 2:
            segments = [s for s in parts[1].split("?")[0].split("/") if s]
            if len(segments) >= 2:
                username = segments[0]
                repo_name = segments[1]
            elif len(segments) == 1:
                username = segments[0]
            else:
                raise InvalidUsernameError(raw)
        else:
            raise InvalidUsernameError(raw)
    else:
        if "/" in raw:
            segments = [s for s in raw.split("/") if s]
            if len(segments) == 2:
                username, repo_name = segments[0], segments[1]
            else:
                username = segments[0]
        else:
            username = raw

    if username.startswith("@"):
        username = username[1:]

    if not _USERNAME_RE.match(username):
        raise InvalidUsernameError(raw)

    return username, repo_name


def validate_username(raw: str) -> str:
    """
    Accept a GitHub username **or** profile/repo URL and return a clean username.
    """
    username, _ = parse_github_target(raw)
    return username


class GitHubClient:
    """Async HTTP client for the GitHub REST API v3."""

    BASE_URL = "https://api.github.com"

    def __init__(self, config: GitHubConfig | None = None):
        self._config = config or settings
        self._api_calls = 0
        self._rate_remaining: int | None = None
        self._rate_reset: int | None = None

        headers: dict[str, str] = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ProdaptHackathon-CandidateScreening/1.0",
        }
        if self._config.token:
            headers["Authorization"] = f"Bearer {self._config.token}"

        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=headers,
            timeout=httpx.Timeout(self._config.request_timeout),
            follow_redirects=True,
        )

    # ── Properties ────────────────────────────────────────────

    @property
    def api_calls(self) -> int:
        return self._api_calls

    @property
    def rate_limit_remaining(self) -> int | None:
        return self._rate_remaining

    # ── Context manager ───────────────────────────────────────

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "GitHubClient":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()

    # ── Core request methods ──────────────────────────────────

    async def get(
        self, path: str, params: dict[str, Any] | None = None
    ) -> dict | list | None:
        """GET with retries, rate-limit wait, and error mapping."""
        last_err: Exception | None = None

        for attempt in range(self._config.max_retries):
            try:
                await self._wait_for_rate_limit()

                resp = await self._client.get(path, params=params)
                self._api_calls += 1
                self._read_rate_headers(resp)

                if resp.status_code == 200:
                    return resp.json()
                if resp.status_code == 404:
                    return None
                if resp.status_code == 401:
                    raise AuthenticationError()
                if resp.status_code == 403:
                    if self._rate_remaining == 0:
                        raise RateLimitError(self._rate_reset)
                    raise GitHubAPIError(403, resp.text[:200], path)
                if resp.status_code >= 500:
                    last_err = GitHubAPIError(resp.status_code, resp.text[:200], path)
                    await self._backoff(attempt)
                    continue
                raise GitHubAPIError(resp.status_code, resp.text[:200], path)

            except httpx.TimeoutException:
                last_err = GitHubAPIError(408, "Request timed out", path)
                await self._backoff(attempt)
            except (httpx.ConnectError, httpx.ReadError) as exc:
                last_err = GitHubAPIError(0, str(exc)[:200], path)
                await self._backoff(attempt)

        raise last_err  # type: ignore[misc]

    async def get_paginated(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        max_items: int = 100,
    ) -> list[dict]:
        """Fetch paginated results up to *max_items*."""
        params = dict(params or {})
        params.setdefault("per_page", min(max_items, 100))

        items: list[dict] = []
        page = 1

        while len(items) < max_items:
            params["page"] = page
            result = await self.get(path, params=params)

            if not result or not isinstance(result, list):
                break

            items.extend(result)

            if len(result) < params["per_page"]:
                break  # last page
            page += 1

        return items[:max_items]

    # ── Internal helpers ──────────────────────────────────────

    def _read_rate_headers(self, resp: httpx.Response) -> None:
        rem = resp.headers.get("x-ratelimit-remaining")
        rst = resp.headers.get("x-ratelimit-reset")
        if rem is not None:
            self._rate_remaining = int(rem)
        if rst is not None:
            self._rate_reset = int(rst)
        if self._rate_remaining is not None and self._rate_remaining < 10:
            logger.warning("GitHub rate-limit low: %d remaining", self._rate_remaining)

    async def _wait_for_rate_limit(self) -> None:
        if self._rate_remaining is not None and self._rate_remaining <= 0:
            if self._rate_reset:
                wait = max(0, self._rate_reset - int(time.time())) + 1
                if 0 < wait < 900:  # wait up to 15 min
                    logger.info("Rate-limited. Waiting %ds …", wait)
                    await asyncio.sleep(wait)
                else:
                    raise RateLimitError(self._rate_reset)

    @staticmethod
    async def _backoff(attempt: int) -> None:
        wait = 2**attempt
        logger.warning("Retry #%d in %ds …", attempt + 1, wait)
        await asyncio.sleep(wait)
