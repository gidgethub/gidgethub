import datetime

import pytest

from .. import BadRequest, ValidationFailure
from .. import sansio


class TestValidateEvent:

    """Tests for gidgethub.sansio.validate_event()."""

    secret = "123456"
    payload = "gidget".encode("UTF-8")
    hash_signature = "6ea124f8bfc2e6f5a0a40687201c351716110bec"
    signature = "sha1=" + hash_signature

    def test_malformed_signature(self):
        """Error out if the signature doesn't start with "sha1="."""
        with pytest.raises(ValidationFailure):
            sansio.validate_event(self.payload, secret=self.secret,
                                  signature=self.hash_signature)

    def test_validation(self):
        """Success case."""
        sansio.validate_event(self.payload, secret=self.secret,
                              signature=self.signature)

    def test_failure(self):
        with pytest.raises(ValidationFailure):
            sansio.validate_event(self.payload + b'!', secret=self.secret,
                                  signature=self.signature)


class TestEvent:

    """Tests for gidgethub.sansio.Event."""

    data = {"action": "opened"}
    data_bytes = '{"action": "opened"}'.encode("UTF-8")
    secret = "123456"
    headers = {"content-type": "application/json",
               "X-GitHub-Event": "pull_request",
               "X-GitHub-Delivery": "72d3162e-cc78-11e3-81ab-4c9367dc0958",
               "X-Hub-Signature": "sha1=13ed44049d52492cab0f3aa22215091d35be4d58"}

    def check_event(self, event):
        """Check that an event matches the test data provided by the class."""
        assert event.event == self.headers["X-GitHub-Event"]
        assert event.delivery_id == self.headers["X-GitHub-Delivery"]
        assert event.data == self.data

    def test_init(self):
        ins = sansio.Event(self.data, event=self.headers["X-GitHub-Event"],
                           delivery_id=self.headers["X-GitHub-Delivery"])
        self.check_event(ins)

    def test_from_http(self):
        """Construct an event from complete HTTP information."""
        event = sansio.Event.from_http(self.headers, self.data_bytes,
                                       secret=self.secret)
        self.check_event(event)

    def test_from_http_not_json(self):
        """Only accept data when content-type is application/json."""
        headers_no_content_type = self.headers.copy()
        del headers_no_content_type["content-type"]
        with pytest.raises(BadRequest):
            sansio.Event.from_http(headers_no_content_type, self.data_bytes,
                                   secret=self.secret)

    def test_from_http_missing_secret(self):
        """Signature but no secret raises ValidationFailure."""
        with pytest.raises(ValidationFailure):
            sansio.Event.from_http(self.headers, self.data_bytes)

    def test_from_http_missing_signature(self):
        """Secret but no signature raises ValidationFailure."""
        headers_no_sig = self.headers.copy()
        del headers_no_sig["X-Hub-Signature"]
        with pytest.raises(ValidationFailure):
            sansio.Event.from_http(headers_no_sig, self.data_bytes,
                                   secret=self.secret)

    def test_from_http_bad_signature(self):
        with pytest.raises(ValidationFailure):
            sansio.Event.from_http(self.headers, self.data_bytes,
                                   secret=self.secret + "no secret")


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
        headers = sansio.create_headers(user_agent, accept=test_api,
                                        oauth_token=oauth_token)
        assert len(headers) == 3
        for key in headers.keys():
            assert key == key.lower()
        assert headers["user-agent"] == user_agent
        assert headers["accept"] == test_api
        assert headers["authorization"] == f"token {oauth_token}"


class TestRateLimit:

    def test_init(self):
        left = 42
        rate = 64
        reset = datetime.datetime.now(datetime.timezone.utc)
        rate_limit = sansio.RateLimit(left=left, rate=rate,
                                      reset_epoch=reset.timestamp())
        assert rate_limit.left == left
        assert rate_limit.rate == rate
        assert rate_limit.reset_datetime == reset

    def test_from_http(self):
        left = 42
        rate = 65
        reset = datetime.datetime.now(datetime.timezone.utc)
        headers = {"X-RateLimit-Limit": str(rate),
                   "X-RateLimit-Remaining": str(left),
                   "X-RateLimit-Reset": str(reset.timestamp())}
        rate_limit = sansio.RateLimit.from_http(headers)
        assert rate_limit.rate == rate
        assert rate_limit.left == left
        assert rate_limit.reset_datetime == reset
