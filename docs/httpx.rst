:mod:`gidgethub.httpx` --- httpx support
=============================================

.. module:: gidgethub.httpx

.. class:: GitHubAPI(client, requester, *, oauth_token=None, cache=None)

    An implementation of :class:`gidgethub.abc.GitHubAPI` using
    `httpx <https://www.encode.io/httpx>`_. Typical usage will be::

        import httpx
        import gidgethub.httpx


        async with httpx.AsyncClient() as client:
            gh = gidgethub.httpx.GitHubAPI(client, requester,
                                           oauth_token=oauth_token)
            # Make your requests, e.g. ...
            data = await gh.getitem("/rate_limit")
