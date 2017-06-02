import asyncio
from typing import Mapping, Tuple

import aiohttp

from . import abc as gh_abc


class GitHubAPI(gh_abc.GitHubAPI):

    def __init__(self, session: aiohttp.ClientSession, *args, **kwargs) -> None:
        self._session = session
        super().__init__(*args, **kwargs)

    async def _request(self, method: str, url: str, headers: Mapping,
                       body: bytes = b'') -> Tuple[int, Mapping, bytes]:
        async with self._session.request(method, url, headers=headers,
                                         data=body) as response:
            return response.status, response.headers, await response.read()

    async def sleep(self, seconds: float) -> None:
        await asyncio.sleep(seconds)
