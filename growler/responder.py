#
# growler/responder.py
#
"""
Event loop independent class for managing clients' requests and
server responses.
"""

import abc


class GrowlerResponder(abc.ABC):
    """
    Abstract base class for 'responder' objects that handle the
    stream of client data.

    Responders are designed to be event-loop independent, so
    applications may change backend without lots of effort.
    Unfortunately, this means that responders should NOT use
    constructs provided by specific libraries (such as asyncio) and
    instead try to use as much from standard python as they can.
    """

    @abc.abstractmethod
    def on_data(self, data):
        raise NotImplementedError()


class CoroutineResponder(GrowlerResponder):
    """
    Special responder object that will 'send' data to a coroutine
    object for processing.
    """

    def __init__(self, coro):
        self._coro = coro

    def on_data(self, data):
        self._coro.send(data)


class ResponderHandler(abc.ABC):
    """
    A common interface for classes that handle GrowlerResponder
    objects.
    The default implementation is the protocol object found in
    growler.aio.protocol.
    """

    @abc.abstractproperty
    def socket(self):
        pass

    @abc.abstractproperty
    def peername(self):
        pass

    @abc.abstractproperty
    def transport(self):
        pass

    @property
    def remote_hostname(self):
        return self.peername[0]

    @property
    def remote_port(self):
        return self.peername[1]
