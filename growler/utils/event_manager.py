#
# growler/utils/event_emitter.py
#

import asyncio
from collections import defaultdict
try:
    from types import CoroutineType, GeneratorType
except ImportError: # shim until python3.4 support is dropped
    from types import GeneratorType
    CoroutineType = type(None)


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

        # async def emit(self, name):
        @asyncio.coroutine
        def emit(self, name):
            """
            Coroutine which executes each of the callbacks added to the event
            identified by 'name'
            """
            for cb in event_dict[name]:
                # if isinstance(cb, CoroutineType):
                    # await cb()
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


class Events:
    """
    A high-level container of asynchronous callback events.
    Objects of this type are intended to be used as a member of a class.

    The standard usage is to have a member named 'events' to which you
    add various callbacks using on.

    Upon this supports both synchronous and asynchronous callbacks.

    In the future, I'd like to have :before & :after tags to strictly
    define whether when callbacks are called relative to another
    function. The current way to do this is to have two events, ``before_foo``
    and ``after_foo`` and it's up to the implementation of 'foo' to ensure
    that these are called appropriately.


    Example:

    >>> my_obj.events.on('foo', bar)
    >>> # some code
    >>> async def run_stuff():
    >>>     await my_obj.events.emit('foo')  # bar() is called

    """

    def __init__(self, *event_names):
        """
        Construct Events object with a set of allowed event names.
        If no event names are given, then all events are allowed.


        """
        if ... in event_names or event_names == ():
            self._event_list = defaultdict(list)
        else:
            self._event_list = {name: [] for name in event_names}


    def on(self, name, _callback=None):
        """
        Add a callback to the event named 'name'.
        Returns callback object for decorationable calls.
        """
        # this must be a decorator
        if _callback is None:
            return lambda cb: self.on(name, cb)

        if not callable(_callback) and not isinstance(_callback, GeneratorType):
            msg = "Callback not callable: {0!r}".format(_callback)
            raise ValueError(msg)

        self._event_list[name].append(_callback)
        return _callback

    # async def emit(self, name):
    @asyncio.coroutine
    def emit(self, name):
        """
        Add a callback to the event named 'name'.
        Returns this object for chained 'on' calls.
        """
        for cb in self._event_list[name]:
            if isinstance(cb, (CoroutineType, GeneratorType)):
                yield from cb
            else:
                cb()

    def sync_emit(self, name):
        """
        Add a callback to the event named 'name'.
        Returns this object for chained 'on' calls.
        """
        for cb in self._event_list[name]:
            cb()
