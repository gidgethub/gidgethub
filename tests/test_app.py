from unittest import mock

import jwt
import pytest

from gidgethub import app

from .test_abc import MockGitHubAPI


class TestGitHubAppUtils:

    """Tests for GitHub App utilities."""

    @mock.patch("time.time")
    def test_get_jwt(self, time_mock):
        app_id = 12345

        time_mock.return_value = 1587069751.5588422

        # test file copied from https://github.com/jpadilla/pyjwt/blob/master/tests/keys/testkey_rsa
        with open("tests/samples/test_rsa_key", "r") as fp:
            private_key = fp.read()

            result = app._get_jwt(app_id=app_id, private_key=private_key)
            expected_payload = {
                "iat": 1587069751,
                "exp": 1587069751 + (10 * 60),
                "iss": app_id,
            }

            assert result == jwt.encode(
                expected_payload, private_key, algorithm="RS256"
            ).decode("utf-8")

    @pytest.mark.asyncio
    async def test_get_installation_access_token(self):
        gh = MockGitHubAPI()
        installation_id = 6789
        app_id = 12345

        with open("tests/samples/test_rsa_key", "r") as fp:
            private_key = fp.read()

        await app.get_installation_access_token(
            gh, installation_id=installation_id, app_id=app_id, private_key=private_key
        )

        assert gh.url == "https://api.github.com/app/installations/6789/access_tokens"
