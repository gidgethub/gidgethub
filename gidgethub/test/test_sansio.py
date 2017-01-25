import pytest

import gidgethub as gh
from .. import sansio


class TestValidate:

    """Tests for gidgethub.sansio.validate()."""

    secret = "123456"
    payload = "gidget".encode("UTF-8")
    hash_signature = "6ea124f8bfc2e6f5a0a40687201c351716110bec"
    signature = "sha1=" + hash_signature

    def test_malformed_signature(self):
        """Error out if the signature doesn't start with "sha1="."""
        with pytest.raises(gh.ValidationFailure):
            sansio.validate(self.payload, secret=self.secret,
                            signature=self.hash_signature)

    def test_validation(self):
        """Success case."""
        sansio.validate(self.payload, secret=self.secret,
                        signature=self.signature)

    def test_failure(self):
        with pytest.raises(gh.ValidationFailure):
            sansio.validate(self.payload + b'!', secret=self.secret,
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
        with pytest.raises(gh.BadRequest):
            sansio.Event.from_http(headers_no_content_type, self.data_bytes,
                                   secret=self.secret)

    def test_from_http_missing_secret(self):
        """Signature but no secret raises ValidationFailure."""
        with pytest.raises(gh.ValidationFailure):
            sansio.Event.from_http(self.headers, self.data_bytes)

    def test_from_http_missing_signature(self):
        """Secret but no signature raises ValidationFailure."""
        headers_no_sig = self.headers.copy()
        del headers_no_sig["X-Hub-Signature"]
        with pytest.raises(gh.ValidationFailure):
            sansio.Event.from_http(headers_no_sig, self.data_bytes,
                                   secret=self.secret)

    def test_from_http_bad_signature(self):
        with pytest.raises(gh.ValidationFailure):
            sansio.Event.from_http(self.headers, self.data_bytes,
                                   secret=self.secret + "no secret")
