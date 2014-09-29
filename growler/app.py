#
# growler/app.py
#

import asyncio
import re

from time import (time, sleep)
from datetime import (datetime, timezone, timedelta)

# from .http import (HTTPParser, HTTPError, HTTPRequest, HTTPResonse, Errors)
from .http import *
from .router import Router

class App(object):
  """A Growler application object."""

  # default configuration goes here
  config = {'host':'127.0.0.1', 'port': '8000'}

  def __init__(self, name, settings = {}, loop = None, no_default_router = False, debug = True):
    """
    Creates an application object.
    
    name - does nothing right now
    settings - server configuration
    loop - asyncio event loop to run on
    """
    self.name = name
    self.cache = {}

    self.config.update(settings)

    print(__name__, self.config)

    # rendering engines
    self.engines = {}
    self.patterns = []
    self.loop = loop if loop else asyncio.get_event_loop()
    self.loop.set_debug(debug)

    self.middleware = [{'path': None, 'cb' : self._middleware_boot}]

    # set the default router
    self.routers = [] if no_default_router else [{'path':'/', 'router' : Router()}]

  @asyncio.coroutine
  def _server_listen(self):
    """Starts the server. Should be called from 'app.run()'."""
    print ("Server {} listening on {}:{}".format (self.name, self.config['host'], self.config['port']))
    yield from asyncio.start_server(self._handle_connection, self.config['host'], self.config['port'])

  @asyncio.coroutine
  def _handle_connection(self, reader, writer, req_class = HTTPRequest, res_class = HTTPResonse):
    print('[_handle_connection]', self, reader, writer, "\n")

    # create the request object
    req = req_class(reader, self)

    # create the response object
    res = res_class(writer, self)

    # process the request
    try:
      yield from asyncio.Task(req.process())
    except Exception as e:
      print("[Growler::App::_handle_connection] Caught Exception ")
      print (e)

    res.header("content-type", "text/plain; charset=latin-1")
    res.message = "HAI! 😃 - 😄 - 😅 - 😆 - 😇 - 😈 - 😉 - 😊 - 😋 - 😌 - 😍 - 😎 - 😏 - 😐."
    res.send_headers()
    res.send_message()
    res.write_eof()
    # res.send("Text : ")
    print ("Right after process!")
    self.finish()
    # print(request_process_task.exception())


    return

    # futures which will be filled in by the request 'processor'
    request_line = asyncio.Future()
    http_headers = asyncio.Future()
    http_body = asyncio.Future()

    # begin processing the request
    try:
      handle_task = asyncio.Task(req.do_process(request_line, http_headers, http_body))
    except Exception as e:
      handle_task.cancel()
      print("handle_task threw exception!",handle_task)
      print (e)
    # req.do_process(request_line, http_headers, http_body)

    try:
      request = yield from request_line
    except HTTPError as e:
      print ("HTTPError!")
  
    print("Yielded the request line '{}'".format(request_line))
    print("Yielded the request '{}'".format(request))

    headarz = yield from http_headers
    print("Yielded the http_headers '{}'".format(http_headers))
    print("Yielded the headarz '{}'".format(headarz))
    return

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
      print("[_handle_connection] request_line", request_line)
      headers = yield from parser.parse()
      body = yield from parser.parse()
    except HTTPError as err:
      print ("Error in _handle_connection")
      print(err)
      
      h = "HTTP/1.1 {} {}\n".format(err.code, err.phrase)
      h += "Date: {}\n".format(datetime.now(timezone(timedelta())).strftime("%a, %d %b %Y %H:%M:%S %Z"))

      body_content = "<h1>{}</h1>".format(err.phrase)
      b = "<!DOCTYPE html>\n<html><head><title>{}</title></head><body>{}</body></html>\n".format(err.phrase, body_content)
      self.send_message(writer, h, b)
      return None

    self.send_message(writer, "", "")
    return None
      
  def run(self, run_forever = True):
    """
    Starts the server and listens for new connections. If run_forever is true, the 
    event loop is set to block.
    """
    self.loop.run_until_complete(self._server_listen())
    if run_forever:
      try:
        self.loop.run_forever()
      finally:
        print("Run Forever Ended!")
        self.loop.close()

  def after_route(self, f = None):
    for mw in self.middleware:
      mw()
    # self.route_to_use.result()(self.req, self.res)


  # WARNING : This is hiding io, something we want to AVOID!
  def send_message(self, output, header, body):
    msg = "{}\r\n\r\n{}".format(header, body)
    # print("Sending:", msg)
    output.write(msg)
    output.write_eof()

  def get(self, patt):
    """A 'VERB' function which is called upon a GET HTTP request"""
    # regex = re.compile(patt)
    print("GET:", self, patt)

    def wrap(a):
      print ("wrap::", a)
      self.patterns.append(('GET', patt, a))

    def _(req, res):
      print ("this is underscore running calling...")
      print(' _GET:: ', m) # regex.test(m))
    return wrap

  def enable(self, name):
    """Set setting 'name' to true"""
    self.config[name] = True

  def disbale(self, name):
    """Set setting 'name' to false"""
    self.config[name] = False

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

  def use(self, middleware, path = None):
    """
    Use the middleware (a callable with parameters res, req, next) upon requests
    match the provided path. A None path matches every request.
    """
    print("[App::use] Adding middleware", middleware)
    self.middleware.append(middleware)

  def _middleware_boot(self, req, res, next):
    """The initial middleware"""
    pass

  def add_router(self, path, router):
    """Adds a router to the list of routers"""
    self.routers.append(router)

  def print_router_tree(self):
    for r in self.routers:
      r.print_tree()

  #
  # Dict like configuration access
  #
  def __setitem__(self, key, value):
    print ("Setting", key)
    self.config[key] = value

  def __getitem__(self, key):
    print ("Getting", key)
    return self.config[key]
