.. gidgethub documentation master file, created by
   sphinx-quickstart on Mon Jan 23 19:03:20 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

gidgethub --- An async library for calling GitHub's API
=======================================================

While there are many
`GitHub libraries <https://developer.github.com/libraries/>`_ for
Python, when this library was created there were none oriented towards
asynchronous usage. On top of that, there were also no libraries which
took a `sans-I/O approach <https://sans-io.readthedocs.io/>`_ to their
design. Because of that, this project was created.

This project has three primary layers to it. The base layer is
:mod:`gidgethub.sansio` which provides the tools necessary to work
with GitHub's API. The next layer up is :mod:`gidgethub.abc` which
provides an abstract base class for a cleaner, unified API. Finally,
the top layer is using an implementation of the abstract base class,
e.g. :mod:`gidgethub.aiohttp`.

The vast majority of users will want to use one of the concrete
implementations, but for those that have an HTTP library which is not
supported or simply want the base tools, this library will still be
useful. And the higher-level API has been designed to abstract away
GitHub-specific details in making API calls, but it does not try to
separate you from the GitHub API itself, e.g. to get the details of
the ``bug`` label for this project you don't call some
``org("brettcannon").repo("gidgethub").label("bug")`` method, instead
you call
``await gh.getitem("/repos/brettcannon/gidgethub/labels/bug")``. This
makes it so that you can follow GitHub's documentation for their API
closely. You also don't have to wait for an update to this library to
use new features of the GitHub API.


Installation
------------
There's no PyPI package yet; sorry. I'll get to it.


Contents
--------
.. toctree::
   :titlesonly:

   __init__
   sansio
   abc
   aiohttp


About the title
---------------
With there being so many pre-existing GitHub libraries, it was tough
to come up with a new name. So in the end I just named it after my
cat. 😊

"Gidget" sounds somewhat like an elongated version of "git"
so that made some sense phoenetically. And with the
`octocat <https://octodex.github.com/>`_ being the mascot of GitHub,
it seemed fitting to have the name be somewhat feline-related.
