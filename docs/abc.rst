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
    `conditional requests <https://developer.github.com/v3/#conditional-requests>`_,
    one can provide a :class:`collections.abc.MutableMapping` object
    for the *cache* argument to cache requests. It is up to the
    caching object to provide any caching scheme that is desired
    (e.g. the ``Cache`` classes provided by the
    `cachetools package <https://pypi.org/project/cachetools/>`_).

    There are common arguments across methods that make requests to
    GitHub. The *url_vars* argument is used to perform
    `URI template expansion <https://developer.github.com/v3/#hypermedia>`_
    via :func:`gidgethub.sansio.format_url`.The *accept* argument
    specifies what response format is acceptable and can be
    constructed by using :func:`gidgethub.sansio.accept_format`. For
    methods that send data to GitHub, there is a *data* argument which
    accepts an object which can be serialized to JSON (because
    ``None`` is a legitimate JSON value, ``""`` is used to represent
    no data).

    The returned value for GitHub requests is the decoded body of the
    response according to :func:`gidgethub.sansio.decipher_response`.
    If the status code returned by the HTTP request is anything other
    than ``200``, ``201``, or ``204``, then an appropriate
    :exc:`~gidgethub.HTTPException` is raised.

    .. versionchanged:: 2.0
        Methods no longer automatically sleep when there is a chance
        of exceeding the
        `rate limit <https://developer.github.com/v3/#rate-limiting>`_.
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

    .. abstractcoroutine:: _request(method, url, headers, body=b'')

        An abstract :term:`coroutine` to make an HTTP request. The
        given *headers* will have lower-case keys and include not only
        GitHub-specific fields but also ``content-length`` (and
        ``content-type`` if appropriate).

        The expected return value is a tuple consisting of the status
        code, headers, and the body of the HTTP response. The headers
        dictionary is expected to work with lower-case keys.


    .. abstractcoroutine:: sleep(seconds)

        An abstract :term:`coroutine` which causes the coroutine to
        sleep for the specified number of seconds. This is provided to
        help prevent from going over one's
        `rate limit <https://developer.github.com/v3/#rate-limiting>`_.

        .. versionchanged:: 2.0

            Renamed from ``_sleep()``.


    .. coroutine:: getitem(url, url_vars={}, *, accept=sansio.accept_format(), jwt=None, oauth_token=None)

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


    .. coroutine:: getiter(url, url_vars={}, *, accept=sansio.accept_format(), jwt=None, oauth_token=None)

        Get all items from a GitHub API endpoint.

        An asynchronous iterable is returned which will yield all items
        from the endpoint (i.e. use ``async for`` on the result). Any
        `pagination <https://developer.github.com/v3/#pagination>`_
        will automatically be followed.

        *jwt* is the value of the JSON web token, for authenticating as a GitHub
        App.

        *oauth_token* is the value of the oauth token, for making an authenticated
        API call.

        Only one of *oauth_token* or *jwt* may be passed. A ``ValueError`` is
        raised if both are passed. If neither was passed, it defaults to the
        value of the *oauth_token* attribute.

        .. versionchanged:: 3.0

            Added *jwt* and *oauth_token*.

        .. versionchanged:: 3.1

            Added support for for endpoints which return a JSON object with an
            ``items`` value instead of a list.

        .. note::
            For ``GET`` calls that return only a single item, see
            :meth:`getitem`.


    .. coroutine:: post(url, url_vars={}, *, data, accept=sansio.accept_format(), jwt=None, oauth_token=None)

        Send a ``POST`` request to GitHub.

        *jwt* is the value of the JSON web token, for authenticating as a GitHub
        App.

        *oauth_token* is the value of the oauth token, for making an authenticated
        API call.

        Only one of *oauth_token* or *jwt* may be passed. A ``ValueError`` is
        raised if both are passed. If neither was passed, it defaults to the
        value of the *oauth_token* attribute.

        A few GitHub POST endpoints do not take any *data* argument, for example
        the endpoint to `create an installation access token <https://developer.github.com/v3/apps/#create-a-github-app-from-a-manifest>`_. For this situation, you can pass ``data=b""``.

        .. versionchanged:: 3.0

            Added *jwt* and *oauth_token*.


    .. coroutine:: patch(url, url_vars={}, *, data, accept=sansio.accept_format(), jwt=None, oauth_token=None)

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


    .. coroutine:: put(url, url_vars={}, *, data=b"", accept=sansio.accept_format(), jwt=None, oauth_token=None)

        Send a ``PUT`` request to GitHub.

        Be aware that some ``PUT`` endpoints such as
        `locking an issue <https://developer.github.com/v3/issues/#lock-an-issue>`_
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


    .. coroutine:: delete(url, url_vars={}, *, data=b"", accept=sansio.accept_format(), jwt=None, oauth_token=None)

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

    .. coroutine:: graphql(query, *, endpoint="https://api.github.com/graphql", **variables)

       Make a request of the `GraphQL v4 API <https://developer.github.com/v4/>`_.

       The *endpoint* argument specifies the
       `root endpoint <https://developer.github.com/v4/guides/forming-calls/#the-graphql-endpoint>`_
       to use for the GraphQL request.
       The *variables* argument collects all other keyword arguments to pass in
       `variables <https://developer.github.com/v4/guides/forming-calls/#working-with-variables>`_
       for the query.

       Exceptions raised directly by this method all subclass
       :exc:`~gidgethub.GraphQLException`.

       .. versionadded:: 4.0
