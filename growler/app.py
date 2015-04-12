#
# growler/app.py
#
"""
Defines the base application (App) that defines a 'growlerific' program. This
is where the developers should start writing their own application, as all of
the HTTP handling is done elsewhere. The typical use case is a single instance
of an application which is the endpoint for a (or multiple) webserver.

Currently the only webserver which can forward requests to a Growler App is the
growler webserver packaged, but it would be nice to expand this to other
popular web frameworks.

A simple app can be created raw (no subclassing) and then decorate functions or
a class to modify the behavior of the app. (decorators explained elsewhere)

app = App()

@app.use
def myfunc(req, res):
    print("myfunc")

"""

import asyncio
import os

from .http import (
    HTTPRequest,
    HTTPResponse,
    HTTPError,
    HTTPErrorInternalServerError,
    HTTPErrorNotFound
)
from .router import Router


class App(object):
    """
    A Growler application object. You can use a 'raw' app and modify it by
    decorating functions and objects with the app object, or subclass App and
    define request handling and middleware from within.

    The typical use case is a single App instance which is the end-point for a
    dedicated webserver. Upon each connection from a client, the
    _handle_connection method is called, which constructs the request and
    response objects from the asyncio.Stream{Reader,Writer}. The app then
    proceeds to pass these req and res objects to each middleware object in its
    chain, which may modify either. The default behavior is to have a
    growler.router as the last middleware in the chain and finds the first
    pattern which matches the req.path variable, and calls this function.

    If at any point in the middleware chain, res is found to be in the 'closed'
    state, we simply stop the chain. If after the last middleware is called and
    the res is NOT in the 'closed' state, an error will be thrown. If at any
    point in the middleware chain an exception is thrown, the exception type is
    searched for in a chain of error handlers, and if found is called, with the
    expectation that res will be closed. If it is NOT closed at this point or
    if a handler was not found, the default implementation throws a '500 -
    Server Error' to the user.

    Each middleware in the chain can either be a normal function or an
    asyncio.coroutine. Either will be called asynchronously. There is no
    timeout variable yet, but I think I will put one in later, to ensure that
    the middleware is as responsive as the dev expects.
    """

    def __init__(self,
                 name=__name__,
                 loop=asyncio.get_event_loop(),
                 no_default_router=False,
                 debug=True,
                 request_class=HTTPRequest,
                 response_class=HTTPResponse,
                 **kw
                 ):
        """
        Creates an application object.

        @param name: does nothing right now
        @type name: str

        @param loop: The event loop to run on
        @type loop: asyncio.AbstractEventLoop

        @param debug: (de)Activates the loop's debug setting
        @type debug: boolean

        @param request_class: The factory of request objects, the default of
            which is growler.HTTPRequest. This should only be set in special
            cases, like debugging or if the dev doesn't want to modify default
            request objects via middleware.
        @type request_class: runnable

        @param response_class: The factory of response objects, the default of
            which is growler.HTTPResponse. This should only be set in special
            cases, like debugging or if the dev doesn't want to modify default
            response objects via middleware.
        @type response_class: runnable

        @param kw: Any other custom variables for the application. This dict is
            stored as 'self.config' in the application
        @type kw: dict

        """
        self.name = name
        self.cache = {}

        self.config = kw

        # rendering engines
        self.engines = {}
        self.patterns = []
        self.loop = loop
        self.loop.set_debug(debug)

        self.middleware = []  # [{'path': None, 'cb' : self._middleware_boot}]

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

    def __call__(self, req, res):
        print("Calling growler", req, res)

    @asyncio.coroutine
    def _server_listen(self):
        """
        Starts the server. Should be called from 'app.run()' or equivalent.
        """
        print("Server {} listening on {}:{}".format(
            self.name,
            self.config['host'],
            self.config['port'])
        )
        yield from asyncio.start_server(
            self._handle_connection,
            self.config['host'],
            self.config['port']
        )

    @asyncio.coroutine
    def _handle_connection(self, reader, writer):
        """
        Called upon a connection from remote server. This is the default
        behavior if application is run using '_server_listen' method. Request
        and response objects are created from the stream reader/writer and
        middleware is cycled through and applied to each. Changing behavior of
        the server should be handled using middleware and NOT overloading
        _handle_connection.

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
            print(err)
            for f in self._on_http_error:
                f(err, req, res)
            return
        except Exception as err:
            processing_task.cancel()
            print("[Growler::App::_handle_connection] Caught Exception ")
            print(err)
            for f in self._on_error:
                f(err, req, res)
            return

        # Call each action for the event 'OnHeaders'
        for f in self._on_headers:
            yield from self._call_and_handle_error(f, req, res)

            if res.has_ended:
                print("[OnHeaders] Res has ended.")
                return

        # Loop through middleware
        for md in self.middleware:
            print("Running Middleware : ", md)

            yield from self._call_and_handle_error(md, req, res)

            if res.has_ended:
                print("[middleware] Res has ended.")
                return

        route_generator = self.routers[0].match_routes(req)
        for route in route_generator:
            waitforme = asyncio.Future()
            if not route:
                raise HTTPErrorInternalServerError()

        yield from self._call_and_handle_error(route, req, res)

        if res.has_ended:
            print("[Route] Res has ended.")
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

        # Provided middleware is a 'normal' function - we just wrap with the
        # local 'cofunction'
        if not (asyncio.iscoroutinefunction(func) or
                asyncio.iscoroutine(func)):
            func = cofunctitize(func)

        try:
            yield from func(req, res)
        except HTTPError as err:
            # func.cancel()
            err.PrintSysMessage()
            print(err)
            for f in self._on_http_error:
                f(err, req, res)
            return
        except Exception as err:
            # func.cancel()
            print("[Growler::App::_handle_connection] Caught Exception ")
            print(err)
            for f in self._on_error:
                f(err, req, res)
            return

    def onstart(self, cb):
        print("Callback : ", cb)
        self._on_start.append(cb)

    def run(self, run_forever=True):
        """
        Starts the server and listens for new connections. If run_forever is
        true, the event loop is set to block.
        """
        # for func in self._on_start:
        #   self.loop.run_until_complete(f)
        #   self.loop.async(func):
        # self.loop.run_until_complete(asyncio.Task(self.wait_for_all()))
        # print("RUN ::")

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
        """
        Called before running the server, ensures all required coroutines have
        finished running.
        """
        # print("[wait_for_all] Begin ", self._wait_for)

        for x in self._wait_for:
            yield from x

    def all(self, path="/", middleware=None):
        """
        An alias call for simple access to the default router. The middleware
        provided is called upon a GET HTTP request matching the path.
        """
        return self.routers[0].all(path, middleware)

    def get(self, path="/", middleware=None):
        """
        An alias call for simple access to the default router. The middleware
        provided is called upon a GET HTTP request matching the path.
        """
        if middleware is None:
            return self.routers[0].get(path, middleware)
        self.routers[0].get(path, middleware)

    def set(self, key, value):
        """Set a configuration option (Alias of app[key] = value)"""
        self.config[key] = value

    def post(self, path="/", middleware=None):
        """
        An alias call for simple access to the default router. The middleware
        provided is called upon a POST HTTP request matching the path.
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
        """
        Will wait for the future before beginning to serve web pages. Useful
        for database connections.
        """
        # if type(future) is asyncio.Future:
        #   self._wait_for['futures'].append(future)
        # elif inspect.isgeneratorfunction(future):
        #   print("GeneratorFunction!")
        #   self._wait_for['generators'].append(future)
        # elif inspect.isgenerator(future):
        #   print("Generator!")
        #   self._wait_for['generators'].append(future)
        # else:
        #   print("[require] Unknown Type of 'Future'", future, type(future))
        self._wait_for.append(future)

    def _find_route(self, method, path):
        found = None
        for r in self.patterns:
            print('r', r)
            if r[1] == path:
                print("path matches!!!")
                # self.route_to_use.set_result(r(2))
                # return
                found = r[2]
                print("found:: ", found)
                break
        self.route_to_use.set_result(found)
        print("_find_route done ({})".format(found))
        if found is None:
            raise HTTPErrorNotFound()
        # return self.route_to_use
        # yield from asyncio.sleep(1)
        # yield

    def use(self, middleware, path=None):
        """
        Use the middleware (a callable with parameters res, req, next) upon
        requests match the provided path. A None path matches every request.
        Returns 'self' so the middleware may be nicely chained.
        """
        print("[App::use] Adding middleware", middleware)
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
    # dict-like access for application configuration options
    #
    def __setitem__(self, key, value):
        """Sets a member of the application's configuration."""
        self.config[key] = value

    def __getitem__(self, key):
        """Gets a member of the application's configuration."""
        return self.config[key]
