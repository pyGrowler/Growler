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
    self.routes = {};

  def add_router(self, router):
    self.subrouters.append(router)

  def get(self, middleware, path):
    print (__name__, path)

  def post(self, middleware, path):
    print (__name__, path)

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
  