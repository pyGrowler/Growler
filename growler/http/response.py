#
# growler/http/response.py
#

import sys
import growler
import json
import time
from datetime import datetime
import io
from wsgiref.handlers import format_date_time as format_RFC_1123
from wsgiref.headers import Headers

from .status import Status


class HTTPResponse:
    """

    Response class which handles HTTP formatting and sending a response to the
    client. If the response has sent a message (the `has_ended` property
    evaluates to True) the middleware chain will stop.

    There are many convenience functions such as `send_json` and `send_html`
    which will handle formatting data, setting headers and sending objects and
    strings for you.

    A typical use is the modification of the response object by the standard
    Renderer middleware, which adds a `render` method to the response object.
    Any middleware after this one (i.e. your routes) can then call
    res.render("template_name", data) to automatically render a web view and
    send it to.

    Parameters
    ----------
    protocol : GrowlerHTTPProtocol
        Protocol object creating the response
    EOL : str
        The string with which to end lines
    """
    SERVER_INFO = 'Growler/{growler_version} Python/{py_version}'.format(
        py_version=".".join(map(str, sys.version_info[:2])),
        growler_version=growler.__version__,
    )

    protocol = None
    has_sent_headers = False
    has_ended = False
    status_code = 200
    headers = None
    message = ''
    EOL = ''
    phrase = None

    _events = None

    def __init__(self, protocol, EOL="\r\n"):
        self.protocol = protocol
        self.EOL = EOL

        self.headers = Headers()

        self._events = {
            'before_headers': [],
            'after_send': [],
            'headerstrings': []
        }

    def _set_default_headers(self):
        """
        Create some default headers that should be sent along with every HTTP
        response
        """
        time_string = self.get_current_time()
        self.headers.setdefault('Date', time_string)
        self.headers.setdefault('Server', self.SERVER_INFO)
        self.headers.setdefault('Content-Length', "%d" % len(self.message))
        if self.app.enabled('x-powered-by'):
            self.headers.setdefault('X-Powered-By', 'Growler')

    def send_headers(self):
        """
        Sends the headers to the client
        """
        for func in self._events['before_headers']:
            func()

        self.headerstrings = [self.status_line]

        self._set_default_headers()
        self.protocol.transport.write(bytes(self.headers))

    def write(self, msg=None):
        msg = self.message if msg is None else msg
        msg = msg.encode() if isinstance(msg, str) else msg
        self.protocol.transport.write(msg)

    def write_eof(self):
        self.protocol.transport.write_eof()
        self.has_ended = True
        for f in self._events['after_send']:
            f()

    @property
    def status_line(self):
        """
        Returns the first line of response, including http version, status
        and a phrase (OK).
        """
        if not self.phrase:
            self.phrase = Status.Phrase(self.status_code)
        return "{} {} {}".format("HTTP/1.1", self.status_code, self.phrase)

    def end(self):
        """
        Ends the response. Useful for quickly ending connection with no data
        sent
        """
        self.send_headers()
        self.write()
        self.write_eof()
        self.has_ended = True

    def redirect(self, url, status=302):
        """
        Redirect to the specified url, optional status code defaults to 302.
        """
        self.status_code = status
        self.headers = Headers([('location', url)])
        self.message = ''
        self.end()

    def set(self, header, value=None):
        """Set header to the key"""
        if value is None:
            for k, v in header.items():
                self.headers[k] = v
        else:
            self.headers[header] = value

    def header(self, header, value=None):
        """Alias for 'set()'"""
        self.set(header, value)

    def set_type(self, res_type):
        self.set('Content-Type', res_type)

    def get(self, field):
        """Get a header"""
        return self.headers[field]

    def cookie(self, name, value, options={}):
        """Set cookie name to value"""
        self.cookies[name] = value

    def clear_cookie(self, name, options={}):
        """Removes a cookie"""
        options.setdefault("path", "/")
        del self.cookies[name]

    def location(self, location):
        """Set the location header"""
        self.headers['location'] = location

    def links(self, links):
        """Sets the Link """
        s = []
        for rel in links:
            s.append("<{}>; rel=\"{}\"".format(links[rel], rel))
        self.headers['Link'] = ','.join(s)

    # def send(self, obj, status = 200):
    #  """
    #    Responds to request with obj; action is dependent on type of obj.
    #    If obj is a string, it sends text,
    #
    #  """
    #  func = {
    #    str: self.send_text
    #  }.get(type(obj), self.send_json)
    #  func(obj, status)

    def json(self, body, status=200):
        """Alias of send_json"""
        return self.send_json(body, status)

    def send_json(self, obj, status=200):
        """
        Sends a stringified JSON response to client. Automatically sets the
        content-type header to application/json.

        Parameters
        ----------
        obj : mixed
            Any object which will be serialized by the json.dumps module
            function
        status : int, optional
            The HTTP status code, defaults to 200 (OK)
        """
        self.headers['content-type'] = 'application/json'
        self.status_code = status
        message = json.dumps(obj)
        self.send_text(message)

    def send_html(self, html, status=200):
        """
        Sends html response to client. Automatically sets the content-type
        header to text/html.

        Parameters
        ----------
        html : str
            The raw html string to be sent back to the client
        status : int, optional
            The HTTP status code, defaults to 200 (OK)
        """
        self.headers.setdefault('content-type', 'text/html')
        self.message = html
        self.status_code = status
        self.send_headers()
        self.write()
        self.write_eof()

    def send_text(self, txt, status=200):
        """
        Sends plaintext response to client. Automatically sets the content-type
        header to text/plain. If txt is not a string, it will be formatted as
        one.

        Parameters
        ----------
        txt : str
            The plaintext string to be sent back to the client
        status : int, optional
            The HTTP status code, defaults to 200 (OK)
        """
        self.headers.setdefault('content-type', 'text/plain')
        if isinstance(txt, bytes):
            self.message = txt
        else:
            self.message = str(txt)
        self.status_code = status
        self.end()

    def send_file(self, filename, status=200):
        """
        Reads in the file 'filename' and sends bytes to client

        Parameters
        ----------
        filename : str
            Filename of the file to read
        status : int, optional
            The HTTP status code, defaults to 200 (OK)
        """
        with io.FileIO(filename) as f:
            self.message = f.read()
        self.status_code = status
        self.send_headers()
        self.write()
        self.write_eof()

    def on_headers(self, cb):
        self._events['before_headers'].append(cb)

    def on_send_end(self, cb):
        self._events['after_send'].append(cb)

    def on_headerstrings(self, cb):
        self._events['headerstrings'].append(cb)

    def send(self, *args, **kwargs):
        return self.write(*args, **kwargs)

    @property
    def info(self):
        return self.SERVER_INFO

    @property
    def stream(self):
        return self.protocol.transport

    @property
    def app(self):
        return self.protocol.http_application

    @staticmethod
    def get_current_time():
        # return time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
        return format_RFC_1123(time.mktime(datetime.now().timetuple()))
