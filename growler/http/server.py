#
# growler/http/server.py
#
"""
Classes for running an http server
"""

import asyncio

class HTTPServer():
    """
    This is the reference implementation of an HTTP server for the Growler
    project.
    """

    def __init__(self, cb, loop=None,ssl=None,message=""):
        """
        Construct a server
        @param cb runnable: The callback to handle requests
        @param loop asyncio.event_loop: the event loop this server is using. If
            none it will default to asyncio.get_event_loop
        @param ssl ssl.SSLContext: If not none, we are hosting HTTPS
        @param message str: a message to be printed for debugging
        """
        self.callback = cb
        self.loop = loop if loop is not None else asyncio.get_event_loop()
        self.ssl = ssl
        if message:
            print (message)

    def listen(self, port, host='127.0.0.1'):
        """
        Method to indicate to the server to listen on a particular port.
        @param host str: hostname or ip address to listen on
        @param port: The port number to listen on
        """
        self.coro = self.loop.create_server(http_proto, host, port, ssl=self.ssl)
        self.srv = self.loop.run_until_complete(self.coro)
        print('serving on {}'.format(self.srv.sockets[0].getsockname()))
        print(' sock {}'.format(self.srv.sockets[0]))
