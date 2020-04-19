from unittest import mock

import importlib_resources
import jwt
import pytest

from gidgethub import apps
from .test_abc import MockGitHubAPI

from .samples import rsa_key as rsa_key_samples


class TestGitHubAppUtils:

    """Tests for GitHub App utilities."""

    @mock.patch("time.time")
    def test_get_jwt(self, time_mock):
        app_id = 12345

        time_mock.return_value = 1587069751.5588422

        # test file copied from https://github.com/jpadilla/pyjwt/blob/master/tests/keys/testkey_rsa
        private_key = importlib_resources.read_binary(rsa_key_samples, "test_rsa_key")

        result = apps.get_jwt(app_id=app_id, private_key=private_key)
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

        private_key = importlib_resources.read_binary(rsa_key_samples, "test_rsa_key")

        await apps.get_installation_access_token(
            gh, installation_id=installation_id, app_id=app_id, private_key=private_key
        )

        assert gh.url == "https://api.github.com/app/installations/6789/access_tokens"
        assert gh.body == b""
