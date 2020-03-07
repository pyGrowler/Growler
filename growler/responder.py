#
# growler/responder.py
#
"""
Event loop independent class for managing clients' requests and
server responses.
"""

from typing import Optional
from asyncio import BaseTransport
from socket import socket as Socket

from abc import ABC, abstractmethod


class GrowlerResponder(ABC):
    """
    Abstract base class for 'responder' objects that handle the
    stream of client data.

    Responders are designed to be event-loop independent, so
    applications may change backend without lots of effort.
    Unfortunately, this means that responders should NOT use
    constructs provided by specific libraries (such as asyncio) and
    instead try to use as much from standard python as they can.
    """
    @abstractmethod
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



class ResponderHandler:
    """
    A common interface for classes that handle GrowlerResponder
    objects.
    The default implementation is the protocol object found in
    growler.aio.protocol.
    """

    __slots__ = (
        'transport',
    )

    transport: Optional[BaseTransport]

    @property
    def socket(self) -> Optional[Socket]:
        return (self.transport.get_extra_info('socket')
                if self.transport is not None
                else None)

    @property
    def peername(self):
        return (self.transport.get_extra_info('peername')
                if self.transport is not None
                else None)

    @property
    def cipher(self):
        return (self.transport.get_extra_info('cipher')
                if self.transport is not None
                else None)

    @property
    def remote_hostname(self):
        return (self.peername[0]
                if self.transport is not None
                else None)

    @property
    def remote_port(self):
        return (self.peername[1]
                if self.transport is not None
                else None)


# clean namespace
del ABC
del abstractmethod
del BaseTransport
del Optional
del Socket
