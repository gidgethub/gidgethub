import datetime

import aiohttp
import pytest

from .. import aiohttp as gh_aiohttp
from .. import sansio


@pytest.mark.asyncio
async def test_sleep():
    delay = 1
    start = datetime.datetime.now()
    async with aiohttp.ClientSession() as session:
        gh = gh_aiohttp.GitHubAPI(session, "gidgethub")
        await gh._sleep(delay)
    stop = datetime.datetime.now()
    assert (stop - start) > datetime.timedelta(seconds=delay)


@pytest.mark.asyncio
async def test_request():
    request_headers = sansio.create_headers("gidgethub")
    async with aiohttp.ClientSession() as session:
        gh = gh_aiohttp.GitHubAPI(session, "gidgethub")
        aio_call = await gh._request("GET", "https://api.github.com/rate_limit",
                                     request_headers)
    data, rate_limit, _ = sansio.decipher_response(*aio_call)
    assert "rate" in data
