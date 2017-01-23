import pytest


@pytest.mark.skip("not implemented")
class TestValidate:

    """Tests for gidgethub.sansio.validate()."""

    def test_malformed_signature(self):
        """Error out if the signature doesn't start with "sha1="."""

    def test_validation(self):
        """Success case."""
