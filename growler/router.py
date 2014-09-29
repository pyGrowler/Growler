#
# growler/router.py
#


class Router():
  """
      The router class which contains a tree of routes which a path is chosen to.
  """
  def __init__(self, path = '/'):
    self.path = path
    self.subrouters = []
    self.routes = [];

  def add_router(self, router):
    self.subrouters.append(router)

  def all(self, path = '/', middleware = None):
    """
    The middleware provided is called upon all HTTP requests matching the path.
    """
    if middleware == None: # assume decorator
      def wrap(func):
        self.routes.append(('ALL', path, func))
      return wrap
    self.routes.append(('ALL', path, middleware))

  def get(self, path = '/', middleware = None):
    print (__name__, path)
    self.routes.append(('GET', path, middleware))

  def post(self, path = '/', middleware = None):
    print (__name__, path)
    self.routes.append(('POST', path, middleware))

  def delete(self, path = '/', middleware = None):
    print (__name__, path)
    self.routes.append(('DELETE', path, middleware))

  def use(self, middleware, path = None):
    """
    Use the middleware (a callable with parameters res, req, next) upon requests
    match the provided path. A None path matches every request.
    """
    print("[Router::use] Adding middleware", middleware)
    self.middleware.append(middleware)

  def print_tree(self, prefix = ''):
    for x in self.routes:
      print ("{}{}".format(prefix, x))
    for x in self.subrouters:
      x.print_tree(prefix + "  ")
  
  def match_routes(self, req):
    print ("matching routes to", req)
    for method, path, func in self.routes:
      if method == "ALL" or method.upper() == req.method.upper():
        print ("MATCHED", method, "checking",req.path, path)
        if self.match_path(req.path, path):
          yield func
    yield None

  def match_path(self, request, path):
    return request == path
