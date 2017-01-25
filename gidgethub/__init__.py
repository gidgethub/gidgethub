from typing import Any


class GitHubException(Exception):

    """Base exception for this library."""


class ValidationFailure(GitHubException):

    """An exception representing failed validation of a webhook event."""
    # https://developer.github.com/webhooks/securing/#validating-payloads-from-github


class HTTPException(GitHubException):

    """A general exception to represent HTTP responses."""

    def __init__(self, status_code: int, *args: Any) -> None:
        self.status_code = status_code
        super().__init__(*args)


class BadRequest(HTTPException):
    """The request is invalid.

    Used for 4XX HTTP errors.
    """
    # https://developer.github.com/v3/#client-errors
