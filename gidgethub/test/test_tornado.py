import datetime

import pytest

from .. import BadRequest
from .. import sansio
from .. import tornado as gh_tornado


async def test_sleep():
    delay = 1
    start = datetime.datetime.now()
    gh = gh_tornado.GitHubAPI("gidgethub")
    await gh.sleep(delay)
    stop = datetime.datetime.now()
    assert (stop - start) > datetime.timedelta(seconds=delay)


async def test__request():
    """Make sure that that abstract method is implemented properly."""
    request_headers = sansio.create_headers("gidgethub")
    gh = gh_tornado.GitHubAPI("gidgethub")
    tornado_call = await gh._request("GET", "https://api.github.com/rate_limit",
                                     request_headers)
    data, rate_limit, _ = sansio.decipher_response(*tornado_call)
    assert "rate" in data


async def test__request_with_body():
    """Make sure that that abstract method is implemented properly."""
    request_headers = sansio.create_headers("gidgethub")
    gh = gh_tornado.GitHubAPI("gidgethub")
    # This leads to a 404.
    tornado_call = await gh._request("POST", "https://api.github.com/rate_limit",
                                     request_headers, b'bogus')
    with pytest.raises(BadRequest):
        sansio.decipher_response(*tornado_call)


async def test_get():
    """Integration test."""
    gh = gh_tornado.GitHubAPI("gidgethub")
    data = await gh.getitem("/rate_limit")
    assert "rate" in data
