:mod:`gidgethub.sansio` --- sans-I/O support
============================================

.. module:: gidgethub.sansio

Webhook events
--------------
`Webhook events <https://developer.github.com/webhooks/>`_ are represented by
:class:`Event` objects. The expectation is that a server will receive an HTTP
request from GitHub and then use :meth:`Event.from_http` to create an
:class:`Event` instance. For example::

  import os
  import aiohttp.web

  SECRET = os.environ["GITHUB_SECRET"]

  async def index(request):
      headers = request.headers
      body = await request.read()
      event = gidgethub.Event.from_http(headers, body,
                                        secret=SECRET)

This is not required, though, as the :class:`Event` class can be constructed
in a more traditional way. The :func:`validate_event` function is also provided
to allow for manual validation that a event came from a supported project
without requiring the use of the :class:`Event` class.

.. function:: validate_event(payload, *, signature, secret)

   `Validate the signature <https://developer.github.com/webhooks/securing/#validating-payloads-from-github>`_
   of a webhook event.

   :exc:`~gidgethub.ValidationFailure` is raised if the signature is malformed
   or if the provided signature does not match the calculated signature using
   *payload* and *secret*. If the validation passes then no exception is
   raised (i.e. there's no need to check the return value of the function as an
   exception is raised if validation fails).


.. class:: Event(data, *, event, delivery_id)

   Representation of a GitHub webhook event.

   .. attribute:: data

      The `payload <https://developer.github.com/webhooks/#payloads>`_ of the
      event.


   .. attribute:: event

      The string representation of the
      `triggering event <https://developer.github.com/webhooks/#events>`_.


   .. attribute:: delivery_id

      The unique ID of the event.


   .. classmethod:: from_http(headers, body, *, secret=None)

      Construct an :class:`Event` instance from HTTP headers and body data.

      The *headers* mapping is expected to support lowercase keys.

      Since this method assumes the body of the HTTP request is only of the
      `content type that GitHub sends <https://developer.github.com/webhooks/creating/#content-type>`_,
      :exc:`~gidgethub.BadRequest` is raised if the content type is
      unexpected.

      If the appropriate headers are provided for event validation, then
      the *secret* argument is required. Any failure in validation
      (including not providing the *secret* argument) will lead to
      :exc:`~gidgethub.ValidationFailure` being raised.


Calling the GitHub API
----------------------
As well as receiving webhook events in response to actions occurring on GitHub,
you can use the `GitHub API <https://developer.github.com/v3/>`_ to make calls
to REST endpoints. This library provides support to both construct a request to
the GitHub API as well as deciphering the response to a request.


Requests
''''''''

This module provides functions to help in the construction of a URL request
by helping to automate the GitHub-specific aspects of a REST call.
::

  import requests

  request_headers = create_headers("brettcannon", oauth_token=auth)
  url = "https://api.github.com/repos/brettcannon/gidgethub/issues/1"
  response = requests.get(url, headers=request_headers)

.. function:: accept_format(*, version="v3", media=None, json=True)

   Construct the specification of the format that a request should return. This
   is used in the ``accept`` header field of a request to specify the
   `media type <https://developer.github.com/v3/media/>`_.

   The *version* argument specifies what version of the GitHub API that the
   request applies to. Typically this only needs to be specified if you are
   using an API that is in beta.

   The *media* argument along with the *json* argument specifies what format
   the response should take. Do note that only some GitHub API endpoints support
   alternative formats from the default JSON format. For example, if you wanted
   a comment body to include the rendered HTML then the function call would be
   ``accept_format(media="html")`` to get a media type of
   ``application/vnd.github.v3.html+json``. If you wanted the diff of a commit
   then the function call would be ``accept_format(media="diff", json=False)``
   to get a media type of ``application/vnd.github.v3.diff``.

   The default arguments of this function will always return the
   `latest version <https://developer.github.com/v3/#current-version>`_ of the
   GitHub API with the default response format that this library is designed to
   support.


.. function:: create_headers(requester, *, accept=accept_format(), oauth_token=None, jwt=None)

   Create a dict representing GitHub-specific header fields.

   The user agent is set according to who the *requester* is.
   `GitHub asks <https://developer.github.com/v3/#user-agent-required>`_ it be
   either a username or project name.

   The *accept* argument corresponds to the ``'accept'`` field and defaults to
   the default result of :func:`accept_format`. You should only need to change
   this value if you are using a different version of the API -- e.g. one that
   is under development -- or if you are looking for a different format for the
   response, e.g. wanting the rendered HTML of a Markdown file.

   The *oauth_token* allows making an
   `authenticated request <https://developer.github.com/v3/#authentication>`_.
   This can be important if you need the expanded rate limit provided by an
   authenticated request.

   The *jwt* allows making an authenticated request as a `GitHub App
   <https://developer.github.com/apps/building-github-apps/authenticating-with-github-apps/#authenticating-as-a-github-app>`_.
   You can pass only one: *oauth_token* or *jwt*, but not both.

   ``ValueError`` will be raised if both *jwt* and *oauth_token* are supplied.

   For consistency, all keys in the returned dict will be lowercased.

   .. versionchanged:: 3.0

       Added ``jwt`` argument.


Responses
'''''''''

Decipher a response from the GitHub API gather together all of the details
that are provided to you. Continuing from the example in the Requests_ section::

  # Assuming `response` contains a requests.Response object.
  import datetime


  status_code = response.status_code
  headers = response.headers
  body = response.content
  data, rate, more = decipher_response(status_code, headers, body)
  # Response details are in `data`.
  if more:
      if not rate.remaining:
          now = datetime.datetime.now(datetime.tzinfo.utc)
          wait = rate.reset_datetime - now
          time.sleep(wait.total_seconds())
      response_more = requests.get(more, headers=request_headers)
      # Decipher `response_more` ...

.. class:: RateLimit(*, limit, remaining, reset_epoch)

    The `rate limit <https://developer.github.com/v3/#rate-limiting>`_ imposed
    upon the requester.

    The *reset_epoch* argument is expected to be UTC seconds from the epoch.

    The boolean value of an instance whether another request can be made. This
    is determined based on whether there are any remaining requests or if the
    reset datetime has passed.


    .. attribute:: limit

        The maximum limit of requests per hour the requester can make.


    .. attribute:: remaining

        How many requests are left for the request until their quota is reset.


    .. attribute:: reset_datetime

        The :class:`datetime.datetime` object representing when the requester's
        quota is refreshed. The object is timezone-aware to UTC.


    .. classmethod:: from_http(headers)

        Create a :class:`RateLimit` instance from the HTTP headers of a GitHub API
        response.  Returns ``None`` if the ratelimit is not found in the headers.

        .. versionchanged:: 3.0

            Returns ``None`` if the ratelimit is not found in the headers.

.. function:: decipher_response(status_code, headers, body)

    Decipher an HTTP response for a GitHub API request.

    The mapping providing the headers is expected to support lowercase keys.

    The parameters of this function correspond to the three main parts
    of an HTTP response: the status code, headers, and body. Assuming
    no errors which lead to an exception being raised, a 3-item tuple
    is returned. The first item is the decoded body (typically a JSON
    object, but possibly ``None`` or a string depending on the content
    type of the body). The second item is a :class:`RateLimit` instance
    based on what the response specified.

    The last item of the tuple is the URL where to request the
    `next set of results <https://developer.github.com/v3/#pagination>`_.
    If there are no more results then ``None`` is returned. Do be aware
    that the URL
    `can be a URI template <https://developer.github.com/v3/#link-header>`_
    and so it may need to be expanded.

    If the status code is anything other than ``200``, ``201``, or ``204``,
    then an appropriate :exc:`~gidgethub.HTTPException` is raised.


Utilities
---------

.. function:: format_url(url, url_vars, *, base_url=DOMAIN)

    Construct a URL for the GitHub API.

    The URL may be absolute or relative. In the latter case the appropriate
    domain will be added. This is to help when copying the relative URL directly
    from the GitHub developer documentation.

    The dict provided in *url_vars* is used in
    `URI template expansion <https://developer.github.com/v3/#hypermedia>`_.
    Appropriate URL quoting is automatically done on the values of the dict.

    Enterprise GitHub users can specify their custom base URL in *base_url*.
    By default, https://api.github.com/ is used as the base URL.
