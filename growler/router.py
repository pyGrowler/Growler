#
# growler/router.py
#


class Router():
  """
  The router class which contains a tree of routes which a path is chosen to.
  """
  def __init__(self, path = '/'):
    """Create a router mounted at 'path'"""
    self.path = path
    self.subrouters = []
    self.routes = [];

  def add_router(self, router):
    """Add a router to the list of subrouters."""
    self.subrouters.append(router)

  def all(self, path = '/', middleware = None):
    """
    The middleware provided is called upon all HTTP requests matching the path.
    """
    if middleware == None: # assume decorator
      def wrap(func):
        self.routes.append(('ALL', path, func))
      return wrap
    else:
      self.routes.append(('ALL', path, middleware))
    return self

  def get(self, path = '/', middleware = None):
    """Add a route in response to the GET HTTP method."""
    print (__name__, path)
    if middleware == None: # assume decorator
      def wrap(func):
        self.routes.append(('GET', path, func))
      return wrap
    else:
      self.routes.append(('GET', path, middleware))
    return self

  def post(self, path = '/', middleware = None):
    """Add a route in response to the POST HTTP method."""
    print (__name__, path)
    self.routes.append(('POST', path, middleware))
    return self

  def delete(self, path = '/', middleware = None):
    """Add a route in response to the DELETE HTTP method."""
    print (__name__, path)
    self.routes.append(('DELETE', path, middleware))
    return self

  def use(self, middleware, path = None):
    """
    Use the middleware (a callable with parameters res, req, next) upon requests
    match the provided path. A None path matches every request.
    """
    print("[Router::use] Adding middleware", middleware)
    self.middleware.append(middleware)
    return self

  def print_tree(self, prefix = ''):
    for x in self.routes:
      print ("{}{}".format(prefix, x))
    for x in self.subrouters:
      x.print_tree(prefix + "  ")
  
  def match_routes(self, req):
    print ("matching routes to path '{}'".format(req.path))
    print ("# routes: ",len(self.routes))
    for method, path, func in self.routes:
      if method == "ALL" or method.upper() == req.method.upper():
        print ("MATCHED method ", method)
        if self.match_path(req.path, path):
          print ("MATCHED path", req.path, path, ' yielding', func)
          yield func
    yield None

  def match_path(self, request, path):
    return request == path
