from typing import Mapping, Tuple

from twisted.internet import defer
from twisted.web.http_headers import Headers

import treq

from . import abc as gh_abc


class GitHubAPI(gh_abc.GitHubAPI):
    def __init__(self, *args, **kwargs):
        from twisted.internet import reactor
        self._reactor = reactor
        super().__init__(*args, **kwargs)

    async def _request(self, method: str, url: str,
                       headers: Mapping[str, str],
                       body: bytes = b'') -> Tuple[int, Mapping[str, str], bytes]:
        # We need to encode the headers to a format that Twisted will like.
        headers = Headers(
            {k.encode('utf-8'): [v.encode('utf-8')] for k, v in headers.items()}
        )
        response = await treq.request(method, url, headers=headers, data=body)

        # We need to map the headers back now. In the future, we should fix
        # this up so that any header that appears more than once is handled
        # appropriately.
        response_headers = {
            k.decode('utf-8').lower(): v[0].decode('utf-8')
            for k, v in response.headers.getAllRawHeaders()
        }
        return response.code, response_headers, await response.content()

    async def _sleep(self, seconds: float) -> None:
        d = defer.Deferred()
        self._reactor.callLater(seconds, d.callback, None)
        await d
