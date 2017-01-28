"""Code to help with HTTP requests, responses, and events from GitHub's developer API.

This code has been constructed to perform no I/O of its own. This allows you to
use any HTTP library you prefer while not having to implement common details
when working with GitHub's API (e.g. validating webhook events or specifying the
API version you want your request to work against).
"""
import datetime
import hashlib
import hmac
import json
from typing import Any, Dict, Mapping

from . import BadRequest, ValidationFailure


JSONDict = Dict[str, Any]


def validate_event(payload: bytes, *, signature: str, secret: str) -> None:
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
                validate_event(body, signature=headers["X-Hub-Signature"],
                               secret=secret)
        elif secret is not None:
            raise ValidationFailure("signature is missing")
        data = json.loads(body.decode("UTF-8"))
        return cls(data, event=headers["X-GitHub-Event"],
                   delivery_id=headers["X-GitHub-Delivery"])


def accept_format(*, version: str = "v3", media: str = None,
                  json: bool = True) -> str:
    """Construct the specification of the format that a request should return.

    The version argument defaults to v3 of the GitHub API and is applicable to
    all requests. The media argument along with 'json' specifies what format
    the request should return, e.g. requesting the rendered HTML of a comment.
    Do note that not all of GitHub's API supports alternative formats.

    The default arguments of this function will always return the latest stable
    version of the GitHub API in the default format that this library is
    designed to support.
    """
    # https://developer.github.com/v3/media/
    # https://developer.github.com/v3/#current-version
    accept = f"application/vnd.github.{version}"
    if media is not None:
        accept += f".{media}"
    if json:
        accept += "+json"
    return accept


def create_headers(requester: str, *,
                   accept: str = accept_format(),
                   oauth_token: str = None) -> Dict[str, str]:
    """Create a dict representing GitHub-specific header fields.

    The user agent is set according to who the requester is. GitHub asks it be
    either a username or project name.

    The 'accept' argument corresponds to the 'accept' field and defaults to the
    default result of accept_format(). You should only need to change this value
    if you are using a different version of the API -- e.g. one that is under
    development -- or if you are looking for a different format return type,
    e.g. wanting the rendered HTML of a Markdown file.

    The oauth_token allows making an authetnicated request. This can be
    important if you need the extended rate limit provided by an authenticated
    request.

    For consistency, all keys in the returned dict will be lowercased.
    """
    # user-agent: https://developer.github.com/v3/#user-agent-required
    # accept: https://developer.github.com/v3/#current-version
    #         https://developer.github.com/v3/media/
    # authorization: https://developer.github.com/v3/#authentication
    headers = {"user-agent": requester, "accept": accept}
    if oauth_token is not None:
        headers["authorization"] = f"token {oauth_token}"
    return headers


class RateLimit:

    """The rate limit imposed upon the requester.

    The 'rate' attribute specifies the rate of requests per hour the client is
    allowed to make.

    The 'left' attribute specifies how many requests are left within the
    current rate limit.

    The reset_datetime attribute is a datetime object representing when
    effectively 'left' resets to 'rate'. The datetime object is timezone-aware
    and set to UTC.
    """

    # https://developer.github.com/v3/#rate-limiting

    def __init__(self, *, rate: int, left: int,
                 reset_epoch: float) -> None:
        """Instantiate a RateLimit object.

        The reset_epoch argument should be in seconds since the UTC epoch.
        """
        self.rate = rate
        self.left = left
        self.reset_datetime = datetime.datetime.fromtimestamp(reset_epoch,
                                                              datetime.timezone.utc)

    @classmethod
    def from_http(cls, headers: Mapping[str, str]) -> "RateLimit":
        """Gather rate limit information from HTTP headers."""
        rate = int(headers["X-RateLimit-Limit"])
        left = int(headers["X-RateLimit-Remaining"])
        reset_epoch = float(headers["X-RateLimit-Reset"])
        return cls(rate=rate, left=left, reset_epoch=reset_epoch)
