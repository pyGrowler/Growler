#
# growler/middleware/logger.py
#

from . import middleware

import growler

@middleware
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

  def info(self, message):
    return " {} info {} - {} ".format(self.CYAN, self.DEFAULT, message)

  def warn(self, message):
    return " {} warning {} - {} ".format(self.YELLOW, self.DEFAULT, message)

  def error(self, message):
    return " {} error {} - {} ".format(self.RED, self.DEFAULT, message)

  def critical_error(self, message):
    return " {} ERROR {} - {} ".format(self.RED, self.DEFAULT, message)

  def __call__(self, req, res, next):
    print (self.info("Connection from {}".format(req.ip)))
    next()

  @middleware
  def mw(self, req, res, next):
    print("[mw] % %" % (req, res))

