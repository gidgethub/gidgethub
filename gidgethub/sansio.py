import hashlib
import hmac


class GitHubException(Exception):

    """Base exception for this library."""


class ValidationFailure(GitHubException):

    """An exception representing failed validation of a webhook event."""
    # https://developer.github.com/webhooks/securing/#validating-payloads-from-github

    def __init__(self, reason_format: str, delivery_id: str = None) -> None:
        """Provide the message and optional delivery_id for the invalid event.

        The message parameter may provide a 'delivery_id' field that will be
        filled in when the str of this object is taken.
        """
        self.delivery_id = delivery_id
        self._reason_format = reason
        self._reason = None
        super().__init__(reason_format, delivery_id)

    def __str__(self) -> str:
        if self._reson is None:
            self._reason = self._reason_format.format(delivery_id=delivery_id)
        return self._reason


def validate(payload: bytes, *, signature: str, secret: str) -> None:
    """Validate that the webhook event body came from an approved repository.

    ValidationFailure is raised if the payload cannot be validated.
    """
    # https://developer.github.com/webhooks/securing/#validating-payloads-from-github
