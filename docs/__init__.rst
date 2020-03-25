:mod:`gidgethub` --- Exceptions
===============================

.. module:: gidgethub


Exceptions
----------

.. exception:: GitHubException

   Base exception for this library.


.. exception:: ValidationFailure

   An exception representing
   `failed validation of a webhook event <https://developer.github.com/webhooks/securing/#validating-payloads-from-github>`_.

   Inherits from :exc:`GitHubException`.


.. exception:: HTTPException(status_code, *args)

   A general exception to represent HTTP responses. Inherits from
   :exc:`GitHubException`. The *status_code* is expected to be an
   :class:`http.HTTPStatus` enum value.

   .. attribute:: status_code

      The :class:`http.HTTPStatus` status code that the exception represents.


.. exception:: RedirectionException

   Exception for 3XX HTTP responses.

   Inherits from :exc:`HTTPException`.


.. exception:: BadRequest

   Exception for 4XX HTTP responses.

   Inherits from :exc:`HTTPException`.


.. exception:: BadRequestUnknownError

   Exception for ``422`` status code responses which do not include a JSON
   response.

   .. versionadded:: XXX

   .. attribute:: response

      The response as returned by GitHub.


.. exception:: RateLimitExceeded(rate_limit)

    Raised when one's rate limit has been reached. A subclass of
    :exc:`BadRequest`.

    .. versionadded:: 2.0

    .. attribute:: rate_limit

        The :class:`~gidgethub.sansio.RateLimit` object with the rate
        limit details which triggered the raising of the exception.


.. exception:: InvalidField(errors, *args)

   Raised when a
   `field in a request is invalid <https://developer.github.com/v3/#client-errors>`_.

   Inherits from :exc:`BadRequest` and explicitly specifies a ``422`` status
   code. Details of what fields were invalid are stored in the :attr:`errors`
   attribute.

   .. attribute:: errors

      A list of error details for each field which was invalid.


.. exception:: ValidationError(errors, *args)

   A request was unable to be completed.

   Inherits from :exc:`BadRequest` a 422 HTTP response.

   .. attribute:: errors

      Error details.


.. exception:: GitHubBroken

   An exception representing 5XX HTTP responses.

   Inherits from :exc:`HTTPException`.


GraphQL-specific
''''''''''''''''

.. exception:: GraphQLException(message, response)

   Base exception for all GraphQL-related exceptions.

   Inherits from :exc:`GitHubException`.

   .. attribute:: response

      The decoded JSON response from GitHub.


.. exception:: BadGraphQLRequest(status_code, response)

   A 4XX HTTP response to a GraphQL request.

   Inherits from :exc:`GraphQLException`.

   .. attribute:: response

      The decoded JSON response from GitHub.


.. exception:: GraphQLAuthorizationFailure(response)

   A 401 HTTP response due to an authorization failure.

   Inherits from :exc:`BadGraphQLRequest`.

.. exception:: QueryError(response)

   An exception representing an error relating to the GraphQL query itself.

   Inherits from :exc:`GraphQLException`.
