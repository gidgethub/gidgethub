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
:mod:`gidgethub.sansio` and :mod:`gidgethub.routing` which provide the
tools necessary to work with GitHub's API. The next layer up is
:mod:`gidgethub.abc` which provides an abstract base class for a
cleaner, unified API. Finally, the top layer is using an
implementation of the abstract base class,
e.g. :mod:`gidgethub.aiohttp`.

Quickstart
----------

Here is a complete example of a production server that responds to
webhooks which will add a ``needs review`` label to all new pull
requests (this is taken from the
`Bedevere bot <https://github.com/python/bedevere>`_ used by the
Python project; the only change is inlining some code and showing code
responding to only a single type of webhook event)::

  import asyncio
  import importlib
  import os
  import sys
  import traceback

  import aiohttp
  from aiohttp import web
  import cachetools
  from gidgethub import aiohttp as gh_aiohttp
  from gidgethub import routing
  from gidgethub import sansio


  router = routing.Router()
  cache = cachetools.LRUCache(maxsize=500)


  @router.register("pull_request", action="opened")
  async def opened_pr(event, gh, *arg, **kwargs):
      """Mark new PRs as needing a review."""
      pull_request = event.data["pull_request"]
      await gh.post(pull_request["labels_url"], data=["needs review"])


  async def main(request):
      try:
          body = await request.read()
          secret = os.environ.get("GH_SECRET")
          event = sansio.Event.from_http(request.headers, body, secret=secret)
          print('GH delivery ID', event.delivery_id, file=sys.stderr)
          if event.event == "ping":
              return web.Response(status=200)
          oauth_token = os.environ.get("GH_AUTH")
          async with aiohttp.ClientSession() as session:
              gh = gh_aiohttp.GitHubAPI(session, "brettcannon/gidgethub-example",
                                        oauth_token=oauth_token,
                                        cache=cache)
              # Give GitHub some time to reach internal consistency.
              await asyncio.sleep(1)
              await router.dispatch(event, gh)
          try:
              print('GH requests remaining:', gh.rate_limit.remaining)
          except AttributeError:
              pass
          return web.Response(status=200)
      except Exception as exc:
          traceback.print_exc(file=sys.stderr)
          return web.Response(status=500)


  if __name__ == "__main__":
      app = web.Application()
      app.router.add_post("/", main)
      port = os.environ.get("PORT")
      if port is not None:
          port = int(port)
  web.run_app(app, port=port)

Motivation
----------

The vast majority of users will want to use one of the concrete
implementations, but for those that have an HTTP library which is not
supported or simply want the base tools, this library will still be
useful. And the higher-level API has been designed to abstract away
GitHub-specific details in making API calls, but it does not try to
separate you from the GitHub API itself, e.g. to get the details of
the ``bug`` label for this project you don't call something like::

  org("brettcannon").repo("gidgethub").label("bug")

Instead, you call::

  await gh.getitem("/repos/brettcannon/gidgethub/labels/bug")

This makes it so that you can follow GitHub's documentation for their
API closely. You also don't have to wait for an update to this library
to use new features of the GitHub API.


Installation
------------

`Gidgethub is on PyPI <https://pypi.org/project/gidgethub/>`_.
::

  python3 -m pip install gidgethub


Contents
--------
.. toctree::
   :titlesonly:

   changelog
   __init__
   sansio
   actions
   routing
   abc
   aiohttp
   tornado
   httpx


About the title
---------------
With there being so many pre-existing GitHub libraries, it was tough
to come up with a new name. So in the end I just named it after my
cat. 😊

"Gidget" sounds somewhat like an elongated version of "git"
so that made some sense phonetically. And with the
`octocat <https://octodex.github.com/>`_ being the mascot of GitHub,
it seemed fitting to have the name to be feline-related somehow.
