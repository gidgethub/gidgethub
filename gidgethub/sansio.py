"""Code to help with HTTP requests, responses, and events from GitHub's developer API.

This code has been constructed to perform no I/O of its own. This allows you to
use any HTTP library you prefer while not having to implement common details
when working with GitHub's API (e.g. validating webhook events or specifying the
API version you want your request to work against).
"""
import hashlib
import hmac
import json
from typing import Any, Dict, Mapping

from . import BadRequest, ValidationFailure


JSONDict = Dict[str, Any]


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
        raise ValidationFailure("payload's signature does not align "
                                           "with the secret")


class Event:

    """Details of a GitHub webhook event."""

    def __init__(self, data: JSONDict, *, event: str, delivery_id: str) -> None:
        # https://developer.github.com/v3/activity/events/types/
        # https://developer.github.com/webhooks/#delivery-headers
        self.data = data
        # Event is not an enum as GitHub provides the string. This allows them
        # to add new events without having to mirror them here. There's also no
        # direct worry of a user typing in the wrong event name and thus no need
        # for an enum's typing protection.
        self.event = event
        self.delivery_id = delivery_id

    @classmethod
    def from_http(cls, headers: Mapping[str, str], body: bytes,
                  *, secret: str = None) -> "Event":
        """Construct an event from HTTP headers and JSON body data.

        Since this method assumes the body of the HTTP request is JSON, a check
        is performed for a content-type of "application/json" (GitHub does
        support other content-types). If the content-type does not match,
        BadRequest is raised.

        If the appropriate headers are provided for event validation, then it
        will be performed unconditionally. Any failure in validation
        (including not providing a secret) will lead to ValidationFailure being
        raised.
        """
        if headers.get("content-type") != "application/json":
            raise BadRequest(400, "expected a content-type of "
                                             "'application/json'")
        if "X-Hub-Signature" in headers:
                if secret is None:
                    raise ValidationFailure("secret not provided")
                validate(body, signature=headers["X-Hub-Signature"],
                         secret=secret)
        elif secret is not None:
            raise ValidationFailure("signature is missing")
        data = json.loads(body.decode("UTF-8"))
        return cls(data, event=headers["X-GitHub-Event"],
                   delivery_id=headers["X-GitHub-Delivery"])


def create_headers(requester: str, *,
                   api_version: str = "application/vnd.github.v3+json",
                   oauth_token: str = None) -> Dict[str, str]:
    """Create a dict representing GitHub-specific header fields.

    The user agent is set according to who the requester is. GitHub asks it be
    either a username or project name.

    The api_version corresponds to the 'accepts' field and defaults to the v3
    version of the API. You should only need to change this value if you are
    using a feature of the API that is under active development by GitHub.

    The oauth_token allows making an authetnicated request. This can be
    important if you need the extended rate limit provided by an authenticated
    request.

    For consistency, all keys in the returned dict will be lowercased.
    """
    # https://developer.github.com/v3/#user-agent-required
    # https://developer.github.com/v3/#current-version
    # https://developer.github.com/v3/#authentication
    headers = {"user-agent": requester, "accept": api_version}
    if oauth_token is not None:
        headers["authorization"] = f"token {oauth_token}"
    return headers
