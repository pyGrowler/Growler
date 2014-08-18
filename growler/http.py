#
# growler/http.py
#

import asyncio
import sys
from urllib.parse import quote
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
  def countdown(self, n):
    print ("Counting down from", n)
    while n > 0:
        yield n
        n -= 1
    print ("Done counting down")

  @asyncio.coroutine
  def parse(self, stream):
    """
      Read an HTTP request from stream object.
    """
    @asyncio.coroutine
    def process_request_line(aString):
      print('[process_request_line] ::', aString)

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
      if stream.at_eof():
        raise HTTPErrorBadRequest()

      # read in the next block of data
      next_data = yield from stream.read(MAX_REQUEST_LENGTH - bytes_read)
      bytes_read += len(next_data)

      # transform bytes to string
      try:
        next_str = next_data.decode('latin_1','replace')
      except UnicodeDecodeError:
        raise HTTPErrorBadRequest()

        print("current '{}'".format(quote(''.join(chunks + [next_str]))))

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
          header_lines += current_string[:header_ends_at].split(eol_token)
        body = current_string[header_ends_at+(len(eol_token)*2):]
        chunks.clear()
        # break out of loop
        break

      # still in the header -
      #  split the current string into lines
      #  add those completed into header_lines
      #  put last one back into chunks
      new_headers = current_string.split(eol_token)
      header_lines += new_headers[:-1]
      chunks = [eol_token] if new_headers[-1] == '' else [new_headers[-1]]

    # At this point we have a list of headers in header_lines and maybe some data in body

    # print("header_lines", header_lines)
    # print("")
    # print("body: '" + body + "'")
    # print("")
    # 
    try:
      method, request_uri, version = header_lines.pop(0).split()
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
    for line in header_lines:
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
    return headers, body

    # finish reading the stream, passing the stream and the body string
    # return finish(stream, bstr)
    
  @asyncio.coroutine
  def next_header(self, reader):
    bytes_read = 0
    line_end = 0
    string_read = ''

    # loop until break
    # while True:
      # print ("Awaiting next line")
    for next_line in reader.read(MAX_REQUEST_LENGTH - bytes_read):
      # read in some data
      # next_line = yield from reader.read(MAX_REQUEST_LENGTH - bytes_read)
      print("NEXT LINE:",next_line)
      bytes_read += len(next_line)

      # convert into string
      try:
        next_str = str(next_line, 'latin_1', 'replace')
      except UnicodeDecodeError:
        raise HTTPErrorBadRequest()
      
      print( "Read in '{}' ({})\n".format(next_str, bytes_read))
      string_read += next_str

      # look for end of line
      line_ends_at = string_read.find("\n")

      # Not found
      if line_ends_at == -1:

        # We must be still parsing the header - check for overflow
        if bytes_read >= MAX_REQUEST_LENGTH:
          raise HTTPErrorRequestTooLarge()

        print ("no end line read -- waiting for more data")
        # go back and wait for more data
        continue

      # the ending of the line has not be determined - figure out now (the first time)
      elif line_end == 0:
        # set the line ending based on the end of the line
        line_end = "\r\n" if string_read[line_ends_at-1] == '\r' else "\n"
        print ("Detected ending as {}".format("\\r\\n"if line_end == "\r\n" else "\\n"))

      # check for the end of header (double the detected line end)
      header_ends_at = string_read.find(line_end * 2)
      
      if header_ends_at != -1:
        print ("Found that the header ends at", header_ends_at)
        # yield string_read.split(line_end)
        for line in string_read.split(line_end):
          print ("split", line)
          yield line
        break
      else:
        for line in string_read.split(line_end):
          yield line

      print ("next line???")
    # while line_ends_at == -1:
    #   next_line += yield from reader.read(MAX_REQUEST_LENGTH - bytes_read)
    #   print( "read in {}".format(next_line))
    #   line_ends_at = next_line.find("\n")
    # while 
    # read = reader.read
    print ("DONE")
    # return None

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
