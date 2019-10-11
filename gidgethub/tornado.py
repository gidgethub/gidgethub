from typing import Mapping, Tuple

from tornado import gen
from tornado import httpclient

from . import abc as gh_abc


class GitHubAPI(gh_abc.GitHubAPI):

    async def _request(self, method: str, url: str, headers: Mapping[str, str],
                       body: bytes = b'') -> Tuple[int, Mapping[str, str], bytes]:
        """Make an HTTP request."""
        # passing body = None raises an error in mypy:
        # Argument 4 to "HTTPRequest" has incompatible type "Optional[bytes]";
        # expected "Union[bytes, str]"
        request = (
            httpclient.HTTPRequest(url, method, dict(headers))
            if method == "GET" and not body else
            httpclient.HTTPRequest(url, method, dict(headers), body)
        )
        # Since Tornado has designed AsyncHTTPClient to be a singleton, there's
        # no reason not to simply instantiate it every time.
        client = httpclient.AsyncHTTPClient()
        response = await client.fetch(request, raise_error=False)
        return response.code, response.headers, response.body

    async def sleep(self, seconds: float) -> None:
        """Sleep for the specified number of seconds."""
        await gen.sleep(seconds)
