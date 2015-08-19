
from os import path

import asyncio

from growler import (App)
from growler.middleware import (Logger, Renderer)

app = App('GrowlerServer')

this_dir = path.dirname(__file__)

app.use(Logger())
app.use(Renderer(path.join(this_dir, "views"), "jade"))


@app.get('/')
def index(req, res):
    res.render("home")


@app.get('/hello')
def hello_world(req, res):
    res.send_text("Hello World!!")


@app.use
def error_handler(req, res, err):
    res.send_text("404 : Hello World!!")


app.print_middleware_tree()

loop = asyncio.get_event_loop()

loop.run_until_complete(loop.create_server(app._protocol_factory(app),
                                           host='127.0.0.1',
                                           port=8000))
loop.run_forever()
