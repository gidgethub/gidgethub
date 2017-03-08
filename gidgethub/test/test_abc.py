import asyncio
import datetime
import json
import types

import pytest

from .. import abc as gh_abc
from .. import sansio


class MockGitHubAPI(gh_abc.GitHubAPI):

    DEFAULT_HEADERS = {"x-ratelimit-limit": "2", "x-ratelimit-remaining": "1",
                       "x-ratelimit-reset": "0"}

    def __init__(self, status_code=200, headers=DEFAULT_HEADERS, body=b''):
        self.response_code = status_code
        self.response_headers = headers
        self.response_body = body
        super().__init__("test_abc", oauth_token="oauth token")

    async def _request(self, method, url, headers, body=b''):
        """Make an HTTP request."""
        self.method = method
        self.url = url
        self.headers = headers
        self.body = body
        response_headers = self.response_headers.copy()
        try:
            # Don't loop forever.
            del self.response_headers["link"]
        except KeyError:
            pass
        return self.response_code, response_headers, self.response_body

    async def _sleep(self, seconds):
        """Sleep for the specified number of seconds."""
        self.slept = seconds


@pytest.mark.asyncio
async def test_rate_limit():
    """The sleep() method is called appropriately if the rate limit is hit."""
    # Default rate limit does not block.
    gh = MockGitHubAPI()
    await gh._make_request("GET", "/rate_limit", {}, "", sansio.accept_format())
    assert not hasattr(gh, "slept")
    # No reason to sleep.
    now = datetime.datetime.now(datetime.timezone.utc)
    year_from_now = now + datetime.timedelta(365)
    rate_limit = sansio.RateLimit(limit=2, remaining=1,
                                  reset_epoch=year_from_now.timestamp())
    gh.rate_limit = rate_limit
    await gh._make_request("GET", "/rate_limit", {}, "", sansio.accept_format())
    assert not hasattr(gh, "slept")
    # Expected to sleep.
    rate_limit = sansio.RateLimit(limit=2, remaining=0,
                                  reset_epoch=year_from_now.timestamp())
    gh.rate_limit = rate_limit
    await gh._make_request("GET", "/rate_limit", {}, "", sansio.accept_format())
    assert hasattr(gh, "slept")
    # Enough time has passed since year_from_now was calculated that it's safer
    # to assume that the time left is less then 365 days but more than 364 days.
    assert gh.slept > datetime.timedelta(364).total_seconds()
    assert gh.slept <= datetime.timedelta(365).total_seconds()


@pytest.mark.asyncio
async def test_url_formatted():
    """The URL is appropriately formatted."""
    gh = MockGitHubAPI()
    await gh._make_request("GET", "/users/octocat/following{/other_user}",
                           {"other_user": "brettcannon"}, "",
                           sansio.accept_format())
    assert gh.url == "https://api.github.com/users/octocat/following/brettcannon"


@pytest.mark.asyncio
async def test_headers():
    """Appropriate headers are created."""
    accept = sansio.accept_format()
    gh = MockGitHubAPI()
    await gh._make_request("GET", "/rate_limit", {}, "", accept)
    assert gh.headers["user-agent"] == "test_abc"
    assert gh.headers["accept"] == accept
    assert gh.headers["authorization"] == "token oauth token"


@pytest.mark.asyncio
async def test_rate_limit_set():
    """The rate limit is updated after receiving a response."""
    rate_headers = {"x-ratelimit-limit": "42", "x-ratelimit-remaining": "1",
                    "x-ratelimit-reset": "0"}
    gh = MockGitHubAPI(headers=rate_headers)
    await gh._make_request("GET", "/rate_limit", {}, "", sansio.accept_format())
    assert gh.rate_limit.limit == 42


@pytest.mark.asyncio
async def test_decoding():
    """Test that appropriate decoding occurs."""
    original_data = {"hello": "world"}
    headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
    headers['content-type'] = "application/json; charset=utf-8"
    gh = MockGitHubAPI(headers=headers,
                       body=json.dumps(original_data).encode("utf8"))
    data, _ = await gh._make_request("GET", "/rate_limit", {}, '',
                                          sansio.accept_format())
    assert data == original_data


@pytest.mark.asyncio
async def test_more():
    """The 'next' link is returned appropriately."""
    headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
    headers['link'] = ("<https://api.github.com/fake?page=2>; "
                       "rel=\"next\"")
    gh = MockGitHubAPI(headers=headers)
    _, more = await gh._make_request("GET", "/fake", {}, "",
                                          sansio.accept_format())
    assert more == "https://api.github.com/fake?page=2"


@pytest.mark.asyncio
async def test_getitem():
    original_data = {"hello": "world"}
    headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
    headers['content-type'] = "application/json; charset=UTF-8"
    gh = MockGitHubAPI(headers=headers,
                       body=json.dumps(original_data).encode("utf8"))
    data = await gh.getitem("/fake")
    assert gh.method == "GET"
    assert data == original_data


@pytest.mark.asyncio
async def test_getiter():
    """Test that getiter() returns an async iterable as well as URI expansion."""
    original_data = [1, 2]
    next_url = "https://api.github.com/fake{/extra}?page=2"
    headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
    headers['content-type'] = "application/json; charset=UTF-8"
    headers["link"] = f'<{next_url}>; rel="next"'
    gh = MockGitHubAPI(headers=headers,
                       body=json.dumps(original_data).encode("utf8"))
    data = []
    async for item in gh.getiter("/fake", {"extra": "stuff"}):
        data.append(item)
    assert gh.method == "GET"
    assert gh.url == "https://api.github.com/fake/stuff?page=2"
    assert len(data) == 4
    assert data[0] == 1
    assert data[1] == 2
    assert data[2] == 1
    assert data[3] == 2


@pytest.mark.asyncio
async def test_post():
    send = [1, 2, 3]
    send_json = json.dumps(send).encode("utf-8")
    receive = {"hello": "world"}
    headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
    headers['content-type'] = "application/json; charset=utf-8"
    gh = MockGitHubAPI(headers=headers,
                       body=json.dumps(receive).encode("utf-8"))
    data = await gh.post("/fake", data=send)
    assert gh.method == "POST"
    assert gh.headers['content-type'] == "application/json; charset=utf-8"
    assert gh.body == send_json
    assert gh.headers['content-length'] == str(len(send_json))


@pytest.mark.asyncio
async def test_patch():
    send = [1, 2, 3]
    send_json = json.dumps(send).encode("utf-8")
    receive = {"hello": "world"}
    headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
    headers['content-type'] = "application/json; charset=utf-8"
    gh = MockGitHubAPI(headers=headers,
                       body=json.dumps(receive).encode("utf-8"))
    data = await gh.patch("/fake", data=send)
    assert gh.method == "PATCH"
    assert gh.headers['content-type'] == "application/json; charset=utf-8"
    assert gh.body == send_json
    assert gh.headers['content-length'] == str(len(send_json))


@pytest.mark.asyncio
async def test_put():
    send = [1, 2, 3]
    send_json = json.dumps(send).encode("utf-8")
    receive = {"hello": "world"}
    headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
    headers['content-type'] = "application/json; charset=utf-8"
    gh = MockGitHubAPI(headers=headers,
                       body=json.dumps(receive).encode("utf-8"))
    data = await gh.put("/fake", data=send)
    assert gh.method == "PUT"
    assert gh.headers['content-type'] == "application/json; charset=utf-8"
    assert gh.body == send_json
    assert gh.headers['content-length'] == str(len(send_json))


@pytest.mark.asyncio
async def test_delete():
    gh = MockGitHubAPI()
    data = await gh.delete("/fake")
    assert gh.method == "DELETE"
    assert data is None
