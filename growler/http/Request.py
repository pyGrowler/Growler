
import asyncio

from urllib.parse import (quote, urlparse, parse_qs)

from . import HTTPParser
from termcolor import colored


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
    self.path = ''

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
      @asyncio.coroutine
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
    """Checks the values of the three elements of the HTTP header."""
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

