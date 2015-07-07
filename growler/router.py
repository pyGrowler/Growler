#
# growler/router.py
#

import re
from growler.http.errors import HTTPErrorNotFound


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
        self.routes.append((method, path, endpoint))
        return self

    def all(self, path='/', middleware=None):
        """
        The middleware provided is called upon all HTTP requests matching the
        path.
        """
        if middleware is None:  # assume decorator
            def wrap(func):
                self.routes.append(('ALL', path, func))
            return wrap
        else:
            self.routes.append(('ALL', path, middleware))
        return self

    def get(self, path='/', middleware=None):
        """Add a route in response to the GET HTTP method."""

        # Handle explicit and decorator calls
        if middleware is not None:
            return self.add_route('GET', path, middleware)
        else:
            return lambda func: self.add_route('GET', path, func)

    def post(self, path='/', middleware=None):
        """Add a route in response to the POST HTTP method."""
        if middleware is not None:
            return self.add_route('POST', path, middleware)
        else:
            return lambda func: self.add_route('POST', path, func)

    def delete(self, path='/', middleware=None):
        """Add a route in response to the DELETE HTTP method."""
        if middleware is not None:
            return self.add_route('DELETE', path, middleware)
        else:
            return lambda func: self.add_route('DELETE', path, func)

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
        print("matching routes to path '{}'".format(req.path))
        print(" (# routes: %d)" % len(self.routes))
        for method, path, func in self.routes:
            if method == "ALL" or method.upper() == req.method.upper():
                print("MATCHED method", method)
                if self.match_path(req.path, path):
                    print("MATCHED path", req.path, path, ' yielding', func)
                    yield func
        print("End of match_routes")
        return None

    def match_path(self, request, path):
        return request == path

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
    print("DEBUG: Creating a routerclass with class", cls)
    regex = re.compile("(get|post|delete)_.*", re.IGNORECASE)
    router = Router()
    router_dict = {
        'get': router.get,
        'post': router.post,
        'delete': router.delete
    }

    for name, val in cls.__dict__.items():
        routeable = regex.match(name)
        if routeable is None or val.__doc__ is None:
            continue
        func = router_dict[routeable.group(1).lower()]
        path = val.__doc__.strip().split(' ', 1)[0]
        func(path=path, middleware=val)
    cls.__growler_router = router
    return cls
