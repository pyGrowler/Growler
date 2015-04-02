#
# growler/middleware/auth.py
#

class Auth():

  """
    Authentication middleware used to log users or validate
    services.
  """
  def __init__(self):
    print ("[Auth]")

  def __call__(self, req, res):
    """Unimplemented middleware to be overloaded by subclasses"""
    raise NotImplementedError()
