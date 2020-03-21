import http

from gidgethub import (
    BadGraphQLRequest,
    BadRequest,
    BadRequestUnknownError,
    GitHubBroken,
    GraphQLAuthorizationFailure,
    GraphQLException,
    HTTPException,
    InvalidField,
    RateLimitExceeded,
    RedirectionException,
    QueryError,
)
from gidgethub import sansio


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


def test_BadRequestUnknownError():
    exc = BadRequestUnknownError("uh-oh")
    assert exc.status_code == http.HTTPStatus.UNPROCESSABLE_ENTITY
    assert exc.response == "uh-oh"


def test_RateLimitExceeded():
    rate = sansio.RateLimit(limit=1, remaining=0, reset_epoch=1)
    exc = RateLimitExceeded(rate)
    assert exc.status_code == http.HTTPStatus.FORBIDDEN
    exc = RateLimitExceeded(rate, "stuff happened")
    assert str(exc) == "stuff happened"


def test_InvalidField():
    errors = [{"resource": "Issue", "field": "title", "code": "missing_field"}]
    exc = InvalidField(errors, "Validation Failed")
    assert exc.errors == errors
    assert exc.status_code == http.HTTPStatus.UNPROCESSABLE_ENTITY


def test_RedirectionException():
    exc = RedirectionException(http.HTTPStatus.MOVED_PERMANENTLY)
    assert exc.status_code == http.HTTPStatus.MOVED_PERMANENTLY


def test_GraphQLException():
    exc = GraphQLException("hello", {"hello": "world"})
    assert exc.response == {"hello": "world"}
    assert str(exc) == "hello"


def test_BadGraphQLRequest():
    response = {"message": "hello, world"}
    exc = BadGraphQLRequest(http.HTTPStatus(400), response)
    assert exc.status_code == http.HTTPStatus(400)
    assert exc.response == response
    assert str(exc) == response["message"]


def test_GraphQLAuthorizationFailure():
    response = {"message": "hello, world"}
    exc = GraphQLAuthorizationFailure(response)
    assert exc.response == response
    assert exc.status_code == http.HTTPStatus(401)
    assert str(exc) == response["message"]


def test_QueryError():
    response = {"errors": [{"message": "hello, world"}]}
    exc = QueryError(response)
    assert exc.response == response
    assert str(exc) == response["errors"][0]["message"]
