:mod:`gidgethub.apps` --- Support for GitHub App
================================================

.. module:: gidgethub.apps

.. versionadded:: 4.1.0

This module is to help provide support for `GitHub Apps <https://developer.github.com/v3/apps/>`_.

Example on how you would obtain the access token for authenticating as a GitHub App installation::

    from gidgethub.apps import get_installation_access_token

    private_key = """-----BEGIN RSA PRIVATE KEY-----
    zBgqFIin/uQEb0he006F9pNC6Kga0AMY5b0cCdZ4ge9qyFro2eVA
    ...
    -----END RSA PRIVATE KEY-----
    """

    access_token_response = await get_installation_access_token(
        installation_id=123,
        app_id=456,
        private_key=private_key
    )

    data = gh.getitem("/rate_limit", oauth_token=access_token_response["token"])

.. coroutine:: get_installation_access_token(gh, *, installation_id, app_id, private_key)

    Obtain a GitHub App's installation access token.

    **installation_id** is the GitHub App installation's id.

    **app_id** is the GitHub App's identifier.

    **private_key** is the content of the GitHub App's private key (``.PEM`` format) file.

    It returns the response from GitHub's
    `Authenticating as an installation <https://developer.github.com/apps/building-github-apps/authenticating-with-github-apps/#authenticating-as-an-installation>`_ API endpoint.


.. function:: get_jwt(*, app_id, private_key)

   Construct the JWT (JSON Web Token), that can be used to access endpoints
   that require it.

   Example::

       from gidgethub.apps import get_jwt

       private_key = """-----BEGIN RSA PRIVATE KEY-----
       zBgqFIin/uQEb0he006F9pNC6Kga0AMY5b0cCdZ4ge9qyFro2eVA
       ...
       -----END RSA PRIVATE KEY-----
       """

       token = get_jwt(app_id=123, private_key=private_key)
       data = gh.getitem(
           "/app/installations",
           jwt=token,
           accept="application/vnd.github.machine-man-preview+json",
       )
