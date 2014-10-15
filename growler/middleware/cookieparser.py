#
# growler/middleware/cookieparser.py
#
#

from http.cookies import (SimpleCookie)

from . import middleware

@middleware
def CookieParser(self, req, res, next):
  """Parses cookies"""
  # Do not clobber cookies
  if req.cookies: return next()

  # Create an empty cookie state
  req.cookies = SimpleCookie()

  # If the request had a cookie, load it!
  if 'cookie' in req.headers.keys():
    req.cookies.load(req.headers['cookie'])

  print ("Loaded in cookies :", req.cookies)
  return next()
