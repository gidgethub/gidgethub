import datetime
import http
import json
import pathlib


import pytest

from gidgethub import (
    BadRequest,
    BadRequestUnknownError,
    GitHubBroken,
    HTTPException,
    InvalidField,
    RateLimitExceeded,
    RedirectionException,
    ValidationError,
    ValidationFailure,
)
from gidgethub import sansio


class TestValidateEvent:

    """Tests for gidgethub.sansio.validate_event()."""

    secret = "123456"
    payload = "gidget".encode("UTF-8")
    hash_signature = "8acc2ae97633ec018f118577f4872e103f24ef58"
    signature = "sha1=" + hash_signature

    def test_malformed_signature(self):
        """Error out if the signature doesn't start with "sha1="."""
        with pytest.raises(ValidationFailure):
            sansio.validate_event(
                self.payload, secret=self.secret, signature=self.hash_signature
            )

    def test_validation(self):
        """Success case."""
        sansio.validate_event(
            self.payload, secret=self.secret, signature=self.signature
        )

    def test_failure(self):
        with pytest.raises(ValidationFailure):
            sansio.validate_event(
                self.payload + b"!", secret=self.secret, signature=self.signature
            )


class TestEvent:

    """Tests for gidgethub.sansio.Event."""

    data = {"action": "opened"}
    data_bytes = '{"action": "opened"}'.encode("UTF-8")
    secret = "123456"
    headers = {
        "content-type": "application/json",
        "x-github-event": "pull_request",
        "x-github-delivery": "72d3162e-cc78-11e3-81ab-4c9367dc0958",
        "x-hub-signature": "sha1=c28e33b2e56e548956c446e890929a6cbec3ac89",
    }

    def check_event(self, event):
        """Check that an event matches the test data provided by the class."""
        assert event.event == self.headers["x-github-event"]
        assert event.delivery_id == self.headers["x-github-delivery"]
        assert event.data == self.data

    def test_init(self):
        ins = sansio.Event(
            self.data,
            event=self.headers["x-github-event"],
            delivery_id=self.headers["x-github-delivery"],
        )
        self.check_event(ins)

    def test_from_http_json(self):
        """Construct an event from complete HTTP information."""
        event = sansio.Event.from_http(
            self.headers, self.data_bytes, secret=self.secret
        )
        self.check_event(event)

    def test_from_http_urlencoded(self):
        headers, body = sample("ping_urlencoded", 200)
        event = sansio.Event.from_http(headers, body)
        assert event.data["zen"] == "Keep it logically awesome."

    def test_from_http_no_content_type(self):
        """Only accept data when content-type is application/json."""
        headers_no_content_type = self.headers.copy()
        del headers_no_content_type["content-type"]
        with pytest.raises(BadRequest):
            sansio.Event.from_http(
                headers_no_content_type, self.data_bytes, secret=self.secret
            )

    def test_from_http_unknown_content_type(self):
        headers = headers = {
            "content-type": "image/png",
            "x-github-event": "pull_request",
            "x-github-delivery": "72d3162e-cc78-11e3-81ab-4c9367dc0958",
        }
        with pytest.raises(BadRequest):
            sansio.Event.from_http(headers, self.data_bytes)
        pass

    def test_from_http_missing_secret(self):
        """Signature but no secret raises ValidationFailure."""
        with pytest.raises(ValidationFailure):
            sansio.Event.from_http(self.headers, self.data_bytes)

    def test_from_http_missing_signature(self):
        """Secret but no signature raises ValidationFailure."""
        headers_no_sig = self.headers.copy()
        del headers_no_sig["x-hub-signature"]
        with pytest.raises(ValidationFailure):
            sansio.Event.from_http(headers_no_sig, self.data_bytes, secret=self.secret)

    def test_from_http_bad_signature(self):
        with pytest.raises(ValidationFailure):
            sansio.Event.from_http(
                self.headers, self.data_bytes, secret=self.secret + "no secret"
            )

    def test_from_http_no_signature(self):
        headers = self.headers.copy()
        del headers["x-hub-signature"]
        event = sansio.Event.from_http(headers, self.data_bytes)
        self.check_event(event)


class TestAcceptFormat:

    """Tests for gidgethub.sansio.accept_format()."""

    def test_defaults(self):
        assert sansio.accept_format() == "application/vnd.github.v3+json"

    def test_format(self):
        expect = "application/vnd.github.v3.raw+json"
        assert sansio.accept_format(media="raw") == expect

    def test_no_json(self):
        expect = "application/vnd.github.v3.raw"
        assert sansio.accept_format(media="raw", json=False) == expect

    def test_version(self):
        expect = "application/vnd.github.cloak-preview+json"
        assert sansio.accept_format(version="cloak-preview") == expect


class TestCreateHeaders:

    """Tests for gidgethub.sansio.create_headers()."""

    def test_common_case(self):
        user_agent = "brettcannon"
        oauth_token = "secret"
        headers = sansio.create_headers(user_agent, oauth_token=oauth_token)
        assert headers["user-agent"] == user_agent
        assert headers["authorization"] == f"token {oauth_token}"

    def test_api_change(self):
        test_api = "application/vnd.github.cloak-preview+json"
        user_agent = "brettcannon"
        headers = sansio.create_headers(user_agent, accept=test_api)
        assert headers["user-agent"] == user_agent
        assert headers["accept"] == test_api

    def test_all_keys_lowercase(self):
        """Test all header fields are lowercase."""
        user_agent = "brettcannon"
        test_api = "application/vnd.github.cloak-preview+json"
        oauth_token = "secret"
        headers = sansio.create_headers(
            user_agent, accept=test_api, oauth_token=oauth_token
        )
        assert len(headers) == 3
        for key in headers.keys():
            assert key == key.lower()
        assert headers["user-agent"] == user_agent
        assert headers["accept"] == test_api
        assert headers["authorization"] == f"token {oauth_token}"

    def test_authorization_with_jwt(self):
        user_agent = "brettcannon"
        jwt = "secret"
        headers = sansio.create_headers(user_agent, jwt=jwt)
        assert headers["user-agent"] == user_agent
        assert headers["authorization"] == f"bearer {jwt}"

    def test_cannot_pass_both_jwt_and_oauth(self):
        user_agent = "brettcannon"
        jwt = "secret jwt"
        oauth_token = "secret oauth token"
        with pytest.raises(ValueError) as exc_info:
            sansio.create_headers(user_agent, oauth_token=oauth_token, jwt=jwt)
        assert str(exc_info.value) == "Cannot pass both oauth_token and jwt."


class TestRateLimit:
    def test_init(self):
        left = 42
        rate = 64
        reset = datetime.datetime.now(datetime.timezone.utc)
        rate_limit = sansio.RateLimit(
            remaining=left, limit=rate, reset_epoch=reset.timestamp()
        )
        assert rate_limit.remaining == left
        assert rate_limit.limit == rate
        assert rate_limit.reset_datetime == reset

    def test_bool(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        year_from_now = now + datetime.timedelta(365)
        year_ago = now - datetime.timedelta(365)
        # Requests left.
        rate = sansio.RateLimit(
            remaining=1, limit=1, reset_epoch=year_from_now.timestamp()
        )
        assert rate
        # Reset passed.
        rate = sansio.RateLimit(remaining=0, limit=1, reset_epoch=year_ago.timestamp())
        assert rate
        # No requests and reset not passed.
        rate = sansio.RateLimit(
            remaining=0, limit=1, reset_epoch=year_from_now.timestamp()
        )
        assert not rate

    def test_from_http(self):
        left = 42
        rate = 65
        reset = datetime.datetime.now(datetime.timezone.utc)
        headers = {
            "x-ratelimit-limit": str(rate),
            "x-ratelimit-remaining": str(left),
            "x-ratelimit-reset": str(reset.timestamp()),
        }
        rate_limit = sansio.RateLimit.from_http(headers)
        assert rate_limit.limit == rate
        assert rate_limit.remaining == left
        assert rate_limit.reset_datetime == reset

    def test___str__(self):
        left = 4200
        rate = 65000
        reset = datetime.datetime.now(datetime.timezone.utc)
        message = str(
            sansio.RateLimit(limit=rate, remaining=left, reset_epoch=reset.timestamp())
        )
        assert format(left, ",") in message
        assert format(rate, ",") in message
        assert str(reset) in message

    def test_from_http_no_ratelimit(self):
        headers = {}
        rate_limit = sansio.RateLimit.from_http(headers)
        assert rate_limit is None


def sample(directory, status_code):
    # pytest doesn't set __spec__.origin :(
    sample_dir = pathlib.Path(__file__).parent / "samples" / directory
    headers_path = sample_dir / f"{status_code}.json"
    with headers_path.open("r") as file:
        headers = json.load(file)
    body = (sample_dir / "body").read_bytes()
    return headers, body


class TestDecipherResponse:

    """Tests for gidgethub.sansio.decipher_response()."""

    def test_5XX(self):
        status_code = 502
        with pytest.raises(GitHubBroken) as exc_info:
            sansio.decipher_response(status_code, {}, b"")
        assert exc_info.value.status_code == http.HTTPStatus(status_code)

    def test_4XX_no_message(self):
        status_code = 400
        with pytest.raises(BadRequest) as exc_info:
            sansio.decipher_response(status_code, {}, b"")
        assert exc_info.value.status_code == http.HTTPStatus(status_code)

    def test_4XX_message(self):
        status_code = 400
        message = json.dumps({"message": "it went bad"}).encode("UTF-8")
        headers = {"content-type": "application/json; charset=utf-8"}
        with pytest.raises(BadRequest) as exc_info:
            sansio.decipher_response(status_code, headers, message)
        assert exc_info.value.status_code == http.HTTPStatus(status_code)
        assert str(exc_info.value) == "it went bad"

    def test_404(self):
        status_code = 404
        headers, body = sample("pr_not_found", status_code)
        with pytest.raises(BadRequest) as exc_info:
            sansio.decipher_response(status_code, headers, body)
        assert exc_info.value.status_code == http.HTTPStatus(status_code)
        assert str(exc_info.value) == "Not Found"

    def test_403_rate_limit_exceeded(self):
        status_code = 403
        headers = {
            "content-type": "application/json; charset=utf-8",
            "x-ratelimit-limit": "2",
            "x-ratelimit-remaining": "0",
            "x-ratelimit-reset": "1",
        }
        body = json.dumps({"message": "oops"}).encode("UTF-8")
        with pytest.raises(RateLimitExceeded) as exc_info:
            sansio.decipher_response(status_code, headers, body)
        assert exc_info.value.status_code == http.HTTPStatus(status_code)

    def test_403_forbidden(self):
        status_code = 403
        headers = {
            "content-type": "application/json; charset=utf-8",
            "x-ratelimit-limit": "2",
            "x-ratelimit-remaining": "1",
            "x-ratelimit-reset": "1",
        }
        with pytest.raises(BadRequest) as exc_info:
            sansio.decipher_response(status_code, headers, b"")
        assert exc_info.value.status_code == http.HTTPStatus(status_code)

    def test_422(self):
        status_code = 422
        errors = [{"resource": "Issue", "field": "title", "code": "missing_field"}]
        body = json.dumps({"message": "it went bad", "errors": errors})
        body = body.encode("utf-8")
        headers = {"content-type": "application/json; charset=utf-8"}
        with pytest.raises(InvalidField) as exc_info:
            sansio.decipher_response(status_code, headers, body)
        assert exc_info.value.status_code == http.HTTPStatus(status_code)
        assert str(exc_info.value) == "it went bad for 'title'"

    def test_422_custom_code(self):
        status_code = 422
        errors = [
            {
                "resource": "PullRequest",
                "code": "custom",
                "message": "A pull request already exists for foo:1.",
            }
        ]
        body = json.dumps({"message": "it went bad", "errors": errors})
        body = body.encode("utf-8")
        headers = {"content-type": "application/json; charset=utf-8"}
        with pytest.raises(ValidationError) as exc_info:
            sansio.decipher_response(status_code, headers, body)
        assert exc_info.value.status_code == http.HTTPStatus(status_code)
        assert (
            str(exc_info.value)
            == "it went bad: 'A pull request already exists for foo:1.'"
        )

    def test_422_no_errors_object(self):
        status_code = 422
        body = json.dumps(
            {
                "message": "Reference does not exist",
                "documentation_url": "https://developer.github.com/v3/git/refs/#delete-a-reference",
            }
        )
        body = body.encode("utf-8")
        headers = {"content-type": "application/json; charset=utf-8"}
        with pytest.raises(InvalidField) as exc_info:
            sansio.decipher_response(status_code, headers, body)
        assert exc_info.value.status_code == http.HTTPStatus(status_code)
        assert str(exc_info.value) == "Reference does not exist"

    def test_422_html_response(self):
        # https://github.com/brettcannon/gidgethub/issues/81
        status_code = 422
        body = "<html><body>Mistakes were made ...</body></html>"
        encoded_body = body.encode("utf-8")
        headers = {"content-type": "text/html; charset=utf-8"}
        with pytest.raises(BadRequestUnknownError) as exc_info:
            sansio.decipher_response(status_code, headers, encoded_body)
        assert exc_info.value.status_code == http.HTTPStatus(status_code)
        assert exc_info.value.response == body

    def test_3XX(self):
        status_code = 301
        with pytest.raises(RedirectionException) as exc_info:
            sansio.decipher_response(status_code, {}, b"")
        assert exc_info.value.status_code == http.HTTPStatus(status_code)

    def test_2XX_error(self):
        status_code = 205
        with pytest.raises(HTTPException) as exc_info:
            sansio.decipher_response(status_code, {}, b"")
        assert exc_info.value.status_code == http.HTTPStatus(status_code)

    def test_200(self):
        status_code = 200
        headers, body = sample("pr_single", status_code)
        data, rate_limit, more = sansio.decipher_response(status_code, headers, body)
        assert more is None
        assert rate_limit.remaining == 53
        assert data["url"] == "https://api.github.com/repos/python/cpython/pulls/1"

    def test_201(self):
        """Test a 201 response along with non-pagination Link header."""
        status_code = 201
        headers = {
            "x-ratelimit-limit": "60",
            "x-ratelimit-remaining": "50",
            "x-ratelimit-reset": "12345678",
            "content-type": "application/json; charset=utf-8",
            "link": '<http://example.com>; test="unimportant"',
        }
        data = {
            "id": 208_045_946,
            "url": "https://api.github.com/repos/octocat/Hello-World/labels/bug",
            "name": "bug",
            "color": "f29513",
            "default": True,
        }
        body = json.dumps(data).encode("UTF-8")
        returned_data, rate_limit, more = sansio.decipher_response(
            status_code, headers, body
        )
        assert more is None
        assert rate_limit.limit == 60
        assert returned_data == data

    def test_204(self):
        """Test both a 204 response and an empty response body."""
        status_code = 204
        headers, body = sample("pr_merged", status_code)
        data, rate_limit, more = sansio.decipher_response(status_code, headers, body)
        assert more is None
        assert rate_limit.remaining == 41
        assert data is None

    def test_next(self):
        status_code = 200
        headers, body = sample("pr_page_1", status_code)
        data, rate_limit, more = sansio.decipher_response(status_code, headers, body)
        assert more == "https://api.github.com/repositories/4164482/pulls?page=2"
        assert rate_limit.remaining == 53
        assert data[0]["url"] == "https://api.github.com/repos/django/django/pulls/8053"

        headers, body = sample("pr_page_2", status_code)
        data, rate_limit, more = sansio.decipher_response(status_code, headers, body)
        assert more == "https://api.github.com/repositories/4164482/pulls?page=3"
        assert rate_limit.remaining == 50
        assert data[0]["url"] == "https://api.github.com/repos/django/django/pulls/7805"

        headers, body = sample("pr_page_last", status_code)
        data, rate_limit, more = sansio.decipher_response(status_code, headers, body)
        assert more is None
        assert rate_limit.remaining == 48
        assert data[0]["url"] == "https://api.github.com/repos/django/django/pulls/6395"

    def test_next_with_search_api(self):
        status_code = 200
        headers, body = sample("search_issues_page_1", status_code)
        data, rate_limit, more = sansio.decipher_response(status_code, headers, body)
        assert more == (
            "https://api.github.com/search/issues"
            "?q=repo%3Abrettcannon%2Fgidgethub+state%3Aclosed"
            "+rate+&per_page=3&page=2"
        )
        assert rate_limit.remaining == 9
        assert {"items", "incomplete_results", "total_count"} == data.keys()
        expected_first_url = (
            "https://api.github.com/repos/brettcannon/gidgethub/issues/25"
        )
        assert data["items"][0]["url"] == expected_first_url

        headers, body = sample("search_issues_page_last", status_code)
        data, rate_limit, more = sansio.decipher_response(status_code, headers, body)
        assert more is None
        assert rate_limit.remaining == 9
        assert {"items", "incomplete_results", "total_count"} == data.keys()
        expected_first_url = (
            "https://api.github.com/repos/brettcannon/gidgethub/issues/10"
        )
        assert data["items"][0]["url"] == expected_first_url

    def test_text_body(self):
        """Test requesting non-JSON data like a diff."""
        status_code = 200
        headers, body = sample("pr_diff", status_code)
        data, rate_limit, more = sansio.decipher_response(status_code, headers, body)
        assert more is None
        assert rate_limit.remaining == 43
        assert data.startswith("diff --git")

    def test_no_ratelimit(self):
        """Test no ratelimit in headers."""
        status_code = 201
        headers = {
            "content-type": "application/json; charset=utf-8",
            "link": '<http://example.com>; test="unimportant"',
        }
        data = {
            "id": 208_045_946,
            "url": "https://api.github.com/repos/octocat/Hello-World/labels/bug",
            "name": "bug",
            "color": "f29513",
            "default": True,
        }
        body = json.dumps(data).encode("UTF-8")
        returned_data, rate_limit, more = sansio.decipher_response(
            status_code, headers, body
        )
        assert more is None
        assert rate_limit is None
        assert returned_data == data


class TestFormatUrl:

    """Tests for gidgethub.sansio.format_url()."""

    @pytest.mark.parametrize(
        "base_url",
        ["https://api.github.com/notifications", "https://my.host.com/notifications"],
    )
    def test_absolute_url(self, base_url):
        url = sansio.format_url(base_url, {}, base_url=base_url)
        assert url == base_url

    def test_different_base_and_absolute_url(self):
        url = sansio.format_url(
            "https://api.github.com/notifications",
            {},
            base_url="https://my.host.com/notifications",
        )
        assert url == "https://api.github.com/notifications"

    @pytest.mark.parametrize(
        "base_url", ["https://api.github.com", "https://my.host.com"]
    )
    def test_relative_url(self, base_url):
        url = sansio.format_url("/notifications", {}, base_url=base_url)
        assert url == f"{base_url}/notifications"

    def test_template(self):
        template_url = "https://api.github.com/users/octocat/gists{/gist_id}"
        template_data = {"gist_id": "1234"}
        # Substituting an absolute URL.
        url = sansio.format_url(template_url, template_data)
        assert url == "https://api.github.com/users/octocat/gists/1234"
        # No substituting an absolute URL.
        url = sansio.format_url(template_url, {})
        assert url == "https://api.github.com/users/octocat/gists"
        # Substituting a relative URL.
        url = sansio.format_url("/users/octocat/gists{/gist_id}", template_data)
        assert url == "https://api.github.com/users/octocat/gists/1234"

    def test_template_with_base_url(self):
        template_url = "https://my.host.com/users/octocat/gists{/gist_id}"
        template_data = {"gist_id": "1234"}
        # Substituting an absolute URL.
        url = sansio.format_url(
            template_url, template_data, base_url="https://my.host.com"
        )
        assert url == "https://my.host.com/users/octocat/gists/1234"
        # No substituting an absolute URL.
        url = sansio.format_url(template_url, {}, base_url="https://my.host.com")
        assert url == "https://my.host.com/users/octocat/gists"
        # Substituting a relative URL.
        url = sansio.format_url(
            "/users/octocat/gists{/gist_id}",
            template_data,
            base_url="https://my.host.com",
        )
        assert url == "https://my.host.com/users/octocat/gists/1234"

    @pytest.mark.parametrize(
        "base_url", ["https://api.github.com", "https://my.host.com"]
    )
    def test_quoting(self, base_url):
        template_url = "https://api.github.com/repos/python/cpython/labels{/name}"
        label = {"name": "CLA signed"}
        url = sansio.format_url(template_url, label, base_url=base_url)
        assert url == "https://api.github.com/repos/python/cpython/labels/CLA%20signed"
