#
# growler/middleware/cookieparser.py
#
#

from http.cookies import (SimpleCookie)

import uuid


class CookieParser():

    def __init__(self, opts={}):
        print("[CookieParser]")

    def __call__(self, req, res):
        """Parses cookies"""
        # Do not clobber cookies
        try:
            req.cookies
            return next()
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

    # print ("===", req.headers['cookie'])
    # print ("  Loaded in cookies :", req.cookies)
    # print ("Loaded in cookies quick id :", req.cookies['qid'].value)

        def _send_headers():
            if res.cookies:
                cookie_string = res.cookies.output(sep=res.EOL)
            # print ("RES:", cookie_string)
            res.headerstrings.append(cookie_string)

        res.on_headerstrings(_send_headers)
