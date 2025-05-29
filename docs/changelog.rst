Changelog
=========

Unreleased
----------

- Make :meth:`gidgethub.abc.GitHubAPI.getiter` be iterative instead of
  recursive
  (`PR #219 <https://github.com/gidgethub/gidgethub/pull/219>`_)

- :meth:`gidgethub.apps.get_jwt` now accepts an ``expiration`` parameter to
  configure JWT token expiration time
  (`PR #215 <https://github.com/gidgethub/gidgethub/pull/215>`_)

- Add support for Python 3.12-3.13 and drop EOL Python 3.7
  (`PR #209 <https://github.com/gidgethub/gidgethub/pull/209>`_)

5.3.0
-----

- Add support passing ``extra_headers`` when making requests
  (`PR #192 <https://github.com/gidgethub/gidgethub/pull/192>`_)

- Add a getstatus() method for APIs that do not return content.
  (`PR #194 <https://github.com/gidgethub/gidgethub/pull/194>`_)

5.2.1
-----

- Fix cgi and importlib_resources deprecations.
  (`PR #185 <https://github.com/gidgethub/gidgethub/pull/185>`_)

- Add support for Python 3.11 and drop EOL Python 3.6
  (`PR #184 <https://github.com/gidgethub/gidgethub/pull/184>`_)

5.2.0
-----

- Make the minimum version of PyJWT be v2.4.0.

5.1.0
-----

- Use ``X-Hub-Signature-256`` header for webhook validation when available.
  (`PR #160 <https://github.com/gidgethub/gidgethub/pull/160>`_).

- The documentation is now built using Sphinx v>= 4.0.0.
  (`Issue #143 <https://github.com/gidgethub/gidgethub/issues/143>`_)

- :meth:`gidgethub.abc.GitHubAPI.getiter` now accepts ``iterable_key`` parameter
  in order to support the Checks API.
  (`Issue #164 <https://github.com/gidgethub/gidgethub/issues/164>`_)

- Accept HTTP 202 ACCEPTED as successful.
  (`PR #174 <https://github.com/gidgethub/gidgethub/pull/174>`_)

5.0.1
-----

- Drop the ``machine-man-preview`` header from :meth:`gidgethub.apps.get_installation_access_token`
  because it is out of preview. The ``machine-man-preview`` is `no longer
  required <https://developer.github.com/changes/#--machine-man-and-sailor-v-previews-graduate>`_
  as of August 20, 2020.


5.0.0
-----

- Add :meth:`gidgethub.routing.Router.fetch` for obtaining a frozenset of functions
  registered to the router that the event would be called on.
  (`Issue #74 <https://github.com/gidgethub/gidgethub/issues/74>`_).
- Add support for GitHub Actions Environment Files with :meth:`gidgethub.actions.setenv`
  and :meth:`gidgethub.actions.addpath`.
  (`Issue #137 <https://github.com/gidgethub/gidgethub/issues/132>`_).
- Make router callback execution order non-deterministic to avoid relying on
  registration order.
  (`Issue #74 <https://github.com/gidgethub/gidgethub/issues/74>`_).
- Fix mypy errors in ``gidgethub.httpx.GitHubAPI._request``
  (`Issue #133 <https://github.com/gidgethub/gidgethub/issues/133>`_).
- Make the minimum version of PyJWT be v2.0.0.

4.2.0
-----

- :meth:`gidgethub.abc.GitHubAPI.post` now accepts ``content_type`` parameter.
  If supplied, the ``content_type`` value will be used in the request headers,
  and the raw form of the data will be passed to the request. If not supplied,
  by default the data will be parsed as JSON, and the "application/json" content
  type will be used. (`Issue #115 <https://github.com/gidgethub/gidgethub/issues/115>`_).

4.1.1
-----

- Fix :meth:`gidgethub.abc.GitHubAPI.graphql` to accept response content types lacking
  spaces; affects GitHub Enterprise
  (`Issue #122 <https://github.com/gidgethub/gidgethub/pull/122>`_)

- Specify PyJWT[crypto] as a dependency, and dropped the explicit dependency to
  ``cryptography`` (`Issue #116 <https://github.com/gidgethub/gidgethub/issues/116>`_).

4.1.0
-----

- Introduce :mod:`gidgethub.apps`.

- Introduce :meth:`gidgethub.apps.get_installation_access_token`
  for obtaining an installation access token that can be used to authenticate as
  a GitHub App installation. (`Issue #71 <https://github.com/gidgethub/gidgethub/issues/71>`_).

- Introduce :meth:`gidgethub.apps.get_jwt` for constructing the JSON Web Token
  that can be used to access endpoints that require it.

4.0.0
-----

- Add :meth:`gidgethub.abc.GitHubAPI.graphql` and related exceptions.
- Add :exc:`gidgethub.BadRequestUnknownError` when something other than JSON is
  returned for a 422 response.
- Remove `gidgethub.treq`; tests were not passing and a request for help on
  Twitter came back with no response (happy to add back if someone steps forward
  to help out).
- Remove `gidgethub.test` from the distribution.
- Introduce :mod:`gidgethub.actions`.
- Add :exc:`gidgethub.ValidationError` for when the HTTP response is a 422 but not
  field-related. (`#83 <https://github.com/gidgethub/gidgethub/pull/83>`_;
  thanks `John Hossler <https://github.com/jmhossler>`_)
- Allow GitHub Enterprise users to specify a base URL, by passing in **base_url**
  to the :meth:`gidgethub.abc.GitHubAPI` constructor.

3.3.0
-----

- Adapt to the new ``httpx`` API to support
  `versions >= 0.11.0 <https://github.com/encode/httpx/blob/master/CHANGELOG.md>`_
  (thanks `Dave Hirschfeld <https://github.com/dhirschfeld>`_)

3.2.0
-----

- Fix mypy warnings about the :class:`typing.Dict` and :class:`typing.Mapping`
  generic types lacking type parameters.
- Add :mod:`gidgethub.httpx` backend.
- Add a ``py.typed`` file to mark the project as fully typed.

3.1.0
-----

- :meth:`gidgethub.abc.GitHubAPI.getiter` now works with
  `GitHub's search API <https://docs.github.com/en/rest/search>`_
  (thanks `Pablo Galindo <https://github.com/pablogsal>`_).

3.0.0
-----

- :meth:`gidgethub.sansio.RateLimit.from_http` returns ``None`` if ratelimit is
  not found in the headers.
- Allow authenticating as a GitHub App by using JSON web token.
  :func:`gidgethub.sansio.create_headers` now accepts
  ``jwt`` argument. ``gidgethub.abc.GitHubAPI._make_request``,
  :meth:`gidgethub.abc.GitHubAPI.getitem`, :meth:`gidgethub.abc.GitHubAPI.getiter`,
  :meth:`gidgethub.abc.GitHubAPI.post`, :meth:`gidgethub.abc.GitHubAPI.patch`,
  :meth:`gidgethub.abc.GitHubAPI.put`, and :meth:`gidgethub.abc.GitHubAPI.delete` now
  accept ``jwt`` and ``oauth_token`` arguments.

- gidgethub is now packaged using `flit <https://flit.readthedocs.io/en/latest/>`_.

2.5.0
-----

- Tighten type hints for parameters that have a default of ``None``
  but were not typed as :data:`typing.Optional`.

- Tweak code to not change semantics but reach 100% coverage.

- Provide a human-readable string representation of
  :class:`gidgethub.sansio.RateLimit`.

- Use the ``message`` data as the error message
  if the ``errors`` object was not returned.

- Add the *data* keyword argument to :meth:`gidgethub.abc.GitHubAPI.delete`.


2.4.1
-----

- Tighten up protections against caching ineligible responses.


2.4.0
-----

- Expand :meth:`gidgethub.routing.Router.dispatch`.


2.3.0
-----

- Add support for ``application/x-www-form-urlencoded`` webhook event payloads.
  (This also allows for API calls to return this content type, although GitHub
  currently does not do that.)

- Introduce :mod:`gidgethub.routing` to help route webhook events to registered
  asynchronous callbacks.

- Add type hints.

- Add a *cache* argument to :class:`gidgethub.abc.GitHubAPI`.


2.2.0
-----

- Introduce :mod:`gidgethub.tornado` to support
  `Tornado <http://www.tornadoweb.org/>`_ (thanks to
  Matthias Bussonnier and A. Jesse Jiryu Davis for the PR reviews).


2.1.0
-----

- The default value for the *data* argument of :meth:`gidgethub.abc.GitHubAPI.put`
  was changed from ``""`` to ``b""``.
- All type hints were removed (due to mypy not supporting yield in an async
  function, they were not being tested as being valid).


2.0.0
-----

- Renamed ``gidgethub.abc.GitHubAPI._sleep()`` to
  :meth:`~gidgethub.abc.GitHubAPI.sleep()` to make the method public.
- Renamed the "test" extra to "tests" and added the "dev" extra.
- Introduced the :exc:`gidgethub.RateLimitExceeded` exception.
- Methods on :class:`gidgethub.abc.GitHubAPI` no longer automatically sleep when it's
  possible that the call will exceed the user's rate limit (it's now up to the
  user to prevent from going over the rate limit).
- Made the ``[treq]`` install extra depend on ``Twisted[tls]``.


1.2.0
-----

- :meth:`gidgethub.sansio.Event.from_http` raises a :exc:`gidgethub.BadRequest` of ``415``
  instead of ``400`` when a content-type other than ``application/json``
  is provided.
- More robustly decode the body in :meth:`gidgethub.sansio.Event.from_http`
  (i.e. if the ``content-type`` doesn't specify ``charset``, assume ``UTF-8``).
- Changed the signature of :class:`gidgethub.sansio.Event` to accept
  :data:`typing.Any` for the *data* argument.
- Fixed signature verification.


1.1.0
-----

- Introduced ``gidgethub.treq`` (thanks to Cory Benfield).


1.0.0
-----

Initial release.
