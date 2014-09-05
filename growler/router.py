
class Router():
  
  def __init__(self):
    pass

  def get(self, middleware, path):
    print 

  def use(self, middleware, path = None):
    """
    Use the middleware (a callable with parameters res, req, next) upon requests
    match the provided path. A None path matches every request.
    """
    print("[Router::use] Adding middleware", middleware)
    self.middleware.append(middleware)

