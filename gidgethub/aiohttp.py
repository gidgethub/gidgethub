import asyncio
from typing import Dict, Tuple

import aiohttp

from . import abc as gh_abc


class GitHubAPI(gh_abc.GitHubAPI):

    def __init__(self, session: aiohttp.ClitnSession, requester: str,
                 *, oauth_token: str = None) -> None:
        self._session = session
        super().__init__(requester, oauth_token=oauth_token)

    async def _request(self, method: str, url: str, headers: Dict,
                       body: bytes = b'') -> Tuple[int, Dict, bytes]:
        async with self._session.request(method, url, headers=headers,
                                         data=body) as response:
            return response.status, response.headers, await response.read()

    async def sleep(self, seconds: float) -> None:
        await asyncio.sleep(seconds)
