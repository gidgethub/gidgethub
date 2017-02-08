import http
from typing import Any


class GitHubException(Exception):

    """Base exception for this library."""


class ValidationFailure(GitHubException):

    """An exception representing failed validation of a webhook event."""
    # https://developer.github.com/webhooks/securing/#validating-payloads-from-github


class HTTPException(GitHubException):

    """A general exception to represent HTTP responses."""

    def __init__(self, status_code: http.HTTPStatus, *args: Any) -> None:
        self.status_code = status_code
        if args:
            super().__init__(*args)
        else:
            super().__init__(status_code.phrase)


class RedirectionException(HTTPException):

    """Exception for 3XX HTTP responses."""


class BadRequest(HTTPException):
    """The request is invalid.

    Used for 4XX HTTP errors.
    """
    # https://developer.github.com/v3/#client-errors


class InvalidField(BadRequest):

    """A field in the request is invalid.

    GitHub responds with a 422 HTTP response and details in the body.
    (https://developer.github.com/v3/#client-errors)
    """

    # resource: str
    # field: str
    # error_code: str

    def __init__(self, resource: str, field: str, error_code: str,
                 *args: Any) -> None:
        """Store the error details."""


class GitHubBroken(HTTPException):

    """Exception for 5XX HTTP responses."""
