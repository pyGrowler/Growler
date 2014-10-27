#!/usr/bin/env python3
#
# Example1 - DefaultSession
#

import os
import asyncio

from growler import (App)
from growler.middleware import (Logger, Static, CookieParser, DefaultSessionStorage)

app = App('GrowlerServer', {'host':'127.0.0.1', 'port': 8000})

app.use(Logger())
app.use(CookieParser())
app.use(DefaultSessionStorage())

@app.get('/')
def index(req, res):
  req.session['counter'] = int(req.session.get('counter', -1)) + 1
  print(" -- Session '{}' returned {} times".format(req.session['id'], req.session['counter']))
  res.send_text("Hello!! You've been here [[{}]] times".format(req.session['counter']))
  req.session.save()

app.run()
