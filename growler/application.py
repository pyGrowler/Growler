#
# growler/application.py
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

.. code:: python

    app = growler.App()

    @app.use
    def myfunc(req, res):
        print("myfunc")

"""

import asyncio
import os
import types
import logging

from .http import (
    HTTPRequest,
    HTTPResponse,
    GrowlerHTTPProtocol,
)
from .http.errors import (
    HTTPError,
    HTTPErrorNotFound,
)
from .router import Router


class Application(object):
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
                 loop=None,
                 debug=True,
                 request_class=HTTPRequest,
                 response_class=HTTPResponse,
                 protocol_factory=GrowlerHTTPProtocol.get_factory,
                 **kw
                 ):
        """
        Creates an application object.

        :param name: does nothing right now
        :type name: str

        :param loop: The event loop to run on
        :type loop: asyncio.AbstractEventLoop

        :param debug: (de)Activates the loop's debug setting
        :type debug: boolean

        :param request_class: The factory of request objects, the default of
            which is growler.HTTPRequest. This should only be set in special
            cases, like debugging or if the dev doesn't want to modify default
            request objects via middleware.
        :type request_class: runnable

        :param response_class: The factory of response objects, the default of
            which is growler.HTTPResponse. This should only be set in special
            cases, like debugging or if the dev doesn't want to modify default
            response objects via middleware.
        :type response_class: runnable


        :param protocol_factory: Factory function this application uses to
            construct the asyncio protocol object which responds to client
            connections. The default is the GrowlerHTTPProtocol.get_factory
            method, which simply
        :type protocol_factory: runnable

        :param kw: Any other custom variables for the application. This dict is
            stored as 'self.config' in the application. These variables are
            accessible by the application's dict-access, as in:

            ``app = app(..., val='VALUE')``
            ``app['val'] #=> VALUE``

        :type kw: dict

        """
        self.name = name
        self._cache = {}

        self.config = kw

        self.loop = asyncio.get_event_loop() if loop is None else loop
        self.loop.set_debug(debug)

        self.middleware = []  # [{'path': None, 'cb' : self._middleware_boot}]

        # set the default router
        self.router = Router()

        self.enable('x-powered-by')
        self['env'] = os.getenv('GROWLER_ENV', 'development')

        self._events = {
            'startup': [],
            'connection': [],
            'headers': [],
            'error': [],
            'http_error': [],
        }
        self.error_handlers = []

        self._wait_for = [asyncio.sleep(0.1)]

        self._request_class = request_class
        self._response_class = response_class
        self._protocol_factory = protocol_factory

    def __call__(self, req, res):
        """
        Calls the growler server with the request and response objects.
        """
        print("Calling growler", req, res)

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
            for f in self._events['http_error']:
                f(err, req, res)
            return
        except Exception as err:
            # func.cancel()
            print("[Growler::App::_handle_connection] Caught Exception ")
            print(err)
            for f in self._events['error']:
                f(err, req, res)
            return

    def on_start(self, cb):
        print("Callback : ", cb)
        self._events['startup'].append(cb)

    @asyncio.coroutine
    def wait_for_required(self):
        """
        Called before running the server, ensures all required coroutines have
        finished running.
        """
        for x in self._wait_for:
            yield from x

    #
    # Middleware adding functions
    #
    # These functions can be called explicity or decorate functions. They are
    # forwarding functions which call the same function name on the root
    # router.
    # These could be assigned on construction using the form:
    #
    #    self.all = self.router.all
    #
    # , but that would not allow the user to switch the root router (easily)
    #

    def all(self, path="/", middleware=None):
        """
        An alias of the default router's 'all' method. The middleware provided
        is called upon any HTTP request that matching the path, regardless of
        the method.
        """
        return self.router.all(path, middleware)

    def get(self, path="/", middleware=None):
        """
        An alias call for simple access to the default router. The middleware
        provided is called upon any HTTP 'GET' request which matches the path.
        """
        return self.router.get(path, middleware)

    def post(self, path="/", middleware=None):
        """
        An alias of the default router's 'post' method. The middleware provided
        is called upon a POST HTTP request matching the path.
        """
        return self.router.post(path, middleware)

    def use(self, middleware, path=None):
        """
        Use the middleware (a callable with parameters res, req, next) upon
        requests match the provided path. A None path matches every request.
        Returns 'self' so the middleware may be nicely chained.

        :param middleware callable: A function with signature '(req, res)' to
                                    be called with every request which matches
                                    'path'
        :param path: A string or regex wich will be used to match request
                     paths.
        """
        debug = "[App::use] Adding middleware <{}> listening on path {}"
        if hasattr(middleware, '__growler_router'):
            router = getattr(middleware, '__growler_router')
            if isinstance(router, types.MethodType):
                router = router()
            self.add_router(path, router)
        elif hasattr(middleware, '__iter__'):
            for mw in middleware:
                self.use(mw, path)
        else:
            logging.info(debug.format(middleware, path))
            self.middleware.append(middleware)
        return self

    def add_router(self, path, router):
        """
        Adds a router to the list of routers

        :param path: The path the router binds to
        :type path: str

        :param router: The router which will respond to objects
        :type router: growler.Router
        """
        debug = "[App::add_router] Adding router {} on path {}"
        print(debug.format(router, path))
        self.router.add_router(path, router)

    def middleware_chain(self, req):
        """
        A generator which yields all the middleware in the chain which match
        the provided request object 'req'
        """
        yield from self.middleware
        yield from self.router.middleware_chain(req)

    def next_error_handler(self, req=None):
        """
        A generator providing the chain of error handlers for server exception
        catching. If there are no error handlers set, the app will use the
        classmethod 'default_error_handler'.

        An optional 'req' parameter is present in the event that request
        specific  handling (i.e. by path or session) is neccessary. This is
        currently unimplemented and should be ignored.
        """
        if len(self.error_handlers) == 0:
            yield self.default_error_handler
        yield from self.error_handlers

    @classmethod
    def default_error_handler(cls, req, res, error):
        html = ("<html><head><title>404 - Not Found</title></head><body>"
                "<h1>404 - Not Found</h1><hr>"
                "<p style='font-family:monospace;'>"
                "The page you requested: '%s', could not be found"
                "</p></body></html")
        res.send_html(html % req.path)

    #
    # Configuration functions
    #

    def enable(self, name):
        """Set setting 'name' to true"""
        self.config[name] = True

    def disable(self, name):
        """Set setting 'name' to false"""
        self.config[name] = False

    def enabled(self, name):
        """
        Returns whether a setting has been enabled. This just casts the
        configuration value to a boolean.
        """
        return bool(self.config[name])

    def require(self, future):
        """
        Will wait for the future before beginning to serve web pages. Useful
        for things like database connections.
        """
        self._wait_for.append(future)

    #
    # dict-like access for application configuration options
    #

    def __setitem__(self, key, value):
        """Sets a member of the application's configuration."""
        self.config[key] = value
        return value

    def __getitem__(self, key):
        """Gets a member of the application's configuration."""
        return self.config[key]

    def __delitem__(self, key):
        """Deletes a configuration parameter from the web-app"""
        del self.config[key]

    def __contains__(self, key):
        """Returns whether a key is in the application configuration."""
        return self.config.__contains__(key)

    #
    # Helper Functions for easy server creation
    #

    def create_server(self, gen_coroutine=False, **server_config):
        """
        Helper function which constructs a listening server, using the default
        growler.http.protocol.Protocol which responds to this app.

        This function exists only to remove boilerplate code for starting up a
        growler app.

        :param gen_coroutine bool: If True, this function only returns the
            coroutine generator returned by self.loop.create_server, else it
            will 'run_until_complete' the generator and return the created
            server object.
        :param server_config: These keyword arguments parameters are passed
            directly to the BaseEventLoop.create_server function. Consult their
            documentation for details.
        :returns mixed: An asyncio.coroutine which should be run inside a call
            to loop.run_until_complete() if gen_coroutine is True, else an
            asyncio.Server object created with teh server_config parameters.
        """
        create_server = self.loop.create_server(
            self._protocol_factory(self),
            **server_config
        )
        if gen_coroutine:
            return create_server
        else:
            return self.loop.run_until_complete(create_server)

    def create_server_and_run_forever(self, **server_config):
        """
        Helper function which constructs an HTTP server and listens the loop
        forever.

        This function exists only to remove boilerplate code for starting up a
        growler app.

        :param server_config: These keyword arguments parameters are passed
            directly to the BaseEventLoop.create_server function. Consult their
            documentation for details.
        """
        self.create_server(**server_config)
        self.loop.run_forever()
