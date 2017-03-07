:mod:`gidgethub.aiohttp` --- An implementation of :mod:`gidgethub.abc` using ``aiohttp``
=========================================================================================

.. module:: gidgethub.aiohttp

.. class:: GitHubAPI(session: aiohttp.ClientSession, requester: str, *, oauth_token: str = None)

    An implementation of :class:`gidgethub.abc.GitHubAPI` using
    `aiohttp <https://aiohttp.readthedocs.io>`_. Typical usage will be::

        import aiohttp
        import gidgethub.aiohttp


        async with aiohttp.ClientSession() as session:
            gh = gidgethub.aiohttp.GitHubAPI(session, requester,
                                             oauth_token=oauth_token)
            # Make your requests, e.g. ...
            data = await gh.getitem("/rate_limit")
