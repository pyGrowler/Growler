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

from .status import Status


class HTTPResponse(object):
    """
    Response class which handles writing to the client.
    """
    SERVER_INFO = 'Python/{0[0]}.{0[1]} Growler/{1}'.format(sys.version_info,
                                                            growler.__version__
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
        """
        Create the http response.

        :param protocol: GrowlerHTTPProtocol object creating the response
        :param EOL str: The string with which to end lines
        """
        self.protocol = protocol
        self.EOL = EOL

        self.headers = dict()

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
        # time_string = time.strftime("%a, %d %b %Y %H:%M:%S GMT",
        #  time.gmtime())
        self.headers.setdefault('Date', time_string)
        self.headers.setdefault('Server', self.SERVER_INFO)
        self.headers.setdefault('Content-Length', len(self.message))
        if self.app.enabled('x-powered-by'):
            self.headers.setdefault('X-Powered-By', 'Growler')

    def send_headers(self):
        """Sends the headers to the client"""
        for func in self._events['before_headers']:
            func()

        self.headerstrings = [self.StatusLine()]

        self._set_default_headers()

        self.headerstrings += ["%s: %s" % (k, v)
                               for k, v in self.headers.items()]

        for func in self._events['headerstrings']:
            func()

        http_header = self.EOL.join(self.headerstrings + [self.EOL])
        self.protocol.transport.write(http_header.encode())

    def write(self, msg=None):
        msg = self.message if msg is None else msg
        msg = msg.encode() if isinstance(msg, str) else msg
        self.protocol.transport.write(msg)

    def write_eof(self):
        self.protocol.transport.write_eof()
        self.has_ended = True
        for f in self._events['after_send']:
            f()

    def StatusLine(self):
        self.phrase = self.phrase if self.phrase else Status.Phrase(
            self.status_code)
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
        self.headers = {'Location': url}
        self.message = ''
        self.end()

    def set(self, header, value=None):
        """Set header to the key"""
        if value is None:
            self.headers.update(header)
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
        self.headers['content-type'] = 'application/json'
        self.status_code = status
        self.send_text(json.dumps(obj))

    def send_html(self, html, status=200):
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

        :param txt str: The plaintext string to be sent back to the client
        :param status int: The HTTP status code, defaults to 200 (OK)
        """
        self.headers.setdefault('content-type', 'text/plain')
        self.message = str(txt)
        self.status_code = status
        self.end()

    def send_file(self, filename, status=200):
        """Reads in the file 'filename' and sends string."""
        # f = open(filename, 'r')
        # f = io.FileIO(filename)
        # print ("[send_file] sending file :", filename)
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
        return 'Python/{0[0]}.{0[1]} growler/{1}'

    @property
    def stream(self):
        return self.protocol.transport

    @property
    def app(self):
        return self.protocol.http_application

    @staticmethod
    def get_current_time():
        return format_RFC_1123(time.mktime(datetime.now().timetuple()))
