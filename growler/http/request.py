#
# growler/http/request.py
#

import asyncio


class HTTPRequest(object):
    """
    Helper class which handles the parsing of an incoming http request.
    The usage should only be from an HTTPRequest object calling the parse()
    function.
    """

    _protocol = None
    headers = None
    body = None

    def __init__(self, protocol, headers):
        """
        The HTTPRequest object is all the information you could want about the
        incoming http connection. It gets passed along with the HTTPResponse
        object to all the middleware of the app.

        :param protocol growler.HTTPProtocol: A reference to the protocol which
            was responsible for handling th e client's request and creating
            this HTTPRequest object.

        :param headers dict: The headers gathered from the incoming stream
        """
        self._protocol = protocol
        self.headers = headers

        if 'CONTENT-LENGTH' in headers:
            self.body = asyncio.Future()

    def param(self, name, default=None):
        """
        Return value of HTTP parameter 'name' if found, else return provided
        'default'

        :param name: Key to search the query dict for
        :type name: str

        :param default: Returned if 'name' is not found in the query dict
        """
        return self.query.get(name, default)

    def get_body(self, timeout=0):
        """
        A helper function which blocks until the body has been read completely.
        Returns the bytes of the body which the user should decode. An optional
        timeout parameter can be set to throw an asyncio.TimeoutError if the
        body does not complete before 'timeout' number of seconds.

        If the request does not have a body part (i.e. it is a GET request)
        this function returns None
        """
        if self.body is None:
            return None
        coro = asyncio.wait_for(self.body, timeout, loop=self.loop)
        self._protocol.loop.run_until_complete(coro)
        return self.body.result()

    def type_is(self, mime_type):
        """
        returns True if content-type of the request matches the mime_type
        parameter.
        """
        return self.headers['content-type'] == mime_type

    @property
    def ip(self):
        return self._protocol.socket.getpeername()[0]

    @property
    def app(self):
        return self._protocol.http_application

    @property
    def path(self):
        return self._protocol.request['url'].path

    @property
    def originalURL(self):
        return self._protocol.request['url'].path

    @property
    def loop(self):
        return self._protocol.loop

    @property
    def query(self):
        return self._protocol.client_query

    @property
    def hostname(self):
        return self.headers['HOST']

    @property
    def method(self):
        return self._protocol.client_method

    @property
    def protocol(self):
        """
        The name of the protocol being used
        """
        return 'https' if (self.protocol.cipher) else 'http'
