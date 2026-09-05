"""
Custom exceptions for the GitHub Verification module.

Design rules:
  • Never include tokens or credentials in error messages.
  • Provide enough context for the caller to decide what to do.
  • All exceptions inherit from GitHubVerifierError for easy catching.
"""


class GitHubVerifierError(Exception):
    """Base exception for all GitHub verifier errors."""


class GitHubAPIError(GitHubVerifierError):
    """Error returned by the GitHub REST API."""

    def __init__(self, status_code: int, message: str, url: str = ""):
        self.status_code = status_code
        self.url = url  # path only — never includes tokens
        super().__init__(f"GitHub API error {status_code}: {message}")


class RateLimitError(GitHubAPIError):
    """GitHub API rate limit exceeded."""

    def __init__(self, reset_at: int | None = None):
        self.reset_at = reset_at
        msg = "Rate limit exceeded"
        if reset_at:
            msg += f" (resets at Unix timestamp {reset_at})"
        super().__init__(status_code=403, message=msg)


class AuthenticationError(GitHubAPIError):
    """Invalid or missing GitHub token."""

    def __init__(self):
        super().__init__(
            status_code=401,
            message="Authentication failed — check GITHUB_TOKEN",
        )


class ProfileNotFoundError(GitHubVerifierError):
    """GitHub user profile does not exist or is not accessible."""

    def __init__(self, username: str):
        self.username = username
        super().__init__(f"GitHub profile not found: {username}")


class InvalidUsernameError(GitHubVerifierError):
    """The supplied string is not a valid GitHub username."""

    def __init__(self, username: str):
        self.username = username
        super().__init__(
            f"Invalid GitHub username: '{username}' "
            "(must be 1–39 alphanumeric characters or hyphens)"
        )
