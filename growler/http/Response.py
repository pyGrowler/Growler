
import asyncio
import sys
import growler

import time
from datetime import (datetime, timezone, timedelta)

class HTTPResponse(object):
  """
  Response class which handles writing to the client.
  """
  SERVER_INFO = 'Python/{0[0]}.{0[1]} growler/{1}'.format(sys.version_info, growler.__version__)

  def __init__(self, ostream, app = None, EOL = "\r\n"):
    """
    Create the response
    @param ostream: asyncio.StreamWriter Output stream, expected
    @type growler.App: The growler app creating the response
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
    self.has_ended = False
    self._do_before_headers = []

  def _set_default_headers(self):
    """Create some default headers that should be sent along with every HTTP response"""
    time_string = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
    self.headers.setdefault('Date', time_string)
    self.headers.setdefault('Server', self.SERVER_INFO)
    self.headers.setdefault('Content-Length', len(self.message))
    if self.app.enabled('x-powered-by'):
      self.headers.setdefault('X-Powered-By', 'Growler')

  def send_headers(self):
    print ("*** Calling %d functions" % len(self._do_before_headers))

    for func in self._do_before_headers:
      func(res)

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
    self.has_ended = True

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
    """Alias for 'set()'"""
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
