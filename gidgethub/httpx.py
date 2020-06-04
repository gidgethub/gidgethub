import asyncio
from typing import Mapping, Tuple, Any

import httpx

from . import abc as gh_abc


class GitHubAPI(gh_abc.GitHubAPI):
    def __init__(self, client: httpx.AsyncClient, *args: Any, **kwargs: Any) -> None:
        self._client = client
        super().__init__(*args, **kwargs)

    async def _request(
        self, method: str, url: str, headers: Mapping[str, str], body: bytes = b""
    ) -> Tuple[int, Mapping[str, str], bytes]:
        """Make an HTTP request."""
        response = await self._client.request(
            method, url, headers=dict(headers), data=body
        )
        return response.status_code, response.headers, response.content

    async def sleep(self, seconds: float) -> None:
        """Sleep for the specified number of seconds."""
        await asyncio.sleep(seconds)
