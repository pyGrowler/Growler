#
# growler/http/server.py
#
"""
Functions and classes for running an http server
"""

import asyncio
import ssl


def create_server(
        host='127.0.0.1',
        port=8000,
        ssl=None,
        loop=None,
        **kargs
        ):
    """
    This is a function to assist in the creation of a growler HTTP server.

    @param host str: hostname or ip address on which to bind
    @param port: the port on which the server will listen
    @param ssl ssl.SSLContext: The SSLContext for using TLS over the connection
    @param loop asyncio.BaseEventLoop: The event loop to
    @param kargs: Extra parameters passed to the HTTPServer instance created.
                  If there is an ssl parameter passed to this function, kargs
                  will require the value 'key' to be present, and an optional
                  'cert' parameter to pass to load_cert_chain.
    @return An HTTPServer instance
    """

    loop = asyncio.get_event_loop() if loop is None else loop

    if ssl:
        sslctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        key = kargs.pop('key')
        try:
            sslctx.load_cert_chain(certfile=kargs.pop('cert'),
                                   keyfile=key)
        except KeyError:
            sslctx.load_cert_chain(certfile=key)
    else:
        sslctx = None

    # What do I use as a 'callback' here?
    srv = HTTPServer(loop=loop, ssl=sslctx)
    coro = loop.create_server(srv.generate_protocol(), host, port, ssl=sslctx)
    server = loop.run_until_complete(coro)
    return server


class HTTPServer():
    """
    This is the reference implementation of an HTTP server for the Growler
    project.
    """

    def __init__(self, cb=None, loop=None, ssl=None, message="", **kargs):
        """
        Construct a server. Parameters given here will be forwarded to the
        asyncio.create_server function.

        @param cb runnable: The callback to handle requests
        @param loop asyncio.event_loop: the event loop this server is using. If
            none it will default to asyncio.get_event_loop
        @param ssl ssl.SSLContext: If not none, we are hosting HTTPS
        @param message str: a message to be printed for debugging
        @param kargs: Any extra arguments to be given to the server
        """
        self.callback = cb
        self.loop = loop or asyncio.get_event_loop()
        self.ssl = ssl
        self.server_kargs = {
            'loop': self.loop
        }
        self.proto_args = dict()
        self.kargs = kargs
        if message:
            print(message)

    def serve_forever(self):
        """
        Simply calls the event loop's run forever method.
        """
        self.loop.run_forever()

    def listen(self, port, host='127.0.0.1', block=False):
        """
        Method to indicate to the server to listen on a particular port.

        @param host str: hostname or ip address to listen on
        @param port: The port number to listen on
        @param block bool: If true, this function will run until the server
            stops running.
        """
        self.coro = self.loop.create_server(http_proto, host, port,
                                            ssl=self.ssl)
        self.srv = self.loop.run_until_complete(self.coro)
        self.proto_args = dict()
        print('serving on {}'.format(self.srv.sockets[0].getsockname()))
        print(' sock {}'.format(self.srv.sockets[0]))

    def generate_protocol(self):
        """
        Helper function to act as a protocol factory for the
        GrowlerHTTPProtocol
        """
        return growler.protocol.GrowlerHTTPProtocol(**self.proto_args)

    def __call__(self, **kargs):
        """
        Calling a server object returns a coroutine created from a call to
        asyncio.BaseEventLoop.create_server, this coroutine can be wrapped in a
        task or called however the user wishes.
        """
        coro = loop.create_server(self.generate_protocol, **self.server_kargs)
        return coro
