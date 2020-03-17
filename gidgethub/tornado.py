from typing import Mapping, Tuple, Union, List, Dict, Any

from tornado import gen
from tornado import httpclient

from . import abc as gh_abc


class GitHubAPI(gh_abc.GitHubAPI):
    async def _request(
        self, method: str, url: str, headers: Mapping[str, str], body: bytes = b""
    ) -> Tuple[int, Mapping[str, str], bytes]:
        """Make an HTTP request."""
        # Setting 'body' to None fails type checking, so only add a 'body' argument if necessary.
        args: List[Union[str, Dict[Any, Any], bytes]] = [url, method, dict(headers)]
        if method != "GET" and body:
            args.append(body)
        # The below line is skipped from mypy because Tornado's HTTPRequest signature
        # requires many types of arguments some of which are internal to it
        # adding all of them to the `args` would be impractical.
        request = httpclient.HTTPRequest(*args)  # type: ignore
        # Since Tornado has designed AsyncHTTPClient to be a singleton, there's
        # no reason not to simply instantiate it every time.
        client = httpclient.AsyncHTTPClient()
        response = await client.fetch(request, raise_error=False)
        return response.code, response.headers, response.body

    async def sleep(self, seconds: float) -> None:
        """Sleep for the specified number of seconds."""
        await gen.sleep(seconds)
