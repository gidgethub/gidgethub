"""An async GitHub API library"""
__version__ = "4.0.0"

import http
from typing import Any


class GitHubException(Exception):

    """Base exception for this library."""


class ValidationFailure(GitHubException):

    """An exception representing failed validation of a webhook event."""

    # https://developer.github.com/webhooks/securing/#validating-payloads-from-github


class HTTPException(GitHubException):

    """A general exception to represent HTTP responses."""

    def __init__(self, status_code: http.HTTPStatus, *args: Any) -> None:
        self.status_code = status_code
        if args:
            super().__init__(*args)
        else:
            super().__init__(status_code.phrase)


class RedirectionException(HTTPException):

    """Exception for 3XX HTTP responses."""


class BadRequest(HTTPException):
    """The request is invalid.

    Used for 4XX HTTP errors.
    """

    # https://developer.github.com/v3/#client-errors


class BadRequestUnknownError(BadRequest):

    """A bad request whose response body is not JSON."""

    def __init__(self, response: str) -> None:
        self.response = response
        super().__init__(http.HTTPStatus.UNPROCESSABLE_ENTITY)


class RateLimitExceeded(BadRequest):

    """Request rejected due to the rate limit being exceeded."""

    # Technically rate_limit is of type gidgethub.sansio.RateLimit, but a
    # circular import comes about if you try to properly declare it.
    def __init__(self, rate_limit: Any, *args: Any) -> None:
        self.rate_limit = rate_limit

        if not args:
            super().__init__(http.HTTPStatus.FORBIDDEN, "rate limit exceeded")
        else:
            super().__init__(http.HTTPStatus.FORBIDDEN, *args)


class InvalidField(BadRequest):

    """A field in the request is invalid.

    Represented by a 422 HTTP Response. Details of what fields were
    invalid are stored in the errors attribute.
    """

    def __init__(self, errors: Any, *args: Any) -> None:
        """Store the error details."""
        self.errors = errors
        super().__init__(http.HTTPStatus.UNPROCESSABLE_ENTITY, *args)


class ValidationError(BadRequest):

    """A request was unable to be completed.

    Represented by a 422 HTTP response. Details of what went wrong
    are stored in the *errors* attribute.
    """

    def __init__(self, errors: Any, *args: Any) -> None:
        """Store the error details."""
        self.errors = errors
        super().__init__(http.HTTPStatus.UNPROCESSABLE_ENTITY, *args)


class GitHubBroken(HTTPException):

    """Exception for 5XX HTTP responses."""


class GraphQLException(GitHubException):

    """Base exception for the GraphQL v4 API."""

    def __init__(self, message: str, response: Any) -> None:
        self.response = response
        super().__init__(message)


class BadGraphQLRequest(GraphQLException):

    """A 4XX HTTP response."""

    def __init__(self, status_code: http.HTTPStatus, response: Any) -> None:
        assert 399 < status_code < 500
        self.status_code = status_code
        super().__init__(response["message"], response)


class GraphQLAuthorizationFailure(BadGraphQLRequest):

    """401 HTTP response to a bad oauth token."""

    def __init__(self, response: Any) -> None:
        super().__init__(http.HTTPStatus(401), response)


class QueryError(GraphQLException):

    """An error occurred while attempting to handle a GraphQL v4 query."""

    def __init__(self, response: Any) -> None:
        super().__init__(response["errors"][0]["message"], response)
