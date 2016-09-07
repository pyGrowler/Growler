#
# growler/http/response.py
#

import io
import sys
import json
import time
import growler

from pathlib import Path
from itertools import chain
from datetime import datetime
from collections import OrderedDict
from growler.utils.event_manager import Events
from wsgiref.handlers import format_date_time as format_RFC_1123

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

    def __init__(self, protocol, EOL="\r\n"):
        self.protocol = protocol
        self.EOL = EOL

        self.headers = Headers()
        self.events = Events()

    def _set_default_headers(self):
        """
        Create some default headers that should be sent along with every HTTP
        response
        """
        self.headers.setdefault('Date', self.get_current_time)
        self.headers.setdefault('Server', self.SERVER_INFO)
        self.headers.setdefault('Content-Length', "%d" % len(self.message))
        if self.app.enabled('x-powered-by'):
            self.headers.setdefault('X-Powered-By', 'Growler')

    def send_headers(self):
        """
        Sends the headers to the client
        """
        self.events.sync_emit('headers')
        self._set_default_headers()
        header_str = self.status_line + self.EOL + str(self.headers)
        self.protocol.transport.write(header_str.encode())
        self.events.sync_emit('after_headers')

    def write(self, msg=None):
        msg = self.message if msg is None else msg
        msg = msg.encode() if isinstance(msg, str) else msg
        self.protocol.transport.write(msg)

    def write_eof(self):
        self.stream.write_eof()
        self.has_ended = True
        self.events.sync_emit('after_send')

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

    def redirect(self, url, status=None):
        """
        Redirect to the specified url, optional status code defaults to 302.
        """
        self.status_code = 302 if status is None else status
        self.headers = Headers([('location', url)])
        self.message = ''
        self.end()

    def set(self, header, value=None):
        """Set header to the value"""
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

    # def cookie(self, name, value, options={}):
    #     """Set cookie name to value"""
    #     self.cookies[name] = value
    #
    # def clear_cookie(self, name, options={}):
    #     """Removes a cookie"""
    #     options.setdefault("path", "/")
    #     del self.cookies[name]

    def location(self, location):
        """Set the location header"""
        self.headers['location'] = location

    def links(self, links):
        """Sets the Link """
        s = ['<{}>; rel="{}"'.format(link, rel)
             for link, rel in links.items()]
        self.headers['Link'] = ','.join(s)

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
        self.headers['Content-Type'] = 'application/json'
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
        self.headers.setdefault('Content-Type', 'text/html')
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
        if not isinstance(txt, bytes):
            txt = str(txt).encode()
        self.message = txt
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
        if isinstance(filename, Path) and sys.version_info >= (3, 5):
            self.message = filename.read_bytes()
        else:
            with io.FileIO(str(filename)) as f:
                self.message = f.read()
        self.status_code = status
        self.send_headers()
        self.write()
        self.write_eof()

    def send(self, *args, **kwargs):
        raise NotImplementedError
        # return self.write(*args, **kwargs)

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


class Headers:
    """
    A class for maintaining HTTP headers, offering a dict-like interface. Keys
    must be strings, and are stored in a case-insensitive manner. Values are
    strings, , lists of strings or bytes, or a callable, which will be
    called upon stringification of the headers.

    The mechanism behind case insensitivity is python's str.casefold, so any
    peculiarities should be investigated starting there.

    Stringification of the headers will provide an HTTP compatible header
    string, terminated by two EOL chars.
    """

    EOL = '\r\n'

    def __init__(self, headers={}, **kw_headers):
        """
        Construct a headers object.

        The constructor provides the same interface as the standard
        dict constructor.

        The default value is an empty container, which will .

        """
        self._header_data = OrderedDict()
        headers = dict(headers)
        headers.update(kw_headers)
        for key, value in headers.items():
            self[key] = value

    def __getitem__(self, key):
        ci_key = self.escape(key).casefold()
        return self._header_data[ci_key][1]

    def __setitem__(self, key, value):
        key = self.escape(key)
        ci_key = key.casefold()
        self._header_data[ci_key] = (key, value)

    def __delitem__(self, key):
        key = self.escape(key)
        ci_key = key.casefold()
        del self._header_data[ci_key]

    def setdefault(self, key, default=None):
        key = self.escape(key)
        ci_key = key.casefold()

        try:
            v = self._header_data[ci_key]
            return v
        except KeyError:
            self._header_data[ci_key] = (key, default)
            return default

    def update(self, *args, **kwargs):
        """
        Equivalent to the python dict update method.

        Update the dictionary with the key/value pairs from other, overwriting
        existing keys.

        Args:
            other (dict): The source of key value pairs to add to headers
        Keyword Args:
            All keyword arguments are stored in header directly

        Returns:
            None
        """
        for next_dict in chain(args, (kwargs, )):
            for k, v in next_dict.items():
                self[k] = v

    def add_header(self, key, value, **params):
        """
        Add a header to the collection, including potential parameters.

        Args:
            key (str): The name of the header
            value (str): The value to store under that key
            params: Option parameters to be appended to the value,
                automatically formatting them in a standard way
        """

        key = self.escape(key)
        ci_key = key.casefold()

        def quoted_params(items):
            for p in items:
                param_name = self.escape(p[0])
                param_val = self.de_quote(self.escape(p[1]))
                yield param_name, param_val

        sorted_items = sorted(params.items())

        quoted_iter = ('%s="%s"' % p for p in quoted_params(sorted_items))
        param_str = ' '.join(quoted_iter)

        if param_str:
            value = "%s; %s" % (value, param_str)

        self._header_data[ci_key] = (key, value)

    def stringify(self, use_bytes=False):
        """
        Returns representation of headers as a valid HTTP header string. This
        is called by __str__.

        Args:
            use_bytes (bool): Returns a bytes object instead of a str.
        """
        def _str_value(value):
            if isinstance(value, (list, tuple)):
                value = (self.EOL + '\t').join(map(_str_value, value))
            elif callable(value):
                value = _str_value(value())
            return value

        s = self.EOL.join(("{key}: {value}".format(key=key,
                                                   value=_str_value(value))
                           for key, value in self._header_data.values()
                           if value is not None))
        return s + (self.EOL * 2)

    @staticmethod
    def escape(value):
        return value.replace("\n", r"\n")

    @staticmethod
    def de_quote(value):
        return value.replace('"', r'\"')

    def __str__(self):
        return self.stringify()
