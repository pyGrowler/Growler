#
# growler/utils/event_emitter.py
#

import asyncio


def event_emitter(cls_=None, *, events=('*',), loop=None):
    """
    A class-decorator which will add the specified events and the methods 'on'
    and 'emit' to the class.
    """

    if loop is None:
        loop = asyncio.get_event_loop()

    # create a dictionary from items in the 'events' parameter and with empty
    # lists as values
    event_dict = dict.fromkeys(events, [])

    # if '*' was in the events tuple - then pop it out of the event_dict
    # and store the fact that we may allow any event name to be added to the
    # event emitter.
    allow_any_eventname = event_dict.pop('*', False) == []

    def _event_emitter(cls):

        def on(self, name, callback):
            """
            Add a callback to the event named 'name'. Returns the object for
            chained 'on' calls.
            """
            if not callable(callback):
                msg = "Callback not callable: {0!r}".format(callback)
                raise ValueError(msg)

            try:
                event_dict[name].append(callback)
            except KeyError:
                if allow_any_eventname:
                    event_dict[name] = [callback]
                else:
                    msg = "Event Emitter has no event {0!r}".format(name)
                    raise KeyError(msg)

            return self

        @asyncio.coroutine
        def emit(self, name):
            """
            Coroutine which executes each of the callbacks added to the event
            identified by 'name'
            """
            for cb in event_dict[name]:
                if asyncio.iscoroutinefunction(cb):
                    yield from cb()
                else:
                    cb()

        cls.on = on
        cls.emit = emit

        return cls

    if cls_ is None:
        return _event_emitter
    else:
        return _event_emitter(cls_)


def emits(pre=None, *, post=None):
    pass
