#
# growler/core/application.py
#
"""
Defines the base application (App) that defines a 'growlerific' program.
This is where the developers should start writing their own application,
as all of the HTTP handling is done elsewhere.
The typical use case is a single instance of an application which is the
endpoint for a (or multiple) webserver.

Currently the only webserver which can forward requests to a Growler App
is the growler webserver packaged, but it would be nice to expand this
to other popular web frameworks.

A simple app can be created raw (no subclassing) and then decorate
functions or a class to modify the behavior of the app. (decorators
explained elsewhere)

.. code:: python

    app = growler.App()

    @app.use
    def myfunc(req, res):
        print("myfunc")
"""

import os
import sys
import types
import inspect
import logging

from ..utils.event_manager import Events
from .router import Router, RouterMeta
from .middleware_chain import MiddlewareChain

from ..http import (
    HTTPRequest,
    HTTPResponse,
    HTTPMethod,
)

log = logging.getLogger(__name__)


class GrowlerStopIteration(StopIteration):
    """
    Exception to raise when it is desirable to stop the growler
    application from continuing to loop over middleware.
    This is necessary to, for example, add a new HTTPResponder which
    does not interact with the application.

    No data is sent to the response object; if not careful, the client
    could time out.
    """
    pass


class Application:
    """
    A Growler application object. You can use a 'raw' app and modify
    it by decorating functions and objects with the app object, or
    subclass App and define request handling and middleware from within.

    The typical use case is a single App instance which is the end-point
    for a dedicated webserver. Upon each connection from a client, the
    _handle_connection method is called, which constructs the request and
    response objects from the asyncio.Stream{Reader,Writer}. The app then
    proceeds to pass these req and res objects to each middleware object
    in its chain, which may modify either. The default behavior is to
    have a growler.router as the last middleware in the chain and finds
    the first pattern which matches the req.path variable, and calls
    this function.

    If at any point in the middleware chain, res is found to be in the
    'closed' state, we simply stop the chain. If after the last
    middleware is called and the res is NOT in the 'closed' state, an
    error will be thrown. If at any point in the middleware chain an
    exception is thrown, the exception type is searched for in a chain
    of error handlers, and if found is called, with the expectation that
    res will be closed. If it is NOT closed at this point or if a handler
    was not found, the default implementation throws a '500 - Server
    Error' to the user.

    Each middleware in the chain can either be a normal function or an
    asyncio.coroutine. Either will be called asynchronously. There is
    no timeout variable yet, but I think I will put one in later, to
    ensure that the middleware is as responsive as the dev expects.
    """

    error_recursion_max_depth = 10

    def __init__(self,
                 name=__name__,
                 debug=True,
                 request_class=HTTPRequest,
                 response_class=HTTPResponse,
                 middleware_chain=None,
                 **kw
                 ):
        """
        Creates an application object.

        Args:
            name (str): Does nothing right now except identify object

            debug (bool): (de)Activates the loop's debug setting

            request_class (type or callable): The factory of request
                objects, the default of which is
                :class:`growler.HTTPRequest`.
                This should only be set in special cases, like
                debugging or if the dev doesn't want to modify
                default request objects via middleware.

            response_class (type or callable): The factory of
                response objects, the default of which is
                :class:`growler.HTTPResponse`.
                This should only be set in special cases, like
                debugging or if the dev doesn't want to modify
                default response objects via middleware.

            middleware_chain (type or callable): If a type or
                function-like object, it will be called and the
                return value will be interpreted as the middleware
                chain.
                Otherwise, if not None, it will use the argment as
                the middleware chain.
                The default value, if parameter is `None`, is the
                :class:`MiddlewareChain` class.
                This value is accessible via the attribute
                :attr:`middleware`.

        Keyword Args:
            Any other custom variables for the application.
            This dict is stored as the attribute 'config' in the
            application.
            These variables are accessible by the application's
            dict-access, as in:

                .. code:: python

                    app = App(..., val='VALUE')
                    app['val'] #=> VALUE
        """
        self.name = name

        self.config = {
            'x-powered-by': True,
            'env': os.getenv('GROWLER_ENV', 'development')
        }
        self.config.update(kw)

        if middleware_chain is None:
            middleware_chain = MiddlewareChain()
        elif isinstance(middleware_chain, (types.FunctionType, type)):
            middleware_chain = middleware_chain()

        self.middleware = middleware_chain

        self.events = Events()
        self.strict_router_check = False

        self._request_class = request_class
        self._response_class = response_class

        self.handle_404 = self.default_404_handler

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
        An alias of the default router's 'all' method. The middleware
        provided is called upon any HTTP request that matching the
        path, regardless of the method.

        Args:
            path (str): The URL path on which the middleware is mounted
            middleware (callable): The middleware function called upon
                a request matching the url
        """
        return self.router.all(path, middleware)

    def get(self, path="/", middleware=None):
        """
        An alias call for simple access to the default router. The
        middleware provided is called upon any HTTP 'GET' request which
        matches the path.

        Args:
            path (str): The URL path on which the middleware is mounted
            middleware (callable): The middleware function called upon
                a request matching the url
        """
        return self.router.get(path, middleware)

    def post(self, path="/", middleware=None):
        """
        An alias of the default router's 'post' method. The middleware
        provided is called upon a POST HTTP request matching the path.

        Args:
            path (str): The URL path on which the middleware is mounted
            middleware (callable): The middleware function called upon
                a request matching the url
        """
        return self.router.post(path, middleware)

    def put(self, path="/", middleware=None):
        """
        An alias of the default router's 'put' method. The middleware
        provided is called upon a PUT HTTP request matching the path.

        Args:
            path (str): The URL path on which the middleware is mounted
            middleware (callable): The middleware function called upon
                a request matching the url
        """
        return self.router.put(path, middleware)

    def delete(self, path="/", middleware=None):
        """
        An alias of the default router's 'delete' method.
        The middleware provided is called upon a DELETE HTTP request
        matching the path.

        Args:
            path (str): The URL path on which the middleware is mounted
            middleware (callable): The middleware function called upon
                a request matching the url
        """
        return self.router.delete(path, middleware)

    def use(self, middleware=None, path='/', method_mask=HTTPMethod.ALL):
        """
        Use the middleware (a callable with parameters res, req, next)
        upon requests match the provided path.
        A None path matches every request.
        Returns the middleware so this method may be used as a decorator.

        Args:
            middleware (callable): A function with signature '(req, res)'
                to be called with every request which matches path.

            path (str or regex): Object used to test the requests
                path. If it matches, either by equality or a successful
                regex match, the middleware is called with the req/res
                pair.

            method_mask (Optional[HTTPMethod]): Filters requests by HTTP
                method. The HTTPMethod enum behaves as a bitmask, so
                multiple methods may be joined by `+` or `\|`, removed
                with `-`, or toggled with `^`
                (e.g. `HTTPMethod.GET + HTTPMethod.POST`,
                      `HTTPMethod.ALL - HTTPMethod.DELETE`).

        Returns:
            Returns the provided middleware; a requirement for this method
            to be used as a decorator.
        """

        # catch decorator pattern
        if middleware is None:
            return lambda mw: self.use(mw, path, method_mask)

        if hasattr(middleware, '__growler_router'):
            router = getattr(middleware, '__growler_router')
            if isinstance(router, (types.MethodType,)):
                router = router()
            self.add_router(path, router)
        elif isinstance(type(middleware), RouterMeta):
            router = middleware._RouterMeta__growler_router()
            self.add_router(path, router)
        elif hasattr(middleware, '__iter__'):
            for mw in middleware:
                self.use(mw, path, method_mask)
        else:
            log.info("{} Using {} on path {}", id(self), middleware, path)
            self.middleware.add(path=path,
                                func=middleware,
                                method_mask=method_mask)
        return middleware

    def add_router(self, path, router):
        """
        Adds a router to the list of routers

        Args:
            path (str or regex): The path on which the router binds
            router (growler.Router): The router which will respond to
                requests

        Raises:
            TypeError: If `strict_router_check` attribute is True and
                the router is not an instance of growler.Router.
        """
        if self.strict_router_check and not isinstance(router, Router):
            raise TypeError("Expected object of type Router, found %r" % type(router))

        log.info("{} Adding router {} on path {}", id(self), router, path)
        self.middleware.add(path=path,
                            func=router,
                            method_mask=HTTPMethod.ALL,)

    @property
    def router(self):
        """
        Property returning the router at the top of the middleware
        chain's stack (the last item in the list). If the list is empty
        OR the item is not an instance of growler.Router, one is created
        and added to the middleware chain, matching all requests.
        """
        if not self.has_root_router:
            self.middleware.add(HTTPMethod.ALL,
                                MiddlewareChain.ROOT_PATTERN,
                                Router())
        return self.middleware.last().func

    @property
    def has_root_router(self):
        """
        Returns true if the bottom middleware of the chain is an
        instance of growler.Router, the mask matches ALL methods, and
        the path is the root (/) path.

        Returns:
            bool: Whether the last element in chain is a "root router"
        """
        try:
            mw = self.middleware.last()
        except IndexError:
            return False

        return (
            isinstance(mw.func, Router)
            and mw.mask == HTTPMethod.ALL
            and mw.path is MiddlewareChain.ROOT_PATTERN
        )

    async def handle_client_request(self, req, res):
        """
        Entry point for the request + response middleware chain.
        This is called by growler.HTTPResponder (the default responder)
        after the headers have been processed in the begin_application
        method.

        This iterates over all middleware in the middleware list which
        matches the client's method and path.
        It executes the middleware and continues iterating until the
        res.has_ended property is true.

        If the middleware raises a GrowlerStopIteration exception, this
        method immediately returns None, breaking the loop and leaving
        res without sending any information back to the client. Be *sure*
        that you have another coroutine scheduled that will take over
        handling client data.

        If a middleware function raises any other exception, the
        exception is forwarded to the middleware generator, which changes
        behavior to generating any error handlers it had encountered.
        This method then calls the handle_server_error method which
        *should* handle the error and notify the user.

        If after the chain is exhausted, either with an exception raised
        or not, res.has_ended does not evaluate to true, the response
        is sent a simple server error message in text.

        Args:
            req (growler.HTTPRequest): The incoming request, containing
                all information about the client.
            res (growler.HTTPResponse): The outgoing response, containing
                methods for sending headers and data back to the client.
        """
        # create a middleware generator
        mw_generator = self.middleware(req.method, req.path)

        # loop through middleware
        for mw in mw_generator:

            # try calling the function
            try:
                ret_val = mw(req, res)
                if inspect.isawaitable(ret_val):
                    await ret_val

            # special exception - immediately stop the loop
            #  - do not check if res has sent
            except GrowlerStopIteration:
                return None

            # on an unhandled exception - notify the generator of the error
            except Exception as error:
                mw_generator.throw(error)
                await self.handle_server_error(req, res, mw_generator, error)
                return

            if res.has_ended:
                break

        if not res.has_ended:
            self.handle_response_not_sent(req, res)

    async def handle_server_error(self, req, res, mw_generator, error, err_count=0):
        """
        Entry point for handling an exception that occured during
        execution of the middleware chain.
        This loops through the middleware generator - which should
        produce error-handling functions of signature `(req, res, error)`.
        If an error occurs during this method,

        There is currently no way to do error recovery of the middleware
        chain.

        Args:
            req (growler.HTTPRequest): The incoming request, containing
                all information about the client.

            res (growler.HTTPResponse): The outgoing response, containing
                methods for sending headers and data back to the client.

            mw_generator (Generator): The generator producing middleware.
                This has already been 'notified' of the error and should
                now only yield error handling middleware.

            error (Exception): The exception raised during middleware
                processing.

            err_count (int): A value for keeping track of recursive calls
                to the error handler.
                If this value equals self.error_recursion_max_depth, a
                new exception is raised, potentially confusing everyone
                involved.
        """
        if err_count >= self.error_recursion_max_depth:
            raise Exception("Too many exceptions:" + error)

        for mw in mw_generator:
            try:
                if inspect.iscoroutinefunction(mw):
                    await mw(req, res, error)
                else:
                    mw(req, res, error)
            except Exception as new_error:
                await self.handle_server_error(
                    req,
                    res,
                    mw_generator,
                    new_error,
                    err_count + 1,
                )
            finally:
                if res.has_ended:
                    break
        else:
            self.default_error_handler(req, res, error)
            if not res.has_ended:  # noqa pragma: no cover
                print("Default error handler did not send a response to "
                      "client!", file=sys.stderr)

    def handle_response_not_sent(self, req, res):
        """
        Method called upon reaching the end of the middleware chain
        with no request being sent.
        Default implementation is to call the handle_404 method, which
        may be overloaded for custom handling.
        """
        # res.send_text("404 - Not Found", 404)
        self.handle_404(req, res)

    def print_middleware_tree(self, *, EOL=os.linesep, **kwargs):  # noqa pragma: no cover
        """
        Prints a unix-tree-like output of the structure of the web
        application to the file specified (stdout by default).

        Args:
            EOL (str): The character or string that ends the line.
            **kwargs: Arguments pass to the standard print function.
                This allows specifying the file to write to and the
                ability to flush output upon creation.
        """

        def mask_to_method_name(mask):
            if mask == HTTPMethod.ALL:
                return 'ALL'
            methods = set(HTTPMethod) - {HTTPMethod.ALL}
            names = (method.name for method in methods if method.value & mask)
            return '+'.join(names)

        def path_to_str(path):
            if isinstance(path, str):
                return path
            return path.pattern.replace('\\', '')

        def decend_into_tree(chain, level):
            lines_ = []
            for mw in chain:
                info = (mask_to_method_name(mw.mask),
                        path_to_str(mw.path),
                        mw.func)
                prefix = "│   " * level
                lines_ += [prefix + "├── %s %s %s" % info]
                if mw.is_subchain:
                    lines_ += decend_into_tree(mw.func, level + 1)
            if level:
                lines_[-1] = lines_[-1].replace('├', '└')
            return lines_

        lines = [self.name]
        lines += decend_into_tree(self.middleware, 0)
        lines.append('┴')
        print(EOL.join(lines), **kwargs)

    @staticmethod
    def default_error_handler(req, res, error: Exception):
        from io import StringIO
        import traceback

        trace = StringIO()
        traceback.print_exc(file=trace)
        html = ("<!DOCTYPE html>"
                "<html><head><title>500 - Server Error</title></head>"
                "<body>"
                "<h1>500 - Server Error</h1><hr>"
                "<p style='font-family:monospace;'>"
                "The server encountered an error while processing your request to {path}"
                "</p><pre>{trace}</pre></body></html>\n")
        res.send_html(html.format(path=req.path, trace=trace.getvalue()), 500)

    @staticmethod
    def default_404_handler(req, res, error=None):
        html = ("<!DOCTYPE html>"
                "<html><head><title>404 - Not Found</title></head>"
                "<body>"
                "<h1>404 - Not Found</h1><hr>"
                "<p style='font-family:monospace;'>"
                "The page you requested: '{path}', could not be found"
                "</p></body></html>\n")
        res.send_html(html.format(path=req.path), 404)

    #
    # Configuration functions
    #

    def enable(self, name):
        """
        Set setting 'name' to true

        Args:
            name (str): The name of the the configuration option
        """
        self.config[name] = True

    def disable(self, name):
        """
        Set setting 'name' to false

        Args:
            name (str): The name of the the configuration option
        """
        self.config[name] = False

    def enabled(self, name):
        """
        Returns whether a setting has been enabled.
        This just casts the configuration value to a boolean.
        If the name is not found in the configuration, None is returned
        so evaluating.

        Args:
            name (str): The name of the the configuration option
        Returns:
            boolean or None
        """
        try:
            return bool(self.config[name])
        except KeyError:
            return None

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

    def create_server(self,
                      loop=None,
                      as_coroutine=False,
                      protocol_factory=None,
                      **server_config):
        """
        Helper function which constructs a listening server, using the
        default growler.http.protocol.Protocol which responds to this
        app.

        This function exists only to remove boilerplate code for
        starting up a growler app when using asyncio.

        Args:
            as_coroutine (bool): If True, this function does not wait
                for the server to be created, and only returns the
                coroutine generator object returned by loop.create_server.
                This mode should be used when already inside an async
                function.
                The default mode is to call :method:`run_until_complete`
                on the loop paramter, blocking until the server is
                created and added to the event loop.

            server_config (mixed): These keyword arguments parameters
                are passed directly to the BaseEventLoop.create_server
                function. Consult their documentation for details.
            loop (BaseEventLoop): This is the asyncio event loop used
                to provide the underlying `create_server` method, and,
                if as_coroutine is False, will block until the server
                is created.

            protocol_factory (callable): Function returning an asyncio
                protocol object (or more specifically, a
                `growler.aio.GrowlerProtocol` object) to be called upon
                client connection.
                The default is the :class:`GrowlerHttpProtocol` factory
                function.

            **server_config (mixed): These keyword arguments parameters are
                passed directly to the BaseEventLoop.create_server function.
                Consult their documentation for details.

        Returns:
            asyncio.Server: The result of asyncio.BaseEventLoop.create_server
                which has been passed to the event loop and setup with
                the provided parameters. This is returned if gen_coroutine
                is False (default).
            asyncio.coroutine: An asyncio.coroutine which will
                produce the asyncio.Server from the provided configuration parameters.
                This is returned if gen_coroutine is True.
        """
        if loop is None:
            import asyncio
            loop = asyncio.get_event_loop()

        if protocol_factory is None:
            from growler.aio import GrowlerHTTPProtocol
            protocol_factory = GrowlerHTTPProtocol.get_factory

        create_server = loop.create_server(
            protocol_factory(self, loop=loop),
            **server_config
        )

        if as_coroutine:
            return create_server
        else:
            return loop.run_until_complete(create_server)

    def create_server_and_run_forever(self, loop=None, **server_config):
        """
        Helper function which constructs an HTTP server and listens the
        loop forever.

        This function exists only to remove boilerplate code for starting
        up a growler app.

        Args:
            **server_config: These keyword arguments are forwarded
                directly to the BaseEventLoop.create_server function.
                Consult their documentation for details.
        Parameters:
            loop (asyncio.BaseEventLoop): Optional parameter for specifying
                an event loop which will handle socket setup.

            **server_config: These keyword arguments are forwarded directly to
                the create_server function.
        """
        if loop is None:
            import asyncio
            loop = asyncio.get_event_loop()

        self.create_server(loop=loop, **server_config)
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
