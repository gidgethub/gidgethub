import datetime

import aiohttp
import pytest

from gidgethub import aiohttp as gh_aiohttp
from gidgethub import sansio


@pytest.mark.asyncio
async def test_sleep():
    delay = 1
    start = datetime.datetime.now()
    async with aiohttp.ClientSession() as session:
        gh = gh_aiohttp.GitHubAPI(session, "gidgethub")
        await gh.sleep(delay)
    stop = datetime.datetime.now()
    assert (stop - start) > datetime.timedelta(seconds=delay)


@pytest.mark.asyncio
async def test__request():
    """Make sure that that abstract method is implemented properly."""
    request_headers = sansio.create_headers("gidgethub")
    async with aiohttp.ClientSession() as session:
        gh = gh_aiohttp.GitHubAPI(session, "gidgethub")
        aio_call = await gh._request(
            "GET", "https://api.github.com/rate_limit", request_headers
        )
    data, rate_limit, _ = sansio.decipher_response(*aio_call)
    assert "rate" in data


@pytest.mark.asyncio
async def test_get():
    """Integration test."""
    async with aiohttp.ClientSession() as session:
        gh = gh_aiohttp.GitHubAPI(session, "gidgethub")
        data = await gh.getitem("/rate_limit")
    assert "rate" in data
