#
# growler/middleware/logger.py
#

class Logger():
  
  DEFAULT = '/033[30m'
  RED     = '/033[31m'
  GREEN   = '/033[32m'
  YELLOW  = '/033[33m'
  BLUE    = '/033[34m'
  MAGENTA = '/033[35m'
  CYAN    = '/033[36m'
  WHITE   = '/033[37m'

  def __init__(self):
    pass

  def __call__(self, req, res, next):
    print (" {} info {} - Connection from {} ".format(self.CYAN, self.DEFAULT, req.ip))
    next()
