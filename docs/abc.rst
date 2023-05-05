:mod:`gidgethub.abc` --- Abstract base class for simplified requests
====================================================================

.. module:: gidgethub.abc

While :mod:`gidgethub.sansio` provides all of the building blocks
necessary to make a request to the GitHub API, it still requires you
to pull together all the requisite parts of a request for the HTTP
library you prefer to use. As that can be repetitive and mostly
boilerplate between HTTP libraries, this module was created to
abstract out the HTTP library being used so all boilerplate could
be taken care.

Users should instantiate an appropriate subclass once for any single
set of calls to the GitHub API. Then one can use the appropriate method
to make requests simply, e.g.::

    # Assume `gh` has an implementation of GitHubAPI.
    data = await gh.getitem("/rate_limit")

This allows one to use the GitHub API directly without dealing with
lower-level details. Most importantly, any changes to the GitHub API
does not require an update to the library, allowing one to use
experimental APIs without issue.


.. class:: GitHubAPI(requester, *, oauth_token=None, cache=None, base_url=sansio.DOMAIN)

    Provide an :py:term:`abstract base class` which abstracts out the
    HTTP library being used to send requests to GitHub. The class is
    initialized with the requester's name and optionally their
    OAuth token and a cache object.

    To allow for
    `conditional requests <https://docs.github.com/en/free-pro-team@latest/rest/overview/resources-in-the-rest-api#conditional-requests>`_,
    one can provide a :class:`collections.abc.MutableMapping` object
    for the *cache* argument to cache requests. It is up to the
    caching object to provide any caching scheme that is desired
    (e.g. the ``Cache`` classes provided by the
    `cachetools package <https://pypi.org/project/cachetools/>`_).

    There are common arguments across methods that make requests to
    GitHub. The *url_vars* argument is used to perform
    `URI template expansion <https://docs.github.com/en/free-pro-team@latest/rest/overview/resources-in-the-rest-api#hypermedia>`_
    via :func:`gidgethub.sansio.format_url`.The *accept* argument
    specifies what response format is acceptable and can be
    constructed by using :func:`gidgethub.sansio.accept_format`. For
    methods that send data to GitHub, there is a *data* argument which
    accepts an object which can be serialized to JSON (because
    ``None`` is a legitimate JSON value, ``""`` is used to represent
    no data). The *extra_headers* argument optionally is ``dict[str, str]``,
    and allows passing extra headers to the request specifying extra
    options that the GitHub API allows.

    The returned value for GitHub requests is the decoded body of the
    response according to :func:`gidgethub.sansio.decipher_response`.
    If the status code returned by the HTTP request is anything other
    than ``200``, ``201``, or ``204``, then an appropriate
    :exc:`~gidgethub.HTTPException` is raised.

    .. versionchanged:: 2.0
        Methods no longer automatically sleep when there is a chance
        of exceeding the
        `rate limit <https://docs.github.com/en/free-pro-team@latest/rest/overview/resources-in-the-rest-api#rate-limiting>`_.
        This leads to :exc:`~gidgethub.RateLimitExceeded` being raised
        when the rate limit has been execeeded.

    .. versionchanged:: 2.3
        Introduced the *cache* argument to the constructor.

    .. versionchanged:: 4.0
        Introduced the *base_url* argument to the constructor.

    .. attribute:: requester

        The requester's name (typically a GitHub username or project
        name).


    .. attribute:: oauth_token

        The provided OAuth token (if any).

    .. attribute:: base_url

        The base URL for the GitHub API. By default it is https://api.github.com.
        Enterprise GitHub users can specify a custom URL endpoint.

    .. attribute:: rate_limit

        An instance of :class:`gidgethub.sansio.RateLimit`
        representing the last known rate limit imposed upon the user.
        This attribute is automatically updated after every successful
        HTTP request.

    .. py:method:: _request(method, url, headers, body=b'')
        :async:
        :abstractmethod:

        An abstract :term:`coroutine` to make an HTTP request. The
        given *headers* will have lower-case keys and include not only
        GitHub-specific fields but also ``content-length`` (and
        ``content-type`` if appropriate).

        The expected return value is a tuple consisting of the status
        code, headers, and the body of the HTTP response. The headers
        dictionary is expected to work with lower-case keys.


    .. py:method:: sleep(seconds)
        :async:
        :abstractmethod:

        An abstract :term:`coroutine` which causes the coroutine to
        sleep for the specified number of seconds. This is provided to
        help prevent from going over one's
        `rate limit <https://docs.github.com/en/free-pro-team@latest/rest/overview/resources-in-the-rest-api#rate-limiting>`_.

        .. versionchanged:: 2.0

            Renamed from ``_sleep()``.


    .. py:method:: getitem(url, url_vars={}, *, accept=sansio.accept_format(), jwt=None, oauth_token=None, extra_headers=None)
        :async:

        Get a single item from GitHub.

        *jwt* is the value of the JSON web token, for authenticating as a GitHub
        App.

        *oauth_token* is the value of the oauth token, for making an authenticated
        API call.

        Only one of *oauth_token* or *jwt* may be passed. A ``ValueError`` is
        raised if both are passed. If neither was passed, it defaults to the
        value of the *oauth_token* attribute.

        .. versionchanged:: 3.0

            Added *jwt* and *oauth_token*.

        .. note::
            For ``GET`` calls that can return multiple values and
            potentially require pagination, see ``getiter()``.

    .. py:method:: getstatus(url, url_vars={}, *, accept=sansio.accept_format(), jwt=None, oauth_token=None)
        :async:

        Get a single item's *HTTP status* from GitHub.

        *jwt* is the value of the JSON web token, for authenticating as a GitHub
        App.

        *oauth_token* is the value of the oauth token, for making an authenticated
        API call.

        Only one of *oauth_token* or *jwt* may be passed. A ``ValueError`` is
        raised if both are passed. If neither was passed, it defaults to the
        value of the *oauth_token* attribute.

        .. note::
            This method discards any returned content, and is only for use
            on API endpoints like /orgs/{org}/members/{username} where the
            HTTP response code is the relevant answer.

    .. py:method:: getiter(url, url_vars={}, *, accept=sansio.accept_format(), jwt=None, oauth_token=None, iterable_key="items", , extra_headers=None)
        :async:

        Get all items from a GitHub API endpoint.

        An asynchronous iterable is returned which will yield all items
        from the endpoint (i.e. use ``async for`` on the result). Any
        `pagination <https://docs.github.com/en/free-pro-team@latest/rest/overview/resources-in-the-rest-api#pagination>`_
        will automatically be followed.

        *jwt* is the value of the JSON web token, for authenticating as a GitHub
        App.

        *oauth_token* is the value of the oauth token, for making an authenticated
        API call.

        Only one of *oauth_token* or *jwt* may be passed. A ``ValueError`` is
        raised if both are passed. If neither was passed, it defaults to the
        value of the *oauth_token* attribute.

        *iterable_key* is the value of the dictionary key to be iterated upon.
        It defaults to ``"items"``.

        .. versionchanged:: 3.0

            Added *jwt* and *oauth_token*.

        .. versionchanged:: 3.1

            Added support for endpoints which return a JSON object with an
            ``items`` value instead of a list.

        .. versionchanged:: 5.1.0

            Added *iterable_key*.

        .. note::
            For ``GET`` calls that return only a single item, see
            :meth:`getitem`.


    .. py:method:: post(url, url_vars={}, *, data, accept=sansio.accept_format(), jwt=None, oauth_token=None, content_type="application/json", extra_headers=None)
        :async:

        Send a ``POST`` request to GitHub.

        *jwt* is the value of the JSON web token, for authenticating as a GitHub
        App.

        *oauth_token* is the value of the oauth token, for making an authenticated
        API call.

        Only one of *oauth_token* or *jwt* may be passed. A ``ValueError`` is
        raised if both are passed. If neither was passed, it defaults to the
        value of the *oauth_token* attribute.

        *content_type* is the value of the desired request header's content type.
        If supplied, the data will be passed as the body in its raw format.
        If not supplied, it will assume the default "application/json" content type,
        and the data will be parsed as JSON.

        A few GitHub POST endpoints do not take any *data* argument, for example
        the endpoint to `create an installation access token <https://docs.github.com/en/free-pro-team@latest/developers/apps/creating-a-github-app-from-a-manifest#implementing-the-github-app-manifest-flow>`_.
        For this situation, you can pass ``data=b""``.


        .. versionchanged:: 4.2.0
            Added *content_type*.


        .. versionchanged:: 3.0

            Added *jwt* and *oauth_token*.


    .. py:method:: patch(url, url_vars={}, *, data, accept=sansio.accept_format(), jwt=None, oauth_token=None, extra_headers=None)
        :async:

        Send a ``PATCH`` request to GitHub.

        *jwt* is the value of the JSON web token, for authenticating as a GitHub
        App.

        *oauth_token* is the value of the oauth token, for making an authenticated
        API call.

        Only one of *oauth_token* or *jwt* may be passed. A ``ValueError`` is
        raised if both are passed. If neither was passed, it defaults to the
        value of the *oauth_token* attribute.

        .. versionchanged:: 3.0

            Added *jwt* and *oauth_token*.


    .. py:method:: put(url, url_vars={}, *, data=b"", accept=sansio.accept_format(), jwt=None, oauth_token=None, extra_headers=None)
        :async:

        Send a ``PUT`` request to GitHub.

        Be aware that some ``PUT`` endpoints such as
        `locking an issue <https://docs.github.com/en/rest/issues/issues#lock-an-issue>`_
        will return no content, leading to ``None`` being returned.

        *jwt* is the value of the JSON web token, for authenticating as a GitHub
        App.

        *oauth_token* is the value of the oauth token, for making an authenticated
        API call.

        Only one of *oauth_token* or *jwt* may be passed. A ``ValueError`` is
        raised if both are passed. If neither was passed, it defaults to the
        value of the *oauth_token* attribute.

        .. versionchanged:: 3.0

            Added *jwt* and *oauth_token*.


    .. py:method:: delete(url, url_vars={}, *, data=b"", accept=sansio.accept_format(), jwt=None, oauth_token=None, extra_headers=None)
        :async:

        Send a ``DELETE`` request to GitHub.

        *jwt* is the value of the JSON web token, for authenticating as a GitHub
        App.

        *oauth_token* is the value of the oauth token, for making an authenticated
        API call.

        Only one of *oauth_token* or *jwt* may be passed. A ``ValueError`` is
        raised if both are passed. If neither was passed, it defaults to the
        value of the *oauth_token* attribute.

        .. versionchanged:: 2.5

            Added *data* argument.

        .. versionchanged:: 3.0

            Added *jwt* and *oauth_token*.

    .. py:method:: graphql(query, *, endpoint="https://api.github.com/graphql", **variables)
        :async:

        Make a request of the `GraphQL v4 API <https://docs.github.com/en/free-pro-team@latest/graphql>`_.

        The *endpoint* argument specifies the
        `root endpoint <https://docs.github.com/en/free-pro-team@latest/graphql/guides/forming-calls-with-graphql#the-graphql-endpoint>`_
        to use for the GraphQL request.
        The *variables* argument collects all other keyword arguments to pass in
        `variables <https://docs.github.com/en/free-pro-team@latest/graphql/guides/forming-calls-with-graphql#working-with-variables>`_
        for the query.

        Exceptions raised directly by this method all subclass
        :exc:`~gidgethub.GraphQLException`.

        .. versionadded:: 4.0
