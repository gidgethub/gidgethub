import pytest


@pytest.mark.skip("not implemented")
class TestValidationFailure:

    """Tests for gidgethub.sansio.ValidationFailure."""

    def test_simple_str(self):
        """Test a message that has no formatting."""

    def test_str_formatting(self):
        """Test lazy string formatting."""


@pytest.mark.skip("not implemented")
class TestValidate:

    """Tests for gidgethub.sansio.validate()."""

    def test_malformed_signature(self):
        """Error out if the signature doesn't start with "sha1="."""

    def test_validation(self):
        """Success case."""
