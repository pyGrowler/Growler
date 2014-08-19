#
# growler/http.py
#

import asyncio
import sys
from urllib.parse import quote
from pprint import PrettyPrinter

from datetime import (datetime, timezone, timedelta)


MAX_REQUEST_LENGTH = 4096 # 4KB
MAX_POST_LENGTH = 2 * 1024**3 # 2MB

# MAX_REQUEST_LENGTH = 96

# End of line and end of header
# EOL = "\r\n"
EOL = "\n"
HEADER_DELIM = EOL * 2


class HTTPParser(object):

  def __init__(self, req, instream):
    self._stream = instream
    self._req = req
    self._buffer = ''

  def store_buffer(func):
    def _store(self, data):
      print('data', data)
      self._buffer += data.decode()
      func(self, data)
    return _store

  # @asyncio.coroutine
  @store_buffer
  def determine_line_ending(self, data):
    print('determine_line_ending {}'.format(data.decode()))
    # look for end of line
    ending_at = self._buffer.find("\n")

    # Not found
    if ending_at == -1:
      print ("Not found, buffer length", len(self._buffer) )
      # We must be still parsing the header - check for overflow
      if len(self._buffer) >= MAX_REQUEST_LENGTH:
        raise HTTPErrorRequestTooLarge()

      print ("no end line read -- waiting for more data")

    elif ending_at == 0:
      raise HTTPErrorBadRequest()

    else:
      self._line_ending = "\r\n" if self._buffer[ending_at-1] == '\r' else "\n"
      print('determined line ending {}'.format(len(self._line_ending)))
      self.cb = self.next_step 
    
  @asyncio.coroutine
  @store_buffer
  def next_step(self, data):
    pass
    
    
  @asyncio.coroutine
  def countdown(self, n):
    print ("Counting down from", n)
    while n > 0:
        yield n
        n -= 1
    print ("Done counting down")

  @asyncio.coroutine
  def parse(self):
    res = yield from self.parse_headers()
    done = yield from self.parse_body(res)

  @asyncio.coroutine
  def parse_headers(self):
    """
      Read an HTTP request from stream object.
    """
    # for function in [self.determine_line_ending(), self.next_step()]:
      # print(function)
    # set the callback read_data will have to use
    # self.cb = self.determine_line_ending
    # yield from self.read_data()
    # print ("xxxx")

    # number of bytes read in 'so far'
    bytes_read = 0

    # list of lines in the header
    header_lines = []

    # list of read in data
    chunks = []

    # position of the end of the header (-1 to begin)
    header_end = -1

    # token for end of line
    eol_token = None

    request_line = ''

    body = ''

    # loop while we have not yet loaded the header
    while header_end == -1:
      # If stream is dead - raise a 'bad request' error
      if self._stream.at_eof():
        print ("self._stream.at_eof()")
        raise HTTPErrorBadRequest()

      # read in the next block of data
      next_data = yield from self._stream.read(MAX_REQUEST_LENGTH - bytes_read)
      bytes_read += len(next_data)

      # transform bytes to string
      try:
        next_str = next_data.decode('latin_1','replace')
      except UnicodeDecodeError:
        raise HTTPErrorBadRequest()

      # look for end of line
      line_ends_at = next_str.find("\n")

      # no end of line in the current 
      if line_ends_at == -1:
        # We must be still parsing the header - check for overflow
        if bytes_read >= MAX_REQUEST_LENGTH:
          raise HTTPErrorRequestTooLarge()

        #print ("no end line read -- waiting for more data")

        # add string to the next_line
        chunks.append(next_str)

        # go back and wait for more data
        continue

      # the ending of the line has not been set - determine now (the first time encountered)
      elif eol_token == None:
        # special case where first character is newline
        if line_ends_at == 0:
          # ensure we have a non-empty string in the previous chunk of data
          if len(chunks) != 0 and len(chunks[-1]) != 0:
            eol_token = "\r\n" if chunks[-1][-1] == '\r' else "\n"
          else:
            raise HTTPErrorBadRequest()
        else:
          # set the end of line token to detected line
          eol_token = "\r\n" if next_str[line_ends_at-1] == '\r' else "\n"
        print ("Detected ending as {}".format("\\r\\n" if eol_token == "\r\n" else "\\n"))
        request_str = next_str[:line_ends_at + 1 - len(eol_token)]
        
        try:
          # method, request_uri, version
          req_lst = request_str.split()
          if len(req_lst) != 3: raise HTTPErrorBadRequest()
          header_processor = self._req.process_request_line(*req_lst)
        except ValueError as e:
          print ('error', e)
          raise HTTPErrorBadRequest(e)
        
        
        next_str = next_str[line_ends_at + 1:]
        print ("next_str '{}'".format(next_str))
      # we have an end of line in current string - join together everything and split it up
      current_string = ''.join(chunks + [next_str])

      # check for the end of header (double eol)
      header_ends_at = current_string.find(eol_token * 2)
      # print ("current_string:: '{}'".format(current_string))
      # print ("header_ends_at::", header_ends_at)

      # The header delimiter has been found
      if header_ends_at != -1:
        # split up "current string" into headers and body
        if header_ends_at != 0:
          # header_lines += current_string[:header_ends_at].split(eol_token)
          for hl in current_string[:header_ends_at].split(eol_token):
            header_lines.append(hl)
            # handle.send(hl)
        body = current_string[header_ends_at+(len(eol_token)*2):]
        chunks.clear()
        # break out of loop
        break

      # still in the header -
      #  split the current string into lines
      #  add those completed into header_lines
      #  put last one back into chunks
      new_headers = current_string.split(eol_token)
      # header_lines += new_headers[:-1]
      for hl in new_headers[:-1]:
        if hl != '':
          header_lines.append(hl)
        # handle.send(hl)

      chunks = [eol_token] if new_headers[-1] == '' else [new_headers[-1]]

    # At this point we have a list of headers in header_lines and maybe some data in body

    # print("header_lines", header_lines)
    # print("")
    # print("body: '" + body + "'")
    # print("")
    # 

    print("header_lines",header_lines)
    for line in header_lines:
      # split and strip the key and value
      try:
        k_v = map(str.strip, line.split(":", 1))
      except ValueError as e:
        raise HTTPErrorBadRequest(e)
      header_processor.send(k_v)

    # Inform _req we have finished sending the headers
    header_processor.send(None)
    header_processor.close()
    return body
  

  @asyncio.coroutine
  def parse_body(self, body_str):
    print('parsing body')
    bytes_read = len(body_str)
    while True:
      next_data = yield from self._stream.read(MAX_POST_LENGTH - bytes_read)
      if len(next_data) == 0: break
      bytes_read += len(next_data)
      body_str += next_data.decode()
    yield body_str

  @asyncio.coroutine
  def read_data(self, read_max):
    bytes_read = 0
    next_line = ''
    print("Setting up read_data")
    # run forever
    while True:
      next_data = yield from self._stream.read(MAX_REQUEST_LENGTH - bytes_read)
      print("[next_line]", next_data)
      bytes_read += len(next_data)
      if self.cb:
        self.cb(next_data)
        # yield self.cb.send(next_data)
      else:
        yield next_line


  @asyncio.coroutine
  def read_next_line(self, cb = None):
    bytes_read = 0
    next_line = ''
    print("Setting up read_next_line")
    # run forever
    while True:
      next_data = yield from self._stream.read(MAX_REQUEST_LENGTH - bytes_read)
      if cb:
        yield cb.send(next_line)
      else:
        yield next_line

class HTTPRequest(object):
  
  def __init__(self, istream, delay_processing = False, parser_class = HTTPParser, loop = None):
    self._stream = istream
    self._parser = parser_class(self, self._stream)
    self._loop = loop if loop != None else asyncio.get_event_loop()

  @asyncio.coroutine
  def process(self):
    # parsed_stream = self._loop.run_until_complete(self._parser.parse())
    parsing_stream = self._parser.parse()
    q = True
    while q != None:
      q = yield from parsing_stream
      print ('parsing_stream yielded:',q)
    return ("DONE")
    # print("[HTTPRequest::process]")
    # print(" [parsed_stream]", parsed_stream)
    # parsed_stream.send(None)
    # request_line = next(parsed_stream)
    # print(" request_line", request_line)
    
    # yield from self._parser
    # import 

  def process_request_line(self, method, request_uri, version):
    # method, request_uri, version = (yield)
    if version not in ('HTTP/1.1', 'HTTP/1.0'):
      raise HTTPErrorVersionNotSupported()

    self.method = method;
    self._process_headers = {
      "GET" : self._process_get_request
    }.get(method, None)
    
    if self._process_headers == None:
      print ("Unknown HTTP Method '{}'".format(method))
      raise HTTPErrorNotImplemented()
    

    # setup the header receiver
    self.process_headers = self._process_headers()
    self.process_headers.send(None)
    print ("[_process_request_line] :", self.process_headers)
    print ("[_process_request_line] method :", method)
    
    # This is required to return to the 'sending' function and not to
    # the 'yield from' function
    # return (yield self.process_headers)
    return self.process_headers

  def _process_get_request(self):
    headers = {}
    while True:
      header = (yield)
      if header == None: break
      key, value = header
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

class HTTPResonse(object):
    
  def __init__(self, ostream):
    self._stream = ostream
    self.send = self.write
    # Assume we are OK
    self.status_code = 200
    self.phrase = "OK"
    self.has_sent_headers = False
    self.message = ''
    self.headers = {}

  def send_headers(self):
    EOL = "\r\n"
    headerstrings = [self.StatusLine()]

    self.headers.setdefault('Date', datetime.now(timezone(timedelta())).strftime("%a, %d %b %Y %H:%M:%S %Z"))
    self.headers.setdefault('Content-Length', len(self.message))
    
    headerstrings += ["{}: {}".format(k, self.headers[k]) for k in self.headers]
    self._stream.write(EOL.join(headerstrings).encode())
    self._stream.write((EOL * 2).encode())

  def send_message(self):
    # self._stream.write(self.message.encode())
    self.write(self.message)

  def write(self, msg):
    self._stream.write(msg.encode())

  def write_eof(self):
    self._stream.write_eof()

  def StatusLine(self):
    return "{} {} {}".format("HTTP/1.1", self.status_code, self.phrase)


  def end(self):
    self.send_headers()
    self.send_message()
    self.write_eof()

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

class HTTPErrorBadRequest(HTTPError):
  def __init__(self, ex = None):
    HTTPError.__init__(self, "Bad Request", 400, ex)

class HTTPErrorUnauthorized(HTTPError):  
  def __init__(self):
    HTTPError.__init__(self, "Unauthorized", 401)

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
