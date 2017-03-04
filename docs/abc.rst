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

    All methods that make a request to GitHub have some common
    arguments. The *url_vars* argument is used to perform
    `URI template expansion <https://developer.github.com/v3/#hypermedia>`_.
    The *accept* argument specifies what response format is acceptable
    and can be constructed by using
    :func:`gidgethub.sansio.accept_format`.


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


    .. abstractcoroutine:: _request(self, method: str, url: str, headers: Mapping[str, str], body: bytes = None) -> Tuple[int, Mapping[str, str], bytes]

        Abstract :term:`coroutine` to make an HTTP request. The
        expected return value is a tuple consisting of the status
        code, headers, and body of the HTTP response.


    .. abstractcoroutine:: _sleep(seconds: float) -> None

        An abstract :term:`coroutine` which causes the coroutine to
        sleep for the specified number of seconds. This is used to
        prevent the user from going over their request
        `rate limit <https://developer.github.com/v3/#rate-limiting>`_.


    .. coroutine:: getitem(self, url: str, url_vars: Dict[str, str] = {}, *, accept=sansio.accept_format()) -> Any

        Get a single item from GitHub.

        The returned value is the decoded body of the response according
        to :func:`gidgethub.sansio.decipher_response`. As this method
        is only to be used for single items, no checking for pagination
        is performed.
