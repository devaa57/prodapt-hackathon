"""Tests for client.py — username validation (no network calls)."""
import pytest

from github_verifier.client import validate_username
from github_verifier.exceptions import InvalidUsernameError


class TestValidateUsername:
    """All tests run offline — no GitHub API calls."""

    def test_plain_username(self):
        assert validate_username("octocat") == "octocat"

    def test_at_prefix(self):
        assert validate_username("@octocat") == "octocat"

    def test_https_url(self):
        assert validate_username("https://github.com/octocat") == "octocat"

    def test_https_url_trailing_slash(self):
        assert validate_username("https://github.com/octocat/") == "octocat"

    def test_http_url(self):
        assert validate_username("http://github.com/octocat") == "octocat"

    def test_url_with_path(self):
        assert validate_username("https://github.com/octocat/repo") == "octocat"

    def test_whitespace_stripped(self):
        assert validate_username("  octocat  ") == "octocat"

    def test_hyphenated_username(self):
        assert validate_username("my-user-name") == "my-user-name"

    def test_single_char(self):
        assert validate_username("x") == "x"

    def test_max_length_39(self):
        name = "a" * 39
        assert validate_username(name) == name

    # ── Invalid inputs ────────────────────────────────────────

    def test_empty_string(self):
        with pytest.raises(InvalidUsernameError):
            validate_username("")

    def test_starts_with_hyphen(self):
        with pytest.raises(InvalidUsernameError):
            validate_username("-octocat")

    def test_ends_with_hyphen(self):
        with pytest.raises(InvalidUsernameError):
            validate_username("octocat-")

    def test_too_long(self):
        with pytest.raises(InvalidUsernameError):
            validate_username("a" * 40)

    def test_special_chars(self):
        with pytest.raises(InvalidUsernameError):
            validate_username("user@name!")

    def test_non_github_url(self):
        with pytest.raises(InvalidUsernameError):
            validate_username("https://gitlab.com/user")
