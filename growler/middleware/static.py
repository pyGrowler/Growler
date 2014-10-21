#
# growler/middleware/static.py
#


import asyncio
import os
import mimetypes

# @middleware
class Static():
  """
    Static middleware catches any uri paths which match a filesystem file and
    serves that file.
  """
  def __init__(self, path):
    self.path = os.path.abspath(path) # os.getcwd() + path
    print ("[Static] Serving static files out of {}".format(self.path))
    if not os.path.exists(self.path):
      print ("[Static] Error:", "No path exists at {}".format(self.path))
      raise Exception("Path '{}' does not exist.".format(self.path))

  @asyncio.coroutine
  def __call__(self, req, res):
    print ("[Static] ", req.path)
    filename = self.path + req.path
    if os.path.isfile(filename):
      mime = mimetypes.guess_type(filename)
      print ("  Found: {} ({})".format(filename, mime[0]))
      res.set_type(mime[0])
      res.send_file(self.path + req.path)
      print ("  DONE!")
