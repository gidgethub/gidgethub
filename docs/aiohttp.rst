:mod:`gidgethub.aiohttp` --- aiohttp support
=============================================

.. module:: gidgethub.aiohttp

.. class:: GitHubAPI(session, requester, *, oauth_token=None, cache=None)

    An implementation of :class:`gidgethub.abc.GitHubAPI` using
    `aiohttp <https://aiohttp.readthedocs.io>`_. Typical usage will be::

        import aiohttp
        import gidgethub.aiohttp


        async with aiohttp.ClientSession() as session:
            gh = gidgethub.aiohttp.GitHubAPI(session, requester,
                                             oauth_token=oauth_token)
            # Make your requests, e.g. ...
            data = await gh.getitem("/rate_limit")
