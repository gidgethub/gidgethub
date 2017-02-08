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
in a traditional way. The :func:`validate_event` function is also provided to
allow for manual validation that a event came from a supported project.

.. autofunction:: validate_event


.. autoclass:: Event
   :members:


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
