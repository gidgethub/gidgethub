import datetime

import aiohttp
import pytest

from .test_abc import call_async
from .. import aiohttp as gh_aiohttp
from .. import sansio


async def call_aiohttp(what, *args, **kwargs):
    async with aiohttp.ClientSession() as session:
        gh = gh_aiohttp.GitHubAPI(session, "gidgethub")
        return await getattr(gh, what)(*args, **kwargs)


def test_sleep(call_async):
    delay = 1
    start = datetime.datetime.now()
    call_async(call_aiohttp("_sleep", delay))
    stop = datetime.datetime.now()
    assert (stop - start) > datetime.timedelta(seconds=delay)


def test_request(call_async):
    request_headers = sansio.create_headers("gidgethub")
    aio_call = call_aiohttp("_request", "GET",
                            "https://api.github.com/rate_limit", request_headers)
    data, rate_limit, _ = sansio.decipher_response(*call_async(aio_call))
    assert "rate" in data
