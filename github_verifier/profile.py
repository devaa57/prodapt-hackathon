"""Fetch a GitHub user's public profile."""
from __future__ import annotations

from datetime import datetime

from .client import GitHubClient, validate_username
from .exceptions import ProfileNotFoundError
from .models import GitHubProfile


async def fetch_profile(client: GitHubClient, username: str) -> GitHubProfile:
    """
    GET /users/{username}

    Raises ProfileNotFoundError if the user does not exist.
    """
    username = validate_username(username)
    data = await client.get(f"/users/{username}")

    if data is None:
        raise ProfileNotFoundError(username)

    return GitHubProfile(
        username=data["login"],
        name=data.get("name"),
        bio=data.get("bio"),
        company=data.get("company"),
        location=data.get("location"),
        public_repos=data.get("public_repos", 0),
        followers=data.get("followers", 0),
        following=data.get("following", 0),
        created_at=_parse_dt(data["created_at"]),
        profile_url=data["html_url"],
        avatar_url=data.get("avatar_url"),
    )


def _parse_dt(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))
