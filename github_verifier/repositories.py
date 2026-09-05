"""
Repository listing with pagination and smart filtering.

Design notes:
  • Repos are sorted by most-recently-pushed so the most active
    projects are analysed first.
  • Forks and archived repos are excluded by default (configurable).
  • We fetch slightly more than max_repos to allow for filtering.
"""
from __future__ import annotations

from datetime import datetime

from .client import GitHubClient
from .config import GitHubConfig, settings
from .models import Repository


async def fetch_repositories(
    client: GitHubClient,
    username: str,
    config: GitHubConfig | None = None,
) -> list[Repository]:
    """Return up to *config.max_repos* non-fork, non-archived repos."""
    cfg = config or settings

    # Fetch extra so filtering still leaves enough results
    raw = await client.get_paginated(
        f"/users/{username}/repos",
        params={"type": "owner", "sort": "pushed", "direction": "desc"},
        max_items=cfg.max_repos * 2,
    )

    if not raw:
        return []

    repos: list[Repository] = []
    for item in raw:
        if item.get("fork", False) and not cfg.include_forks:
            continue
        if item.get("archived", False) and not cfg.include_archived:
            continue

        repos.append(
            Repository(
                name=item["name"],
                full_name=item["full_name"],
                description=item.get("description"),
                url=item["url"],
                html_url=item["html_url"],
                owner=item["owner"]["login"],
                primary_language=item.get("language"),
                topics=item.get("topics", []),
                stars=item.get("stargazers_count", 0),
                forks=item.get("forks_count", 0),
                created_at=_dt(item["created_at"]),
                updated_at=_dt(item["updated_at"]),
                pushed_at=_dt(item["pushed_at"]) if item.get("pushed_at") else None,
                default_branch=item.get("default_branch", "main"),
                is_fork=item.get("fork", False),
                is_archived=item.get("archived", False),
                size_kb=item.get("size", 0),
            )
        )

        if len(repos) >= cfg.max_repos:
            break

    return repos


async def fetch_languages(
    client: GitHubClient,
    repo_full_name: str,
) -> dict[str, int]:
    """GET /repos/{owner}/{repo}/languages → {lang: bytes}."""
    data = await client.get(f"/repos/{repo_full_name}/languages")
    return data if isinstance(data, dict) else {}


def _dt(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))
