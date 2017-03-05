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


.. class:: GitHubAPI(requester: str, *, oauth_token: str = None)

    Provide an :py:term:`abstract base class` which abstracts out the
    HTTP library being used to send requests to GitHub. The class is
    initialized with the requester's name and (optionally) their
    OAuth token.

    There are common arguments across methods that make requests to
    GitHub. The *url_vars* argument is used to perform
    `URI template expansion <https://developer.github.com/v3/#hypermedia>`_.
    The *accept* argument specifies what response format is acceptable
    and can be constructed by using
    :func:`gidgethub.sansio.accept_format`. For methods that send data
    to GitHub, there is a *data* argument which accepts an object
    which can be serialized to JSON (because ``None`` is a legitimate
    JSON value, ``""`` is used to represent no data).

    The returned value for GitHub requests is the decoded body of the
    response according to :func:`gidgethub.sansio.decipher_response`.
    If the status code returned by the HTTP request is anything other
    than ``200``, ``201``, or ``204``, then an appropriate
    :exc:`~gidgethub.HTTPException` is raised.


    .. attribute:: requester

        The requester's name (typically a GitHub username or project
        name).


    .. attribute:: oauth_token

        The provided OAuth token (if any).


    .. attribute:: rate_limit

        An instance of :class:`gidgethub.sansio.RateLimit`
        representing the last known rate limit imposed upon the user.
        This attribute is automatically updated after every successful
        HTTP request.


    .. abstractcoroutine:: _request(self, method: str, url: str, headers: Mapping[str, str], body: bytes = b'') -> Tuple[int, Mapping[str, str], bytes]

        An abstract :term:`coroutine` to make an HTTP request. The
        given *headers* will have lower-case keys and include not only
        GitHub-specific fields but also ``content-length`` (and
        ``content-type`` if appropriate).

        The expected return value is a tuple consisting of the status
        code, headers, and the body of the HTTP response. The headers
        dictionary is expected to work with lower-case keys.


    .. abstractcoroutine:: _sleep(seconds: float) -> None

        An abstract :term:`coroutine` which causes the coroutine to
        sleep for the specified number of seconds. This is used to
        help prevent the user from going over their request
        `rate limit <https://developer.github.com/v3/#rate-limiting>`_.


    .. coroutine:: getitem(url: str, url_vars: Dict[str, str] = {}, *, accept=sansio.accept_format()) -> Any

        Get a single item from GitHub.

        .. note::
            For ``GET`` calls that can return multiple values and
            potentially require pagination, see ``getiter()``.


    .. coroutine:: getiter(url: str, url_vars: Dict[str, str] = {}, *,
                      accept: str = sansio.accept_format()) -> AsyncIterable[Any]

        Get all items from a GitHub API endpoint.

        An asynchronous iterable is returned which will yield all items
        from the endpoint (i.e. use ``async for`` on the result). Any
        `pagination <https://developer.github.com/v3/#pagination>`_
        will automatically be followed.

        .. note::
            For ``GET`` calls that return only a single item, see
            :meth:`getitem`.

    .. coroutine:: post(url: str, url_vars: Dict[str, str] = {}, *, data: Any, accept: str = sansio.accept_format()) -> Any

        Send a ``POST`` request to GitHub.


    .. coroutine:: patch(url: str, url_vars: Dict[str, str] = {}, *, data: Any, accept: str = sansio.accept_format()) -> Any

        Send a ``PATCH`` request to GitHub.


    .. coroutine:: put(url: str, url_vars: Dict[str, str] = {}, *, data: Any = "", accept: str = sansio.accept_format()) -> Any

        Send a ``PUT`` request to GitHub.

        Be aware that some ``PUT`` endpoints such as
        `locking an issue <https://developer.github.com/v3/issues/#lock-an-issue>`_
        will return no content, leading to ``None`` being returned.


    .. coroutine:: delete(url: str, url_vars: Dict[str, str] = {}, *, accept: str = sansio.accept_format()) -> None

        Send a ``DELETE`` request to GitHub.
