#
# examples/example0/__main__.py
#
"""
Example script to demonstrate route decorating, string-template rendering and
low-level server.
"""


from os import path

import asyncio

from growler import (App)
from growler.middleware import (
    Logger,
    StringRenderer,
)

app = App('GrowlerServer')

view_dir = path.join(path.dirname(__file__), "views")

app.use(Logger())
app.use(StringRenderer(view_dir, extensions=['.html.tmpl']))


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
