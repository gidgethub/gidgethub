"""Provide an abstract base class for easier requests."""
import abc
import datetime
from typing import Any, Dict, Mapping, Tuple

from . import sansio


class GitHubAPI(abc.ABC):

    """Provide an idiomatic API for making calls to GitHub's API."""

    def __init__(self, requester: str, *, oauth_token: str = None) -> None:
        self.requester = requester
        self.oauth_token = oauth_token
        self.rate_limit: sansio.RateLimit = None

    @abc.abstractmethod
    async def _request(self, method: str, url: str,
                       headers: Mapping[str, str],
                       body: bytes = None) -> Tuple[int, Mapping[str, str], bytes]:
        """Make an HTTP request."""

    @abc.abstractmethod
    async def _sleep(self, seconds: float) -> None:
        """Sleep for the specified number of seconds."""

    async def _make_request(self, method: str, url: str,
                            url_vars: Dict[str, str], body: bytes,
                            accept) -> Tuple[Any, str]:
        """Construct and make an HTTP request."""
        # If the rate limit isn't known yet then assume there's enough quota.
        if self.rate_limit is not None:
            if self.rate_limit:
                # Proactively assume this request is counted by GitHub so as to
                # not have a race condition on the final request.
                self.rate_limit.remaining -= 1
            else:
                # /rate_limit returns the current rate limit,
                # but the assumption is an async application won't be making multi-threaded calls with
                # the same oauth token so the last call will have set the rate_limit accurately.
                now = datetime.datetime.now(datetime.timezone.utc)
                wait = self.rate_limit.reset_datetime - now
                await self._sleep(wait.total_seconds())

        request_headers = sansio.create_headers(self.requester, accept=accept,
                                                oauth_token=self.oauth_token)
        filled_url = sansio.format_url(url, url_vars)
        response = await self._request(method, filled_url, request_headers, body)
        data, self.rate_limit, more = sansio.decipher_response(*response)
        return data, more

    async def getitem(self, url: str, url_vars: Dict[str, str] = {}, *,
                      accept=sansio.accept_format()) -> Any:
        """Send a GET request for a single item to the specified endpoint."""
        data, _ = await self._make_request("GET", url, url_vars, b'', accept)
        return data
