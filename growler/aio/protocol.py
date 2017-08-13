#
# growler/aio/protocol.py
#
"""
Code containing Growler's asyncio.Protocol code for handling all
streaming (TCP) connections.
This module has a 'hard' dependency on asyncio, so if you're using a
diffent event loop (for example, curio) then you should NOT be using
this class.

Alternative Protocol classes may use this as an example.

For more information, see the :module:`growler.core.responder` module
for event-loop independent client handling.
"""

import asyncio
import logging
from growler.core.responder import ResponderHandler

logger = logging.getLogger(__name__)


class GrowlerProtocol(asyncio.Protocol, ResponderHandler):
    """
    The 'base' protocol for handling all requests made to a growler
    application.
    This implementation internally uses a stack of 'responder'
    objects, the top of which will receive incoming client data via
    the `on_data` method.
    This design provides a way to temporarily (or permanently) modify
    the server's behavior.
    To change behavior when a client has already connected, such as
    during an HTTP upgrade or to support starttls encryption, simply
    add a new responder to the protocol's stack.

    If all responders are removed, the :method:`handle_error` method
    will be called with the IndexError exception.
    This method is not implemented by default and SHOULD be
    implemented in all subclasses.

    Because of this delegate-style design, the user should NOT
    overload the :method:`data_received` method when creating a
    subclass of GrowlerProtocol.

    To simplify the creation of the initial responder, a factory (or
    simply the type/constructor) is passed to the GrowlerProtocol
    object upon construction.
    This factory is run when 'connection_made' is called on the
    protocol (which should happen immediately after construction).
    It is recommended that subclasses of :class:`GrowlerProtocol`
    specify a particular *default responder* by setting the keyword
    argument, `responder_factory`, in a call to super().__init__().

    Two methods, :method:`factory` and :method:`get_factory`, are
    provided to make the construction of servers 'easy', without the
    need for lambdas.

    If you have a subclass:
    .. code:: python

        class GP(GrowlerProtocol):
            ...

    you can create a server easy using this protocol via:
    .. code:: python

        asyncio.get_event_loop().create_server(GP.factory, ...)
    or
    .. code:: python

        asyncio.get_event_loop().create_server(GP.get_factory('a','b'), ...)

    arguments passed to get_factory in the later example are
    forwarded to the protocol constructor (called whenever a client
    connects).
    Note, calling GP.factory() will not work as `create_server`
    expects the factory and *not an instance* of the protocol.
    """

    transport = None
    responders = None
    is_done_transmitting = False

    def __init__(self, loop, responder_factory):
        """
        Args:
            loop (asyncio.BaseEventLoop): The event loop managing all
                asynchronous activity of this protocol.
            responder_factory (callable): Returns the first responder
                for this protocol.
                This could simply be a constructor for the type (i.e.
                the type's name).
                This function will only be passed the protocol object.
                The event loop should be aquired from the protocol via
                the 'loop' member.
                The responder returned only needs to have a method
                defined called 'on_data' which gets passed the bytes
                received.
                Note: 'on_data' should only be a function and NOT a
                coroutine.
        """
        self.make_responder = responder_factory
        self.loop = loop if (loop is not None) else asyncio.get_event_loop()
        self.log = logger.getChild("id=%x" % id(self))

    def connection_made(self, transport):
        """
        (asyncio.Protocol member)

        Called upon when there is a new socket connection.
        This creates a new responder (as determined by the member
        'responder_type') and stores in a list.
        Incoming data from this connection will always call on_data
        to the last element of this list.

        Args:
            transport (asyncio.Transport): The Transport handling the
                socket communication
        """
        self.transport = transport
        self.responders = [self.make_responder(self)]

        try:
            good_func = callable(self.responders[0].on_data)
        except AttributeError:
            good_func = False

        if not good_func:
            err_str = "Provided responder MUST implement an 'on_data' method"
            raise TypeError(err_str)

        self.log.info("Connection from %s:%d",
                      self.remote_hostname, self.remote_port)

    def connection_lost(self, exc):
        """
        (asyncio.Protocol member)

        Called upon when a socket closes.
        This class simply logs the disconnection

        Args:
            exc (Exception or None): Error if connection closed
                unexpectedly, None if closed cleanly.
        """
        if exc:
            self.log.error("connection_lost %r", exc)
        else:
            self.log.info("connection_lost")

    def data_received(self, data):
        """
        (asyncio.Protocol member)

        Called upon when there is new data to be passed to the
        protocol.
        The data is forwarded to the top of the responder stack (via
        the on_data method).
        If an excpetion occurs while this is going on, the Exception
        is forwarded to the protocol's handle_error method.

        Args:
            data (bytes): Bytes from the latest data transmission
        """
        try:
            self.responders[-1].on_data(data)
        except Exception as error:
            self.handle_error(error)

    def eof_received(self):
        """
        (asyncio.Protocol member)

        Called upon when the client signals it will not be sending
        any more data to the server.
        Default behavior is to simply set the `is_done_transmitting`
        property to True.
        """
        self.is_done_transmitting = True
        self.log.info("eof_received")

    def handle_error(self, error):
        """
        An error handling function which will be called when an error
        is raised during a responder's :method:`on_data()` function.
        There is no default functionality and all subclasses SHOULD
        overload this.

        Args:
            error (Exception): The exception raised from the code
        """
        raise NotImplementedError(error)

    @property
    def socket(self):
        return self.transport.get_extra_info('socket')

    @property
    def cipher(self):
        return self.transport.get_extra_info('cipher')

    @property
    def peername(self):
        return self.transport.get_extra_info('peername')

    @classmethod
    def factory(cls, *args, **kw):
        """
        A class function which simply calls the constructor.
        Useful for explicity stating that this is a factory.
        All arguments are forwarded to the constructor.
        """
        return cls(*args, **kw)

    @classmethod
    def get_factory(cls, *args, **kw):
        """
        A class function which returns a runnable which calls the
        factory function (i.e. the constructor) of the class with
        the arguments provided.
        This should makes it easy to bind `GrowlerProtocol`
        construction explicitly.
        All arguments are forwarded to the constructor.
        """
        return lambda: cls.factory(*args, **kw)
