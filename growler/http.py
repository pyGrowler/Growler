#
# growler/http.py
#

import asyncio
import sys

from pprint import PrettyPrinter

MAX_REQUEST_LENGTH = 4096
# MAX_REQUEST_LENGTH = 96

class HTTPParser(object):

  def __init__(self):
    print("Constructing HTTPParser")

  # @asyncio.coroutine
  def parse(self, stream):
    """
      Read an HTTP request from stream object.
    """
    # request length
    request_length = 0

    # list of lines in the header
    header_lines = []

    # read in at most MAX_REQUEST_LENGTH bytes from the stream
    line0 = yield from stream.read(MAX_REQUEST_LENGTH)

    try:
      # request_line = line0.decode('iso_8859_1', 'strict')
      request_line = str(line0, 'latin_1', 'replace')
    except UnicodeDecodeError as e:
      print ('ERROR', e)
      return None

    try:
      hstr, bstr = request_line.split("\r\n\r\n", 1)
    except ValueError:
      print ("HTTP Error")
      raise Request_Too_Large

    print("hstr: '" + hstr + "'")
    print("")
    print("bstr: '" + bstr + "'")
    print("")
    r_lines = request_line.strip().split("\r\n")

    try:
      method, path, version = r_lines.pop(0).split()
    except ValueError as ve:
      print ("HTTP Error")
      return None
    except:
      e = sys.exc_info()[0]
      print ("HTTP Error")
      print ("yup fail")
      print (e)

    print ('method', method)
    print ('path', path)
    print ('version', version)

    if version not in ('HTTP/1.1', 'HTTP/1.0'):
      raise HTTPErrorVersionNotSupported()

    def get_f():
      print ("[get_f]")

    def post_f():
      print ("[post_f]")

    def delete_f():
      print ("[delete_f]")

    def unknown_f():
      print ("[unknown_f]")
      raise HTTPErrorNotImplemented()

    func = {
       "GET" : get_f,
      "POST" : post_f,
    "DELETE" : delete_f
    }.get(method, unknown_f)
    
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
        
    pp = PrettyPrinter()
    pp.pprint (headers)
      
    print(func)
    func()
    

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

class HTTPErrorNotFound(HTTPError):
  def __init__(self):
    HTTPError.__init__(self, "Not Found", 404)

class HTTPErrorRequestTooLarge(HTTPError):
  def __init__(self):    
    HTTPError.__init__(self, "Request-URI Too Large", 414)

class HTTPErrorInternalServerError(HTTPError):
  def __init__(self):
    HTTPError.__init__(self, "Internal Server Error", 500)

class HTTPErrorNotImplemented(HTTPError):
  def __init__(self):
    HTTPError.__init__(self, "Method Not Implemented", 501)

class HTTPErrorVersionNotSupported(HTTPError):
  def __init__(self):
    HTTPError.__init__(self, "Version not supported", 505)
