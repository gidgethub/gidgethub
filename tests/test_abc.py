import http
import json
import re
from typing import ClassVar
from unittest import mock

import importlib_resources
import pytest

from gidgethub import (
    BadGraphQLRequest,
    BadRequest,
    GitHubBroken,
    GraphQLAuthorizationFailure,
    GraphQLException,
    GraphQLResponseTypeError,
    QueryError,
    RedirectionException,
    sansio,
)
from gidgethub import abc as gh_abc
from gidgethub.abc import JSON_UTF_8_CHARSET

from .samples import GraphQL as graphql_samples


class MockGitHubAPI(gh_abc.GitHubAPI):
    DEFAULT_HEADERS: ClassVar = {
        "x-ratelimit-limit": "2",
        "x-ratelimit-remaining": "1",
        "x-ratelimit-reset": "0",
        "content-type": JSON_UTF_8_CHARSET,
    }

    def __init__(
        self,
        status_code=200,
        headers=DEFAULT_HEADERS,
        body=b"",
        *,
        cache=None,
        oauth_token=None,
        app_id=None,
        private_key=None,
        base_url=sansio.DOMAIN,
    ):
        self.response_code = status_code
        self.response_headers = headers
        self.response_body = body
        self.call_count = 0
        super().__init__(
            "test_abc",
            oauth_token=oauth_token,
            app_id=app_id,
            private_key=private_key,
            cache=cache,
            base_url=base_url,
        )

    async def _request(self, method, url, headers, body=b""):
        """Make an HTTP request."""
        self.call_count += 1
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

    async def sleep(self, seconds):  # pragma: no cover
        """Sleep for the specified number of seconds."""
        self.slept = seconds


class TestGeneralGitHubAPI:
    @pytest.mark.parametrize(
        ("credentials", "message"),
        [
            ({"app_id": "12345"}, "app_id and private_key must be provided together."),
            (
                {"private_key": "private key"},
                "app_id and private_key must be provided together.",
            ),
            (
                {
                    "oauth_token": "oauth token",
                    "app_id": "12345",
                    "private_key": "private key",
                },
                "oauth_token cannot be combined with app_id or private_key.",
            ),
        ],
    )
    def test_constructor_credentials(self, credentials, message):
        with pytest.raises(ValueError, match=message):
            MockGitHubAPI(**credentials)

    @pytest.mark.asyncio
    async def test_url_formatted(self):
        """The URL is appropriately formatted."""
        gh = MockGitHubAPI()
        await gh._make_request(
            "GET",
            "/users/octocat/following{/other_user}",
            {"other_user": "brettcannon"},
            "",
            sansio.accept_format(),
        )
        assert gh.url == "https://api.github.com/users/octocat/following/brettcannon"

    @pytest.mark.asyncio
    async def test_url_formatted_with_base_url(self):
        """The URL is appropriately formatted."""
        gh = MockGitHubAPI(base_url="https://my.host.com")
        await gh._make_request(
            "GET",
            "/users/octocat/following{/other_user}",
            {"other_user": "brettcannon"},
            "",
            sansio.accept_format(),
        )
        assert gh.url == "https://my.host.com/users/octocat/following/brettcannon"

    @pytest.mark.asyncio
    async def test_headers(self):
        """Appropriate headers are created."""
        accept = sansio.accept_format()
        gh = MockGitHubAPI(oauth_token="oauth token")
        await gh._make_request("GET", "/rate_limit", {}, "", accept)
        assert gh.headers["user-agent"] == "test_abc"
        assert gh.headers["accept"] == accept
        assert gh.headers["authorization"] == "token oauth token"

    @pytest.mark.asyncio
    @mock.patch("gidgethub.apps.get_jwt", return_value="managed token")
    @mock.patch("time.monotonic", side_effect=[1000, 1479, 1480])
    async def test_managed_app_jwt_is_cached_and_refreshed(
        self, monotonic_mock, get_jwt_mock
    ):
        gh = MockGitHubAPI(app_id="12345", private_key=b"private key")

        await gh._make_request("GET", "/rate_limit", {}, "", sansio.accept_format())
        assert gh.headers["authorization"] == "bearer managed token"
        get_jwt_mock.assert_called_once_with(
            app_id="12345", private_key=b"private key", expiration=9 * 60
        )

        await gh._make_request("GET", "/rate_limit", {}, "", sansio.accept_format())
        get_jwt_mock.assert_called_once()

        get_jwt_mock.return_value = "refreshed token"
        await gh._make_request("GET", "/rate_limit", {}, "", sansio.accept_format())
        assert gh.headers["authorization"] == "bearer refreshed token"
        assert get_jwt_mock.call_count == 2
        assert monotonic_mock.call_count == 3

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("credentials", "request_credentials", "authorization"),
        [
            (
                {"app_id": "12345", "private_key": "private key"},
                {"jwt": "explicit jwt"},
                "bearer explicit jwt",
            ),
            (
                {"app_id": "12345", "private_key": "private key"},
                {"oauth_token": "explicit oauth token"},
                "token explicit oauth token",
            ),
            ({}, {}, None),
        ],
    )
    @mock.patch("gidgethub.apps.get_jwt")
    async def test_managed_app_jwt_overrides_and_unauthenticated_requests(
        self, get_jwt_mock, credentials, request_credentials, authorization
    ):
        gh = MockGitHubAPI(**credentials)
        await gh._make_request(
            "GET",
            "/rate_limit",
            {},
            "",
            sansio.accept_format(),
            **request_credentials,
        )

        assert gh.headers.get("authorization") == authorization
        get_jwt_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_auth_headers_with_passed_token(self):
        """Test the authorization header with the passed oauth_token."""
        accept = sansio.accept_format()
        gh = MockGitHubAPI()
        await gh._make_request(
            "GET", "/rate_limit", {}, "", accept, oauth_token="oauth token"
        )
        assert gh.headers["user-agent"] == "test_abc"
        assert gh.headers["accept"] == accept
        assert gh.headers["authorization"] == "token oauth token"

    @pytest.mark.asyncio
    async def test_auth_headers_with_passed_jwt(self):
        """Test the authorization header with the passed jwt."""
        accept = sansio.accept_format()
        gh = MockGitHubAPI()
        await gh._make_request(
            "GET", "/rate_limit", {}, "", accept, jwt="json web token"
        )
        assert gh.headers["user-agent"] == "test_abc"
        assert gh.headers["accept"] == accept
        assert gh.headers["authorization"] == "bearer json web token"

    @pytest.mark.asyncio
    async def test_make_request_passing_token_and_jwt(self):
        """Test that passing both jwt and oauth_token raises ValueError."""
        accept = sansio.accept_format()
        gh = MockGitHubAPI()
        with pytest.raises(ValueError) as exc_info:
            await gh._make_request(
                "GET",
                "/rate_limit",
                {},
                "",
                accept,
                jwt="json web token",
                oauth_token="oauth token",
            )
        assert str(exc_info.value) == "Cannot pass both oauth_token and jwt."

    @pytest.mark.asyncio
    async def test_rate_limit_set(self):
        """The rate limit is updated after receiving a response."""
        rate_headers = {
            "x-ratelimit-limit": "42",
            "x-ratelimit-remaining": "1",
            "x-ratelimit-reset": "0",
        }
        gh = MockGitHubAPI(headers=rate_headers)
        await gh._make_request("GET", "/rate_limit", {}, "", sansio.accept_format())
        assert gh.rate_limit is not None
        assert gh.rate_limit.limit == 42

    @pytest.mark.asyncio
    async def test_decoding(self):
        """Test that appropriate decoding occurs."""
        original_data = {"hello": "world"}
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["content-type"] = "application/json; charset=utf-8"
        gh = MockGitHubAPI(
            headers=headers, body=json.dumps(original_data).encode("utf8")
        )
        data, _, _ = await gh._make_request(
            "GET", "/rate_limit", {}, "", sansio.accept_format()
        )
        assert data == original_data

    @pytest.mark.asyncio
    async def test_more(self):
        """The 'next' link is returned appropriately."""
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["link"] = '<https://api.github.com/fake?page=2>; rel="next"'
        gh = MockGitHubAPI(headers=headers)
        _, more, _ = await gh._make_request(
            "GET", "/fake", {}, "", sansio.accept_format()
        )
        assert more == "https://api.github.com/fake?page=2"

    @pytest.mark.asyncio
    async def test_status_code(self):
        """The status code is returned appropriately."""
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["link"] = '<https://api.github.com/fake?page=2>; rel="next"'
        gh = MockGitHubAPI(headers=headers)
        _, _, status_code = await gh._make_request(
            "GET", "/fake", {}, "", sansio.accept_format()
        )
        assert status_code == 200


class TestGitHubAPIManageRateLimit:
    @pytest.mark.asyncio
    async def test_default_is_no_op(self):
        """The default manage_rate_limit() is a no-op and doesn't affect
        normal request behaviour."""
        original_data = {"hello": "world"}
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["content-type"] = "application/json; charset=UTF-8"
        gh = MockGitHubAPI(
            headers=headers, body=json.dumps(original_data).encode("utf8")
        )
        data = await gh.getitem("/fake")
        assert data == original_data

    @pytest.mark.asyncio
    async def test_called_with_correct_arguments(self):
        """manage_rate_limit() is called with the expected arguments, and
        self.rate_limit / self.requests_in_flight reflect the current
        state at call time."""
        calls = []

        class RecordingGitHubAPI(MockGitHubAPI):
            async def manage_rate_limit(self, *, method, url):
                calls.append((method, url, self.rate_limit, self.requests_in_flight))

        original_data = {"hello": "world"}
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["content-type"] = "application/json; charset=UTF-8"
        gh = RecordingGitHubAPI(
            headers=headers, body=json.dumps(original_data).encode("utf8")
        )
        assert gh.rate_limit is None
        assert not gh.requests_in_flight
        await gh.getitem("/fake")

        assert len(calls) == 1
        method, url, rate_limit, requests_in_flight = calls[0]
        assert method == "GET"
        assert url == sansio.format_url("/fake", {})
        assert rate_limit is None
        assert requests_in_flight == 1

    @pytest.mark.asyncio
    async def test_subclass_can_observe_multiple_calls(self):
        """A subclass overriding manage_rate_limit() can observe request
        timing across multiple requests made via getiter()."""

        class RecordingGitHubAPI(MockGitHubAPI):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.manage_rate_limit_calls = []

            async def manage_rate_limit(self, *, method, url):
                self.manage_rate_limit_calls.append(
                    (method, url, self.rate_limit, self.requests_in_flight)
                )

        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["link"] = '<https://api.github.com/fake?page=2>; rel="next"'
        headers["content-type"] = JSON_UTF_8_CHARSET
        gh = RecordingGitHubAPI(
            headers=headers, body=b'[{"hello": "world"}, {"hello": "world 2"}]'
        )
        assert not gh.requests_in_flight

        # Each of the 2 pages returns 2 items, for 4 items total, but
        # manage_rate_limit() is only called once per HTTP request (i.e.
        # once per page), not once per item.
        results = [item async for item in gh.getiter("/fake")]

        assert len(results) == 4
        assert len(gh.manage_rate_limit_calls) == 2
        assert gh.manage_rate_limit_calls[0][1] == sansio.format_url("/fake", {})
        assert gh.manage_rate_limit_calls[1][1] == "https://api.github.com/fake?page=2"
        # requests_in_flight is 1 during each call (one request at a time)...
        assert gh.manage_rate_limit_calls[0][3] == 1
        assert gh.manage_rate_limit_calls[1][3] == 1
        # ...and back to 0 once both requests have completed.
        assert not gh.requests_in_flight

    @pytest.mark.asyncio
    async def test_requests_in_flight_tracked_on_success(self):
        """requests_in_flight increments before the request and decrements
        after it completes successfully."""

        class TrackingGitHubAPI(MockGitHubAPI):
            async def manage_rate_limit(self, *, method, url):
                self.in_flight_during_call = self.requests_in_flight

        gh = TrackingGitHubAPI()
        assert gh.requests_in_flight == 0
        await gh.getitem("/fake")
        assert gh.in_flight_during_call == 1
        assert gh.requests_in_flight == 0

    @pytest.mark.asyncio
    async def test_requests_in_flight_decrements_on_exception(self):
        """requests_in_flight decrements even when the underlying request
        raises an exception."""

        class FailingGitHubAPI(MockGitHubAPI):
            async def _request(self, method, url, headers, body=b""):
                raise RuntimeError("boom")

        gh = FailingGitHubAPI()
        assert gh.requests_in_flight == 0
        with pytest.raises(RuntimeError):
            await gh.getitem("/fake")
        assert gh.requests_in_flight == 0


class TestGitHubAPIHandleRateLimitError:
    @pytest.mark.asyncio
    async def test_default_does_not_retry(self):
        """The default handle_rate_limit_error() is a no-op that doesn't
        retry, so the original exception propagates."""
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        gh = MockGitHubAPI(status_code=403, headers=headers)

        with pytest.raises(BadRequest):
            await gh.getitem("/fake")
        # Only the single, non-retried attempt was made.
        assert gh.call_count == 1

    @pytest.mark.asyncio
    async def test_called_with_correct_arguments(self):
        """handle_rate_limit_error() is called with the expected
        arguments when a request fails."""
        calls = []

        class RecordingGitHubAPI(MockGitHubAPI):
            async def handle_rate_limit_error(self, *, method, url, exception, attempt):
                calls.append((method, url, exception, attempt))
                return False

        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        gh = RecordingGitHubAPI(status_code=403, headers=headers)

        with pytest.raises(BadRequest) as exc_info:
            await gh.getitem("/fake")

        assert len(calls) == 1
        method, url, exception, attempt = calls[0]
        assert method == "GET"
        assert url == sansio.format_url("/fake", {})
        assert exception is exc_info.value
        assert attempt == 1

    @pytest.mark.asyncio
    async def test_returning_true_retries_the_request(self):
        """Returning True from handle_rate_limit_error() causes the
        request to be retried, and eventually succeeds."""

        class RetryingGitHubAPI(MockGitHubAPI):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.attempts_seen = []

            async def handle_rate_limit_error(self, *, method, url, exception, attempt):
                self.attempts_seen.append(attempt)
                if attempt < 2:
                    # Succeed on the second attempt.
                    self.response_code = 200
                    return True
                return False

        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        original_data = {"hello": "world"}
        gh = RetryingGitHubAPI(
            status_code=403,
            headers=headers,
            body=json.dumps(original_data).encode("utf8"),
        )

        data = await gh.getitem("/fake")

        assert data == original_data
        assert gh.attempts_seen == [1]
        assert gh.call_count == 2

    @pytest.mark.asyncio
    async def test_returning_false_reraises_exception(self):
        """Returning False from handle_rate_limit_error() lets the
        original exception propagate without retrying."""

        class NonRetryingGitHubAPI(MockGitHubAPI):
            async def handle_rate_limit_error(self, *, method, url, exception, attempt):
                return False

        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        gh = NonRetryingGitHubAPI(status_code=403, headers=headers)

        with pytest.raises(BadRequest):
            await gh.getitem("/fake")
        assert gh.call_count == 1

    @pytest.mark.asyncio
    async def test_attempt_increments_across_retries(self):
        """The 'attempt' argument passed to handle_rate_limit_error()
        reflects the 1-based count of attempts made so far, including
        across multiple retries."""

        class RecordingGitHubAPI(MockGitHubAPI):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.attempts_seen = []

            async def handle_rate_limit_error(self, *, method, url, exception, attempt):
                self.attempts_seen.append(attempt)
                if attempt < 3:
                    return True
                self.response_code = 200
                return True

        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        gh = RecordingGitHubAPI(
            status_code=403, headers=headers, body=b'{"hello": "world"}'
        )

        await gh.getitem("/fake")

        assert gh.attempts_seen == [1, 2, 3]
        assert gh.call_count == 4


class TestGitHubAPIGetitem:
    @pytest.mark.asyncio
    async def test_getitem(self):
        original_data = {"hello": "world"}
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["content-type"] = "application/json; charset=UTF-8"
        gh = MockGitHubAPI(
            headers=headers, body=json.dumps(original_data).encode("utf8")
        )
        data = await gh.getitem("/fake")
        assert gh.method == "GET"
        assert data == original_data

    @pytest.mark.asyncio
    async def test_with_passed_jwt(self):
        original_data = {"hello": "world"}
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["content-type"] = "application/json; charset=UTF-8"
        gh = MockGitHubAPI(
            headers=headers, body=json.dumps(original_data).encode("utf8")
        )
        await gh.getitem("/fake", jwt="json web token")
        assert gh.method == "GET"
        assert gh.headers["authorization"] == "bearer json web token"

    @pytest.mark.asyncio
    async def test_with_passed_oauth_token(self):
        original_data = {"hello": "world"}
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["content-type"] = "application/json; charset=UTF-8"
        gh = MockGitHubAPI(
            headers=headers, body=json.dumps(original_data).encode("utf8")
        )
        await gh.getitem("/fake", oauth_token="my oauth token")
        assert gh.method == "GET"
        assert gh.headers["authorization"] == "token my oauth token"

    @pytest.mark.asyncio
    async def test_cannot_pass_both_jwt_and_oauth_token(self):
        original_data = {"hello": "world"}
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["content-type"] = "application/json; charset=UTF-8"
        gh = MockGitHubAPI(
            headers=headers, body=json.dumps(original_data).encode("utf8")
        )
        with pytest.raises(ValueError) as exc_info:
            await gh.getitem(
                "/fake", oauth_token="my oauth token", jwt="json web token"
            )

        assert str(exc_info.value) == "Cannot pass both oauth_token and jwt."


class TestGitHubAPIGetStatus:
    @pytest.mark.asyncio
    async def test_getstatus(self):
        original_status = 204
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["content-type"] = "application/json; charset=UTF-8"
        gh = MockGitHubAPI(headers=headers, status_code=original_status)
        data = await gh.getstatus("/fake")
        assert gh.method == "GET"
        assert data == original_status

    @pytest.mark.asyncio
    async def test_getstatus_4xx(self):
        original_status = 404
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["content-type"] = "application/json; charset=UTF-8"
        gh = MockGitHubAPI(headers=headers, status_code=original_status)
        data = await gh.getstatus("/fake")
        assert gh.method == "GET"
        assert data == original_status

    @pytest.mark.asyncio
    async def test_getstatus_5xx(self):
        original_status = 504
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["content-type"] = "application/json; charset=UTF-8"
        gh = MockGitHubAPI(headers=headers, status_code=original_status)
        data = await gh.getstatus("/fake")
        assert gh.method == "GET"
        assert data == original_status


class TestGitHubAPIGetiter:
    @pytest.mark.asyncio
    async def test_getiter(self):
        """Test that getiter() returns an async iterable as well as URI expansion."""
        original_data = [1, 2]
        next_url = "https://api.github.com/fake{/extra}?page=2"
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["content-type"] = "application/json; charset=UTF-8"
        headers["link"] = f'<{next_url}>; rel="next"'
        gh = MockGitHubAPI(
            headers=headers, body=json.dumps(original_data).encode("utf8")
        )
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
    async def test_getiter_with_extra_headers(self):
        """Test that getiter() sends extra headers correctly."""
        original_data = [1, 2]
        next_url = "https://api.github.com/fake{/extra}?page=2"
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["content-type"] = "application/json; charset=UTF-8"
        headers["link"] = f'<{next_url}>; rel="next"'
        gh = MockGitHubAPI(
            headers=headers, body=json.dumps(original_data).encode("utf8")
        )
        extra_headers = {"X-Custom-Header": "custom_value"}
        data = []
        async for item in gh.getiter(
            "/fake", {"extra": "stuff"}, extra_headers=extra_headers
        ):
            data.append(item)
        assert gh.method == "GET"
        assert gh.headers["X-Custom-Header"] == "custom_value"
        assert len(data) == 4
        assert data[0] == 1
        assert data[1] == 2
        assert data[2] == 1
        assert data[3] == 2

    @pytest.mark.asyncio
    async def test_with_passed_jwt(self):
        original_data = [1, 2]
        next_url = "https://api.github.com/fake{/extra}?page=2"
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["content-type"] = "application/json; charset=UTF-8"
        headers["link"] = f'<{next_url}>; rel="next"'
        gh = MockGitHubAPI(
            headers=headers, body=json.dumps(original_data).encode("utf8")
        )
        data = []
        async for item in gh.getiter("/fake", {"extra": "stuff"}, jwt="json web token"):
            data.append(item)
        assert gh.method == "GET"
        assert gh.headers["authorization"] == "bearer json web token"

    @pytest.mark.asyncio
    async def test_with_passed_oauth_token(self):
        original_data = [1, 2]
        next_url = "https://api.github.com/fake{/extra}?page=2"
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["content-type"] = "application/json; charset=UTF-8"
        headers["link"] = f'<{next_url}>; rel="next"'
        gh = MockGitHubAPI(
            headers=headers, body=json.dumps(original_data).encode("utf8")
        )
        data = []
        async for item in gh.getiter(
            "/fake", {"extra": "stuff"}, oauth_token="my oauth token"
        ):
            data.append(item)
        assert gh.method == "GET"
        assert gh.headers["authorization"] == "token my oauth token"

    @pytest.mark.asyncio
    async def test_cannot_pass_both_oauth_and_jwt(self):
        original_data = [1, 2]
        next_url = "https://api.github.com/fake{/extra}?page=2"
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["content-type"] = "application/json; charset=UTF-8"
        headers["link"] = f'<{next_url}>; rel="next"'
        gh = MockGitHubAPI(
            headers=headers, body=json.dumps(original_data).encode("utf8")
        )
        with pytest.raises(ValueError) as exc_info:
            async for _ in gh.getiter(
                "/fake",
                {"extra": "stuff"},
                oauth_token="my oauth token",
                jwt="json web token",
            ):
                pytest.fail("Unreachable")  # pragma: no cover
        assert str(exc_info.value) == "Cannot pass both oauth_token and jwt."

    @pytest.mark.asyncio
    async def test_search_api(self):
        """Test that getiter() returns an async iterable with the items if
        the original data is a dictionary (GitHub search API)."""
        original_data = {"items": [1, 2]}
        next_url = "https://api.github.com/fake{/extra}?page=2"
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["content-type"] = "application/json; charset=UTF-8"
        headers["link"] = f'<{next_url}>; rel="next"'
        gh = MockGitHubAPI(
            headers=headers, body=json.dumps(original_data).encode("utf8")
        )
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
    async def test_checks_api(self):
        """Same as search API, but using the `checks_runs` parameter instead of `items`."""
        original_data = {"check_runs": [1, 2]}
        next_url = "https://api.github.com/fake{/extra}?page=2"
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["content-type"] = "application/json; charset=UTF-8"
        headers["link"] = f'<{next_url}>; rel="next"'
        gh = MockGitHubAPI(
            headers=headers, body=json.dumps(original_data).encode("utf8")
        )
        data = []
        async for item in gh.getiter(
            "/fake", {"extra": "stuff"}, iterable_key="check_runs"
        ):
            data.append(item)
        assert gh.method == "GET"
        assert gh.url == "https://api.github.com/fake/stuff?page=2"
        assert len(data) == 4
        assert data[0] == 1
        assert data[1] == 2
        assert data[2] == 1
        assert data[3] == 2

    @pytest.mark.asyncio
    async def test_extra_headers(self):
        """Test that extra headers are passed correctly."""
        accept = sansio.accept_format()
        extra_headers = {"X-Custom-Header": "custom_value"}
        gh = MockGitHubAPI()
        await gh._make_request(
            "GET", "/rate_limit", {}, "", accept, extra_headers=extra_headers
        )
        assert gh.headers["user-agent"] == "test_abc"
        assert gh.headers["accept"] == accept
        assert "X-Custom-Header" in gh.headers
        assert gh.headers["X-Custom-Header"] == "custom_value"


class TestGitHubAPIPost:
    @pytest.mark.asyncio
    async def test_post(self):
        send = [1, 2, 3]
        send_json = json.dumps(send).encode("utf-8")
        receive = {"hello": "world"}
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        gh = MockGitHubAPI(headers=headers, body=json.dumps(receive).encode("utf-8"))
        await gh.post("/fake", data=send)
        assert gh.method == "POST"
        assert gh.headers["content-type"] == "application/json; charset=utf-8"
        assert gh.body == send_json
        assert gh.headers["content-length"] == str(len(send_json))
        assert gh.headers["content-type"] == JSON_UTF_8_CHARSET

    @pytest.mark.asyncio
    async def test_with_passed_jwt(self):
        send = [1, 2, 3]
        receive = {"hello": "world"}
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        gh = MockGitHubAPI(headers=headers, body=json.dumps(receive).encode("utf-8"))
        await gh.post("/fake", data=send, jwt="json web token")
        assert gh.method == "POST"
        assert gh.headers["authorization"] == "bearer json web token"
        assert gh.headers["content-type"] == JSON_UTF_8_CHARSET

    @pytest.mark.asyncio
    async def test_with_passed_oauth_token(self):
        send = [1, 2, 3]
        receive = {"hello": "world"}
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        gh = MockGitHubAPI(headers=headers, body=json.dumps(receive).encode("utf-8"))
        await gh.post("/fake", data=send, oauth_token="my oauth token")
        assert gh.method == "POST"
        assert gh.headers["authorization"] == "token my oauth token"
        assert gh.headers["content-type"] == JSON_UTF_8_CHARSET

    @pytest.mark.asyncio
    async def test_cannot_pass_both_oauth_and_jwt(self):
        send = [1, 2, 3]
        receive = {"hello": "world"}
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        gh = MockGitHubAPI(headers=headers, body=json.dumps(receive).encode("utf-8"))
        with pytest.raises(ValueError) as exc_info:
            await gh.post(
                "/fake", data=send, oauth_token="my oauth token", jwt="json web token"
            )

        assert str(exc_info.value) == "Cannot pass both oauth_token and jwt."

    @pytest.mark.asyncio
    async def test_with_passed_content_type(self):
        """Assert that the body is not parsed to JSON and the content-type header is set."""
        gh = MockGitHubAPI()
        data = "blabla"
        await gh.post("/fake", data=data, content_type="application/zip")
        assert gh.method == "POST"
        assert gh.headers["content-type"] == "application/zip"
        assert gh.body == data
        assert gh.headers["content-length"] == str(len(data))


class TestGitHubAPIPatch:
    @pytest.mark.asyncio
    async def test_patch(self):
        send = [1, 2, 3]
        send_json = json.dumps(send).encode("utf-8")
        receive = {"hello": "world"}
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["content-type"] = "application/json; charset=utf-8"
        gh = MockGitHubAPI(headers=headers, body=json.dumps(receive).encode("utf-8"))
        await gh.patch("/fake", data=send)
        assert gh.method == "PATCH"
        assert gh.headers["content-type"] == "application/json; charset=utf-8"
        assert gh.body == send_json
        assert gh.headers["content-length"] == str(len(send_json))

    @pytest.mark.asyncio
    async def test_with_passed_jwt(self):
        send = [1, 2, 3]
        receive = {"hello": "world"}
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["content-type"] = "application/json; charset=utf-8"
        gh = MockGitHubAPI(headers=headers, body=json.dumps(receive).encode("utf-8"))
        await gh.patch("/fake", data=send, jwt="json web token")
        assert gh.method == "PATCH"
        assert gh.headers["authorization"] == "bearer json web token"

    @pytest.mark.asyncio
    async def test_with_passed_oauth_token(self):
        send = [1, 2, 3]
        receive = {"hello": "world"}
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["content-type"] = "application/json; charset=utf-8"
        gh = MockGitHubAPI(headers=headers, body=json.dumps(receive).encode("utf-8"))
        await gh.patch("/fake", data=send, oauth_token="my oauth token")
        assert gh.method == "PATCH"
        assert gh.headers["authorization"] == "token my oauth token"

    @pytest.mark.asyncio
    async def test_cannot_pass_both_oauth_and_jwt(self):
        send = [1, 2, 3]
        receive = {"hello": "world"}
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["content-type"] = "application/json; charset=utf-8"
        gh = MockGitHubAPI(headers=headers, body=json.dumps(receive).encode("utf-8"))
        with pytest.raises(ValueError) as exc_info:
            await gh.patch(
                "/fake", data=send, oauth_token="my oauth token", jwt="json web token"
            )

        assert str(exc_info.value) == "Cannot pass both oauth_token and jwt."


class TestGitHubAPIPut:
    @pytest.mark.asyncio
    async def test_put(self):
        send = [1, 2, 3]
        send_json = json.dumps(send).encode("utf-8")
        receive = {"hello": "world"}
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["content-type"] = "application/json; charset=utf-8"
        gh = MockGitHubAPI(headers=headers, body=json.dumps(receive).encode("utf-8"))
        await gh.put("/fake", data=send)
        assert gh.method == "PUT"
        assert gh.headers["content-type"] == "application/json; charset=utf-8"
        assert gh.body == send_json
        assert gh.headers["content-length"] == str(len(send_json))

    @pytest.mark.asyncio
    async def test_with_passed_jwt(self):
        send = [1, 2, 3]
        receive = {"hello": "world"}
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["content-type"] = "application/json; charset=utf-8"
        gh = MockGitHubAPI(headers=headers, body=json.dumps(receive).encode("utf-8"))
        await gh.put("/fake", data=send, jwt="json web token")
        assert gh.method == "PUT"
        assert gh.headers["authorization"] == "bearer json web token"

    @pytest.mark.asyncio
    async def test_with_passed_oauth_token(self):
        send = [1, 2, 3]
        receive = {"hello": "world"}
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["content-type"] = "application/json; charset=utf-8"
        gh = MockGitHubAPI(headers=headers, body=json.dumps(receive).encode("utf-8"))
        await gh.put("/fake", data=send, oauth_token="my oauth token")
        assert gh.method == "PUT"
        assert gh.headers["authorization"] == "token my oauth token"

    @pytest.mark.asyncio
    async def test_cannot_pass_both_oauth_and_jwt(self):
        send = [1, 2, 3]
        receive = {"hello": "world"}
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["content-type"] = "application/json; charset=utf-8"
        gh = MockGitHubAPI(headers=headers, body=json.dumps(receive).encode("utf-8"))
        with pytest.raises(ValueError) as exc_info:
            await gh.put(
                "/fake", data=send, oauth_token="my oauth token", jwt="json web token"
            )

        assert str(exc_info.value) == "Cannot pass both oauth_token and jwt."


class TestGitHubAPIDelete:
    @pytest.mark.asyncio
    async def test_delete(self):
        send = [1, 2, 3]
        send_json = json.dumps(send).encode("utf-8")
        receive = {"hello": "world"}
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["content-type"] = "application/json; charset=utf-8"
        gh = MockGitHubAPI(headers=headers, body=json.dumps(receive).encode("utf-8"))
        await gh.delete("/fake", data=send)
        assert gh.method == "DELETE"
        assert gh.headers["content-type"] == "application/json; charset=utf-8"
        assert gh.body == send_json
        assert gh.headers["content-length"] == str(len(send_json))

    @pytest.mark.asyncio
    async def test_with_passed_jwt(self):
        send = [1, 2, 3]
        receive = {"hello": "world"}
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["content-type"] = "application/json; charset=utf-8"
        gh = MockGitHubAPI(headers=headers, body=json.dumps(receive).encode("utf-8"))
        await gh.delete("/fake", data=send, jwt="json web token")
        assert gh.method == "DELETE"
        assert gh.headers["authorization"] == "bearer json web token"

    @pytest.mark.asyncio
    async def test_with_passed_oauth_token(self):
        send = [1, 2, 3]
        receive = {"hello": "world"}
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["content-type"] = "application/json; charset=utf-8"
        gh = MockGitHubAPI(headers=headers, body=json.dumps(receive).encode("utf-8"))
        await gh.delete("/fake", data=send, oauth_token="my oauth token")
        assert gh.method == "DELETE"
        assert gh.headers["authorization"] == "token my oauth token"

    @pytest.mark.asyncio
    async def test_pass_both_oauth_and_jwt(self):
        send = [1, 2, 3]
        receive = {"hello": "world"}
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["content-type"] = "application/json; charset=utf-8"
        gh = MockGitHubAPI(headers=headers, body=json.dumps(receive).encode("utf-8"))
        with pytest.raises(ValueError) as exc_info:
            await gh.delete(
                "/fake", data=send, oauth_token="my oauth token", jwt="json web token"
            )

        assert str(exc_info.value) == "Cannot pass both oauth_token and jwt."


class TestGitHubAPICache:
    @pytest.mark.asyncio
    async def test_if_none_match_sent(self):
        etag = "12345"
        cache = {"https://api.github.com/fake": (etag, None, "hi", None)}
        gh = MockGitHubAPI(cache=cache)
        await gh.getitem("/fake")
        assert "if-none-match" in gh.headers
        assert gh.headers["if-none-match"] == etag

    @pytest.mark.asyncio
    async def test_etag_received(self):
        cache: gh_abc.CACHE_TYPE = {}
        etag = "12345"
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["etag"] = etag
        gh = MockGitHubAPI(200, headers, b"42", cache=cache)
        data = await gh.getitem("/fake")
        url = "https://api.github.com/fake"
        assert url in cache
        assert cache[url] == (etag, None, 42, None)
        assert data == cache[url][2]

    @pytest.mark.asyncio
    async def test_if_modified_since_sent(self):
        last_modified = "12345"
        cache = {"https://api.github.com/fake": (None, last_modified, "hi", None)}
        gh = MockGitHubAPI(cache=cache)
        await gh.getitem("/fake")
        assert "if-modified-since" in gh.headers
        assert gh.headers["if-modified-since"] == last_modified

    @pytest.mark.asyncio
    async def test_last_modified_received(self):
        cache: gh_abc.CACHE_TYPE = {}
        last_modified = "12345"
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["last-modified"] = last_modified
        gh = MockGitHubAPI(200, headers, b"42", cache=cache)
        data = await gh.getitem("/fake")
        url = "https://api.github.com/fake"
        assert url in cache
        assert cache[url] == (None, last_modified, 42, None)
        assert data == cache[url][2]

    @pytest.mark.asyncio
    async def test_hit(self):
        url = "https://api.github.com/fake"
        cache = {url: ("12345", "67890", 42, None)}
        gh = MockGitHubAPI(304, cache=cache)
        data = await gh.getitem(url)
        assert data == 42

    @pytest.mark.asyncio
    async def test_miss(self):
        url = "https://api.github.com/fake"
        cache = {url: ("12345", "67890", 42, None)}
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["etag"] = "09876"
        headers["last-modified"] = "54321"
        gh = MockGitHubAPI(200, headers, body=b"-13", cache=cache)
        data = await gh.getitem(url)
        assert data == -13
        assert cache[url] == ("09876", "54321", -13, None)

    @pytest.mark.asyncio
    async def test_ineligible(self):
        cache: gh_abc.CACHE_TYPE = {}
        gh = MockGitHubAPI(cache=cache)
        url = "https://api.github.com/fake"
        # Only way to force a GET request with a body.
        await gh._make_request("GET", url, {}, 42, "asdf")
        assert url not in cache
        await gh.post(url, data=42)
        assert url not in cache

    @pytest.mark.asyncio
    async def test_redirect_without_cache(self):
        cache: gh_abc.CACHE_TYPE = {}
        gh = MockGitHubAPI(304, cache=cache)
        with pytest.raises(RedirectionException):
            await gh.getitem("/fake")

    @pytest.mark.asyncio
    async def test_no_cache(self):
        headers = MockGitHubAPI.DEFAULT_HEADERS.copy()
        headers["etag"] = "09876"
        headers["last-modified"] = "54321"
        gh = MockGitHubAPI(headers=headers)
        await gh.getitem("/fake")  # No exceptions raised.


_SAMPLE_QUERY = """query {
    viewer {
        name
        repositories(last: 3) {
            nodes {
                name
            }
        }
    }
}
"""

_SAMPLE_QUERY_WITH_VARIABLES = """query ($number_of_repos: Int!) {
    viewer {
        name
        repositories(last: $number_of_repos) {
            nodes {
                name
            }
        }
    }
}
"""


class TestGraphQL:
    """Test gidgethub.abc.GitHubAPI.graphql()."""

    def gh_and_response(self, payload_filename):
        payload = (
            importlib_resources.files(graphql_samples) / payload_filename
        ).read_bytes()
        status_code_match = re.match(r"^.+-(\d+)\.json$", payload_filename)
        assert status_code_match is not None
        status_code = int(status_code_match.group(1))
        return (
            MockGitHubAPI(status_code, body=payload, oauth_token="oauth-token"),
            json.loads(payload.decode("utf-8")),
        )

    @pytest.mark.asyncio
    async def test_5XX_status_code(self):
        response_data = {"hello": "World"}
        gh = MockGitHubAPI(
            500,
            body=json.dumps(response_data).encode("utf-8"),
            oauth_token="oauth-token",
        )
        with pytest.raises(GitHubBroken) as exc:
            await gh.graphql("does not matter")
        assert exc.value.status_code == http.HTTPStatus(500)

    @pytest.mark.asyncio
    async def test_bad_credentials(self):
        gh, response_data = self.gh_and_response("bad-credentials-401.json")
        with pytest.raises(GraphQLAuthorizationFailure) as exc:
            await gh.graphql(_SAMPLE_QUERY)
        assert exc.value.response == response_data
        assert exc.value.status_code == http.HTTPStatus(401)

    @pytest.mark.asyncio
    async def test_4XX_status_code(self):
        """Test a 4XX response for which there is no pre-defined exception.

        The testing of the response to sending bad JSON is inconsequential.
        """
        gh, response_data = self.gh_and_response("malformed-json-400.json")
        with pytest.raises(BadGraphQLRequest) as exc:
            await gh.graphql(_SAMPLE_QUERY)
        assert exc.value.response == response_data
        assert exc.value.status_code == http.HTTPStatus(400)

    @pytest.mark.asyncio
    async def test_malformed_query(self):
        gh, response_data = self.gh_and_response("malformed-query-200.json")
        with pytest.raises(QueryError) as exc:
            await gh.graphql("this isn't right")
        assert exc.value.response == response_data

    @pytest.mark.asyncio
    async def test_missing_variable(self):
        gh, response_data = self.gh_and_response("missing-variable-in-request-200.json")
        with pytest.raises(QueryError) as exc:
            await gh.graphql(_SAMPLE_QUERY_WITH_VARIABLES)
        assert exc.value.response == response_data

    @pytest.mark.asyncio
    async def test_unexpected_200_response(self):
        """200 responses are expected to contain either an "errors" or "data" key."""
        response_data = {"hello": "World"}
        gh = MockGitHubAPI(
            200,
            body=json.dumps(response_data).encode("utf-8"),
            oauth_token="oauth-token",
        )
        with pytest.raises(GraphQLException) as exc:
            await gh.graphql("does not matter")
        assert exc.value.response == response_data

    @pytest.mark.asyncio
    async def test_query(self):
        gh, response_data = self.gh_and_response("success-200.json")
        result = await gh.graphql(_SAMPLE_QUERY)
        assert gh.method == "POST"
        assert gh.url == "https://api.github.com/graphql"
        assert gh.headers["content-type"] == "application/json; charset=utf-8"
        assert gh.headers["content-length"] == str(len(gh.body))
        expected_headers = sansio.create_headers(
            "test_abc",
            accept="application/json; charset=utf-8",
            oauth_token="oauth-token",
        )
        for key, value in expected_headers.items():
            assert gh.headers[key] == value
        body = json.loads(gh.body.decode("utf-8"))
        assert body == {"query": _SAMPLE_QUERY}
        assert result == response_data["data"]

    @pytest.mark.asyncio
    async def test_query_with_variables(self):
        gh, response_data = self.gh_and_response("success-200.json")
        result = await gh.graphql(_SAMPLE_QUERY_WITH_VARIABLES, number_of_repos=3)
        assert gh.method == "POST"
        assert gh.url == "https://api.github.com/graphql"
        assert gh.headers["content-type"] == "application/json; charset=utf-8"
        assert gh.headers["content-length"] == str(len(gh.body))
        expected_headers = sansio.create_headers(
            "test_abc",
            accept="application/json; charset=utf-8",
            oauth_token="oauth-token",
        )
        for key, value in expected_headers.items():
            assert gh.headers[key] == value
        body = json.loads(gh.body.decode("utf-8"))
        assert body == {
            "query": _SAMPLE_QUERY_WITH_VARIABLES,
            "variables": {"number_of_repos": 3},
        }
        assert result == response_data["data"]

    @pytest.mark.asyncio
    async def test_endpoint(self):
        gh, response_data = self.gh_and_response("success-200.json")
        base_url = "https://example.com/graphql"
        result = await gh.graphql(_SAMPLE_QUERY, endpoint=base_url)
        assert gh.method == "POST"
        assert gh.url == base_url
        assert gh.headers["content-type"] == "application/json; charset=utf-8"
        assert gh.headers["content-length"] == str(len(gh.body))
        expected_headers = sansio.create_headers(
            "test_abc",
            accept="application/json; charset=utf-8",
            oauth_token="oauth-token",
        )
        for key, value in expected_headers.items():
            assert gh.headers[key] == value
        body = json.loads(gh.body.decode("utf-8"))
        assert body == {"query": _SAMPLE_QUERY}
        assert result == response_data["data"]

    @pytest.mark.asyncio
    async def test_unexpected_status_code(self):
        response_data = {"hello": "World"}
        gh = MockGitHubAPI(
            300,
            body=json.dumps(response_data).encode("utf-8"),
            oauth_token="oauth-token",
        )
        with pytest.raises(GraphQLException) as exc:
            await gh.graphql("does not matter")
        assert exc.value.response == response_data

    @pytest.mark.asyncio
    async def test_response_content_type_parsing_gh121(self):
        gh, _response_data = self.gh_and_response("success-200.json")
        # Test that a JSON content type still works if formatted without spaces.
        gh.response_headers["content-type"] = "application/json;charset=utf-8"
        # Should not fail.
        resp = await gh.graphql("does not matter")
        assert resp is not None
        # Spaces in the content-type header should not be a problem.
        gh.response_headers["content-type"] = "application/json; charset=utf-8"
        # Should not fail.
        resp = await gh.graphql("does not matter")
        assert resp is not None

    @pytest.mark.asyncio
    async def test_unknown_response_content_type_gh121(self):
        gh, _response_data = self.gh_and_response("success-200.json")
        # A non-JSON response should raise an exception.
        gh.response_headers["content-type"] = "application/gidget;charset=utf-8"
        with pytest.raises(GraphQLResponseTypeError):
            await gh.graphql("does not matter")

    @pytest.mark.asyncio
    async def test_no_response_content_type_gh121(self):
        gh, _response_data = self.gh_and_response("success-200.json")
        # An empty content type should raise an exception.
        gh.response_headers["content-type"] = ""
        with pytest.raises(GraphQLException):
            await gh.graphql("does not matter")
        del gh.response_headers["content-type"]
        with pytest.raises(GraphQLException):
            await gh.graphql("does not matter")

    @pytest.mark.asyncio
    async def test_no_response_data(self):
        # An empty response should raise an exception.
        gh = MockGitHubAPI(200, body=b"", oauth_token="oauth-token")
        with pytest.raises(GraphQLException):
            await gh.graphql("does not matter")
