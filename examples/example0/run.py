
import os

import asyncio

from growler import (App)
from growler.middleware import (Logger, Static, Renderer, Timer)

app = App('GrowlerServer', {'host':'127.0.0.1', 'port': 8000})

app.use(Logger())
app.use(Timer())
app.use(Renderer(os.path.dirname(os.path.relpath(__file__)) + "/views/", "jade"))

@app.get('/')
def index(req, res):
  res.render("home", {'title': "Programmed Title!"})

@app.get('/hello')
def hello_world(req, res):
  res.send_text("Hello World!!")

app.run()
