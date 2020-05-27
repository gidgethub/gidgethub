import datetime

import pytest
import tornado

from tornado.testing import AsyncTestCase

from gidgethub import BadRequest
from gidgethub import sansio
from gidgethub import tornado as gh_tornado


class TornadoTestCase(AsyncTestCase):
    @tornado.testing.gen_test
    async def test_sleep(self):
        delay = 1
        start = datetime.datetime.now()
        gh = gh_tornado.GitHubAPI("gidgethub")
        await gh.sleep(delay)
        stop = datetime.datetime.now()
        assert (stop - start) >= datetime.timedelta(seconds=delay)

    @tornado.testing.gen_test
    async def test__request(self):
        """Make sure that that abstract method is implemented properly."""
        request_headers = sansio.create_headers("gidgethub")
        gh = gh_tornado.GitHubAPI("gidgethub")
        tornado_call = await gh._request(
            "GET", "https://api.github.com/rate_limit", request_headers
        )
        data, rate_limit, _ = sansio.decipher_response(*tornado_call)
        assert "rate" in data

    @tornado.testing.gen_test
    async def test__request_with_body(self):
        """Make sure that that abstract method is implemented properly."""
        request_headers = sansio.create_headers("gidgethub")
        gh = gh_tornado.GitHubAPI("gidgethub")
        # This leads to a 404.
        tornado_call = await gh._request(
            "POST", "https://api.github.com/rate_limit", request_headers, b"bogus"
        )
        with pytest.raises(BadRequest):
            sansio.decipher_response(*tornado_call)

    @tornado.testing.gen_test
    async def test_get(self):
        """Integration test."""
        gh = gh_tornado.GitHubAPI("gidgethub")
        data = await gh.getitem("/rate_limit")
        assert "rate" in data
