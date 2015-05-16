#
# growler/middleware/cookieparser.py
#
#

from http.cookies import (SimpleCookie)

import uuid


class CookieParser():
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
        print("[CookieParser]", opts)
        self.opts = opts

    def __call__(self, req, res):
        """
        Parses cookies of the header request (using the 'cookie' header key)
        and adds a callback to the 'on_headerstrings' response event.
        """
        # Do not clobber cookies
        try:
            req.cookies
            return None
        except AttributeError:
            # Create an empty cookie state
            req.cookies = SimpleCookie()
            res.cookies = SimpleCookie()

        # print ("[CookieParser]")
        # print ("   Headers", req.headers)

        # If the request had a cookie, load it!
        if 'cookie' in req.headers.keys():
            req.cookies.load(req.headers['cookie'])
        else:
            req.cookies["fig"] = "newton"

        if 'qid' not in req.cookies:
            req.cookies['qid'] = uuid.uuid4()
            res.cookies['qid'] = uuid.uuid4()

        def _send_headers():
            if res.cookies:
                cookie_string = res.cookies.output(sep=res.EOL)
                res.headerstrings.append(cookie_string)

        res.on_headerstrings(_send_headers)
