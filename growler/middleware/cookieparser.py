#
# growler/middleware/cookieparser.py
#
#

from http.cookies import SimpleCookie
import logging
import json

log = logging.getLogger(__name__)


class CookieParser:
    """
    Middleware which adds a 'cookies' attribute to requests, which is a
    standard library http.cookies.SimpleCookie object, allowing dict like
    access to session variables.

    This adds a 'on_headerstrings' event to the response, so the cookies will
    be serialized and sent back to the client.

    If the request already has a cookie attribute, this does nothing.
    """

    def __init__(self, **opts):
        """
        Construct a CookieParser with optional 'opts' keyword arguments. These
        do nothing currently except get stored in the CookieParser.opts
        attribute.
        """
        log.info("%d built with %s" % (id(self), json.dumps(opts)))
        self.opts = opts

    def __call__(self, req, res):
        """
        Parses cookies of the header request (using the 'cookie' header key)
        and adds a callback to the 'on_headerstrings' response event.
        """
        # Do not clobber cookies
        try:
            log.info("%d built with %s" % (id(self), json.dumps(self.opts)))
            req.cookies
            return None
        except AttributeError:
            # Create an empty cookie state
            req.cookies, res.cookies = SimpleCookie(), SimpleCookie()

        # If the request had a cookie, load it!
        if 'COOKIE' in req.headers:
            req.cookies.load(req.headers['COOKIE'])

        def _gen_cookie():
            if res.cookies:
                cookie_string = res.cookies.output(header='', sep=res.EOL)
                return cookie_string

        res.headers['Set-Cookie'] = _gen_cookie
