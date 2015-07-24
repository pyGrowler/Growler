#!/usr/bin/env python3
#
# Example1 - DefaultSession
#

from growler import (App)
from growler.middleware import (
    Logger,
    CookieParser,
    DefaultSessionStorage
)

app = App('Example1_Server')

app.use(Logger())
app.use(CookieParser())
app.use(DefaultSessionStorage())


@app.get('/')
def index(req, res):
    """
    Return root page of website.
    """
    req.session['counter'] = int(req.session.get('counter', -1)) + 1
    print(" -- Session '{}' returned {} times".format(req.session['id'],
                                                      req.session['counter']))
    msg = "Hello!! You've been here [[%s]] times" % (req.session['counter'])
    res.send_text(msg)
    req.session.save()

app.create_server_and_run_forever(host='127.0.0.1', port=8000)
