#
# growler/app.py
#

import asyncio
import re

from time import (time, sleep)
from datetime import (datetime, timezone, timedelta)

# from .http import (HTTPParser, HTTPError, HTTPRequest, HTTPResponse, Errors)
from .http import *

class App(object):
  
  def __init__(self, name, settings = {}, loop = None):
    self.cache = {};

    self._config = {'host':'127.0.0.1'}
    self._config.update(settings)

    self.engines = {}
    self.patterns = []
    self.loop = loop if loop != None else asyncio.get_event_loop()
    self.loop.set_debug(True)

    # Unknown at start 
    self.route_to_use = asyncio.Future()
    
    print(__name__, name)

  @asyncio.coroutine
  def GenerateServerListner(self):
    print('[GenerateServerListner]')
    yield from asyncio.start_server(self.handle_connection, 'localhost', 8000)

  @asyncio.coroutine
  def handle_connection(self, reader, writer, req_class = HTTPRequest, res_class = HTTPResponse):
    print('[handle_connection]', reader, writer, "\n")

    # create the request object
    self.req = req = req_class(reader, self)

    # create the response object
    self.res = res = res_class(writer, self)

    try:
      # process the request
      yield from req.process()
    except HTTPError as err:
      err.PrintSysMessage()
      print (err)

      body_content = "<h1>{}</h1>".format(err.phrase)
      b = "<!DOCTYPE html>\n<html><head><title>{}</title></head><body>{}</body></html>\n".format(err.phrase, body_content)

      res.headers['Content-Type'] = 'text/html'
      res.headers['Connection'] = 'close'
      
      res.status_code = err.code
      res.phrase = err.phrase
      res.message = b
      res.end()

    if self.route_to_use.done():
      print("We know which route to use!!!")
      self.after_route()
    else:
      print ("We still do NOT know which route to use")
      self.route_to_use.add_done_callback(self.after_route)

    return None
    # except Exception as e:
      # print ("ERROR")
      # print (e)
      # res.send('There was an error!')
      # return None
    # return None
    parser = HTTPParser(reader)
    parsed_stream = parser.parse()
    try:
      request_line = next(parsed_stream)
      print("[handle_connection] request_line", request_line)
      headers = yield from parser.parse()
      body = yield from parser.parse()
    except HTTPError as err:
      print ("Error in handle_connection")
      print(err)
      
      h = "HTTP/1.1 {} {}\n".format(err.code, err.phrase)
      h += "Date: {}\n".format(datetime.now(timezone(timedelta())).strftime("%a, %d %b %Y %H:%M:%S %Z"))

      body_content = "<h1>{}</h1>".format(err.phrase)
      b = "<!DOCTYPE html>\n<html><head><title>{}</title></head><body>{}</body></html>\n".format(err.phrase, body_content)
      self.send_message(writer, h, b)
      return None

    self.send_message(writer, "", "")
    return None
      
  def run(self):
    self.loop.run_until_complete(self.GenerateServerListner())
    try:
      self.loop.run_forever()
    finally:
      print("Run Forever Ended!")
      self.loop.close()
      
  def after_route(self, f = None):
    self.route_to_use.result()(self.req, self.res)


  # WARNING : This is hiding io, something we want to AVOID!
  def send_message(self, output, header, body):
    msg = "{}\r\n\r\n{}".format(header, body)
    # print("Sending:", msg)
    output.write(msg)
    output.write_eof()

  def get(self, patt):
    # regex = re.compile(patt)
    print("GET:", self, patt)

    def wrap(a):
      print ("wrap::", a)
      self.patterns.append(('GET', patt, a))

    def _(req, res):
      print ("this is underscore running calling...")
      print(' _GET:: ', m) # regex.test(m))
    return wrap

  def _find_route(self, method, path):
    found = None
    for r in self.patterns:
      print ('r', r)
      if r[1] == path:
        print ("path matches!!!")
        # self.route_to_use.set_result(r(2))
        # return
        found = r[2]
        print ("found:: ", found)
        break
    self.route_to_use.set_result(found)
    print ("_find_route done ({})".format(found))
    if found == None: raise HTTPErrorNotFound()
    # sleep(4)
    # return self.route_to_use
    # yield from asyncio.sleep(1)
    # yield

  def finish(self):
    # self.req._parser.parse_body.close()
    pass

  #
  # Dict like configuration access
  #
  def __setitem__(self, key, value):
    print ("Setting", key)
    self._config[key] = value

  def __getitem__(self, key):
    print ("Getting", key)
    return self._config[key]

  def config(self):
    return self._config
