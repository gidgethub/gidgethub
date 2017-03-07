import asyncio
from typing import Mapping, Tuple

import aiohttp

from . import abc as gh_abc


class GitHubAPI(gh_abc.GitHubAPI):

    def __init__(self, session: aiohttp.ClientSession, requester: str, *,
                 oauth_token: str = None) -> None:
        self._session = session
        super().__init__(requester, oauth_token=oauth_token)

    async def _request(self, method: str, url: str,
                       headers: Mapping[str, str],
                       body: bytes = b'') -> Tuple[int, Mapping[str, str], bytes]:
        async with self._session.request(method, url, headers=headers,
                                         data=body) as response:
            return response.status, response.headers, await response.read()

    async def _sleep(self, seconds: float) -> None:
        await asyncio.sleep(seconds)
