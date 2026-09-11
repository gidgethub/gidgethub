"""Provide an abstract base class for easier requests."""

from __future__ import annotations

import abc
import http
import json
from collections.abc import AsyncGenerator, Mapping, MutableMapping
from typing import Any, Optional

from uritemplate import variable

from . import (
    BadGraphQLRequest,
    GitHubBroken,
    GraphQLAuthorizationFailure,
    GraphQLException,
    GraphQLResponseTypeError,
    HTTPException,
    QueryError,
    sansio,
)

# Value represents etag, last-modified, data, and next page.
CACHE_TYPE = MutableMapping[
    str, tuple[Optional[str], Optional[str], Any, Optional[str]]
]

JSON_CONTENT_TYPE = "application/json"
UTF_8_CHARSET = "utf-8"
JSON_UTF_8_CHARSET = f"{JSON_CONTENT_TYPE}; charset={UTF_8_CHARSET}"
ITERABLE_KEY = "items"


class GitHubAPI(abc.ABC):
    """Provide an idiomatic API for making calls to GitHub's API."""

    requester: str
    oauth_token: str | None
    _cache: CACHE_TYPE | None
    base_url: str
    rate_limit: sansio.RateLimit | None
    requests_in_flight: int

    def __init__(
        self,
        requester: str,
        *,
        oauth_token: str | None = None,
        cache: CACHE_TYPE | None = None,
        base_url: str = sansio.DOMAIN,
    ) -> None:
        self.requester = requester
        self.oauth_token = oauth_token
        self._cache = cache
        self.rate_limit: sansio.RateLimit | None = None
        self.base_url = base_url
        self.requests_in_flight = 0

    @abc.abstractmethod
    async def _request(
        self, method: str, url: str, headers: Mapping[str, str], body: bytes = b""
    ) -> tuple[int, Mapping[str, str], bytes]:
        """Make an HTTP request."""

    @abc.abstractmethod
    async def sleep(self, seconds: float) -> None:
        """Sleep for the specified number of seconds."""

    async def manage_rate_limit(
        self,
        *,
        method: str,
        url: str,
        rate_limit: sansio.RateLimit | None,
        requests_in_flight: int,
    ) -> None:
        """Hook called before each HTTP request to allow custom rate-limit
        or backpressure handling (e.g. sleeping until quota resets).

        The default implementation is a no-op. Subclasses can override this
        to implement custom strategies such as sleeping until
        ``rate_limit.reset_datetime``, throttling based on
        *requests_in_flight*, or anything else appropriate for their use
        case.

        Note that *requests_in_flight* (and :attr:`requests_in_flight`) is
        incremented before this hook is called and decremented only once
        the underlying HTTP request has completed (or raised an exception).
        As such, it counts the request as "in flight" for the entire
        duration of this call, including any time spent waiting inside
        ``manage_rate_limit()`` itself.
        """

    async def _make_request(
        self,
        method: str,
        url: str,
        url_vars: Mapping[str, variable.VariableValue] | None,
        data: Any,
        accept: str,
        jwt: str | None = None,
        oauth_token: str | None = None,
        content_type: str = JSON_CONTENT_TYPE,
        extra_headers: dict[str, str] | None = None,
    ) -> tuple[bytes, str | None, int]:
        """Construct and make an HTTP request."""
        if oauth_token is not None and jwt is not None:
            raise ValueError("Cannot pass both oauth_token and jwt.")
        filled_url = sansio.format_url(url, url_vars, base_url=self.base_url)
        if jwt is not None:
            request_headers = sansio.create_headers(
                self.requester, accept=accept, jwt=jwt
            )
        elif oauth_token is not None:
            request_headers = sansio.create_headers(
                self.requester, accept=accept, oauth_token=oauth_token
            )
        else:
            # fallback to using oauth_token
            request_headers = sansio.create_headers(
                self.requester, accept=accept, oauth_token=self.oauth_token
            )
        if extra_headers is not None:
            request_headers.update(extra_headers)
        cached = cacheable = False
        more: str | None = None
        # Can't use None as a "no body" sentinel as it's a legitimate JSON type.
        if data == b"":
            body = b""
            request_headers["content-length"] = "0"
            if method == "GET" and self._cache is not None:
                cacheable = True
                try:
                    etag, last_modified, data, more = self._cache[filled_url]
                    cached = True
                except KeyError:
                    pass
                else:
                    if etag is not None:
                        request_headers["if-none-match"] = etag
                    if last_modified is not None:
                        request_headers["if-modified-since"] = last_modified
        else:
            if content_type != JSON_CONTENT_TYPE:
                # We don't know how to handle other content types, so just pass things along.
                request_headers["content-type"] = content_type
                body = data
            else:
                # Since JSON is so common, add some niceties.
                body = json.dumps(data).encode(UTF_8_CHARSET)
                request_headers["content-type"] = JSON_UTF_8_CHARSET
            request_headers["content-length"] = str(len(body))
        if self.rate_limit is not None:
            self.rate_limit.remaining -= 1
        self.requests_in_flight += 1
        try:
            await self.manage_rate_limit(
                method=method,
                url=filled_url,
                rate_limit=self.rate_limit,
                requests_in_flight=self.requests_in_flight,
            )
            response = await self._request(method, filled_url, request_headers, body)
        finally:
            self.requests_in_flight -= 1
        if not (response[0] == 304 and cached):
            data, self.rate_limit, more = sansio.decipher_response(*response)
            has_cache_details = "etag" in response[1] or "last-modified" in response[1]
            if self._cache is not None and cacheable and has_cache_details:
                etag = response[1].get("etag")
                last_modified = response[1].get("last-modified")
                self._cache[filled_url] = etag, last_modified, data, more
        return data, more, response[0]

    async def getitem(
        self,
        url: str,
        url_vars: Mapping[str, variable.VariableValue] | None = {},
        *,
        accept: str = sansio.accept_format(),
        jwt: str | None = None,
        oauth_token: str | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> Any:
        """Send a GET request for a single item to the specified endpoint."""

        data, _, _ = await self._make_request(
            "GET",
            url,
            url_vars,
            b"",
            accept,
            jwt=jwt,
            oauth_token=oauth_token,
            extra_headers=extra_headers,
        )
        return data

    async def getstatus(
        self,
        url: str,
        url_vars: Mapping[str, variable.VariableValue] | None = {},
        *,
        accept: str = sansio.accept_format(),
        jwt: str | None = None,
        oauth_token: str | None = None,
    ) -> int:
        """Send a GET request for a single item to the specifie endpoint and return its status code."""

        try:
            _, _, status_code = await self._make_request(
                "GET", url, url_vars, b"", accept, jwt=jwt, oauth_token=oauth_token
            )
        except HTTPException as e:
            status_code = e.status_code

        return status_code

    async def getiter(
        self,
        url: str,
        url_vars: Mapping[str, variable.VariableValue] | None = {},
        *,
        accept: str = sansio.accept_format(),
        jwt: str | None = None,
        oauth_token: str | None = None,
        extra_headers: dict[str, str] | None = None,
        iterable_key: str | None = ITERABLE_KEY,
    ) -> AsyncGenerator[Any, None]:
        """Return an async iterable for all the items at a specified endpoint."""
        current_url: str | None = url
        while current_url:
            data, current_url, _ = await self._make_request(
                "GET",
                current_url,
                url_vars,
                b"",
                accept,
                jwt=jwt,
                oauth_token=oauth_token,
                extra_headers=extra_headers,
            )

            if isinstance(data, dict) and iterable_key in data:
                data = data[iterable_key]
            for item in data:
                yield item

    async def post(
        self,
        url: str,
        url_vars: Mapping[str, variable.VariableValue] | None = {},
        *,
        data: Any,
        accept: str = sansio.accept_format(),
        jwt: str | None = None,
        oauth_token: str | None = None,
        extra_headers: dict[str, str] | None = None,
        content_type: str = JSON_CONTENT_TYPE,
    ) -> Any:
        data, _, _ = await self._make_request(
            "POST",
            url,
            url_vars,
            data,
            accept,
            jwt=jwt,
            oauth_token=oauth_token,
            content_type=content_type,
            extra_headers=extra_headers,
        )
        return data

    async def patch(
        self,
        url: str,
        url_vars: Mapping[str, variable.VariableValue] | None = {},
        *,
        data: Any,
        accept: str = sansio.accept_format(),
        jwt: str | None = None,
        oauth_token: str | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> Any:
        data, _, _ = await self._make_request(
            "PATCH",
            url,
            url_vars,
            data,
            accept,
            jwt=jwt,
            oauth_token=oauth_token,
            extra_headers=extra_headers,
        )
        return data

    async def put(
        self,
        url: str,
        url_vars: Mapping[str, variable.VariableValue] | None = {},
        *,
        data: Any = b"",
        accept: str = sansio.accept_format(),
        jwt: str | None = None,
        oauth_token: str | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> Any:
        data, _, _ = await self._make_request(
            "PUT",
            url,
            url_vars,
            data,
            accept,
            jwt=jwt,
            oauth_token=oauth_token,
            extra_headers=extra_headers,
        )
        return data

    async def delete(
        self,
        url: str,
        url_vars: Mapping[str, variable.VariableValue] | None = {},
        *,
        data: Any = b"",
        accept: str = sansio.accept_format(),
        jwt: str | None = None,
        oauth_token: str | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        await self._make_request(
            "DELETE",
            url,
            url_vars,
            data,
            accept,
            jwt=jwt,
            oauth_token=oauth_token,
            extra_headers=extra_headers,
        )

    async def graphql(
        self,
        query: str,
        *,
        endpoint: str = "https://api.github.com/graphql",
        **variables: Any,
    ) -> Any:
        """Query the GraphQL v4 API.

        The *endpoint* argument specifies the endpoint URL to use. The
        *variables* kwargs-style argument collects all variables for the query.
        """
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables
        request_data = json.dumps(payload).encode("utf-8")
        request_headers = sansio.create_headers(
            self.requester, accept=JSON_UTF_8_CHARSET, oauth_token=self.oauth_token
        )
        request_headers.update(
            {
                "content-type": JSON_UTF_8_CHARSET,
                "content-length": str(len(request_data)),
            }
        )
        status_code, response_headers, response_data = await self._request(
            "POST", endpoint, request_headers, request_data
        )

        if not response_data:
            raise GraphQLException("Response contained no data", response_data)

        # Decode content.
        resp_content_type = response_headers.get("content-type")
        type_, encoding = sansio._parse_content_type(resp_content_type)
        response_str = response_data.decode(encoding)
        if type_ == "application/json":
            response: dict[str, Any] = json.loads(response_str)
        else:
            raise GraphQLResponseTypeError(resp_content_type, response_str)

        if status_code >= 500:
            raise GitHubBroken(http.HTTPStatus(status_code))
        elif status_code == 401:
            raise GraphQLAuthorizationFailure(response)
        elif status_code >= 400:
            # 400 corresponds to malformed JSON, but that should never receive
            # that as a response as json.dumps() should have raised its own
            # exception before we made the request.
            raise BadGraphQLRequest(http.HTTPStatus(status_code), response)
        elif status_code == 200:
            self.rate_limit = sansio.RateLimit.from_http(response_headers)
            if "errors" in response:
                raise QueryError(response)
            if "data" in response:
                return response["data"]
            else:
                raise GraphQLException(
                    f"Response did not contain 'errors' or 'data': {response}", response
                )
        else:
            raise GraphQLException(
                f"Unexpected HTTP response to GraphQL request: {status_code}", response
            )
