"""
Configuration for the GitHub Verification module.

All settings are loaded from environment variables.
The GitHub token is NEVER hardcoded or logged.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")


class GitHubConfig:
    """Central configuration — all values come from environment variables."""

    def __init__(
        self,
        token: str | None = None,
        max_repos: int | None = None,
        max_files_per_repo: int | None = None,
        max_commits_per_repo: int | None = None,
    ):
        self.token: str | None = token or os.getenv("GITHUB_TOKEN")

        # Tunable limits (override via constructor or env vars)
        self.max_repos = max_repos or int(os.getenv("GH_MAX_REPOS", "15"))
        self.max_files_per_repo = max_files_per_repo or int(
            os.getenv("GH_MAX_FILES_PER_REPO", "10")
        )
        self.max_commits_per_repo = max_commits_per_repo or int(
            os.getenv("GH_MAX_COMMITS_PER_REPO", "30")
        )
        self.max_file_size_bytes = int(
            os.getenv("GH_MAX_FILE_SIZE", str(512 * 1024))
        )  # 512 KB
        self.request_timeout = float(os.getenv("GH_REQUEST_TIMEOUT", "15.0"))
        self.max_retries = int(os.getenv("GH_MAX_RETRIES", "3"))
        self.include_forks = os.getenv("GH_INCLUDE_FORKS", "false").lower() == "true"
        self.include_archived = (
            os.getenv("GH_INCLUDE_ARCHIVED", "false").lower() == "true"
        )

    @property
    def is_authenticated(self) -> bool:
        return bool(self.token)

    @property
    def rate_limit_per_hour(self) -> int:
        return 5000 if self.is_authenticated else 60

    def __repr__(self) -> str:
        return (
            f"GitHubConfig(authenticated={self.is_authenticated}, "
            f"max_repos={self.max_repos}, "
            f"rate_limit={self.rate_limit_per_hour}/hr)"
        )


# Module-level singleton — importable as `from .config import settings`
settings = GitHubConfig()
