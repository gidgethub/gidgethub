:mod:`gidgethub.apps` --- Support for GitHub App
================================================

.. module:: gidgethub.apps

.. versionadded:: 4.1.0

.. versionchanged:: 5.0.1
   The ``machine-man-preview`` header was removed from the API endpoint.

This module is to help provide support for `GitHub Apps <https://docs.github.com/en/rest/apps>`_.

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

    data = await gh.getitem("/rate_limit", oauth_token=access_token_response["token"])

.. py:method:: get_installation_access_token(gh, *, installation_id, app_id, private_key)
        :async:

    Obtain a GitHub App's installation access token.

    **installation_id** is the GitHub App installation's id.

    **app_id** is the GitHub App's identifier.

    **private_key** is the content of the GitHub App's private key (``.PEM`` format) file.

    It returns the response from GitHub's
    `Authenticating as an installation <https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/about-authentication-with-a-github-app#authentication-as-an-app-installation>`_ API endpoint.


.. function:: get_jwt(*, app_id, private_key, expiration = 10 * 60)

   Construct the JWT (JSON Web Token), that can be used to access endpoints
   that require it. Default expiration period is 10 minutes.

   Example::

       from gidgethub.apps import get_jwt

       private_key = """-----BEGIN RSA PRIVATE KEY-----
       zBgqFIin/uQEb0he006F9pNC6Kga0AMY5b0cCdZ4ge9qyFro2eVA
       ...
       -----END RSA PRIVATE KEY-----
       """

       # Generate a token that expires 30 minutes from now
       token = get_jwt(
           app_id=123, private_key=private_key, expiration = 30 * 60
       )
       data = gh.getitem(
           "/app/installations",
           jwt=token,
       )
