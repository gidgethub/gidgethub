import datetime

import httpx
import pytest

from .. import httpx as gh_httpx


@pytest.mark.asyncio
async def test_sleep():
    delay = 1
    start = datetime.datetime.now()
    async with httpx.AsyncClient() as client:
        gh = gh_httpx.GitHubAPI(client, "gidgethub")
        await gh.sleep(delay)
    stop = datetime.datetime.now()
    assert (stop - start) > datetime.timedelta(seconds=delay)
