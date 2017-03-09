import datetime

from twisted.internet.defer import ensureDeferred
from twisted.trial.unittest import TestCase
from twisted.web.client import Agent, HTTPConnectionPool

from .. import treq as gh_treq
from .. import sansio

import treq._utils


class TwistedPluginTestCase(TestCase):

    def test_sleep(self):
        delay = 1
        start = datetime.datetime.now()
        gh = gh_treq.GitHubAPI("gidgethub")

        def test_done(ignored):
            stop = datetime.datetime.now()
            self.assertTrue((stop - start) > datetime.timedelta(seconds=delay))
        d = ensureDeferred(gh._sleep(delay))
        d.addCallback(test_done)
        return d


    def test_request(self):
        from twisted.internet import reactor
        request_headers = sansio.create_headers("gidgethub")
        gh = gh_treq.GitHubAPI("gidgethub")
        d = ensureDeferred(
            gh._request(
                "GET", "https://api.github.com/rate_limit", request_headers,
            )
        )

        def test_done(response):
            data, rate_limit, _ = sansio.decipher_response(*response)
            self.assertIn("rate", data)

        def cleanup(ignored):
            # We do this just to shut up Twisted.
            pool = treq._utils.get_global_pool()
            pool.closeCachedConnections()

            # We need to sleep to let the connections hang up.
            return ensureDeferred(gh._sleep(0.5))

        d.addCallback(test_done)
        d.addCallback(cleanup)
        return d
