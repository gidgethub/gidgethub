import pytest

from gidgethub import routing
from gidgethub import sansio


class Callback:
    def __init__(self):
        self.called = False

    async def meth(self, event, *args, **kwargs):
        self.called = True
        self.event = event
        self.args = args
        self.kwargs = kwargs


@pytest.mark.asyncio
async def test_shallow_callback():
    router = routing.Router()
    callback = Callback()
    router.add(callback.meth, "pull_request")
    event = sansio.Event({}, event="pull_request", delivery_id="1234")
    await router.dispatch(event)
    assert callback.called
    assert callback.event == event
    assert not callback.args
    assert not callback.kwargs
    await router.dispatch(event, 42, hello="world")
    assert callback.args == (42,)
    assert callback.kwargs == {"hello": "world"}


@pytest.mark.asyncio
async def test_deep_callback():
    router = routing.Router()
    callback = Callback()
    router.add(callback.meth, "pull_request", data=42)
    event = sansio.Event({"data": 42}, event="pull_request", delivery_id="1234")
    await router.dispatch(event)
    assert callback.called
    assert callback.event == event
    assert not callback.args
    assert not callback.kwargs


def test_too_much_detail():
    router = routing.Router()
    with pytest.raises(TypeError):
        router.add(None, "pull_request", data=42, too_much=6)


@pytest.mark.asyncio
async def test_register():
    router = routing.Router()
    called = False

    @router.register("pull_request", action="new")
    async def callback(event):
        nonlocal called
        called = True

    event = sansio.Event({"action": "new"}, event="pull_request", delivery_id="1234")
    await router.dispatch(event)
    assert called


@pytest.mark.asyncio
async def test_dispatching():
    router = routing.Router()
    event = sansio.Event(
        {"action": "new", "count": 42}, event="nothing", delivery_id="1234"
    )
    await router.dispatch(event)  # Should raise no exceptions.

    shallow_registration = Callback()
    deep_registration_1 = Callback()
    deep_registration_2 = Callback()
    deep_registration_3 = Callback()
    never_called_1 = Callback()
    never_called_2 = Callback()
    never_called_3 = Callback()
    # Wrong event.
    router.add(never_called_1.meth, "something")
    # Wrong event and data detail.
    router.add(never_called_1.meth, "something", action="new")
    # Wrong data detail key.
    router.add(never_called_1.meth, "nothing", never=42)
    # Wrong data detail value.
    router.add(never_called_1.meth, "nothing", count=-13)
    await router.dispatch(event)
    assert not never_called_1.called

    router = routing.Router()
    router.add(shallow_registration.meth, "something")
    router.add(deep_registration_1.meth, "something", action="new")
    router.add(deep_registration_2.meth, "something", action="new")
    router.add(deep_registration_3.meth, "something", count=42)
    router.add(never_called_1.meth, "something else")
    router.add(never_called_2.meth, "something", never="called")
    router.add(never_called_3.meth, "something", count=-13)
    event = sansio.Event(
        {"action": "new", "count": 42, "ignored": True},
        event="something",
        delivery_id="1234",
    )
    await router.dispatch(event)
    assert shallow_registration.called
    assert deep_registration_1.called
    assert deep_registration_2.called
    assert deep_registration_3.called
    assert not never_called_1.called
    assert not never_called_2.called
    assert not never_called_3.called


@pytest.mark.asyncio
async def test_router_copy():
    router = routing.Router()
    deep_callback = Callback()
    shallow_callback = Callback()
    router.add(deep_callback.meth, "something", extra=42)
    router.add(shallow_callback.meth, "something")
    event = sansio.Event({"extra": 42}, event="something", delivery_id="1234")
    await router.dispatch(event)
    assert deep_callback.called
    assert shallow_callback.called
    deep_callback.called = shallow_callback.called = False
    other_router = routing.Router(router)
    await other_router.dispatch(event)
    assert deep_callback.called
    assert shallow_callback.called
