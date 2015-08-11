#
# growler/router.py
#

import re
from collections import OrderedDict
from growler.http.errors import HTTPErrorNotFound

ROUTABLE_NAME_REGEX = re.compile("(all|get|post|delete)_.*", re.IGNORECASE)


class Router():
    """
    The router class holds all the 'routes': callbacks connected assigned to
    HTTP method and regular expression pairs. If a regex matches with the
    request's path member, the callback is called with the req, res pair.

    Routes are added on a per-method basis, using the router.*method*(path, cb)
    syntax, for example:
        router.get("/home", cb)
    will call cb(req, res) upon every incoming HTTP connection with the request
    line: GET /home HTTP/1.1. To catch all methods, use the 'router.all'
    member.

    Routers can be linked together in a tree-like structure using the member
    'use'. so components of websites can be developed in their own "namespace"
    and mounted to the website on its own path:
        blog_router.get("/list", ...)
        blog_router.post("/new_post", ...)

        root_router.use("/blog", blog_router)

    The default growler.App has its root router at self.router, and offers
    convience aliases to automatically add routes:
        app.get(..) == app.router.get(...)
    """
    sinatra_param_regex = re.compile(":(\w+)")
    regex_type = type(sinatra_param_regex)

    def __init__(self):
        """Create a router"""
        self.subrouters = []
        self.routes = []

    def __call__(self, req, res):
        """
        To call a router is to treat it as middleware...
        ...this is not implemented yet.
        """
        raise NotImplemented

    def add_router(self, path, router):
        """
        Add a (regex, router) pair to the list of subrouters. Any req.path that
        matches the regex will pass the request/response objects to that
        router.
        """
        self.subrouters.append((re.compile(path), router))

    def add_route(self, method, path, endpoint):
        """
        """
        self.routes.append((method, re.compile(path), endpoint))
        return self

    def _apply_decorator(self, method, path):
        """
        An internal function used when adding a route via a decorator instead
        of the 'standard' function call. This is needed so we can return the
        router in the add_route method, but return the original function when
        decorating (else the decorated function name becomes this router!)
        """
        def wrapper(func):
            self.add_route(method, path, func)
            return func
        return wrapper

    def all(self, path='/', middleware=None):
        """
        The middleware provided is called upon all HTTP requests matching the
        path.
        """
        if middleware is not None:
            return self.add_route('ALL', path, middleware)
        else:
            return self._apply_decorator('ALL', path)

    def get(self, path='/', middleware=None):
        """Add a route in response to the GET HTTP method."""
        # Handle explicit and decorator calls
        if middleware is not None:
            return self.add_route('GET', path, middleware)
        else:
            return self._apply_decorator('GET', path)

    def post(self, path='/', middleware=None):
        """Add a route in response to the POST HTTP method."""
        if middleware is not None:
            return self.add_route('POST', path, middleware)
        else:
            return self._apply_decorator('POST', path)

    def delete(self, path='/', middleware=None):
        """Add a route in response to the DELETE HTTP method."""
        if middleware is not None:
            return self.add_route('DELETE', path, middleware)
        else:
            return self._apply_decorator('DELETE', path)

    def use(self, middleware, path=None):
        """
        Use the middleware (a callable with parameters res, req, next) upon
        requests match the provided path. A None path matches every request.
        """
        print("[Router::use] Adding middleware", middleware)
        self.middleware.append(middleware)
        return self

    def print_tree(self, prefix=''):
        for x in self.subrouters:
            x.print_tree(prefix + "  ")

    def match_routes(self, req):
        """
        Yields a sequence of 'route' functions which match the path in the
        request.
        """
        print("matching routes to path '{}'".format(req.path))
        print(" (# routes: %d)" % len(self.routes))
        for method, path, func in self.routes:
            if method == "ALL" or method.upper() == req.method.upper():
                print("MATCHED method", method)
                print("path", req.path, path, req.path == path)
                if self.match_path(req.path, path):
                    print("MATCHED path", req.path, path, ' yielding', func)
                    yield func

        for mount_point, sub_router in self.subrouters:
            print("trying subrouter", sub_router, 'at', mount_point)
            print(mount_point, '??', req.path)
            matches = mount_point.match(req.path)
            print("matches>", matches)
            if matches:
                print('matches', matches)
                req.path = req.path[matches.span()[1]:]
                for submatch in sub_router.match_routes(req):
                    print("==", submatch)
                    yield submatch
        print("End of match_routes")
        return None

    def match_path(self, request, path):
        # return request == path
        return path.fullmatch(request)

    def middleware_chain(self, req):
        """
        A generator that yields a series of middleware which are appropriate
        for the request 'req', provided.
        """
        matches = 0
        for route in self.match_routes(req):
            matches += 1
            yield route
        if matches == 0:
            raise HTTPErrorNotFound()

    @classmethod
    def sinatra_path_to_regex(cls, path):
        """
        Converts a sinatra-style path to a regex with named parameters.
        """
        # Return the path if already a (compiled) regex
        if type(path) is cls.regex_type:
            return path

        # Build a regular expression string which is split on the '/' character
        regex = [
            "(?P<{}>\w+)".format(segment[1:])
            if cls.sinatra_param_regex.match(segment)
            else segment
            for segment in path.split('/')
        ]
        return re.compile('/'.join(regex))


class RouterMeta(type):
    """
    A metaclass for classes that should automatically be converted into growler
    application routers. The only feature this metaclass includes right now is
    providing an ordered dictionary of members, allowing guarenteed route
    placement.
    """

    @classmethod
    def __prepare__(metacls, name, bases, **kargs):
        """
        Metaclass attribute which creates the mapping object - in this case the
        a standard collections.OrderedDict object to preserve order of method
        names. Name is the name of the class, bases are baseclasses, kargs are
        any keyword arguments we may provide in the future for fun options.
        """
        return OrderedDict()

    def __new__(cls, name, bases, classdict):
        """
        Creates the class type, adding an additional attributes
        __ordered_attrs__, a snapshot of the dictionary keys, and
        __growler_router, a method which will generate a growler.Router
        """
        child_class = type.__new__(cls, name, bases, classdict)

        def build_router(self):
            router = Router()
            # should keys be instead classdict.keys()
            nxt = get_routing_attributes(self, keys=self.__ordered_attrs__)
            for method, path, func in nxt:
                getattr(router, method)(path=path, middleware=func)
            self.__growler_router = router
            return router

        child_class.__ordered_attrs__ = classdict.keys()
        child_class.__growler_router = build_router
        return child_class


def get_routing_attributes(obj, modify_doc=False, keys=None):
    """
    Loops through the provided object (using the dir() function) and finds any
    callables which match the name signature (e.g. get_foo()) AND has a
    docstring beginning with a path-like char string. This does process things
    in alphabetical order (rather than than the unpredictable __dict__
    attribute) so take this into consideration if certain routes should be
    checked before others. Unfortunately, this is a problem because the 'all'
    method will always come before others, so there is no capturing one type
    followed by a catch-all 'all'. Until a solution is found, just make a
    router by hand.
    """
    for attr in dir(obj) if keys is None else keys:
        matches = ROUTABLE_NAME_REGEX.match(attr)
        val = getattr(obj, attr)
        if matches is None or not callable(val):
            continue
        try:
            if modify_doc:
                path, val.__doc__ = val.__doc__.split(maxsplit=1)
            else:
                path = val.__doc__.split(maxsplit=1)[0]
        except AttributeError:
            continue
        if path == '':
            continue
        method = matches.group(1).lower()
        yield method, path, val


def routerclass(cls):
    """
    A class decorator which parses a class, looking for an member functions
    which match an HTTP verb (get, post, etc) followed by an underscore and
    other letters, with a signature of two parameters (req and res) (e.g.
        def get_index(req, res):
            ...
    ).
    To determine the path to take, the string looks at the first complete word
    of a stripped docstring, passing this in to the 'path matching algorithm'
    The order wich the methods are defined are the order the requests will
    attempt to match.
    """
    print("DEBUG: Creating a routerclass with the class", cls)
    cls.__growler_router = lambda self: routerify(self)
    return cls


def routerify(obj):
    """
    Scan through attributes of object parameter looking for any which match a
    route signature. A router will be created and added to the object with
    parameter.

    :param obj: some object (with attributes) from which to setup a router
    @return router: The router created.
    """
    router = Router()

    for method, path, func in get_routing_attributes(obj):
        getattr(router, method)(path=path, middleware=func)

    obj.__growler_router = router
    return router
