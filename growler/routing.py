#
# growler/routing.py
#
"""
Module containing classes that provide the mechanisms of routing
requests to your functions.

These are used by the application, and most code can be written
without directly accessing this.
"""

import re
import logging
from inspect import signature
from collections import OrderedDict
from growler.http import HTTPMethod

ROUTABLE_NAME_REGEX = re.compile(
    "(%s)_.*" % '|'.join([
        "all",
        "get",
        "post",
        "put",
        "delete",
    ]), re.IGNORECASE + re.UNICODE)

logger = logging.getLogger(__name__)


class MiddlewareNode:
    """
    A class representing a node in the MiddlewareChain.
    It contains the actual middleware function, the path this node
    is mounted on, and the 'method mask' which requests must match
    to proceed.
    There are two boolean slots which indicate whether this node
    contains a 'subchain' (i.e. another MiddlewareChain stored in
    func) and if function should be treated as an error handler
    rather than standard middleware.

    A 'subchain' middleware node has the subtree stored as the func
    attribute.
    """

    IGNORE_TRAILING_SLASH = True

    __slots__ = [
        'func',
        'path',
        'mask',
        'is_errorhandler',
        'is_subchain',
    ]

    def __init__(self, **inits):
        """
        The path attribute should be a regular expression.
        If it is a string, it is escaped and then compiled.

        Keyword Args:
            path (String or regex): A regex to be matched upon
                connection Simple mappings to attributes
        """
        for k, v in inits.items():
            if k == 'path' and isinstance(v, str):
                v = self.path_to_regex(v)
            setattr(self, k, v)

    @staticmethod
    def path_to_regex(path):
        """
        Static method wich handles the conversion of a string to the
        regex that will be tested against the incoming request paths.
        """
        # last_slash = '' if path.endswith('/') else '/'
        esc_path = re.escape(path)
        return re.compile(esc_path)

    def matches_method(self, method):
        """
        Method to determine if the http method matches this middleware.
        """
        return self.mask & method

    def path_split(self, path):
        """
        Splits a path into the part matching this middleware and the
        part remaining.
        If path does not exist, it returns a pair of None values.
        If the regex matches the entire pair, the second item in
        returned tuple is None.

        Args:
            path (str): The url to split

        Returns:
            Tuple
            matching_path (str or None): The beginning of the path
                which matches this middleware or None if it does not
                match
            remaining_path (str or None): The 'rest' of the path,
                following the matching part
        """

        match = self.path.match(path)
        if match is None:
            return None, None

        # split string at position
        the_rest = path[match.end():]

        # ensure we split at a '/' character
        if the_rest:
            if match.group().endswith('/'):
                pass
            elif the_rest.startswith('/'):
                pass
            else:
                return None, None

        if self.IGNORE_TRAILING_SLASH and the_rest == '/':
            the_rest = ''

        return match, the_rest


class MiddlewareChain:
    """
    Handles the storage and retrieval of growler middleware functions
    """

    ROOT_PATTERN = re.compile(re.escape('/'))

    def __init__(self):
        self.mw_list = []
        self.log = logging.getLogger("%s:%d" % (__name__, id(self)))

    def __call__(self, method, path):
        """
        Generator yielding the middleware which matches the provided path.

        When called with an HTTP method and path, the middleware
        chain returns a generator object that will walk along the
        chain in a depth-first pattern. Any middleware nodes
        matching both the method code and path are yielded.

        The generator keeps any error handlers encountered walking
        the tree in its internal state. If an error occurs during
        execution of a middleware function, the exception should be
        sent back to the generator via the throw method:
        ``mw_chain.throw(err)``.
        The error handlers will be looped through in reverse order,
        so the most specific handler matching method and path is
        called first.

        If an error occurs during the execution of an error handler,
        it is ignored (for now) until a solution is determined.

        Args:
            method (growler.http.HTTPMethod): The request method which
            path (str): URL path of the request.

        Yields:
            Callable or Coroutine: The next middleware object that
            matches the incoming request

        TODO:
            What to do when the error handler raises a new error?
        """
        error_handler_stack = []

        # loop through all middleware matching the request
        matching_middleware = self.find_matching_middleware(method, path)
        for mw, path_match, rest_url in matching_middleware:

            # If a subchain - loop through middleware
            if mw.is_subchain:

                # We need to call sub middleware with only the URL past the
                # matching string
                subpath = '/' + rest_url

                # middleware func is the generator of sub-middleware
                subchain = mw.func(method, subpath)

                # loop through subchain
                yield from self.iterate_subchain(subchain)

            # add to list of error handlers
            elif mw.is_errorhandler:
                error_handler_stack.append(mw.func)

            # Found a matching request! yield result function
            else:
                try:
                    # Yield the middleware function back to application
                    yield mw.func

                # exception means application threw something back at us
                except Exception as err:
                    # Yielding None here returns execution to the caller,
                    # allowing it to request error handling middleware from us
                    yield None
                    # redirect all other requests to the handle_error loop
                    yield from self.handle_error(err, error_handler_stack)
                    break

    def find_matching_middleware(self, method, path):
        """
        Iterator handling the matching of middleware against a
        method+path pair.

        Yields the middleware, matching path, and the remaining url
        """
        for mw in self.mw_list:
            if not mw.matches_method(method):
                continue

            # get the path matching this middleware and the 'rest' of the url
            # (i.e. the part that comes AFTER the match) to be potentially
            # matched later by a subchain
            path_match, rest_url = mw.path_split(path)
            if self.should_skip_middleware(mw, path_match, rest_url):
                continue

            yield mw, path_match, rest_url

    def iterate_subchain(self, chain):
        """
        A coroutine used by __call__ to forward all requests to a
        subchain.
        """
        for mw in chain:
            try:
                yield mw
            except Exception as err:
                yield chain.throw(err)

    def handle_error(self, error, err_handlers):
        self.log.error(error)
        for errhandler in reversed(err_handlers):
            try:
                yield errhandler
            except Exception:  # except Exception as new_error:
                yield None

    def should_skip_middleware(self, middleware, matching, rest):
        """
        Method used to determine if middleware should be called.
        Returns True (should skip) only if matching evaluates to
        False (no match), otherwise the standard MiddlewareChain
        returns any matching request.
        The Router overrides this and the *entire* request must be
        matched to warrant yielding a function.
        This method was factored out of __call__ so it may be
        overriden with custom logic without reimplementing the whole
        __call__ method.

        Args:
            middleware (MiddlewareNode):

        """
        return bool(not matching)

    def add(self, method_mask, path, func):
        """
        Add a function to the middleware chain.
        This function is returned when iterating over the chain with
        matching method and path.

        Args:
            method_mask (growler.http.HTTPMethod): A bitwise mask
                intended to match specific request methods
            path (str or regex): An object with which to compare
                request urls
            func (callable): The function to be yieled from the
                generator upon a request matching the method_mask
                and path
        """
        is_err = len(signature(func).parameters) == 3
        is_subchain = isinstance(func, MiddlewareChain)
        tup = MiddlewareNode(
            func=func,
            mask=method_mask,
            path=path,
            is_errorhandler=is_err,
            is_subchain=is_subchain,
        )
        self.mw_list.append(tup)

    def __contains__(self, func):
        """
        Returns whether the function is stored anywhere in the
        middleware chain.

        This runs recursively though any subchains.

        Args:
            func (callable): A function which may be present in the
                chain

        Returns:
            bool: True if func is a function contained anywhere in
                the chain.
        """
        return any((func is mw.func) or (mw.is_subchain and func in mw.func)
                   for mw in self.mw_list)

    def count_all(self):
        """
        Returns the total number of middleware in this chain and subchains.
        """
        return sum(x.func.count_all() if x.is_subchain else 1 for x in self)

    def __len__(self):
        """
        Returns the number of middleware contained in the root of
        this chain.
        To count the number of middleware, included in subchains, use
        count_all().
        """
        return len(self.mw_list)

    def __iter__(self):
        """
        Iterates directly through the middleware chain. Does not
        enter any subchains.
        """
        return iter(self.mw_list)

    def __reversed__(self):
        """
        Iterates directly through the middleware chain, starting
        from the bottom.
        Does not enter any subchains along the way.
        """
        return reversed(self.mw_list)

    def first(self):
        """
        Returns first element in list.

        Returns:
            MiddlewareNode: The first middleware in the chain.

        Raises:
            IndexError: If the chain is empty
        """
        return self.mw_list[0]

    def last(self):
        """
        Returns last element in list.

        Returns:
            MiddlewareNode: The last middleware stored in the chain.

        Raises:
            IndexError: If the chain is empty
        """
        return self.mw_list[-1]


class Router(MiddlewareChain):
    """
    The router class holds all the 'routes': callbacks connected
    assigned to HTTP method and regular expression pairs.
    If a regex matches with the request's path member, the callback
    is called with the req, res pair.

    Routes are added on a per-method basis, using the
    :code:`router.*method*(path, cb)` syntax, for example:

    >>> router.get("/home", cb)

    will call cb(req, res) upon every incoming HTTP connection with
    the request line: ``GET /home HTTP/1.1``.
    To catch all methods, use the ``router.all`` member.

    Routers can be linked together in a tree-like structure using the
    `use` method enabling components of websites can be developed in
    their own "namespace" and mounted to the website on its own path:

    >>> blog_router.get("/list", ...)
    >>> blog_router.post("/new_post", ...)
    >>> root_router.use("/blog", blog_router)

    The default growler.App has its root router at self.router, and
    offers convience aliases to automatically add routes:
    >>> app.get(..) == app.router.get(...)
    """
    sinatra_param_regex = re.compile(r":(\w+)")
    regex_type = type(sinatra_param_regex)

    def __init__(self):
        super().__init__()
        self.log = logger.getChild("id=%x" % id(self))
        self.add_route = self.add

    def add_router(self, path, router):
        """
        Add a (regex, router) pair to this router. Any req.path that
        matches the regex will pass the request/response objects to
        that router.
        """
        self.add(HTTPMethod.ALL, path, router)
        return self

    def _add_route(self, method, path, middleware=None):
        """The implementation of adding a route"""
        if middleware is not None:
            self.add(method, path, middleware)
            return self
        else:

            def addroute_decorator(func):
                """
                Function called when _add_route is used as a decorator
                """
                self.add(method, path, func)
                return func

            return addroute_decorator

    def all(self, path, middleware=None):
        """ Matches all HTTP requests """
        return self._add_route(HTTPMethod.ALL, path, middleware)

    def get(self, path, middleware=None):
        """ Matches "GET" HTTP request """
        return self._add_route(HTTPMethod.GET, path, middleware)

    def post(self, path, middleware=None):
        """ Matches "POST" HTTP request """
        return self._add_route(HTTPMethod.POST, path, middleware)

    def put(self, path, middleware=None):
        """ Matches "PUT" HTTP request """
        return self._add_route(HTTPMethod.PUT, path, middleware)

    def delete(self, path, middleware=None):
        """ Matches "DELETE" HTTP request """
        return self._add_route(HTTPMethod.DELETE, path, middleware)

    def use(self, middleware, path=None):
        """
        Call the provided middleware upon requests matching the path.
        If path is not provided or None, all requests will match.

        Args:
            middleware (callable): Callable with the signature
                ``(res, req) -> None``
            path (Optional[str or regex]): a specific path the
                request must match for the middleware to be called.
        Returns:
            This router
        """
        self.log.info(" Using middleware %r", middleware)
        if path is None:
            path = MiddlewareChain.ROOT_PATTERN
        self.add(HTTPMethod.ALL, path, middleware)
        return self

    def match_routes(self, req):
        """
        Yields a sequence of 'route' functions which match the path
        in the request.
        """
        return self(req.method, req.path)

    def iter_routes(self):
        for mw in self.mw_list:
            yield (mw.mask, mw.path, mw.func)

    def should_skip_middleware(self, middleware, matching, rest) -> bool:
        """
        Returns True (i.e. should skip) if request does not match the
        entire middleware path.
        This is a simple check if 'rest' is truthy or not.
        """
        return bool(not matching) or bool(rest)

    @property
    def routes(self):
        return tuple(self.iter_routes())

    @property
    def subrouters(self):
        """
        Generator of sub-routers (middleware inheriting from Router)
        contained within this router.
        """
        yield from filter(lambda mw: isinstance(mw.func, Router), self.mw_list)

    @classmethod
    def sinatra_path_to_regex(cls, path):
        """
        Converts a sinatra-style path to a regex with named
        parameters.
        """
        # Return the path if already a (compiled) regex
        if type(path) is cls.regex_type:
            return path

        # Build a regular expression string which is split on the '/' character
        regex = [
            r"(?P<{}>\w+)".format(segment[1:])
            if cls.sinatra_param_regex.match(segment) else segment
            for segment in path.split('/')
        ]
        return re.compile('/'.join(regex))


class RouterMeta(type):
    """
    A metaclass for classes that should automatically be converted
    into growler application routers.
    The only feature this metaclass includes right now is
    providing an ordered dictionary of members, allowing guarenteed
    route placement.
    """
    @classmethod
    def __prepare__(metacls, name, bases, **kargs):
        """
        Metaclass attribute which creates the mapping object - in
        this case a standard :class:`collections.OrderedDict` object
        to preserve order of method names.

        Args:
            name (str): The name of the class
            base (tuple): Collection of baseclasses
        Return:
            Simple ordered dict to store the class members/methods
        """
        return OrderedDict()

    def __new__(cls, name, bases, classdict):
        """
        Creates the class type, adding an additional attributes
        __ordered_attrs__, a snapshot of the dictionary keys, and
        __growler_router, a method which will generate a growler.Router
        object.
        """
        child_class = type.__new__(cls, name, bases, classdict)

        def build_router(self):
            router = Router()

            routes = get_routing_attributes(self, keys=classdict.keys())
            for method, path, func in routes:
                router.add(method, path, func)
            self.__growler_router = router
            return router

        child_class.__growler_router = build_router
        return child_class


def _find_routeable_attributes(obj, keys):
    """
    From the set of provided `keys`, this function yields the attributes
    of `obj` that fulfill the requirements of 'routeable':
    * callable
    * matched by ROUTABLE_NAME_REGEX
    * has docstring

    """
    for attr in keys:
        matches = ROUTABLE_NAME_REGEX.match(attr)
        if matches is None:
            continue
        try:
            val = getattr(obj, attr)
        except AttributeError:
            continue

        if not callable(val) or val.__doc__ is None:
            continue

        method_name = matches.group(1).upper()
        yield val, method_name


def get_routing_attributes(obj, modify_doc=False, keys=None):
    """
    Loops through the provided object (using the dir() function) and
    finds any callables which match the name signature (e.g.
    get_foo()) AND has a docstring beginning with a path-like char
    string.
    This does process things in alphabetical order (rather than than
    the unpredictable __dict__ attribute) so take this into
    consideration if certain routes should be checked before others.
    Unfortunately, this is a problem because the 'all' method will
    always come before others, so there is no capturing one type
    followed by a catch-all 'all'. Until a solution is found, just
    make a router by hand.
    """
    if keys is None:
        keys = dir(obj)

    for val, method_str in _find_routeable_attributes(obj, keys):

        path, *doc = val.__doc__.split(maxsplit=1) or ('', '')

        if not path:
            continue

        if modify_doc:
            val.__doc__ = ''.join(doc)

        method = HTTPMethod[method_str]

        yield method, path, val


def routerclass(cls):
    """
    A class decorator which parses a class, looking for an member
    functions which match an HTTP verb (get, post, etc) followed by
    an underscore and other letters, with a signature of two
    parameters (req and res). For example
    .. code: python

        def get_index(req, res):
            ...

    To determine the path to take, the string looks at the first
    complete word of a stripped docstring, passing this in to the
    'path matching algorithm'.
    The order wich the methods are defined are the order the requests
    will attempt to match.
    """
    logging.debug("Creating a routerclass with the class %s" % cls)
    cls.__growler_router = lambda self: routerify(self)
    return cls


def routerify(obj):
    """
    Scan through attributes of object parameter looking for any which
    match a route signature.
    A router will be created and added to the object with parameter.

    Args:
        obj (object): The object (with attributes) from which to
            setup a router

    Returns:
        Router: The router created from attributes in the object.
    """
    router = Router()
    for info in get_routing_attributes(obj):
        router.add_route(*info)
    obj.__growler_router = router
    return router
