"""Code to help with HTTP requests, responses, and events from GitHub's developer API.

This code has been constructed to perform no I/O of its own. This allows you to
use any HTTP library you prefer while not having to implement common details
when working with GitHub's API (e.g. validating webhook events or specifying the
API version you want your request to work against).
"""
import cgi
import datetime
import hashlib
import hmac
import http
import json
import re
from typing import Any, Dict, Mapping, Optional, Tuple
import urllib.parse

import uritemplate

from . import (BadRequest, GitHubBroken, HTTPException, InvalidField,
               RedirectionException, ValidationFailure)


JSONDict = Dict[str, Any]


def validate_event(payload: bytes, *, signature: str, secret: str) -> None:
    """Validate the signature of a webhook event."""
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

        The mapping providing the headers is expected to support lowercase keys.

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
            raise BadRequest(http.HTTPStatus(400), "expected a content-type of "
                                             "'application/json'")
        elif "x-hub-signature" in headers:
                if secret is None:
                    raise ValidationFailure("secret not provided")
                validate_event(body, signature=headers["x-hub-signature"],
                               secret=secret)
        elif secret is not None:
            raise ValidationFailure("signature is missing")
        data = json.loads(body.decode("UTF-8"))
        return cls(data, event=headers["x-github-event"],
                   delivery_id=headers["x-github-delivery"])


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

    The oauth_token allows making an authenticated request. This can be
    important if you need the expanded rate limit provided by an authenticated
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

    The 'limit' attribute specifies the rate of requests per hour the client is
    limited to.

    The 'remaining' attribute specifies how many requests remain within the
    current rate limit that the client can make.

    The reset_datetime attribute is a datetime object representing when
    effectively 'left' resets to 'rate'. The datetime object is timezone-aware
    and set to UTC.

    The boolean value of an instance whether another request can be made. This
    is determined based on whether there are any remaining requests or if the
    reset datetime has passed.
    """

    # https://developer.github.com/v3/#rate-limiting

    def __init__(self, *, limit: int, remaining: int,
                 reset_epoch: float) -> None:
        """Instantiate a RateLimit object.

        The reset_epoch argument should be in seconds since the UTC epoch.
        """
        self.limit = limit
        self.remaining = remaining
        self.reset_datetime = datetime.datetime.fromtimestamp(reset_epoch,
                                                              datetime.timezone.utc)

    def __bool__(self) -> bool:
        """True if requests are remaining or the reset datetime has passed."""
        if self.remaining > 0:
            return True
        else:
            now = datetime.datetime.now(datetime.timezone.utc)
            return now > self.reset_datetime

    @classmethod
    def from_http(cls, headers: Mapping[str, str]) -> "RateLimit":
        """Gather rate limit information from HTTP headers.

        The mapping providing the headers is expected to support lowercase
        keys.
        """
        limit = int(headers["x-ratelimit-limit"])
        remaining = int(headers["x-ratelimit-remaining"])
        reset_epoch = float(headers["x-ratelimit-reset"])
        return cls(limit=limit, remaining=remaining, reset_epoch=reset_epoch)


def _decode_body(content_type: str, body: bytes) -> Any:
    if not len(body) or not content_type:
        return None
    type_, parameters = cgi.parse_header(content_type)
    decoded_body = body.decode(parameters["charset"])
    if type_ == "application/json":
        return json.loads(decoded_body)
    return decoded_body


_link_re = re.compile(r'\<(?P<uri>[^>]+)\>;\s*'
                      r'(?P<param_type>\w+)="(?P<param_value>\w+)"(,\s*)?')

def _next_link(link: Optional[str]) -> Optional[str]:
    # https://developer.github.com/v3/#pagination
    # https://tools.ietf.org/html/rfc5988
    if link is None:
        return None
    for match in _link_re.finditer(link):
        if match.group("param_type") == "rel":
            if match.group("param_value") == "next":
                return match.group("uri")
    else:
        return None


def decipher_response(status_code: int, headers: Mapping[str, str],
                      body: bytes) -> Tuple[Any, RateLimit, str]:
    """Decipher an HTTP response for a GitHub API request.

    The mapping providing the headers is expected to support lowercase keys.

    The parameters of this function correspond to the three main parts
    of an HTTP response: the status code, headers, and body. Assuming
    no errors which lead to an exception being raised, a 3-item tuple
    is returned. The first item is the decoded body (typically a JSON
    object, but possibly None or a string depending on the content
    type of the body). The second item is an instance of RateLimit
    based on what the response specified.

    The last item of the tuple is the URL where to request the next
    part of results. If there are no more results then None is
    returned. Do be aware that the URL can be a URI template and so
    may need to be expanded.

    If the status code is anything other than 200, 201, or 204, then
    an HTTPException is raised.
    """
    data = _decode_body(headers.get("content-type"), body)
    if status_code in {200, 201, 204}:
        return data, RateLimit.from_http(headers), _next_link(headers.get("link"))
    else:
        try:
            message = data["message"]
        except (TypeError, KeyError):
            message = None
        exc_type = HTTPException  # For mypy.
        if status_code == 422:
            errors = data["errors"]
            fields = ", ".join(repr(e["field"]) for e in errors)
            message = f"{message} for {fields}"
            raise InvalidField(errors, message)
        # All the below cases are generic.
        elif status_code >= 500:
            exc_type = GitHubBroken
        elif status_code >= 400:
            exc_type = BadRequest
        elif status_code >= 300:
            exc_type = RedirectionException
        else:
            exc_type = HTTPException
        status_code_enum = http.HTTPStatus(status_code)
        args: Tuple
        if message:
            args = status_code_enum, message
        else:
            args = status_code_enum,
        raise exc_type(*args)


DOMAIN = "https://api.github.com"

def format_url(url: str, url_vars: Dict[str, str]) -> str:
    """Construct a URL for the GitHub API.

    The URL may be absolute or relative. In the latter case the appropriate
    domain will be added. This is to help when copying the relative URL directly
    from the GitHub developer documentation.

    The dict provided in url_vars is used in URI template formatting.
    """
    url = urllib.parse.urljoin(DOMAIN, url)  # Works even if 'url' is fully-qualified.
    return uritemplate.expand(url, var_dict=url_vars)
