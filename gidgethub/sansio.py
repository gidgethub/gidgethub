"""Code to help with HTTP requests, responses, and events from GitHub's developer API.

This code has been constructed to perform no I/O of its own. This allows you to
use any HTTP library you prefer while not having to implement common details
when working with GitHub's API (e.g. validating webhook events or specifying the
API version you want your request to work against).
"""
import hashlib
import hmac
from typing import Any, Dict

from . import exceptions


JSONDict = Dict[str, Any]


def validate(payload: bytes, *, signature: str, secret: str) -> None:
    """Validate that the webhook event body came from an approved repository."""
    # https://developer.github.com/webhooks/securing/#validating-payloads-from-github
    signature_prefix = "sha1="
    if not signature.startswith(signature_prefix):
        raise exceptions.ValidationFailure("signature does not start with "
                                           f"{repr(signature_prefix)}")
    hash_ = hashlib.sha1()
    hash_.update(secret.encode("UTF-8"))
    hash_.update(payload)
    calculated_sig = signature_prefix + hash_.hexdigest()
    if not hmac.compare_digest(signature, calculated_sig):
        raise exceptions.ValidationFailure("payload's signature does not align "
                                           "with the secret")


class Event:

    """Details of a GitHub webhook event."""

    def __init__(self, data: JSONDict, *, event: str, delivery_id: str) -> None:
        # https://developer.github.com/v3/activity/events/types/
        # https://developer.github.com/webhooks/#delivery-headers
        self.data = data
        self.event = event
        self.delivery_id = delivery_id
