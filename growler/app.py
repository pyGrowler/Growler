#
# growler/app.py
#

import asyncio
import re
import os
import traceback
import sys

import inspect

from time import (time, sleep)
from datetime import (datetime, timezone, timedelta)

# from .http import (HTTPParser, HTTPError, HTTPRequest, HTTPResponse, Errors)
from .http import *
from .router import Router

class App(object):
  """
  A Growler application object. It's recommended to either subclass growler.App, writing a custom 'run' 
  The 'main leaving the _handle_connection.
  
  """

  # default configuration goes here
  config = {'host':'127.0.0.1', 'port': '8000'}

  def __init__(self, name, settings = {}, loop = None, no_default_router = False, debug = True, request_class = HTTPRequest, response_class = HTTPResponse):
    """
    Creates an application object.
    @param name: does nothing right now
    @type name: str 

    @param settings: initial server configuration
    @type settings: dict

    @param loop: The event loop to run on
    @type loop: asyncio.AbstractEventLoop
    """
    self.name = name
    self.cache = {}

    self.config.update(settings)

    # rendering engines
    self.engines = {}
    self.patterns = []
    self.loop = loop if loop else asyncio.get_event_loop()
    self.loop.set_debug(debug)

    self.middleware = []

    # set the default router
    self.routers = [] if no_default_router else [Router('/')]

    self.enable('x-powered-by')
    self.set('env', os.getenv('GROWLER_ENV', 'development'))
    self._on_connection = []
    self._on_headers = []
    self._on_error = []
    self._on_http_error = []

    self._wait_for = [asyncio.sleep(0.1)]

    self._request_class = request_class
    self._response_class = response_class

  @asyncio.coroutine
  def _server_listen(self):
    """Starts the server. Should be called from 'app.run()' or equivalent."""
    print ("Server {} listening on {}:{}".format (self.name, self.config['host'], self.config['port']))
    yield from asyncio.start_server(self._handle_connection, self.config['host'], self.config['port'])

  @asyncio.coroutine
  def _handle_connection(self, reader, writer):
    """
    Called upon a connection from remote server. This is the default behavior if application is
    run using '_server_listen' method.
    Request and response objects are created from the stream reader/writer and middleware
    is cycled through and applied to each.
    Changing behavior of the server should be handled using middleware and NOT overloading _handle_connection.
    @type reader: asyncio.StreamReader
    @type writer: asyncio.StreamWriter
    """

    print('[_handle_connection]', self, reader, writer, "\n")

    # Call each action for the event 'OnConnection'
    for f in self._on_connection:
      f(reader._transport)

    # create the request object
    req = self._request_class(reader, self)

    # create the response object
    res = self._response_class(writer, self)

    # create an asynchronous task to process the request
    processing_task = asyncio.Task(req.process())

    try:
      # run task
      yield from processing_task
    # Caught an HTTP Error - handle by running through HTTPError handlers
    except HTTPError as err:
      processing_task.cancel()
      err.PrintSysMessage()
      print (err)
      for f in self._on_http_error:
        f(e, req, res)
      return
    except Exception as e:
      processing_task.cancel()
      print("[Growler::App::_handle_connection] Caught Exception!")
      print (type(e))
      print (e)
      for f in self._on_error:
        f(e, req, res)
      return

    # Call each action for the event 'OnHeaders'
    for f in self._on_headers:
      yield from self._call_and_handle_error(f, req, res)

      if res.has_ended:
        # print ("[OnHeaders] Res has ended.")
        return

    # Loop through middleware
    for md in self.middleware:
      #print ("Running Middleware : ", md)

      yield from self._call_and_handle_error(md, req, res)

      if res.has_ended:
        #print ("[middleware] Res has ended.")
        return

    route_generator = self.routers[0].match_routes(req)
    for route in route_generator:
      waitforme = asyncio.Future()
      if not route:
        raise HTTPErrorInternalServerError()

      yield from self._call_and_handle_error(route, req, res)

      if res.has_ended:
        print ("[Route] Res has ended.")
        return
      else:
        yield from waitforme

    # Default
    if not res.has_ended:
      e = Exception("Routes didn't finish!")
      for f in self._on_error:
        f(e, req, res)

  def _call_and_handle_error(self, func, req, res):

    def cofunctitize(_func):
      @asyncio.coroutine
      def cowrap(_req, _res):
        return _func(_req, _res)
      return cowrap

    # Provided middleware is a 'normal' function - we just wrap with the local 'cofunction' 
    if not (asyncio.iscoroutinefunction(func) or asyncio.iscoroutine(func)):
      func = cofunctitize(func)

    try:
      yield from func(req, res)
    except HTTPError as err:
      # func.cancel()
      err.PrintSysMessage()
      print (err)
      for f in self._on_http_error:
        f(e, req, res)
      return
    except Exception as e:
      # func.cancel()
      print("[Growler::App::_call_and_handle_error] Caught Exception!")
      print (type(e))
      print (e)
      traceback.print_exc(file=sys.stdout)
      for f in self._on_error:
        f(e, req, res)
      res.has_ended = True
      return
    

  def onstart(self, cb):
    print ("Callback : ", cb)
    self._on_start.append(cb)


  def run(self, run_forever = True):
    """
    Starts the server and listens for new connections. If run_forever is true, the
    event loop is set to block.
    """
    # for func in self._on_start:
      # self.loop.run_until_complete(f)
      # self.loop.async(func):
    # self.loop.run_until_complete(asyncio.Task(self.wait_for_all()))
    # print ("RUN ::")

    self.loop.run_until_complete(self.wait_for_required())

    self.loop.run_until_complete(self._server_listen())
    if run_forever:
      try:
        self.loop.run_forever()
      finally:
        print("Run Forever Ended!")
        self.loop.close()

  @asyncio.coroutine
  def wait_for_required(self):
    """Called before running the server, ensures all required coroutines have finished running."""
    # print ("[wait_for_all] Begin ", self._wait_for)

    for x in self._wait_for:
      yield from x

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
    """Set a configuration option (Alias of app[key] = value)"""
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
    """Returns whether a setting has been enabled"""
    return self.config[name] == True
    
  def require(self, future):
    """Will wait for the future before beginning to serve web pages. Useful for database connections."""
    # if type(future) is asyncio.Future:
      # self._wait_for['futures'].append(future)
    # elif inspect.isgeneratorfunction(future):
      # print ("GeneratorFunction!")
      # self._wait_for['generators'].append(future)
    # elif inspect.isgenerator(future):
      # print ("Generator!")
      # self._wait_for['generators'].append(future)
    # else:
      # print ("[require] Unknown Type of 'Future'", future, type(future))
    self._wait_for.append(future)

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
    if found == None:
      raise HTTPErrorNotFound()

  def use(self, middleware, path = None):
    """
    Use the middleware (a callable with parameters res, req, next) upon requests
    match the provided path. A None path matches every request.
    Returns 'self' so the middleware may be nicely chained.
    """
    #print ("[App::use] Adding middleware", middleware)
    self.middleware.append(middleware)
    return self

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
  # Dict like access for application configuration options
  #
  def __setitem__(self, key, value):
    """Sets a member of the application's configuration."""
    self.config[key] = value

  def __getitem__(self, key):
    """Gets a member of the application's configuration."""
    return self.config[key]
