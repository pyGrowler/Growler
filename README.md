# Growler

Growler is a web framework utilizing the new asynchronous library (asyncio)
implemented in python 3.4. It takes a cue from nodejs's express library, using
a series of middleware to process HTTP requests.

The core of the framework is the `growler.App` class, which acts as both server and handler.
The App object creates a request and a response object when a client connects and passes the pair to a series of middleware specified when setting up the server. Note: The middleware are processed in the _same order_ they are specified. Headers are parsed and each middleware added to the app (using `app.use()`), then routes are matched and functions called.

## Example Usage

```python
import asyncio

from growler import (App)
from growler.middleware import (Logger, Static, Renderer)

app = App('GrowlerServer', {'host':'127.0.0.1', port: 8000}))

app.use(Logger())
app.use(Renderer("views/", "jade"))


@app.get('/')
def index(req, res):
  res.render("home")

@app.get('/hello')
def hello_world(req, res):
  res.send_text("Hello World!!")

app.run()
```

This code creates an application which is identified by 'GrowlerServer' (this name does nothing at this point) and has some listening options, host and port. Requests are passed to some middleware provided by the Grower package: Logger and Renderer. Logger simply prints the ip address of the connecting client, and Renderer adds the render function to the response object (used in `index(req, res)`).

Decorators are used to add endpoints to the application, so requests matching '/' will call `index(req, res)` and requests matching '/hello' will call `hello_world(req, res)`.

Calling `app.run()` starts the asyncio event loop and calls `asyncio.run_forever`. This does not HAVE to be called; you can create any task which calls the coroutine `app._server_listen()` and pass to the event loop if you prefer.
