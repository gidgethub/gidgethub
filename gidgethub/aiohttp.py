import asyncio

import aiohttp

from . import abc as gh_abc


class GitHubAPI(gh_abc.GitHubAPI):

    def __init__(self, session, requester, *, oauth_token=None):
        self._session = session
        super().__init__(requester, oauth_token=oauth_token)

    async def _request(self, method, url, headers, body=b''):
        async with self._session.request(method, url, headers=headers,
                                         data=body) as response:
            return response.status, response.headers, await response.read()

    async def sleep(self, seconds):
        await asyncio.sleep(seconds)
