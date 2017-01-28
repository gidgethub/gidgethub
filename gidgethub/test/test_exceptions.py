from .. import HTTPException


class TestHTTPException:

    def test_status_code_only(self):
        """The status is the message if a better one isn't provided."""
        exc = HTTPException(400)
        assert exc.status_code == 400
        assert str(exc) == "400"

    def test_message(self):
        """A provided message overrides the status code as the message."""
        message = "a better message"
        exc = HTTPException(400, message)
        assert exc.status_code == 400
        assert str(exc) == message
