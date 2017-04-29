from tornado import gen
from tornado import httpclient

from . import abc as gh_abc


class GitHubAPI(gh_abc.GitHubAPI):

    async def _request(self, method, url, headers, body=b''):
        """Make an HTTP request."""
        if method == "GET" and not body:
            body = None
        request = httpclient.HTTPRequest(url, method, headers, body)
        # Since Tornado has designed AsyncHTTPClient to be a singleton, there's
        # no reason not to simply instantiate it every time.
        client = httpclient.AsyncHTTPClient()
        response = await client.fetch(request, raise_error=False)
        return response.code, response.headers, response.body

    async def sleep(self, seconds):
        """Sleep for the specified number of seconds."""
        await gen.sleep(seconds)
