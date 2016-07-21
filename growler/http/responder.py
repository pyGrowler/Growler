#
# growler/http/responder.py
#
"""
The Growler class responsible for responding to HTTP requests.
"""

from .parser import Parser
from .request import HTTPRequest
from .response import HTTPResponse
from .methods import HTTPMethod

from .errors import (
    HTTPErrorBadRequest,
)


class GrowlerHTTPResponder:
    """
    The Growler Responder for HTTP connections.

    Like *all* growler responders - this class is responsible for
    responding to client data forwarded by a growler protocol object.

    This responder has linear functionality, performing the following
    tasks:

    #) Feed client data to parser until all headers have been sent
    #) Create req/res objects out of the headers
    #) Start application middleware chain with headers (add task to the
       event loop)
    #) Store all remaining client data into the request objects "body"
       attribute (a Future).

    The `on_data` method is the only useful method, where the responder
    acts on the next bit of user data.

    This should really only be constructed from a growler protocol instance.
    """

    body_buffer = None
    content_length = None
    headers = None

    def __init__(self,
                 protocol,
                 parser_factory=Parser,
                 request_factory=HTTPRequest,
                 response_factory=HTTPResponse,
                 ):
        """
        Construct a Responder. This method only requires the 'parent'
        protocol object which has a link to the main Application object.

        Parameters:
            protocol (GrowlerHTTPProtocol): The owner/creator of this
                responder. This object MUST have an `app` attribute
                that points to the application to be called. Some
                connection information (e.g. client's ip address) is
                forwarded from this protocol via some properties.

            parser_factor (type or callable): Factory function (or
                classname) of the object responsible for parsing the
                client's request line and headers. Default value is the
                growler.http.parser.Parser class. The object must have
                a 'consume' method which accepts the incoming data. If
                this data only has partial headers, consume returns
                None, and the parser should expect consume to be called
                again. When the headers have finished, the consume
                function returns any body data past the headers.

            request_factory (type or callable): Factory function (or
                classname) of the request object which gets passed to
                the applications middleware as the first parameter.
                The default value is the class growler.http.HTTPRequest.
                When called, this object must accepts two arguments: the
                protocol handling the connection and the headers
                returned from the parser.

            response_factory (type or callable): Factory function (or
                classname) of the response object which gets passed to
                the applications middleware as the second parameter.
                The default value is the class growler.http.HTTPResponse.
                When called, this object must accept one argument: the
                parent protocol handling the connection.

        """
        self._proto = protocol
        self.parser = parser_factory(self)
        self.build_req = request_factory
        self.build_res = response_factory

    def on_data(self, data):
        """
        This is the function called by the http protocol upon receipt
        of incoming client data.
        The data is passed to the responder's parser class (via the
        consume method), which digests and stores as HTTP fields.

        Upon completion of parsing the HTTP headers, the responder
        creates the request and response objects, and passes them to
        the begin_application method, which starts the parent
        application's middleware chain.

        Parameters:
            data (bytes): HTTP data from the socket, expected to be
                passed directly from the transport/protocol objects.

        Raises:
            HTTPErrorBadRequest: If there is a problem parsing headers
                or body length exceeds expectation.
        """
        # Headers have not been read in yet
        if len(self.headers) == 0:
            # forward data to the parser
            data = self.parser.consume(data)

            # Headers are finished - build the request and response
            if data is not None:

                # setup the request line attributes
                self.set_request_line(self.parser.method,
                                      self.parser.parsed_url,
                                      self.parser.version)

                # initialize "content_length" and "body_buffer" attributes
                self.init_body_buffer(self.method, self.headers)

                # builds request and response out of self.headers and protocol
                self.req, self.res = self.build_req_and_res()

                # add middleware chain to event loop
                self.begin_application(self.req, self.res)

        # if truthy, 'data' now holds body data
        if data:
            self.validate_and_store_body_data(data)

            # if we have reached end of content - put in the request's body
            if len(self.body_buffer) == self.content_length:
                self.req.body.set_result(bytes(self.body_buffer))

    def begin_application(self, req, res):
        """
        Sends the given req/res objects to the application.

        This method calls the target app's handle_client_request method
        and adds this coroutine to the loop as a task.
        This is only to be called after parsing the request headers.

        Parameters:
            req (HTTPRequest): The request
            res (HTTPResponse): The response
        """
        # Add the middleware processing to the event loop - this *should*
        # change the call stack so any server errors do not link back to this
        # function
        self.loop.create_task(self.app.handle_client_request(req, res))

    def set_request_line(self, method, url, version):
        """
        Sets the request line on the responder.
        """
        self.parsed_request = (method, url, version)
        self.request = {
            'method': method,
            'url': url,
            'version': version
        }

    def init_body_buffer(self, method, headers):
        """
        Sets up the body_buffer and content_length attributes based
        on method and headers.
        """
        content_length = headers.get("CONTENT-LENGTH", None)

        if method in (HTTPMethod.POST, HTTPMethod.PUT):
            if content_length is None:
                raise HTTPErrorBadRequest("HTTP Method requires a CONTENT-LENGTH header")
            self.content_length = int(content_length)
            self.body_buffer = bytearray(0)

        elif content_length is not None:
            raise HTTPErrorBadRequest(
                "HTTP method %s may NOT have a CONTENT-LENGTH header"
            )

    def build_req_and_res(self):
        """
        Simple method which calls the request and response factories
        the responder was given, and returns the pair.
        """
        req = self.build_req(self, self.headers)
        res = self.build_res(self._proto)
        return req, res

    def validate_and_store_body_data(self, data):
        """
        Attempts simple body data validation by comparining incoming
        data to the content length header.
        If passes store the data into self._buffer.

        Parameters:
            data (bytes): Incoming client data to be added to the body

        Raises:
            HTTPErrorBadRequest: Raised if data is sent when not
                expected, or if too much data is sent.
        """

        # add data to end of buffer
        self.body_buffer[-1:] = data

        #
        if len(self.body_buffer) > self.content_length:
            problem = "Content length exceeds expected value (%d > %d)" % (
                len(self.body_buffer), self.content_length
            )
            raise HTTPErrorBadRequest(phrase=problem)

    @property
    def method(self):
        """
        The HTTP method as the growler enumerated value
        """
        return self.parser.method

    @property
    def method_str(self):
        """
        The HTTP method as an all-caps string (e.g. 'GET')
        """
        return self.parser.method

    @property
    def parsed_query(self):
        """
        The HTTP query as parsed by the standard python urllib.parse
        library. Simply forwards the result obtained by the parser.
        """
        return self.parser.query

    @property
    def headers(self):
        """
        The dict of HTTP headers.
        """
        return self.parser.headers

    @property
    def loop(self):
        """
        The asyncio event loop this responder belongs to.
        """
        return self._proto.loop

    @property
    def app(self):
        """
        The growler application this responder belongs to.
        """
        return self._proto.http_application

    @property
    def ip(self):
        """
        Ip address of the client. Retrieved from parent protocol object
        """
        return self._proto.socket.getpeername()[0]
