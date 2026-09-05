"""
GitHub commit retrieval.

Design note:
  Commit count does NOT prove the candidate personally wrote all code.
  We extract commit metadata only as *supporting* evidence, never as
  proof of authorship.
"""
from __future__ import annotations

from datetime import datetime

from .client import GitHubClient
from .config import GitHubConfig, settings
from .models import CommitInfo


async def fetch_commits(
    client: GitHubClient,
    repo_full_name: str,
    author: str | None = None,
    config: GitHubConfig | None = None,
) -> list[CommitInfo]:
    """
    GET /repos/{owner}/{repo}/commits

    Optionally filters by *author* (GitHub username).
    Returns up to config.max_commits_per_repo commits.
    """
    cfg = config or settings
    params: dict[str, str] = {}
    if author:
        params["author"] = author

    raw = await client.get_paginated(
        f"/repos/{repo_full_name}/commits",
        params=params,
        max_items=cfg.max_commits_per_repo,
    )

    if not raw:
        return []

    commits: list[CommitInfo] = []
    for item in raw:
        commit = item.get("commit", {})
        author_info = commit.get("author", {})
        gh_author = item.get("author")  # GitHub user object — may be None

        date_str = author_info.get("date")
        if not date_str:
            continue

        commits.append(
            CommitInfo(
                sha=item["sha"],
                author_name=author_info.get("name"),
                author_email=author_info.get("email"),
                author_login=gh_author["login"] if gh_author else None,
                date=datetime.fromisoformat(date_str.replace("Z", "+00:00")),
                message=commit.get("message", ""),
                repository=repo_full_name,
            )
        )

    return commits
