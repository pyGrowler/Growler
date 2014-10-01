#
# growler/http.py
#

__all__ = ['HTTPRequest', 'HTTPResponse', 'HTTPParser', 'HTTPError']

import asyncio
import sys
import time
import json
from urllib.parse import (quote, urlparse, parse_qs)
from pprint import PrettyPrinter

from datetime import (datetime, timezone, timedelta)

import mimetypes
from termcolor import colored

mimetypes.init()

import growler

KB = 1024
MB = KB ** 2

MAX_REQUEST_LENGTH = 4096 # 4KB
MAX_POST_LENGTH = 2 * 1024**3 # 2MB

# MAX_REQUEST_LENGTH = 96

# End of line and end of header
# EOL = "\r\n"
EOL = "\n"
HEADER_DELIM = EOL * 2

HTTPCodes = {
  200 : "OK",
  301 : "Moved Permanently",
  302 : "Found"
}

class HTTPParser(object):

  def __init__(self, req, instream = None, color = 'white'):
    """
    Create a Growler HTTP Parser.

    req: a Growler HTTPRequest object
    instream: the asyncio.streams.StreamReader (defaults to req._stream)"
    """
    self._stream = req._stream if not instream else instream
    self._req = req
    self._buffer = ''
    self.EOL_TOKEN = None
    self.read_buffer = ''
    self.bytes_read = 0
    self.max_read_size = MAX_REQUEST_LENGTH
    self.max_bytes_read = MAX_REQUEST_LENGTH
    self.data_future = asyncio.Future()
    self.c = color
    self._header_buffer = None

  @asyncio.coroutine
  def _read_data(self):
    """Reads in a block of data (at most self.max_read_size bytes) and returns the decoded string"""
    data = yield from self._stream.read(self.max_read_size)
    self.bytes_read += len(data)
    return data.decode()

  @asyncio.coroutine
  def read_next_line(self, line_future = None):
    """
    Returns a single line read from the stream. If the EOL char has not been
    determined, it will wait for '\n' and set EOL to either LF or CRLF. This
    returns a single line, and stores the rest of the read in data in self._buffer
    """
    ## Keep reading data until newline is found
    while self.EOL_TOKEN == None:
      next_str = yield from self._read_data()
      line_end_pos = next_str.find("\n")
      self._buffer += next_str
      if line_end_pos != -1:
        self.EOL_TOKEN = "\r\n" if next_str[line_end_pos-1] == '\r' else "\n"

    line_ends_at = self._buffer.find(self.EOL_TOKEN)

    while line_ends_at == -1:
      self._buffer += yield from self._read_data()
      line_ends_at = self._buffer.find(self.EOL_TOKEN)

    ## split!
    line, self._buffer = self._buffer.split(self.EOL_TOKEN, 1)

    # yield from asyncio.sleep(0.75) # artificial delay
    return line

  @asyncio.coroutine
  def read_next_header(self, header = None):
    """
    A coroutine to generate headers. It uses read_next_line to get headers
    line by line - allowing quick response to invalid requests.
    """
    # No buffer has been saved - get the next line
    if self._header_buffer == None:
      line = yield from self.read_next_line()
    # if there was a header saved, use that (and clear the buffer)
    else:
      line, self._header_buffer = self._header_buffer, None

    if line == '':
      return None

    if line[0] == ' ':
      print ("WARNING: Header leads with whitespace")

    next_line = yield from self.read_next_line()
    
    # Loop through 
    while next_line != '' and next_line[0] == ' ':
      line += next_line
      next_line = yield from self.read_next_line()

    self._header_buffer = next_line

    try:
      key, value = map(str.strip, line.split(":", 1))
    except ValueError as e:
      print (colored("ERROR parsing headers. Input '{}'".format(line), 'red'))
      raise HTTPBadRequest(e)

    return {'key':key, 'value':value}

  @asyncio.coroutine
  def read_body(self):
    """
    Finishes reading the request. This method expects content-length to be defined in self.headers, and will
    read that many bytes from the stream
    """
    # There is no body - return None
    if self.headers['content-length'] == 0:
      return None

    # Get length of whatever is already read into the buffer
    bytes_read = len(self._buffer)
    if self.headers['content-length'] < bytes_read:
      raise "Body too large!"

    self.max_read_size = self.headers['content-length'] - bytes_read

    while self.max_read_size != 0:
      next_str = yield from self._read_data()
      bytes_read += len(next_str)
      self.max_read_size = self.headers['content-length'] - bytes_read
      self._buffer += next_str

    res, self._buffer = self._buffer, ''
    return res

  def parse_request_line(self, req_line):
    """
    Simply splits the request line into three components.
    TODO: Check that there are 3 and validate the method/path/version
    """
    req_lst = req_line.split()
    return req_lst

class HTTPRequest(object):
  """
  Helper class which handles the parsing of an incoming http request.
  The usage should only be from an HTTPRequest object calling the parse()
  function.
  """
  def __init__(self, istream, app = None, delay_processing = False, parser_class = HTTPParser):
    """
    The HTTPRequest object is all the information you could want about the
    incoming http connection. It gets passed along with the HTTPResponse object
    to all the middleware of the app.
    :istream: an asyncio.StreamReader
    :app: the Growler app which created this reqest
    :delay_processing: debug stuff
    :parser_class: A class which behaves as HTTPParser
    """

    # colors = ['grey', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white']
    colors = ['red', 'yellow', 'blue', 'magenta', 'cyan', 'white']
    from random import randint
    self.c = colors[randint(0, len(colors)-1)]
    print (colored("Req", self.c))

    self.ip = istream._transport.get_extra_info('socket').getpeername()[0]
    self._stream = istream
    self._parser = parser_class(self, self._stream, color = self.c)
    self.app = app
    self.headers = {}
    self.body = asyncio.Future()

  @asyncio.coroutine
  def process(self):
    """
    Begins processing the incoming stream - first reading in headers. Then if body
    data is expected, asynchronously read it in.
    """
    # Request Line
    first_line = yield from self._parser.read_next_line()
    req = self._parser.parse_request_line(first_line)
    self.process_request_line(*req)

    # Headers
    header_list = []
    nheader = yield from self._parser.read_next_header()
    while nheader != None:
      header_list.append(nheader)
      self.headers[nheader['key'].lower()] = nheader['value']
      print ( colored("header: {}".format(nheader), self.c))
      nheader = yield from self._parser.read_next_header()

    if not 'content-length' in self.headers:
      self.headers['content-length'] = 0
      self.body.set_result('')
    else:
      print("Body Length:", self.headers['content-length'])
      def async_read_body(body_reader_func):
        body_text = yield from body_reader_func()
        self.body.set_result(body_text)
      # Asynchronously call the parsers' read_body
      asyncio.async(async_read_body(self._parser.read_body))

  @asyncio.coroutine
  def bodytext(self):
    """
    Returns the result from the body. This is an alternate to 'yield from req.body'
    """
    body_txt = yield from self.body
    return body_txt


  def process_request_line(self, method, request_uri, version):
    # method, request_uri, version = (yield)
    if version not in ('HTTP/1.1', 'HTTP/1.0'):
      raise HTTPErrorVersionNotSupported()

    self.method = method
    self._process_headers = {
      "GET" : self._process_get_request
    }.get(method, None)

    if self._process_headers == None:
      print ("Unknown HTTP Method '{}'".format(method))
      raise HTTPErrorNotImplemented()

    self.original_url = request_uri
    self.parsed_url = urlparse(request_uri)
    self.path = self.parsed_url.path
    self.query = parse_qs(self.parsed_url.query)

  def param(self, name, default = None):
    """Return value of 'name' if found, else return provided 'default'"""
    return self.query[name] if name in self.query.keys() else default

  def _process_get_request(self):
    headers = {}
    while True:
      header = (yield)
      if header == None: break
      key, value = header
      key = key.lower()
      # if key is present
      if key in headers.keys():
       if isinstance(list, headers[key]):
         leaders[key].append(value)
       else:
         leaders[key] = [leaders[key]]
      else:
        headers[key] = value
    self.headers = headers

    print('[self.headers]', self.headers)
    yield

class HTTPResponse(object):
  """
  Response class which handles writing to the client.
  """
  SERVER_INFO = 'Python/{0[0]}.{0[1]} growler/{1}'.format(sys.version_info, growler.__version__)

  def __init__(self, ostream, app = None, EOL = "\r\n"):
    """
    Create the response
    :ostream: Output stream, expected asyncio.StreamWriter
    :app: The growler app creating the response
    """
    self._stream = ostream
    self.send = self.write
    # Assume we are OK
    self.status_code = 200
    self.phrase = "OK"
    self.has_sent_headers = False
    self.message = ''
    self.headers = {}
    self.app = app
    self.EOL = EOL
    self.finished = False
    self._do_before_headers = []

  def _set_default_headers(self):
    """Create some default headers that should be sent along with every HTTP response"""
    self.headers.setdefault('Date', datetime.now(timezone(timedelta())).strftime("%a, %d %b %Y %H:%M:%S %Z"))
    self.headers.setdefault('Server', self.SERVER_INFO)
    self.headers.setdefault('Content-Length', len(self.message))

  def send_headers(self):
    print ("*** Calling %d functions" % len(self._do_before_headers))
    for func in self._do_before_headers:
      func()

    headerstrings = [self.StatusLine()]

    self._set_default_headers()

    headerstrings += ["{}: {}".format(k, self.headers[k]) for k in self.headers]
    print ("Sending headerstrings '{}'".format(headerstrings))
    self._stream.write(self.EOL.join(headerstrings).encode())
    self._stream.write((self.EOL * 2).encode())

  def send_message(self):
    # self._stream.write(self.message.encode())
    self.write(self.message)

  def write(self, msg):
    self._stream.write(msg.encode())

  def write_eof(self):
    self._stream.write_eof()
    self.finished = True

  def StatusLine(self):
    return "{} {} {}".format("HTTP/1.1", self.status_code, self.phrase)

  def end(self):
    """Ends the response.  Useful for quickly ending connection with no data sent"""
    self.send_headers()
    self.send_message()
    self.write_eof()

  def redirect(self, url, status = 302):
    """Redirect to the specified url, optional status code defaults to 302"""
    self.status_code = status
    self.phrase = HTTPCodes[status]
    self.headers = {'Location': url}
    self.message = ''
    self.end()

  def set(self, header, value = None):
    """Set header to the key"""
    if value == None:
      self.headers.update(header)
    else:
      self.headers[header] = value

  def header(self, header, value = None):
    self.set(header, value)

  def get(self, field):
    """Get a header"""
    return self.headers[field]

  def cookie(self, name, value, options = {}):
    """Set cookie name to value"""
    self.cookies[name] = value

  def clear_cookie(self, name, options = {}):
    """Removes a cookie"""
    options.setdefault("path", "/")
    del self.cookies[name]

  def redirect(self, url, status = 302):
    """Redirects request to a different url"""
    self.status = status
    self.phrase = "Redirect"

  def location(self, location):
    """Set the location header"""
    self.headers['location'] = location

  def links(self, links):
    """Sets the Link """
    s = []
    for rel in links:
      s.push("<{}>; rel=\"{}\"".format(links[rel], rel))
    self.headers['Link'] = ','.join(s)

  def json(self, body, status = 200):
    self.headers['content-type'] = 'application/json'
    self.write()

  def send_json(self, obj):
    self.headers['content-type'] = 'application/json'
    self.send_text(json.dumps(obj))

  def send_html(self, html):
    self.headers.setdefault('content-type', 'text/html')
    self.message = html
    self.send_headers()
    self.send_message()
    self.write_eof()

  def send_text(self, obj):
    if isinstance(obj, str):
      self.headers.setdefault('content-type', 'text/plain')
      self.message = obj
    else:
      self.message = "{}".format(obj)
    self.end()

  def send_file(self, filename):
    """Reads in the file 'filename' and sends string."""
    f = open(filename, 'r')
    print ("sending file :", filename)
    self.headers.setdefault('content-type', 'text/html')
    self.message = f.read()
    print ('string :', self.message)
    self.send_headers()
    self.send_message()
    self.write_eof()
    print ("state:", self.finished)
    
  def on_headers(self, cb):
    self._do_before_headers.append(cb)

class HTTPError(Exception):

  def __init__(self, phrase, code, ex = None):
    print ("[HTTPError]")
    Exception.__init__(self, phrase)
    self.code = code
    self.phrase = phrase
    self.sys_exception = ex
    self.traceback = sys.exc_info()[2]

  def PrintSysMessage(self, printraceback = True):
    if self.sys_exception:
      print(self.sys_exception)
    if printraceback and self.traceback:
      print (self.traceback)
      # for line in self.traceback:
        # print (line)

  def GetFromCode(self, code):
    return {400: HTTPErrorBadRequest,
            401: HTTPErrorUnauthorized,
            402: HTTPErrorPaymentRequired,
            403: HTTPErrorForbidden,
            404: HTTPErrorNotFound,
            410: HTTPErrorGone}(code, None)

class HTTPErrorBadRequest(HTTPError):
  def __init__(self, ex = None):
    HTTPError.__init__(self, "Bad Request", 400, ex)

class HTTPErrorUnauthorized(HTTPError):
  def __init__(self):
    HTTPError.__init__(self, "Unauthorized", 401)

class HTTPErrorPaymentRequired(HTTPError):
  def __init__(self):
    HTTPError.__init__(self, "Payment Required", 402)

class HTTPErrorForbidden(HTTPError):
  def __init__(self):
    HTTPError.__init__(self, "Forbidden", 403)

class HTTPErrorNotFound(HTTPError):
  def __init__(self):
    HTTPError.__init__(self, "Not Found", 404)

class HTTPErrorGone(HTTPError):
  def __init__(self):
    HTTPError.__init__(self, "Gone", 410)

class HTTPErrorRequestTooLarge(HTTPError):
  def __init__(self):
    HTTPError.__init__(self, "Request-URI Too Large", 414)

class HTTPErrorUnsupportedMediaType(HTTPError):
  def __init__(self):
    HTTPError.__init__(self, "Unsupported Media Type", 415)

class HTTPErrorInternalServerError(HTTPError):
  def __init__(self):
    HTTPError.__init__(self, "Internal Server Error", 500)

class HTTPErrorNotImplemented(HTTPError):
  def __init__(self):
    HTTPError.__init__(self, "Method Not Implemented", 501)

class HTTPErrorVersionNotSupported(HTTPError):
  def __init__(self):
    HTTPError.__init__(self, "Version not supported", 505)
