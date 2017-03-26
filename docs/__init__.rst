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


.. exception:: HTTPException(status_code: http.HTTPStatus, *args: Any)

   A general exception to represent HTTP responses. Inherits from
   :exc:`GitHubException`.

   .. attribute:: status_code: http.HTTPStatus

      The status code that the exception represents.


.. exception:: RedirectionException

   Exception for 3XX HTTP responses.

   Inherits from :exc:`HTTPException`.


.. exception:: BadRequest

   Exception for 4XX HTTP responses.

   Inherits from :exc:`HTTPException`.


.. exception:: RateLimitExceeded(rate_limit: sansio.RateLimit)

    Raised when one's rate limit has been reached. A subclass of
    :exc:`BadRequest`.

    .. versionadded:: 2.0

    .. attribute:: rate_limit: sansio.RateLimit

        The :class:`~gidgethub.sansio.RateLimit` object with the rate
        limit details which triggered the raising of the exception.


.. exception:: InvalidField(errors: List[Any], *args: Any)

   Raised when a
   `field in a request is invalid <https://developer.github.com/v3/#client-errors>`_.

   Inherits from :exc:`BadRequest` and explicitly specifies a ``422`` status
   code. Details of what fields were invalid are stored in the :attr:`errors`
   attribute.

   .. attribute:: errors

      A list of error details for each field which was invalid.


.. exception:: GitHubBroken

   An exception representing 5XX HTTP responses.

   Inherits from :exc:`GitHubException`.

