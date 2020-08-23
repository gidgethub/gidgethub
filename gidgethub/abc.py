"""Provide an abstract base class for easier requests."""
import abc
import http
import json
from typing import Any, AsyncGenerator, Dict, Mapping, MutableMapping, Tuple
from typing import Optional as Opt

from . import (
    BadGraphQLRequest,
    GitHubBroken,
    GraphQLAuthorizationFailure,
    GraphQLException,
    QueryError,
    GraphQLResponseTypeError,
)
from . import sansio


# Value represents etag, last-modified, data, and next page.
CACHE_TYPE = MutableMapping[str, Tuple[Opt[str], Opt[str], Any, Opt[str]]]

JSON_CONTENT_TYPE = "application/json"
UTF_8_CHARSET = "utf-8"
JSON_UTF_8_CHARSET = f"{JSON_CONTENT_TYPE}; charset={UTF_8_CHARSET}"


class GitHubAPI(abc.ABC):

    """Provide an idiomatic API for making calls to GitHub's API."""

    def __init__(
        self,
        requester: str,
        *,
        oauth_token: Opt[str] = None,
        cache: Opt[CACHE_TYPE] = None,
        base_url: str = sansio.DOMAIN,
    ) -> None:
        self.requester = requester
        self.oauth_token = oauth_token
        self._cache = cache
        self.rate_limit: Opt[sansio.RateLimit] = None
        self.base_url = base_url

    @abc.abstractmethod
    async def _request(
        self, method: str, url: str, headers: Mapping[str, str], body: bytes = b""
    ) -> Tuple[int, Mapping[str, str], bytes]:
        """Make an HTTP request."""

    @abc.abstractmethod
    async def sleep(self, seconds: float) -> None:
        """Sleep for the specified number of seconds."""

    async def _make_request(
        self,
        method: str,
        url: str,
        url_vars: Dict[str, str],
        data: Any,
        accept: str,
        jwt: Opt[str] = None,
        oauth_token: Opt[str] = None,
        content_type: str = JSON_CONTENT_TYPE,
    ) -> Tuple[bytes, Opt[str]]:
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
        cached = cacheable = False
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
        response = await self._request(method, filled_url, request_headers, body)
        if not (response[0] == 304 and cached):
            data, self.rate_limit, more = sansio.decipher_response(*response)
            has_cache_details = "etag" in response[1] or "last-modified" in response[1]
            if self._cache is not None and cacheable and has_cache_details:
                etag = response[1].get("etag")
                last_modified = response[1].get("last-modified")
                self._cache[filled_url] = etag, last_modified, data, more
        return data, more

    async def getitem(
        self,
        url: str,
        url_vars: Dict[str, str] = {},
        *,
        accept: str = sansio.accept_format(),
        jwt: Opt[str] = None,
        oauth_token: Opt[str] = None,
    ) -> Any:
        """Send a GET request for a single item to the specified endpoint."""

        data, _ = await self._make_request(
            "GET", url, url_vars, b"", accept, jwt=jwt, oauth_token=oauth_token
        )
        return data

    async def getiter(
        self,
        url: str,
        url_vars: Dict[str, str] = {},
        *,
        accept: str = sansio.accept_format(),
        jwt: Opt[str] = None,
        oauth_token: Opt[str] = None,
    ) -> AsyncGenerator[Any, None]:
        """Return an async iterable for all the items at a specified endpoint."""
        data, more = await self._make_request(
            "GET", url, url_vars, b"", accept, jwt=jwt, oauth_token=oauth_token
        )

        if isinstance(data, dict) and "items" in data:
            data = data["items"]

        for item in data:
            yield item
        if more:
            # `yield from` is not supported in coroutines.
            async for item in self.getiter(
                more, url_vars, accept=accept, jwt=jwt, oauth_token=oauth_token
            ):
                yield item

    async def post(
        self,
        url: str,
        url_vars: Dict[str, str] = {},
        *,
        data: Any,
        accept: str = sansio.accept_format(),
        jwt: Opt[str] = None,
        oauth_token: Opt[str] = None,
        content_type: str = JSON_CONTENT_TYPE,
    ) -> Any:
        data, _ = await self._make_request(
            "POST",
            url,
            url_vars,
            data,
            accept,
            jwt=jwt,
            oauth_token=oauth_token,
            content_type=content_type,
        )
        return data

    async def patch(
        self,
        url: str,
        url_vars: Dict[str, str] = {},
        *,
        data: Any,
        accept: str = sansio.accept_format(),
        jwt: Opt[str] = None,
        oauth_token: Opt[str] = None,
    ) -> Any:
        data, _ = await self._make_request(
            "PATCH", url, url_vars, data, accept, jwt=jwt, oauth_token=oauth_token
        )
        return data

    async def put(
        self,
        url: str,
        url_vars: Dict[str, str] = {},
        *,
        data: Any = b"",
        accept: str = sansio.accept_format(),
        jwt: Opt[str] = None,
        oauth_token: Opt[str] = None,
    ) -> Any:
        data, _ = await self._make_request(
            "PUT", url, url_vars, data, accept, jwt=jwt, oauth_token=oauth_token
        )
        return data

    async def delete(
        self,
        url: str,
        url_vars: Dict[str, str] = {},
        *,
        data: Any = b"",
        accept: str = sansio.accept_format(),
        jwt: Opt[str] = None,
        oauth_token: Opt[str] = None,
    ) -> None:
        await self._make_request(
            "DELETE", url, url_vars, data, accept, jwt=jwt, oauth_token=oauth_token
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
        payload: Dict[str, Any] = {"query": query}
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
            response: Dict[str, Any] = json.loads(response_str)
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
