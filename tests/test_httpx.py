import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import httpx2 as httpx
else:
    try:
        import httpx2 as httpx
    except ModuleNotFoundError:  # pragma: no cover
        import httpx

import pytest

from gidgethub import httpx as gh_httpx
from gidgethub import sansio


@pytest.mark.asyncio
async def test_sleep():
    delay = 1
    start = datetime.datetime.now(datetime.timezone.utc)
    async with httpx.AsyncClient() as client:
        gh = gh_httpx.GitHubAPI(client, "gidgethub")
        await gh.sleep(delay)
    stop = datetime.datetime.now(datetime.timezone.utc)
    assert (stop - start) > datetime.timedelta(seconds=delay)


@pytest.mark.asyncio
async def test__request():
    """Make sure that that abstract method is implemented properly."""
    request_headers = sansio.create_headers("gidgethub")
    async with httpx.AsyncClient() as client:
        gh = gh_httpx.GitHubAPI(client, "gidgethub")
        aio_call = await gh._request(
            "GET", "https://api.github.com/rate_limit", request_headers
        )
    data, _rate_limit, _ = sansio.decipher_response(*aio_call)
    assert "rate" in data


@pytest.mark.asyncio
async def test_get():
    """Integration test."""
    async with httpx.AsyncClient() as client:
        gh = gh_httpx.GitHubAPI(client, "gidgethub")
        data = await gh.getitem("/rate_limit")
    assert "rate" in data
