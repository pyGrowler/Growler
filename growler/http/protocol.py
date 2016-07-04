#
# growler/http/protocol.py
#
"""
Code containing Growler's asyncio.Protocol code for handling HTTP requests.
"""
import traceback
from sys import stderr
from growler.protocol import GrowlerProtocol
from growler.http.responder import GrowlerHTTPResponder
from growler.http.response import HTTPResponse
from growler.http.errors import (
    HTTPError
)


# Or should this be called HTTPGrowlerProtocol?
class GrowlerHTTPProtocol(GrowlerProtocol):
    """
    GrowlerProtocol dealing with HTTP requests. Objects are created with a
    growler.App instance, which contains the relevant event_loop. The default
    responder_type is GrowlerHTTPResponder, which does the data parsing and
    req/res creation.

    Additional responders may be created and used, the req/res pair may be
    lost, but only one GrowlerHTTPProtocol object will persist through the
    connection; it may be wise to store HTTP information in this.

    To change the responder type to something other than GrowlerHTTPResponder,
    overload or replace the http_responder_factory method.
    """

    client_method = None
    client_query = None
    client_headers = None

    def __init__(self, app):
        """
        Construct a GrowlerHTTPProtocol object. This should only be called from
        a growler.HTTPServer instance (or any asyncio.create_server function).

        Parameters
        ----------
        app : growler.Application
            Typically a growler application which is the 'target object' of
            this protocol. Any callable with a 'loop' attribute and a
            handle_client_request coroutine method should work.
        """
        self.http_application = app
        super().__init__(loop=app.loop,
                         responder_factory=self.http_responder_factory)

    @staticmethod
    def http_responder_factory(proto):
        """
        The default factory function which creates a GrowlerHTTPResponder with
        this object as the parent protocol, and the application's req/res
        factory functions.

        To change the default responder, overload this method with the same
        to return your
        own responder.

        Params
        ------
        proto : GrowlerHTTPProtocol
            Explicitly passed protocol object (actually it's what would be
            'self'!)

        Note
        ----
        This method is decorated with @staticmethod, as the connection_made
        method of GrowlerProtocol explicitly passes `self` as a parameters,
        instead of treating as a bound method.
        """
        return GrowlerHTTPResponder(
            proto,
            request_factory=proto.http_application._request_class,
            response_factory=proto.http_application._response_class,
        )

    def handle_error(self, error):
        """
        An error handling function which will be called when an error is raised
        during a responder's on_data() function. There is no default
        functionality and the subclasses must overload this.

        Parameters
        ----------
        error : Exception
            Exception thrown during code execution
        """
        # This error was HTTP-related
        if isinstance(error, HTTPError):
            err_code = error.code
            err_msg = error.msg
            err_info = ''
        else:
            err_code = 500
            err_msg = "Server Error"
            err_info = "%s" % error
            print("Unexpected Server Error", file=stderr)
            traceback.print_tb(error.__traceback__, file=stderr)

        # for error_handler in self.http_application.next_error_handler(req):
        err_str = (
            "<html>"
            "<head></head>"
            "<body><h1>HTTP Error : {code} {message}</h1><p>{info}</p></body>"
            "</html>"
        ).format(
            code=err_code,
            message=err_msg,
            info=err_info
        )

        header_info = {
            'code': err_code,
            'msg': err_msg,
            'date': HTTPResponse.get_current_time(),
            'length': len(err_str.encode()),
            'contents': err_str
        }

        response = '\r\n'.join((
            "HTTP/1.1 {code} {msg}",
            "Content-Type: text/html; charset=UTF-8",
            "Content-Length: {length}",
            "Date: {date}",
            "",
            "{contents}")).format(**header_info)

        self.transport.write(response.encode())
