#
# growler/protocol.py
#
"""
Code containing Growler's asyncio.Protocol code for handling all streaming
(TCP) connections.
"""

import asyncio
import sys


class GrowlerProtocol(asyncio.Protocol):
    """
    The 'base' protocol for handling all requests. This implementation hands
    off all data received to a 'responder' object. Because of this, it does NOT
    expect that the data_received function would be overloaded by a subclass,
    but rather the behavior should be defined by the responder it is passing
    to.

    The protocol maintains a stack of responders, and forwards incoming data to
    the top of the stack via an on_data command. This forwarding is (currently)
    done asynchronously by the asyncio.BaseEventLoop.call_soon function.

    To simplify the creation of the initial responder, a factory (or simply the
    constructor/type) is passed to the GrowlerProtocol object upon
    construction. This factory is run when 'connection_made' is called on the
    protocol.

    Two functions, factory and get_factory, are provided to make the
    construction of servers 'easy', without the need for lambdas. If you have a
    subclass:
        class GP(GrowlerProtocol):
            ...
    you can create a server easy using this protocol via:

        asyncio.get_event_loop().create_server(GP.factory, ...)
    or
        asyncio.get_event_loop().create_server(GP.get_factory('a','b'), ...)

    , the later example forwarding arguments to the factory. Note, calling
    GP.factory() will not work as create_server expects the factory and not an
    instance of the protocol.
    """

    transport = None
    responders = None
    is_done_transmitting = False

    def __init__(self, loop, responder_factory):
        """
        Construct a GrowlerProtocol object.

        :param loop asyncio.BaseEventLoop: The event loop managing all
            asynchronous activity of this protocol.

        :param responder_factory runnable: A callable which returns the first
            responder for this protocol. This could simply be a constructor for
            the type (i.e. the type's name). This function will only be passed
            the protocol object. The event loop should be aquired from the
            protocol via the 'loop' member. The responder returned only needs
            to have a method defined called 'on_data' which gets passed the
            bytes received. Note: 'on_data' should only me a function and NOT a
            coroutine.
        """
        self.make_responder = responder_factory
        self.loop = loop if (loop is not None) else asyncio.get_event_loop()

    def connection_made(self, transport):
        """
        asyncio.Protocol member - called upon when there is a new socket
        connection. This creates a new responder (as determined by the member
        'responder_type') and stores in a list. Incoming data from this
        connection will always call
        on_data to the last element of this list.

        :param transport asyncio.Transport: The Transport handling the socket
            communication
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

        print("Growler Connection from {}:{}".format(self.remote_hostname,
                                                     self.remote_port))

    def connection_lost(self, exc):
        """
        asyncio.Protocol member - called upon when a socket closes.

        :param exc Exception: Error if unexpected closing. None if clean close
        """
        if exc:
            print("[connection_lost]", exc, file=sys.stderr)
        print("[connection_lost]")

    def data_received(self, data):
        """
        asyncio.Protocol member - called upon when there is data to be read

        :param transport bytes: bytes in the latest data transmission
        """
        try:
            self.responders[-1].on_data(data)
        except Exception as error:
            self.handle_error(error)

    def eof_received(self):
        """
        asyncio.Protocol member - called upon when the client signals it will
        not be sending any more data to the server.
        """
        self.is_done_transmitting = True
        print("[GrowlerProtocol::eof_received]")

    def handle_error(self, error):
        """
        An error handling function which will be called when an error is raised
        during a responder's on_data() function. There is no default
        functionality and the subclasses must overload this.

        :param error: Exception thrown in code
        """
        raise NotImplementedError()

    @property
    def socket(self):
        return self.transport.get_extra_info('socket')

    @property
    def cipher(self):
        return self.transport.get_extra_info('cipher')

    @property
    def remote_hostname(self):
        return self.transport.get_extra_info('peername')[0]

    @property
    def remote_port(self):
        return self.transport.get_extra_info('peername')[1]

    @property
    def peername(self):
        return self.transport.get_extra_info('peername')

    @classmethod
    def factory(cls, *args, **kw):
        """
        A class function which simply calls the constructor. Useful for
        explicity stating that this is a factory. All arguments are forwarded
        to the constructor.
        """
        return cls(*args, **kw)

    @classmethod
    def get_factory(cls, *args, **kw):
        """
        A class function which returns a runnable which calls the factory
        function (i.e. the constructor) of the class with the arguments
        provided. This should makes it easy to bind GrowlerProtocol
        construction explicitly. All arguments are forwarded to the
        constructor.
        """
        return lambda: cls.factory(*args, **kw)
