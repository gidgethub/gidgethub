:mod:`gidgethub.actions` --- Support for GitHub Actions
=======================================================

.. module:: gidgethub.actions

.. versionadded:: 4.0.0

This module is to help provide support for `GitHub Actions`_ when writing a
`container action <https://help.github.com/en/actions/building-actions/creating-a-docker-container-action>`__.


.. function:: workspace()

    Return a :class:`pathlib.Path` object representing the ``GITHUB_WORKSPACE``
    path. As the location is considered static, the function is idempotent after
    its initial call.

.. function:: event()

    Return the webhook event data as kept at the path as pointed at by the
    ``GITHUB_EVENT_PATH`` environment variable. As the data is considered
    static, the function is idempotent after its initial call.


.. function:: command(cmd, val, **parameters)

   Issue a `workflow command <https://help.github.com/en/actions/reference/workflow-commands-for-github-actions>`_.

   Note that no automatic string conversion is performed on any arguments.

   ::

     # `::warning file=app.js,line=1,col=5::Missing semicolon`
     gidgethub.actions.command("warning", "Missing semicolon", file="app.js", line="1", col="5")


.. _GitHub Actions: https://help.github.com/en/actions
