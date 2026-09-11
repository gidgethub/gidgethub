from collections.abc import Mapping
from tornado import gen, httpclient

from . import abc as gh_abc


class GitHubAPI(gh_abc.GitHubAPI):
    async def _request(
        self, method: str, url: str, headers: Mapping[str, str], body: bytes = b""
    ) -> tuple[int, Mapping[str, str], bytes]:
        """Make an HTTP request."""
        # Setting 'body' to None fails type checking, so only add a 'body' argument if necessary.
        if method != "GET" and body:
            request = httpclient.HTTPRequest(
                url, method=method, headers=dict(headers), body=body
            )
        else:
            request = httpclient.HTTPRequest(url, method=method, headers=dict(headers))
        # Since Tornado has designed AsyncHTTPClient to be a singleton, there's
        # no reason not to simply instantiate it every time.
        client = httpclient.AsyncHTTPClient()
        response = await client.fetch(request, raise_error=False)
        return response.code, response.headers, response.body

    async def sleep(self, seconds: float) -> None:
        """Sleep for the specified number of seconds."""
        await gen.sleep(seconds)
