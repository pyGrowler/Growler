
from os import path

import asyncio

from growler import (App)
from growler.middleware import (Logger, Static, Renderer, Timer)

this_dir = path.dirname(__file__)

app = App('GrowlerServer', {'host':'127.0.0.1', 'port': 8000})

app.use(Logger())
app.use(Timer())
app.use(Renderer(path.join(this_dir, "views"), "jade"))
app.use(lambda i,o: o.locals.update({'user': {"name": "Arthur"}}))

@app.get('/')
def index(req, res):
  res.render("home", {'title': "Programmed Title!"})

@app.get('/hello')
def hello_world(req, res):
  res.send_text("Hello World!!")

app.run()
