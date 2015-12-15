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
import sys
import logging
import re
import types
from .http import (
    HTTPRequest,
    HTTPResponse,
    GrowlerHTTPProtocol,
)
from .router import Router
from .middleware_chain import MiddlewareChain
from .http.methods import HTTPMethod
import growler.http.methods

log = logging.getLogger(__name__)


class GrowlerStopIteration(StopIteration):
    """
    Exception to raise when it is desireable to stop the growler application
    from continuing to loop over middleware. This is necessary to run over a

    """
    pass


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

    error_recursion_max_depth = 10

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

        self.config = kw

        self.loop = asyncio.get_event_loop() if loop is None else loop
        self.loop.set_debug(debug)

        self.middleware = MiddlewareChain()

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

    #
    # Middleware adding functions
    #
    # These functions can be called explicity or decorate functions. They are
    # forwarding functions which call the same function name on the root
    # router.
    # These could be assigned on construction using the form:
    #
    #    2self.all = self.router.all
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

    def use(self, middleware, path='/', method_mask=HTTPMethod.ALL):
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
        if hasattr(middleware, '__growler_router'):
            router = getattr(middleware, '__growler_router')
            if isinstance(router, (types.MethodType,)):
                router = router()
            self.add_router(path, router)
        elif hasattr(middleware, '__iter__'):
            for mw in middleware:
                self.use(mw, path, method_mask)
        else:
            log.info("%d Using %s on path %s" % (id(self), middleware, path))
            self.middleware.add(path=re.compile(path),
                                func=middleware,
                                method_mask=method_mask)
        return self

    def add_router(self, path, router):
        """
        Adds a router to the list of routers

        :param path: The path the router binds to
        :type path: str

        :param router: The router which will respond to objects
        :type router: growler.Router
        """
        log.info("%d Adding router %s on path %s" % (id(self), router, path))
        self.use(middleware=router,
                 path=path,
                 method_mask=HTTPMethod.ALL,)

    @property
    def router(self):
        """
        Property returning the router at the top of the middleware chain's
        stack (the last item in the list). If the list is empty OR the item is
        not an instance of growler.Router, one is created and added to the
        middleware chain, matching all requests.
        """
        if (len(self.middleware.mw_list) is 0
            or not isinstance(self.middleware.mw_list[-1].func, Router)
            or self.middleware.mw_list[-1].mask != HTTPMethod.ALL
            or self.middleware.mw_list[-1].path != '/'):

            self.middleware.add(HTTPMethod.ALL, '/', Router())
        return self.middleware.mw_list[-1].func

    @types.coroutine
    def handle_client_request(self, req, res):
        """
        Entry point for the request+response middleware chain
        """
        # create a middleware generator
        mw_generator = self.middleware(req.method, req.path)

        # loop through middleware
        for mw in mw_generator:

            # try calling the function
            try:
                if asyncio.iscoroutinefunction(mw):
                    yield from mw(req, res)
                else:
                    mw(req, res)

            # special exception - immediately stop the loop
            #  - do not check if res has sent
            except GrowlerStopIteration:
                return None

            # on an unhandled exception - notify the generator of the error
            except Exception as error:
                mw_generator.send(error)
                self.handle_server_error(req, res, mw_generator, error)
                break

            if res.has_ended:
                break

        if not res.has_ended:
            res.send_text("500 - Server Error", 500)

    def handle_server_error(self, req, res, generator, error, err_count=0):
        """
        Entry point for handling an unhandled error that occured during
        execution of some middleware chain.
        """
        if err_count >= self.error_recursion_max_depth:
            raise Exception("Too many exceptions:" + error)

        for mw in generator:

            try:
                mw(req, res, error)
            except Exception as new_error:
                generator.send(new_error)
                self.handle_server_error(req,
                                         res,
                                         generator,
                                         new_error,
                                         err_count+1)
                break

            if res.has_ended:
                break

    def next_error_handler(self, req=None):
        """
        A generator providing the chain of error handlers for server exception
        catching. If there are no error handlers set, the app will use the
        classmethod 'default_error_handler'.

        An optional 'req' parameter is present in the event that request
        specific  handling (i.e. by path or session) is neccessary. This is
        currently unimplemented and should be ignored.
        """
        yield from self.error_handlers
        yield self.default_error_handler

    def print_middleware_tree(self, *, file=sys.stdout, EOL=os.linesep):  # noqa pragma: no cover
        """
        Prints a unix-tree-like output of the structure of the web application
        to the file specified (stdout by default).

        :param file: file to print to
        :type file: stream that the standard 'print' function writes to

        :param EOL: character/string that ends the line
        :type EOL: str
        """

        def mask_to_method_name(mask):
            if mask == HTTPMethod.ALL:
                return 'ALL'
            methods_names = growler.http.methods.string_to_method.items()
            names = [name for name, key in methods_names if (key & mask)]
            return '+'.join(names)

        def path_to_str(path):
            if isinstance(path, str):
                return path
            return path.pattern

        def decend_into_tree(chain, level):
            lines_ = []
            for mw in chain.mw_list:
                info = (mask_to_method_name(mw.mask),
                        path_to_str(mw.path),
                        mw.func)
                prefix = "│   " * level
                lines_ += [prefix + "├── %s %s %s" % info]
                if mw.is_subchain:
                    lines_ += decend_into_tree(mw.func, level+1)
            lines_[-1] = lines_[-1].replace('├', '└')
            return lines_

        lines = [self.name]
        lines += decend_into_tree(self.middleware, 0)
        print(EOL.join(lines), file=file)

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
        Will wait for the future before creating the asyncio server. Useful
        for things like database connections.
        """
        # TODO: Is this _actually_ useful?
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

        if self._wait_for:
            self.loop.run_until_complete(asyncio.wait(self._wait_for,
                                                      loop=self.loop))
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
