from typing import Any, Callable, Dict, List


class Router:

    """Route webhook events to registered functions."""

    def __init__(self, *other_routers):
        """Instantiate a new router (possibly from other routers)."""
        # event type -> data key -> data value -> callbacks
        self._routes: Dict[str, Dict[str, Dict[Any, List[Callable]]]] = {}
        for other_router in other_routers:
            for event_type, data_details in other_router._routes.items():
                for data_key, data_specifics in data_details.items():
                    for data_value, callbacks in data_specifics.items():
                        for callback in callbacks:
                            detail = {data_key: data_value}
                            self.add(callback, event_type, **detail)

    def add(self, func, event_type, **data_detail):
        """Add a new route.

        After registering 'func' for the specified event_type, an
        optional data_detail may be provided. By providing an extra
        keyword argument, dispatching can occur based on a top-level
        key of the data in the event being dispatched.
        """
        if len(data_detail) > 1:
            msg = ()
            raise TypeError("dispatching based on data details is only "
                            "supported up to one level deep; "
                            f"{len(data_detail)} levels specified")
        elif not data_detail:
            data_key = data_value = None
        else:
            data_key, data_value = data_detail.popitem()
        data_details = self._routes.setdefault(event_type, {})
        specific_detail = data_details.setdefault(data_key, {})
        callbacks = specific_detail.setdefault(data_value, [])
        callbacks.append(func)

    def register(self, event_type, **data_detail):
        """Decorator to apply the add() method to a function."""
        def decorator(func):
            self.add(func, event_type, **data_detail)
            return func
        return decorator

    async def dispatch(self, event):
        """Dispatch an event to all registered function(s)."""
        try:
            details = self._routes[event.event]
        except KeyError:
            return
        found_callbacks = []
        try:
            # The "no data details" case.
            found_callbacks.extend(details[None][None])
        except KeyError:
            pass
        for data_key, data_values in details.items():
            if data_key is None:
                continue
            elif data_key in event.data:
                event_value = event.data[data_key]
                if event_value in data_values:
                    found_callbacks.extend(data_values[event_value])
        for callback in found_callbacks:
            await callback(event)
