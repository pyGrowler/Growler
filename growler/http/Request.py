
import asyncio

from urllib.parse import (quote, urlparse, parse_qs)

from . import HTTPParser
from termcolor import colored

import growler

class HTTPRequest(object):
  """
  Helper class which handles the parsing of an incoming http request.
  The usage should only be from an HTTPRequest object calling the parse()
  function.
  """
  def __init__(self, istream, app = None, delay_processing = False, parser_class = HTTPParser, protocol = "http"):
    """
      The HTTPRequest object is all the information you could want about the
      incoming http connection. It gets passed along with the HTTPResponse object
      to all the middleware of the app.
      @param istream: The StreamReader from which to build the request
      @type istream: asyncio.StreamReader

      @param app: The parent Growler App which created this request
      @type app: growler.App
    
      @param delay_processing: Does nothing
      @type delay_processing: boolean
    
      @param parser_class: The class type which is used to parse the incoming request
      @type parser_class: HTTPParser
    """

    # colors = ['grey', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white']
    colors = ['red', 'yellow', 'blue', 'magenta', 'cyan', 'white']
    from random import randint
    self.c = colors[randint(0, len(colors)-1)]
    print (colored("Req", self.c))
    print (colored(dir(istream._transport), self.c))
    
    self.ip = istream._transport.get_extra_info('socket').getpeername()[0]
    self._stream = istream
    self._parser = parser_class(self, self._stream)
    self.app = app
    self.headers = {}
    self.body = asyncio.Future()
    self.path = ''
    self.protocol = protocol

  @asyncio.coroutine
  def process(self):
    """
      Begins processing the incoming stream - first reading in headers. 
      If body data is expected, asynchronously read it in.
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
      # print ( colored("header: {}".format(nheader), self.c))
      nheader = yield from self._parser.read_next_header()

    # Process the headers - specific to the HTTP method (set in process_request_line)
    self._process_headers()

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

  def process_request_line(self, method, request_uri, version):
    """
      Checks the values of the three elements of the HTTP header.
    
      @param method: The HTTP method. GET, POST, etc...
      @type method: str

      @param request_uri: The uri requested, this gets parsed by 
        python's own urlparse method
      @type request_uri: str

      @param version: The HTTP version. Currently only supports the strings 
        'HTTP/1.1', 'HTTP/1.0' and does NOT distinguish between them - this
        should be fixed by someone who cares.
      @type version: str
    """
    if version not in ('HTTP/1.1', 'HTTP/1.0'):
      raise HTTPErrorVersionNotSupported()

    # save 'method' to self and get the correct function to finish processing
    self.method = method
    self._process_headers = {
      "GET" : self._process_get_headers
    }.get(method, None)

    # Method not found 
    if self._process_headers == None:
      print ("Unknown HTTP Method '{}'".format(method))
      raise HTTPErrorNotImplemented()

    self.original_url = request_uri
    self.parsed_url = urlparse(request_uri)
    self.path = self.parsed_url.path
    self.query = parse_qs(self.parsed_url.query)
    print ("URI",self.protocol)
    print ("parsed_url", self.parsed_url, "PATH", self.path, " QUERY", self.query)

  def param(self, name, default = None):
    """
      Return value of HTTP parameter 'name' if found, else return provided 
      'default'
    
      @param name: Key to search the query dict for
      @type name: str
    
      @param default: Returned if 'name' is not found in the query dict
    """
    return self.query[name] if name in self.query.keys() else default

  def _process_get_headers(self):
    """
      Called upon receiving a GET HTTP request to do specific 'GET' things to the
      list of headers.
    """
    pass
