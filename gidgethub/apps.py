"""Support for GitHub Actions."""

from __future__ import annotations

import time
from typing import Any, cast

import jwt

from gidgethub.abc import GitHubAPI


def get_jwt(*, app_id: str, private_key: str | bytes, expiration: int = 10 * 60) -> str:
    """Construct the JWT (JSON Web Token), used for GitHub App authentication."""
    time_int = int(time.time())
    payload = {"iat": time_int - 60, "exp": time_int + expiration, "iss": app_id}
    bearer_token = jwt.encode(payload, private_key, algorithm="RS256")

    return bearer_token


async def get_installation_access_token(
    gh: GitHubAPI,
    *,
    installation_id: str,
    app_id: str,
    private_key: str | bytes,
) -> dict[str, Any]:
    """Obtain a GitHub App's installation access token.


    Return a dictionary containing access token and expiration time.
    (https://docs.github.com/en/free-pro-team@latest/rest/reference/apps#create-an-installation-access-token-for-an-app)
    """
    access_token_url = f"/app/installations/{installation_id}/access_tokens"
    token = get_jwt(app_id=app_id, private_key=private_key)
    response = await gh.post(
        access_token_url,
        data=b"",
        jwt=token,
    )
    # example response
    # {
    #   "token": "v1.1f699f1069f60xxx",
    #   "expires_at": "2016-07-11T22:14:10Z"
    # }

    return cast(dict[str, Any], response)
