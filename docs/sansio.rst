:mod:`gidgethub.sansio` --- sans-I/O support
============================================

.. automodule:: gidgethub.sansio


Webhook events
--------------
`Webhook events <https://developer.github.com/webhooks/>`_ are represented by
:class:`Event` objects. The expectation is that a server will receive an HTTP
request from GitHub and then use :meth:`Event.from_http` to create an
:class:`Event` instance. For example::

  import os
  import aiohttp.web

  SECRET = os.environ["GITHUB_SECRET"]

  async def index(request: aiohttp.web.BaseRequest):
      headers = request.headers
      body = await request.read()
      event = gidgethub.Event.from_http(headers, body,
                                        secret=SECRET)

This is not required, though, as the :class:`Event` class can be constructed
in a more traditional way. The :func:`validate_event` function is also provided
to allow for manual validation that a event came from a supported project
without requiring the use of the :class:`Event` class.

.. function:: validate_event(payload: bytes, *, signature: str, secret: str) -> None

   `Validate the signature <https://developer.github.com/webhooks/securing/#validating-payloads-from-github>`_
   of a webhook event.

   :exc:`~gidgethub.ValidationFailure` is raised if the signature is malformed
   or if the provided signature does not match the calculated signature using
   *payload* and *secret*. If the validation passes then no exception is
   raised (i.e. there's no need to check the return value of the function as an
   exception is raised if validation fails).


.. class:: Event(data: JSONDict, *, event: str, delivery_id: str)

   Representation of a GitHub webhook event.

   .. attribute:: data

      The `payload <https://developer.github.com/webhooks/#payloads>`_ of the
      event.


   .. attribute:: event

      The string representation of the
      `triggering event <https://developer.github.com/webhooks/#events>`_.


   .. attribute:: delivery_id

      The unique ID of the event.


   .. classmethod:: from_http(headers: Mapping[str, str], body: bytes, *, secret: str = None)

      Construct an :class:`Event` instance from HTTP headers and body data.

      The *headers* mapping is expected to support lowercase keys.

      Since this method assumes the body of the HTTP request is JSON, a check
      is performed for a ``"content-type"`` header field of
      ``"application/json"``. If the content type does not match,
      :exc:`~gidgethub.BadRequest` is raised.

      If the appropriate headers are provided for event validation, then
      the *secret* argument is required. Any failure in validation
      (including not providing the *secret* argument) will lead to
      :exc:`~gidgethub.ValidationFailure` being raised.


Calling the GitHub API
----------------------
As well as receiving webhook events in response to actions occurring on GitHub,
you can use the `GitHub API <https://developer.github.com/v3/>`_ to make calls
to REST endpoints.


Requests
''''''''

.. autofunction:: accept_format

.. autofunction:: create_headers

.. autoclass:: RateLimit
   :members:


Responses
'''''''''

.. autofunction:: decipher_response
