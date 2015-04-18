#
# growler/router.py
#

import re


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
            return lambda func: do_get('GET', path, func)

    def post(self, path='/', middleware=None):
        """Add a route in response to the POST HTTP method."""
        if middleware is not None:
            return self.add_route('POST', path, middleware)
        else:
            return lambda func: do_get('POST', path, func)

    def delete(self, path='/', middleware=None):
        """Add a route in response to the DELETE HTTP method."""
        if middleware is not None:
            return self.add_route('DELETE', path, middleware)
        else:
            return lambda func: do_get('DELETE', path, func)

    def use(self, middleware, path=None):
        """
        Use the middleware (a callable with parameters res, req, next) upon
        requests match the provided path. A None path matches every request.
        """
        print("[Router::use] Adding middleware", middleware)
        self.middleware.append(middleware)
        return self

    def print_tree(self, prefix=''):
        for x in self.routes:
            print("{}{}".format(prefix, x))
        for x in self.subrouters:
            x.print_tree(prefix + "  ")

    def match_routes(self, req):
        print("matching routes to path '{}'".format(req.path))
        print("# routes: ", len(self.routes))
        for method, path, func in self.routes:
            if method == "ALL" or method.upper() == req.method.upper():
                print("MATCHED method ", method)
                if self.match_path(req.path, path):
                    print("MATCHED path", req.path, path, ' yielding', func)
                    yield func

    def match_path(self, request, path):
        return request == path

    def middleware_chain(self, req):
        """
        A generator that yields a series of middleware which are appropriate
        for the request 'req', provided.
        """
        print("req", req.originalURL)
        yield from self.match_routes(req)
