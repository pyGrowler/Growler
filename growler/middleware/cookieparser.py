#
# growler/middleware/cookieparser.py
#
#

from http.cookies import (SimpleCookie)

from . import middleware
import uuid

# @middleware
class CookieParser():

  def __init__(self, opts = {}):
    print ("[CookieParser]")


  def __call__(self, req, res):
    """Parses cookies"""
    # Do not clobber cookies
    try:
      req.cookies
      return next()
    except AttributeError:
      # Create an empty cookie state
      print ("Caught req.cookies")
      req.cookies = SimpleCookie()
      req.cookies["fig"] = "newton"

    print ("Headers", req.headers)
    print ("Has Cookie ::", 'cookie' in req.headers.keys())
    print ("Fig ::", req.cookies["fig"].value)

    # If the request had a cookie, load it!
    if 'cookie' in req.headers.keys():
      req.cookies.load(req.headers['cookie'])

    if not 'qid' in req.cookies:
      req.cookies['qid'] = uuid.uuid4()

    print ("Loaded in cookies :", req.cookies)
    print ("Loaded in cookies quick id :", req.cookies['qid'].value)
