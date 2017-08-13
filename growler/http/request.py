#
# growler/http/request.py
#

import logging

logger = logging.getLogger(__name__)


class HTTPRequest:
    """
    Helper class which normalizes access to client information of an
    incoming http request.
    The object is intended to be mutable, with middleware adding
    methods and members for maximum flexibility.

    The HTTPRequest is almost always paired with a HTTPResponse
    object to reply back to the client.

    Object construction should only happen by an HTTPProtocol object
    after HTTP headers have been parsed; not by any middleware or
    auxillary function.
    """

    _responder = None
    headers = None
    _body = None

    def __init__(self, responder, headers):
        """
        The HTTPRequest object is all the information you could want
        about the incoming http connection.
        It gets passed along with the HTTPResponse object to all the
        middleware of the app.

        Parameters:
            responder (GrowlerHTTPResponder): A reference to the
                responder object responsible for handling the
                client's request and creating this HTTPRequest object.
            headers (dict): The headers gathered from the incoming
                stream.
        """
        self.log = logger.getChild("id=%x" % id(self))
        self._responder = responder
        self.headers = headers

        if 'CONTENT-LENGTH' in headers:
            self._body, self._body_writer = responder.body_storage_pair()

        self.log.info("%r %r", self.method, self.path)

    def param(self, name, default=None):
        """
        Return value of HTTP parameter 'name' if found, else return
        provided 'default'.

        Parameters:
            name (str): Key used to search the query dict
            default (mixed): Value returned if 'name' is not found
                in the query dict
        """
        return self.query.get(name, default)

    async def body(self):
        """
        A helper function which blocks until the body has been read
        completely.
        Returns the bytes of the body which the user should decode.

        If the request does not have a body part (i.e. it is a GET
        request) this function returns None.
        """
        if not isinstance(self._body, bytes):
            self._body = await self._body
            self.log.info("Set body to %d bytes", len(self._body))
        return self._body

    def set_body_data(self, data):
        """
        Sets the body (the thing returned by :method:`body`) to some
        data.
        """
        self._body_writer.send(data)

    def type_is(self, mime_type):
        """
        returns True if content-type of the request matches the
        mime_type parameter.
        """
        return self.headers['content-type'] == mime_type

    @property
    def ip(self):
        return self._responder.ip

    @property
    def app(self):
        return self._responder.app

    @property
    def path(self):
        return self._responder.request['url'].path

    @property
    def originalURL(self):
        return self._responder.request['url'].path

    @property
    def loop(self):
        return self._responder.loop

    @property
    def query(self):
        return self._responder.parsed_query

    @property
    def hostname(self):
        return self.headers['HOST']

    @property
    def method(self):
        return self._responder.method

    @property
    def protocol(self):
        """
        The name of the protocol being used
        """
        return 'https' if self._responder.cipher else 'http'

    @property
    def peercert(self):
        """
        Returns a dictionary of information about the connection's
        ssl cetrificate if a secure channel has been established,
        otherwise return None.

        For more information, see the standard library documentation at
        ``https://docs.python.org/3/library/ssl.html#ssl.SSLSocket.getpeercert``
        """
        return self._handler.socket.getpeercert()
