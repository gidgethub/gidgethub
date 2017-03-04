import asyncio
import datetime
import json
import types

import pytest

from .. import abc as gh_abc
from .. import sansio


@pytest.fixture
def call_async():
    loop = asyncio.new_event_loop()
    try:
        yield loop.run_until_complete
    finally:
        loop.close()


class MockGitHubAPI(gh_abc.GitHubAPI):

    DEFAULT_HEADERS = {"x-ratelimit-limit": "2", "x-ratelimit-remaining": "1",
                       "x-ratelimit-reset": "0"}

    def __init__(self, status_code=200, headers=DEFAULT_HEADERS, body=b''):
        self._response = status_code, headers, body
        super().__init__("test_abc", oauth_token="oauth token")

    async def _request(self, method, url, headers, body=None):
        """Make an HTTP request."""
        self.method = method
        self.url = url
        self.headers = headers
        self.body = body
        return self._response

    async def _sleep(self, seconds):
        """Sleep for the specified number of seconds."""
        self.slept = seconds


def test_rate_limit(call_async):
    """The sleep() method is called appropriately if the rate limit is hit."""
    # Default rate limit does not block.
    gh = MockGitHubAPI()
    _ = call_async(gh._make_request("GET", "/rate_limit", {}, b'',
                                    sansio.accept_format()))
    assert not hasattr(gh, "slept")
    # No reason to sleep.
    now = datetime.datetime.now(datetime.timezone.utc)
    year_from_now = now + datetime.timedelta(365)
    rate_limit = sansio.RateLimit(limit=2, remaining=1,
                                  reset_epoch=year_from_now.timestamp())
    gh.rate_limit = rate_limit
    _ = call_async(gh._make_request("GET", "/rate_limit", {}, b'',
                                    sansio.accept_format()))
    assert not hasattr(gh, "slept")
    # Expected to sleep.
    rate_limit = sansio.RateLimit(limit=2, remaining=0,
                                  reset_epoch=year_from_now.timestamp())
    gh.rate_limit = rate_limit
    _ = call_async(gh._make_request("GET", "/rate_limit", {}, b'',
                                    sansio.accept_format()))
    assert hasattr(gh, "slept")
    # Enough time has passed since year_from_now was calculated that it's safer
    # to assume that the time left is less then 365 days but more than 364 days.
    assert gh.slept > datetime.timedelta(364).total_seconds()
    assert gh.slept <= datetime.timedelta(365).total_seconds()


def test_url_formatted(call_async):
    """The URL is appropriately formatted."""
    gh = MockGitHubAPI()
    _ = call_async(gh._make_request("GET",
                                    "/users/octocat/following{/other_user}",
                                    {"other_user": "brettcannon"}, b'',
                                    sansio.accept_format()))
    assert gh.url == "https://api.github.com/users/octocat/following/brettcannon"


def test_headers(call_async):
    """Appropriate headers are created."""
    accept = sansio.accept_format()
    gh = MockGitHubAPI()
    _ = call_async(gh._make_request("GET", "/rate_limit", {}, b'', accept))
    assert gh.headers["user-agent"] == "test_abc"
    assert gh.headers["accept"] == accept
    assert gh.headers["authorization"] == "token oauth token"


def test_rate_limit_set(call_async):
    """The rate limit is updated after receiving a response."""
    rate_headers = {"x-ratelimit-limit": "42", "x-ratelimit-remaining": "1",
                    "x-ratelimit-reset": "0"}
    gh = MockGitHubAPI(headers=rate_headers)
    _ = call_async(gh._make_request("GET", "/rate_limit", {}, b'',
                                    sansio.accept_format()))
    assert gh.rate_limit.limit == 42


def test_decoding(call_async):
    """Test that appropriate decoding occurs."""
    original_data = {"hello": "world"}
    headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
    headers['content-type'] = "application/json; charset=UTF-8"
    gh = MockGitHubAPI(headers=headers,
                       body=json.dumps(original_data).encode("utf8"))
    data, _ = call_async(gh._make_request("GET", "/rate_limit", {}, b'',
                                          sansio.accept_format()))
    assert data == original_data


def test_more(call_async):
    """The 'next' link is returned appropriately."""
    headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
    headers['link'] = ("<https://api.github.com/fake?page=2>; "
                       "rel=\"next\"")
    gh = MockGitHubAPI(headers=headers)
    _, more = call_async(gh._make_request("GET", "/fake", {}, b'',
                                          sansio.accept_format()))
    assert more == "https://api.github.com/fake?page=2"


def test_getitem(call_async):
    original_data = {"hello": "world"}
    headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
    headers['content-type'] = "application/json; charset=UTF-8"
    gh = MockGitHubAPI(headers=headers,
                       body=json.dumps(original_data).encode("utf8"))
    data = call_async(gh.getitem("/fake"))
    assert data == original_data
