import http

from .. import (BadRequest, GitHubBroken, HTTPException, InvalidField,
                RedirectionException)


class TestHTTPException:

    def test_status_code_only(self):
        """The status is the message if a better one isn't provided."""
        exc = HTTPException(http.HTTPStatus.BAD_REQUEST)
        assert exc.status_code == http.HTTPStatus.BAD_REQUEST
        assert str(exc) == "Bad Request"

    def test_message(self):
        """A provided message overrides the status code as the message."""
        message = "a better message"
        exc = HTTPException(http.HTTPStatus.BAD_REQUEST, message)
        assert exc.status_code == http.HTTPStatus.BAD_REQUEST
        assert str(exc) == message


def test_GitHubBroken():
    exc = GitHubBroken(http.HTTPStatus.BAD_GATEWAY)
    assert exc.status_code == http.HTTPStatus.BAD_GATEWAY

def test_BadRequest():
    exc = BadRequest(http.HTTPStatus.BAD_REQUEST)
    assert exc.status_code == http.HTTPStatus.BAD_REQUEST

def test_InvalidField():
    errors = [{"resource": "Issue", "field": "title", "code": "missing_field"}]
    exc = InvalidField(errors, "Validation Failed")
    assert exc.errors == errors
    assert exc.status_code == http.HTTPStatus.UNPROCESSABLE_ENTITY

def test_RedirectionException():
    exc = RedirectionException(http.HTTPStatus.MOVED_PERMANENTLY)
    assert exc.status_code == http.HTTPStatus.MOVED_PERMANENTLY
