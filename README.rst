gidgethub
==========
An asynchronous `GitHub API <https://developer.github.com/>`_ library.


Development status
------------------

.. image:: https://travis-ci.org/brettcannon/gidgethub.svg?branch=master
    :target: https://travis-ci.org/brettcannon/gidgethub

.. image:: https://codecov.io/gh/brettcannon/gidgethub/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/brettcannon/gidgethub

.. image:: https://readthedocs.org/projects/gidgethub/badge/?version=latest
    :target: http://gidgethub.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status


Installation
------------

::

  python3 -m pip install gidgethub


Goals
-----

The key goal is to provide a base library for the
`GitHub API <https://developer.github.com/>`_ which performs no I/O of its own (a
`sans-I/O <https://sans-io.readthedocs.io/>`_ library). This allows users to
choose whatever HTTP library they prefer while parceling out GitHub-specific
details to this library. This base library is then built upon to provide an
abstract base class to a cleaner API to work with. Finally, implementations of
the abstract base class are provided for asynchronous HTTP libraries for
immediate usage.


Alternative libraries
---------------------

If you think you want a different approach to the GitHub API,
`GitHub maintains a list of libraries <https://developer.github.com/libraries/>`_.


*Aside*: what's with the name?
------------------------------

I couldn't think of a good name that was somehow a play on "GitHub" or somehow
tied into `Monty Python <http://www.montypython.com/>`_. And so I decided to play
off of GitHub's `octocat <https://octodex.github.com/>`_ as a theme and use my
cat's name, Gidget, as part of the name. Since "Gidget" somewhat sounds like
"git", I decided to go with "gidgethub".


Changelog
---------

2.1.0 (in development)
''''''''''''''''''''''
- The default value for the *data* argument of ``gidgethub.abc.GitHubAPI.put()``
  was changed from ``""`` to ``b""``.
- All type hints were removed (due to mypy not supporting yield in an async
  function, they were not being tested as being valid).

2.0.0
''''''''''''''''''''''

- Renamed ``gidgethub.abc._sleep()`` to ``sleep()`` to make the method public.
- Renamed the "test" extra to "tests" and added the "dev" extra.
- Introduced the ``RateLimitExceeded`` exception.
- Methods on ``GitHubAPI`` no longer automatically sleep when it's
  possible that the call will exceed the user's rate limit (it's now up to the
  user to prevent from going over the rate limit).
- Made the ``[treq]`` install extra depend on ``Twisted[tls]``.


1.2.0
''''''''''''''''''''''

- ``gidgethub.sansio.Event.from_http()`` raises a ``BadRequest`` of ``415``
  instead of ``400`` when a content-type other than ``application/json``
  is provided.
- More robustly decode the body in ``gidgethub.sansio.Event.from_http()``
  (i.e. if the ``content-type`` doesn't specify ``charset``, assume ``UTF-8``).
- Changed the signature of ``gidgethub.sansio.Event`` to accept ``Any`` for
  the *data* argment.
- Fixed signature verification


1.1.0
'''''

- Introduced ``gidgethub.treq`` (thanks to Cory Benfield).


1.0.0
'''''

Initial release
