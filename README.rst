gidgethub
=========
An asynchronous `GitHub API <https://docs.github.com/>`_ library.


Development status
------------------

.. image:: https://github.com/brettcannon/gidgethub/workflows/CI/badge.svg?event=push
    :target: https://github.com/brettcannon/gidgethub/actions

.. image:: https://codecov.io/gh/brettcannon/gidgethub/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/brettcannon/gidgethub

.. image:: https://readthedocs.org/projects/gidgethub/badge/?version=latest
    :target: http://gidgethub.readthedocs.io/en/latest/
    :alt: Documentation Status


Installation
------------
Gidgethub is `available on PyPI <https://pypi.org/project/gidgethub/>`_.
::

  python3 -m pip install gidgethub


Gidgethub requires Python version 3.7 and up.


Goals
-----

The key goal is to provide a base library for the
`GitHub API <https://docs.github.com/>`_ which performs no I/O of its own (a
`sans-I/O <https://sans-io.readthedocs.io/>`_ library). This allows users to
choose whatever HTTP library they prefer while parceling out GitHub-specific
details to this library. This base library is then built upon to provide an
abstract base class to a cleaner API to work with. Finally, implementations of
the abstract base class are provided for asynchronous HTTP libraries for
immediate usage.


Alternative libraries
---------------------

If you think you want a different approach to the GitHub API,
`GitHub maintains a list of libraries <https://docs.github.com/en/free-pro-team@latest/rest/overview/libraries>`_.


*Aside*: what's with the name?
------------------------------

I couldn't think of a good name that was somehow a play on "GitHub" or somehow
tied into `Monty Python <http://www.montypython.com/>`_. And so I decided to play
off of GitHub's `octocat <https://octodex.github.com/>`_ mascot and use my own
cat's name, Gidget, in some way. Since "Gidget" somewhat sounds like
"git", I decided to go with "gidgethub".


Changelog
---------

See the documentation for the `full changelog <https://gidgethub.readthedocs.io/en/latest/changelog.html>`_.
