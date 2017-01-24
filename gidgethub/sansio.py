import hashlib
import hmac
from typing import Any, Dict


JSONDict = Dict[str, Any]


class GitHubException(Exception):

    """Base exception for this library."""


class ValidationFailure(GitHubException):

    """An exception representing failed validation of a webhook event."""
    # https://developer.github.com/webhooks/securing/#validating-payloads-from-github


def validate(payload: bytes, *, signature: str, secret: str) -> None:
    """Validate that the webhook event body came from an approved repository."""
    # https://developer.github.com/webhooks/securing/#validating-payloads-from-github
    signature_prefix = "sha1="
    if not signature.startswith(signature_prefix):
        raise ValidationFailure("signature does not start with "
                                f"{repr(signature_prefix)}")
    hash_ = hashlib.sha1()
    hash_.update(secret.encode("UTF-8"))
    hash_.update(payload)
    calculated_sig = signature_prefix + hash_.hexdigest()
    if not hmac.compare_digest(signature, calculated_sig):
        raise ValidationFailure("payload's signature does not align with the "
                                "secret")


class Event:

    """Details of a GitHub webhook event."""

    def __init__(self, data: JSONDict, *, event: str, delivery_id: str) -> None:
        # https://developer.github.com/v3/activity/events/types/
        # https://developer.github.com/webhooks/#delivery-headers
        self.data = data
        self.event = event
        self.delivery_id = delivery_id
