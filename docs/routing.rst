:mod:`gidgethub.routing` --- A router for webhook events
========================================================

.. module:: gidgethub.routing

.. versionadded:: 2.3

When a single web service is used to perform multiple actions based on
a single
`webhook event <https://developer.github.com/webhooks/#events>`_, it
is easier to do those multiple steps in some sort of routing mechanism
to make sure the right objects are called is provided. This module is
meant to provide such a router for :class:`gidgethub.sansio.Event`
instances. This allows for individual ``async`` functions to be
written per event type to help keep logic separated and focused
instead of having to differentiate between different events manually
in user code.


.. class:: Router(*other_routers)

    An object to route a :class:`gidgethub.sansio.Event` instance to
    appropriate registered asynchronous callbacks.

    The initializer for this class takes an arbitrary number of other
    routers to help build a single router from sub-routers. Typically
    this is used when each semantic set of features has a router and
    are then used to construct a server-wide router.

    Each callback registered with this class is expected to be
    :term:`awaitable` and to accept at least a single
    :class:`~gidgethub.sansio.Event` instance:

    .. code-block:: python

        async def callback(event, *args, **kwargs):
            ...


    .. method:: add(func, event_type, **data_detail)

        Add an asynchronous callback for an event.

        The *event_type* argument corresponds to the
        :attr:`gidgethub.sansio.Event.event` attribute of the event
        that the callback is interested in. The arbitrary keyword
        arguments is used as a key/value pair to compare against what
        is provided in :attr:`gidgethub.sansio.Event.data`. Only 0 or
        1 keyword-only arguments may be provided, otherwise
        :exc:`TypeError` is raised.

        For example, to register a callback for any opened issues,
        you would call:

        .. code-block:: python

            async def callback(event):
                ...

            router.add(callback, "issues", action="opened")


    .. decorator:: register(event_type, **data_detail)

        A decorator that calls :meth:`add` on the decorated function.

        .. code-block:: python

            router = gidgethub.routing.Router()

            @router.register("issues", action="opened")
            async def callback(event):
                ...


    .. coroutine:: dispatch(event, *args, **kwargs)

        Call the appropriate asynchronous callbacks for the *event*.
        The provided event and any other arguments will be passed
        down to the callback unmodified.

        .. versionchanged:: 2.4
            Added ``*args`` and ``**kwargs``.
