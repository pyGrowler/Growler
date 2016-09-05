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

import os
import sys
import types
import asyncio
import logging

from growler.utils.event_manager import Events
from growler.http import (
    HTTPRequest,
    HTTPResponse,
    GrowlerHTTPProtocol,
)
import growler.http.methods
from growler.http.methods import HTTPMethod
from growler.router import Router, RouterMeta
from growler.middleware_chain import MiddlewareChain

log = logging.getLogger(__name__)


class GrowlerStopIteration(StopIteration):
    """
    Exception to raise when it is desireable to stop the growler application
    from continuing to loop over middleware. This is necessary to, for example,
    add a new HTTPResponder which does not interact with the application.

    No data is sent to the response object; if not careful, the client could
    time out.
    """
    pass


class Application:
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
                 middleware_chain_factory=MiddlewareChain,
                 **kw
                 ):
        """
        Creates an application object.

        Args:
            name (str): Does nothing right now except identify object
            loop (asyncio.AbstractEventLoop): The event loop to run on
            debug (bool): (de)Activates the loop's debug setting

            request_class (type or callable): The factory of request objects, the default of
                which is growler.HTTPRequest. This should only be set in special cases, like
                debugging or if the dev doesn't want to modify default request objects via
                middleware.

            response_class (type or callable): The factory of response objects, the default of
                which is growler.HTTPResponse. This should only be set in special cases, like
                debugging or if the dev doesn't want to modify default response objects via
                middleware.

            protocol_factory (callable): Factory function this application uses to construct
                the asyncio protocol object which responds to client connections. The default
                is the GrowlerHTTPProtocol.get_factory method, which simply returns a lambda
                returning new GrowlerHTTPProtocol objects.

            middleware_chain_factory (type or callable): Called upon with no arguments to
                create the middleware chain used by the application. This is accessible via
                the attribute 'middleware'.

        Keyword Args:
            Any other custom variables for the application. This dict is stored as the
            attribute 'config' in the application. These variables are accessible by the
            application's dict-access, as in:

            .. code:: python

                app = app(..., val='VALUE')
                app['val'] #=> VALUE
        """
        self.name = name

        self.config = kw

        self.loop = asyncio.get_event_loop() if (loop is None) else loop
        self.loop.set_debug(debug)

        self.middleware = middleware_chain_factory()

        self.enable('x-powered-by')
        self['env'] = os.getenv('GROWLER_ENV', 'development')

        self.events = Events()
        self.strict_router_check = False

        self._request_class = request_class
        self._response_class = response_class
        self._protocol_factory = protocol_factory

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
        An alias of the default router's 'all' method. The middleware provided
        is called upon any HTTP request that matching the path, regardless of
        the method.

        Args:
            path (str): The URL path on which the middleware is mounted
            middleware (callable): The middleware function called upon a
                request matching the url
        """
        return self.router.all(path, middleware)

    def get(self, path="/", middleware=None):
        """
        An alias call for simple access to the default router. The middleware
        provided is called upon any HTTP 'GET' request which matches the path.

        Args:
            path (str): The URL path on which the middleware is mounted
            middleware (callable): The middleware function called upon a
                request matching the url
        """
        return self.router.get(path, middleware)

    def post(self, path="/", middleware=None):
        """
        An alias of the default router's 'post' method. The middleware provided
        is called upon a POST HTTP request matching the path.

        Args:
            path (str): The URL path on which the middleware is mounted
            middleware (callable): The middleware function called upon a
                request matching the url
        """
        return self.router.post(path, middleware)

    def put(self, path="/", middleware=None):
        """
        An alias of the default router's 'put' method. The middleware provided
        is called upon a PUT HTTP request matching the path.

        Args:
            path (str): The URL path on which the middleware is mounted
            middleware (callable): The middleware function called upon a
                request matching the url
        """
        return self.router.put(path, middleware)

    def delete(self, path="/", middleware=None):
        """
        An alias of the default router's 'delete' method.
        The middleware provided is called upon a DELETE HTTP request
        matching the path.

        Args:
            path (str): The URL path on which the middleware is mounted
            middleware (callable): The middleware function called upon a
                request matching the url
        """
        return self.router.delete(path, middleware)

    def use(self, middleware=None, path='/', method_mask=HTTPMethod.ALL):
        """
        Use the middleware (a callable with parameters res, req, next) upon
        requests match the provided path. A None path matches every request.
        Returns the middleware so this method may be used as a decorator.

        Args:
            middleware (callable): A function with signature '(req, res)' to be
                called with every request which matches path.
            path (str or regex): Object used to test the requests path. If it
                matches, either by equality or a successful regex match, the
                middleware is called with the req/res pair.
            method_mask (Optional[HTTPMethod]): Filters requests by HTTP
                method. The HTTPMethod enum behaves as a bitmask, so multiple
                methods may be joined by + or \|, removed with -, or toggled
                with ^ (e.g. HTTPMethod.GET + HTTPMethod.POST, HTTPMethod.ALL -
                HTTPMethod.DELETE).

        Returns:
            Returns the provided middleware; a requirement if the use method is
            a decorator.
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
            log.info("%d Using %s on path %s" % (id(self), middleware, path))
            self.middleware.add(path=path,
                                func=middleware,
                                method_mask=method_mask)
        return middleware

    def add_router(self, path, router):
        """
        Adds a router to the list of routers

        Args:
            path (str or regex): The path on which the router binds
            router (growler.Router): The router which will respond to requests

        Raises:
            TypeError: If strict_router_check is True and the router is not an
                instance of growler.Router
        """
        if self.strict_router_check and not isinstance(router, Router):
            raise TypeError("Expected object of type Router, found %r" % type(router))

        log.info("%d Adding router %s on path %s" % (id(self), router, path))
        self.middleware.add(path=path,
                            func=router,
                            method_mask=HTTPMethod.ALL,)

    @property
    def router(self):
        """
        Property returning the router at the top of the middleware chain's
        stack (the last item in the list). If the list is empty OR the item is
        not an instance of growler.Router, one is created and added to the
        middleware chain, matching all requests.
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

    @asyncio.coroutine
    def handle_client_request(self, req, res):
        """
        Entry point for the request + response middleware chain. This is called
        by growler.HTTPResponder (the default responder) after the headers have
        been processed in the begin_application method.

        This iterates over all middleware in the middleware list which matches the client's
        method and path. It executes the middleware and continues iterating until the
        res.has_ended property is true.

        If the middleware raises a GrowlerStopIteration exception, this method immediatly
        returns None, breaking the loop and leaving res without sending any information back to
        the client. Be *sure* that you have another coroutine scheduled that will take over
        handling client data.

        If a middleware function raises any other exception, the exception is forwarded to the
        middleware generator, which changes behavior to generating any error handlers it had
        encountered. This method then calls the handle_server_error method which *should*
        handle the error and notify the user.

        If after the chain is exhausted, either with an exception raised or not, res.has_ended
        does not evaluate to true, the response is sent a simple server error message in text.

        Args:
            req (growler.HTTPRequest): The incoming request, containing all information
                about the client.
            res (growler.HTTPResponse): The outgoing response, containing
                methods for sending headers and data back to the client.
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
                mw_generator.throw(error)
                yield from self.handle_server_error(req, res, mw_generator, error)
                return

            if res.has_ended:
                break

        # TODO: Decide if a 404 exception should be thrown back into the generator somehow.
        #       This is not easy as the generator should be closed at end of for loop. - could
        #       change generator behavior to yield the exception - prompting app to throw it
        #       back.
        if not res.has_ended:
            self.handle_response_not_sent(req, res)

    @asyncio.coroutine
    def handle_server_error(self, req, res, mw_generator, error, err_count=0):
        """
        Entry point for handling an exception that occured during execution of
        the middleware chain. If an

        Args:
            req (growler.HTTPRequest): The incoming request, containing all
                information about the client.
            res (growler.HTTPResponse): The outgoing response, containing
                methods for sending headers and data back to the client.
            mw_generator (Generator): The generator producing middleware. This
                has already been 'notified' of the error and should now only
                yield error handling middleware.
            error (Exception): The exception raised during middleware execution
            err_count (int): A value for keeping track of recursive calls to
                the error handler. If this value equals
                self.error_recursion_max_depth, a new exception is raised,
                potentially confusing everyone involved.
        """
        if err_count >= self.error_recursion_max_depth:
            raise Exception("Too many exceptions:" + error)

        for mw in mw_generator:
            try:
                if asyncio.iscoroutinefunction(mw):
                    yield from mw(req, res, error)
                else:
                    mw(req, res, error)
            except Exception as new_error:
                yield from self.handle_server_error(
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
        Method called upon reaching the end of the middleware chain with no request being sent.
        Default implementation is to simply respond with a 404 error with a text message.
        """
        # res.send_text("404 - Not Found", 404)
        self.handle_404(req, res)

    def print_middleware_tree(self, *, EOL=os.linesep, **kwargs):  # noqa pragma: no cover
        """
        Prints a unix-tree-like output of the structure of the web application
        to the file specified (stdout by default).

        Args:
            EOL (str): The character or string that ends the line
            **kwargs: Arguments pass to the standard print function. This
                allows specifying the file to write to and the ability to flush
                output upon creation.
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
    def default_error_handler(req, res, error:Exception):
        from io import StringIO
        import traceback

        trace = StringIO()
        try: # fixes anomalous error with python3.4
            traceback.print_exc(file=trace)
        except AttributeError:
            pass
        html = ("<html><head><title>500 - Server Error</title></head><body>"
                "<h1>500 - Server Error</h1><hr>"
                "<p style='font-family:monospace;'>"
                "The server encountered an error while processing your request to {path}"
                "</p><pre>{trace}</pre></body></html")
        res.send_html(html.format(path=req.path, trace=trace.getvalue()), 500)

    @staticmethod
    def default_404_handler(req, res, error=None):
        html = ("<html><head><title>404 - Not Found</title></head><body>"
                "<h1>404 - Not Found</h1><hr>"
                "<p style='font-family:monospace;'>"
                "The page you requested: '{path}', could not be found"
                "</p></body></html>")
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
        Returns whether a setting has been enabled. This just casts the
        configuration value to a boolean.

        Args:
            name (str): The name of the the configuration option
        """
        return bool(self.config[name])

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

        Args:
            gen_coroutine (bool): If True, this function only returns the
                coroutine generator returned by self.loop.create_server, else
                it will 'run_until_complete' the generator and return the
                created server object.

            server_config (mixed): These keyword arguments parameters are
                passed directly to the BaseEventLoop.create_server function.
                Consult their documentation for details.

        Returns:
            asyncio.Server: The result of asyncio.BaseEventLoop.create_server
                which has been passed to the event loop and setup with the
                provided parameters. This is returned if gen_coroutine is False
                (default).
            asyncio.coroutine: An asyncio.coroutine which will produce the
                asyncio.Server from the provided configuration parameters. This
                is returned if gen_coroutine is True.
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

        Args:
            **server_config: These keyword arguments are forwarded directly to
                the BaseEventLoop.create_server function. Consult their
                documentation for details.
        """
        self.create_server(**server_config)
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            pass
