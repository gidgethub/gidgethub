import hashlib
import hmac


class GitHubException(Exception):

    """Base exception for this library."""


class ValidationFailure(GitHubException):

    """An exception representing failed validation of a webhook event."""
    # https://developer.github.com/webhooks/securing/#validating-payloads-from-github


def validate(payload: bytes, *, signature: str, secret: str) -> None:
    """Validate that the webhook event body came from an approved repository.

    ValidationFailure is raised if the payload cannot be validated.
    """
    # https://developer.github.com/webhooks/securing/#validating-payloads-from-github
