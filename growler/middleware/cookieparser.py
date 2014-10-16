#
# growler/middleware/cookieparser.py
#
#

from http.cookies import (SimpleCookie)

from . import middleware
import uuid

@middleware
class CookieParser():

  def __init__(self, opts = {}):
    print ("[CookieParser]")


  def __call__(self, req, res, next):
    """Parses cookies"""
    # Do not clobber cookies
    try:
      req.cookies
      return next()
    except AttributeError:
      print ("Caught req.cookies")
      req.cookies = SimpleCookie()

    # Create an empty cookie state
    print ("Headers", req.headers)

    # If the request had a cookie, load it!
    if 'cookie' in req.headers.keys():
      req.cookies.load(req.headers['cookie'])
    else:
      req.cookies['qid'] = uuid.uuid4()

    print ("Loaded in cookies :", req.cookies)
    return next()
