:mod:`gidgethub.treq` --- treq support
=======================================

.. module:: gidgethub.treq

.. class:: GitHubAPI(requester, *, oauth_token=None, cache=None)

    An implementation of :class:`gidgethub.abc.GitHubAPI` using
    `treq <https://treq.readthedocs.io>`_. Typical usage will be::

        from twisted.internet import reactor, defer, task
        from gidgethub.treq import GitHubAPI

        MY_TOKEN = "INSERT_TOKEN_HERE"
        USER_AGENT = "INSERT_USERNAME_HERE"

        def main(reactor, *args):
            gh = GitHubAPI(USER_AGENT, oauth_token=MY_TOKEN)
            d = defer.ensureDeferred(gh.getitem("/repos/python-hyper/hyper-h2/labels/Easy"))
            d.addCallback(print)
            return d

        task.react(main)
