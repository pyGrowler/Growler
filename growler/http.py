#
# growler/http.py
#

import asyncio
import sys

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

    def get_f():
      print ("[get_f]")

    def post_f():
      print ("[post_f]")

    def unknown_f():
      print ("[unknown_f]")
      raise NotImplemented()

    func = {
       "GET" : get_f,
      "POST" : post_f
    }.get(method, unknown_f)
    
    headers = {}
    for line in r_lines:
      key,value = line.split(":", 1)
      headers[key] = value
    print (headers)
      
    print(func)
    func()
    

class HTTPRequest(object):
  
  def __init__(self):
    pass
    # import 
    
class HTTPError(Exception):
  
  def __init__(self, message, code):
    Exception.__init__(self, message)
    self.code = code
    self.message = message
    print ("HTTP Error")
    
    
class Request_Too_Large(HTTPError):
  
  def __init__(self):    
    HTTPError.__init__(self, "Request-URI Too Large", 414)

class NotImplemented(HTTPError):
  
  def __init__(self):
    HTTPError.__init__(self, "Method Not Implemented", 501)

