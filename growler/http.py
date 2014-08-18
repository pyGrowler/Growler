#
# growler/http.py
#

import asyncio
import sys

from pprint import PrettyPrinter

MAX_REQUEST_LENGTH = 4096
# MAX_REQUEST_LENGTH = 96

# End of line and end of header
# EOL = "\r\n"
EOL = "\n"
HEADER_DELIM = EOL * 2


class HTTPParser(object):

  def __init__(self):
    print("Constructing HTTPParser")

  @asyncio.coroutine
  def parse(self, stream):
    """
      Read an HTTP request from stream object.
    """
    # number of bytes read in 'so far'
    header_length = 0
  
    # list of lines in the header
    header_lines = []
    
    # position of the end of the header (-1 to begin)
    header_end = -1

    request_line = ''

    # loop while we have not yet loaded the header
    while header_end == -1:
      # If stream is dead - raise a 'bad request' error
      if stream.at_eof():
        raise HTTPErrorBadRequest()
      # read in the next block of data
      next_line = yield from stream.read(MAX_REQUEST_LENGTH - header_length)
      print ("the next line is", next_line)

      try:
        next_line = str(next_line, 'latin_1', 'replace')
      except UnicodeDecodeError:
        raise HTTPErrorBadRequest()

      request_line += next_line.replace("\r\n", "\n")

      # find (via reverse find) the end of the header
      header_end = request_line.rfind(HEADER_DELIM)
      header_length += len(next_line)
      print ("no header delim found, reading again..." if header_end == -1 else "FOUND delim {}".format(header_end))
      # request_line.find(HEADER_DELIM)
      # print (header_length)

    try:
      hstr, bstr = request_line.split(HEADER_DELIM, 1)
    except ValueError as err:
      print ("HTTP Error")
      print (err)
      if len(line0) >= MAX_REQUEST_LENGTH:
        raise HTTPErrorRequestTooLarge()

    peer = stream._transport.get_extra_info('peername')
    print ("PEER", peer)

    print("hstr: '" + hstr + "'")
    print("")
    print("bstr: '" + bstr + "'")
    print("")
    r_lines = request_line.strip().split("\r\n")

    try:
      method, request_uri, version = r_lines.pop(0).split()
    except ValueError as ve:
      raise HTTPErrorBadRequest()
    except:
      e = sys.exc_info()[0]
      print ("HTTP Error")
      print ("yup fail")
      print (e)

    print ('method', method)
    print ('path', request_uri)
    print ('version', version)

    if version not in ('HTTP/1.1', 'HTTP/1.0'):
      raise HTTPErrorVersionNotSupported()

    @asyncio.coroutine
    def get_f(ins, body):
      print ("[get_f]")
      print ("  ", body)
      nextline = yield from stream.readline()
      print ("  ", nextline)
      return None

    def post_f(ins, body):
      print ("[post_f]")

    def delete_f(ins, body):
      print ("[delete_f]")
      return None

    finish = {
       "GET" : get_f,
      "POST" : post_f,
    "DELETE" : delete_f
    }.get(method, None)

    if finish == None:
      print ("Unknown HTTP Method '{}'".format(method))
      raise HTTPErrorNotImplemented()
    
    headers = {}
    for line in r_lines:
      # split and strip the key and value 
      key, value = map(str.strip, line.split(":", 1))
      # if key is present
      if key in headers.keys():
        if isinstance(list, headers[key]):
          leaders[key].append(value)
        else:
          leaders[key] = [leaders[key]]
      else:
        headers[key] = value
        
    # print the headers
    pp = PrettyPrinter()
    pp.pprint (headers)

    # return the headers
    yield headers

    # finish reading the stream, passing the stream and the body string
    return finish(stream, bstr)

  @asyncio.coroutine
  def next_header(self, reader):
    pass

class HTTPRequest(object):
  
  def __init__(self):
    pass
    # import 
    
    
class HTTPResonse(object):
    
  def __init__(self):
    Phrase
    
  def StatusLine(self):
    line = "{} {} {}".format("HTTP/1.1", self.status_code, self.phrase)
    return line

class HTTPError(Exception):
  
  def __init__(self, phrase, code):
    Exception.__init__(self, phrase)
    self.code = code
    self.phrase = phrase
    print ("HTTP Error")
    

class HTTPErrorBadRequest(HTTPError):
  def __init__(self):
    HTTPError.__init__(self, "Bad Request", 400)

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
