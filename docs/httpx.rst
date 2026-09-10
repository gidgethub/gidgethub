:mod:`gidgethub.httpx` --- httpx support
=============================================

.. module:: gidgethub.httpx

.. class:: GitHubAPI(client, requester, *, oauth_token=None, cache=None)

    An implementation of :class:`gidgethub.abc.GitHubAPI` using
    `http2 <https://pydantic.dev/docs/httpx2/get-started//>`_.
    Typical usage will be::

        import httpx2 as httpx
        import gidgethub.httpx


        async with httpx.AsyncClient() as client:
            gh = gidgethub.httpx.GitHubAPI(client, requester,
                                           oauth_token=oauth_token)
            # Make your requests, e.g. ...
            data = await gh.getitem("/rate_limit")
