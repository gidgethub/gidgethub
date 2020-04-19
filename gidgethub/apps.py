"""Support for GitHub Actions."""
from typing import cast, Any, Dict

import time
import jwt

from gidgethub.abc import GitHubAPI


def get_jwt(*, app_id: str, private_key: str) -> str:
    """Construct the JWT (JSON Web Token), used for GitHub App authentication."""
    time_int = int(time.time())
    payload = {"iat": time_int, "exp": time_int + (10 * 60), "iss": app_id}
    encoded = jwt.encode(payload, private_key, algorithm="RS256")
    bearer_token = encoded.decode("utf-8")

    return bearer_token


async def get_installation_access_token(
    gh: GitHubAPI, *, installation_id: str, app_id: str, private_key: str
) -> Dict[str, Any]:
    """Obtain a GitHub App's installation access token.


    Return a dictionary containing access token and expiration time.
    (https://developer.github.com/v3/apps/#create-a-new-installation-token)
    """
    access_token_url = f"/app/installations/{installation_id}/access_tokens"
    token = get_jwt(app_id=app_id, private_key=private_key)
    response = await gh.post(
        access_token_url,
        data=b"",
        jwt=token,
        accept="application/vnd.github.machine-man-preview+json",
    )
    # example response
    # {
    #   "token": "v1.1f699f1069f60xxx",
    #   "expires_at": "2016-07-11T22:14:10Z"
    # }

    return cast(Dict[str, Any], response)
