#
# growler/http/request.py
#

import asyncio
import logging

log = logging.getLogger(__name__)


class HTTPRequest:
    """
    Helper class which normalizes access to client information of an incoming
    http request. The object is intended to be mutable, with middleware adding
    methods and members for maximum flexibility.

    The HTTPRequest is almost always paired with a HTTPResponse object to reply
    back to the client.

    Object construction should only happen by an HTTPProtocol object after HTTP
    headers have been parsed; not by any middleware or auxillary function.
    """

    _protocol = None
    headers = None
    body = None

    def __init__(self, responder, headers):
        """
        The HTTPRequest object is all the information you could want about the
        incoming http connection. It gets passed along with the HTTPResponse
        object to all the middleware of the app.

        Parameters
        ----------
        protocol : growler.HTTPProtocol
            A reference to the protocol which was responsible for handling the
            client's request and creating this HTTPRequest object.
        headers : dict
            The headers gathered from the incoming stream
        """
        self._protocol = responder
        self.headers = headers

        if 'CONTENT-LENGTH' in headers:
            self.body = asyncio.Future()

        log.info("%d %s %s" % (id(self), self.method, self.path))

    def param(self, name, default=None):
        """
        Return value of HTTP parameter 'name' if found, else return provided
        'default'

        Parameters
        ----------
        name : str
            Key used to search the query dict
        default : mixed
            Value returned if 'name' is not found in the query dict
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
        return self._protocol.ip

    @property
    def app(self):
        return self._protocol.app

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
        return self._protocol.parsed_query

    @property
    def hostname(self):
        return self.headers['HOST']

    @property
    def method(self):
        return self._protocol.method

    @property
    def protocol(self):
        """
        The name of the protocol being used
        """
        return 'https' if self._protocol.cipher else 'http'
