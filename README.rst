
Growler
=======

Growler is a web framework utilizing the new asynchronous library
(asyncio) described in PEP 3156 and implemented in python 3.4. It takes
a cue from `nodejs <https://nodejs.org>`__'s
`express <http://expressjs.com/>`__ library, using a series of
middleware to process HTTP requests. The custom chain of middleware
provides an easy way to implement complex applications.

Installation
------------

When available, growler will be installable via pip:

.. code:: bash

    $ pip install growler

Optionals
~~~~~~~~~

There are optionals to the install command that will ensure that
additional functionality is working. For example if you want to use the
(quite pythonic) `jade <http://jade-lang.com/>`__ html template engine,
you can install with growler by adding it to the list of optionals:

.. code:: bash

    $ pip install growler[jade]

When multiple optionals are available, they will be listed here.

Usage
-----

The core of the framework is the ``growler.App`` class, which acts as
both server and handler. The App object creates a request and a response
object when a client connects and passes the pair to a series of
middleware specified when setting up the server. Note: The middleware
are processed in the *same order* they are specified. Headers are parsed
and each middleware added to the app (using ``app.use()``), then routes
are matched and functions called. The middleware manipulate the request
and response objects and either respond to the client or pass to the
next middleware in the chain. This stream/filter model makes it very
easy to modularize and extend web applications with any features, backed
by the power of python.

Example Usage
-------------

.. code:: python

    import asyncio

    from growler import App
    from growler.middleware import (Logger, Static, Renderer)

    loop = asyncio.get_event_loop()

    # Construct our application with name GrowlerServer
    app = App('GrowlerServer', loop=loop)

    # Add some growler middleware to the application
    app.use(Logger())
    app.use(Static(path='public'))
    app.use(Renderer("views/", "jade"))

    # Add some routes to the application
    @app.get('/')
    def index(req, res):
        res.render("home")

    @app.get('/hello')
    def hello_world(req, res):
        res.send_text("Hello World!!")

    # Create the server - this automatically adds it to the asyncio event loop
    Server = app.create_server(host='127.0.0.1', port=8000)

    # Tell the event loop to run forever - this will listen to the server's
    # socket and wake up the growler application upon each connection
    loop.run_forever()


This code creates an application which is identified by 'GrowlerServer'
(this name does nothing at this point) and has some listening options,
host and port. Requests are passed to some middleware provided by the
Grower package: Logger and Renderer. Logger simply prints the ip address
of the connecting client, and Renderer adds the render function to the
response object (used in ``index(req, res)``).

Decorators are used to add endpoints to the application, so requests
matching '/' will call ``index(req, res)`` and requests matching
'/hello' will call ``hello_world(req, res)``.

Calling ``app.run()`` starts the asyncio event loop and calls
``asyncio.run_forever``. This does not HAVE to be called; you can create
any task which calls the coroutine ``app._server_listen()`` and pass to
the event loop if you prefer.

Extensions
----------

Growler now defines itself as a 'namespace package', allowing anybody to
write extensions for it that can be imported via
growler.my\_cool\_extension. It is best to place extensions in the
extension path, middleware path, or abbreviated middleware path :
``growler.ext.my_ext``, ``growler.middleware``, ``growler.mw``. This not
mandatory (for now).

There is one 'official' extension,
`indexer <https://github.com/pyGrowler/growler-indexer>`__ which hosts
an automatically generated index of a filesystem directory.

More
----

Currently Growler is single threaded, and not tested very well. Any
submissions or comments would be appreciated.

The name Growler comes from the `beer
bottle <http://en.wikipedia.org/wiki/Beer_bottle#Growler>`__ due to the
apparent convention of giving python micro-web-frameworks fluid container
names.

License
-------

Growler is licensed under `Apache
2.0 <http://www.apache.org/licenses/LICENSE-2.0.html>`__.
