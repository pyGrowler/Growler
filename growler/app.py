#
# growler/app.py
#

import asyncio
import re
import os

from time import (time, sleep)
from datetime import (datetime, timezone, timedelta)

# from .http import (HTTPParser, HTTPError, HTTPRequest, HTTPResponse, Errors)
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

    print('name:', self.name, self.config)

    # rendering engines
    self.engines = {}
    self.patterns = []
    self.loop = loop if loop else asyncio.get_event_loop()
    self.loop.set_debug(debug)

    self.middleware = [] # [{'path': None, 'cb' : self._middleware_boot}]

    # set the default router
    self.routers = [] if no_default_router else [Router('/')]

    self.enable('x-powered-by')
    self.set('env', os.getenv('GROWLER_ENV', 'development'))
    self._on_start = []

  @asyncio.coroutine
  def _server_listen(self):
    """Starts the server. Should be called from 'app.run()'."""
    print ("Server {} listening on {}:{}".format (self.name, self.config['host'], self.config['port']))
    yield from asyncio.start_server(self._handle_connection, self.config['host'], self.config['port'])

  @asyncio.coroutine
  def _handle_connection(self, reader, writer, req_class = HTTPRequest, res_class = HTTPResponse):
    print('[_handle_connection]', self, reader, writer, "\n")

    # create the request object
    req = req_class(reader, self)

    # create the response object
    res = res_class(writer, self)

    # process the request
    processing_task = asyncio.Task(req.process())

    try:
      yield from processing_task
    except HTTPError as err:
      processing_task.cancel()
      err.PrintSysMessage()
      print (err)
    except Exception as e:
      processing_task.cancel()
      print("[Growler::App::_handle_connection] Caught Exception ")
      print (e)

    # res.message = "HAI! 😃 - 😄 - 😅 - 😆 - 😇 - 😈 - 😉 - 😊 - 😋 - 😌 - 😍 - 😎 - 😏 - 😐."
    # res.send_headers()
    # res.send_message()
    # res.write_eof()
    # res.send("Text : ")
    # print ("Right after process!")
    # self.finish()
    # print(request_process_task.exception())

    for md in self.middleware:
      print ("Running Middleware : ", md, asyncio.iscoroutine(md), asyncio.iscoroutinefunction(md))
      waitforme = asyncio.Future()

      def on_next(err = None):
        if (err):
          if (err['status']):
            res.end(err['status'])
          else:
            res.end(500)
        waitforme.set_result(None)

#       md(req, res, lambda: waitforme.set_result(None))

      if asyncio.iscoroutine(md):
        yield from md(req, res, on_next)
      else:
        print (" -- Not a coroutine - running as 'usual'")
        md(req, res, on_next)
        print (" -- Done")

      print ("finished calling md", res.finished)
      if res.finished:
        break
      else:
        yield from waitforme

    route_generator = self.routers[0].match_routes(req)
    for route in route_generator:
      waitforme = asyncio.Future()
      if route.__code__.co_argcount == 2:
        route(req, res)
      else:
        route(req, res, lambda: waitforme.set_result(None))
      print ("finished calling route", res.finished)
      if res.finished:
        break
      else:
        yield from waitforme

  def onstart(self, cb):
    print ("Callback : ", cb)
    self._on_start.append(cb)


  def run(self, run_forever = True):
    """
    Starts the server and listens for new connections. If run_forever is true, the
    event loop is set to block.
    """
    for func in self._on_start:
      # self.loop.async(func)
      asyncio.async(func())

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



  def all(self, path="/", middleware = None):
    """
    An alias call for simple access to the default router. The middleware provided
    is called upon a GET HTTP request matching the path.
    """
    return self.routers[0].all(path, middleware)

  def get(self, path="/", middleware = None):
    """
    An alias call for simple access to the default router. The middleware provided
    is called upon a GET HTTP request matching the path.
    """
    if middleware == None:
      return self.routers[0].get(path, middleware)
    self.routers[0].get(path, middleware)
    
  def set(self, key, value):
    self.config[key] = value

  def post(self, path = "/", middleware = None):
    """
    An alias call for simple access to the default router. The middleware provided
    is called upon a POST HTTP request matching the path.
    """
    return self.routers[0].post(path, middleware)

  def enable(self, name):
    """Set setting 'name' to true"""
    self.config[name] = True

  def disable(self, name):
    """Set setting 'name' to false"""
    self.config[name] = False

  def enabled(self, name):
    return self.config[name] == True

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
    """
    Adds a router to the list of routers
    @type path: str
    @type router: growler.Router
    """
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
