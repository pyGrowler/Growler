
Growler
=======

Growler is a web framework utilizing the new asynchronous library (asyncio) described in `PEP
3156 <https://www.python.org/dev/peps/pep-3156/>`_ and added to the standard library in python
3.4.
It takes a cue from `nodejs <https://nodejs.org>`_'s `express <http://expressjs.com/>`_
library, using a series of middleware to process HTTP requests.
The custom chain of middleware provides an easy way to implement complex applications.

Installation
------------

When available, growler will be installable via pip:

.. code:: bash

    $ pip install growler

Optionals
~~~~~~~~~

There are optionals to the install command that will ensure that additional functionality is
working.
For example if you want to use the (quite pythonic) `jade <http://jade-lang.com/>`__ html
template engine, you can install with growler by adding it to the list of optionals:

.. code:: bash

    $ pip install growler[jade]

When multiple optionals are available, they will be listed here.

Usage
-----

The core of the framework is the ``growler.App`` class, which acts as both server and handler.
The App object creates a request and a response object when a client connects and passes the
pair to a series of middleware specified when setting up the server.
Note: The middleware are processed in the *same order* they are specified.
Headers are parsed and each middleware added to the app (using ``app.use()``), then routes are
matched and functions called.
The middleware manipulate the request and response objects and either respond to the client or
pass to the next middleware in the chain.
This stream/filter model makes it very easy to modularize and extend web applications with any
features, backed by the power of python.

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


This code creates an application which is identified by 'GrowlerServer' (this name does nothing
at this point) and has some listening options, host and port.
Requests are passed to some middleware provided by the Grower package: Logger and Renderer.
Logger simply prints the ip address of the connecting client, and Renderer adds the render
function to the response object (used in ``index(req, res)``).

Decorators are used to add endpoints to the application, so requests with path matching '/'
will call ``index(req, res)`` and requests matching '/hello' will call ``hello_world(req,
res)``.

Calling ``app.create_server(...)`` creates an asyncio server object with the event loop given
in the app's constructor.
You can't do much with the server directly, so after creating, as long as the event loop has
control, the application will run.
The easiest way to do this is to use ``asyncio.run_forever()`` after ``app.create_server``.
Or do it with one line as in ``app.create_server_and_run_forever(...)``.

Extensions
----------

Growler introduces the virtual namespace ``growler_ext`` to which other projects may add their
own growler-specific code.
Of course, these packages may be imported in the standard way, but Growler provides an
autoloading feature via the growler.ext module (note the '.' in place of '_') which will
automatically import any packages found in the growler_ext namespace.
This not only provides a standard interface for extensions, but allows for different
implementations of an interface to be chosen by the environment, rather than hard-coded in.
It also can reduce number of import statements at the beginning of the file.
This specialized importer may be imported as a standalone module:

.. code:: python

    from growler import (App, ext)

    app = App()
    app.use(ext.MyGrowlerExtension())
    ...


or a module to import 'from':

.. code:: python

    from growler import App
    from growler.ext import MyGrowlerExtension

    app = App()
    app.use(MyGrowlerExtension())
    ...

This works by replacing the 'real' ext module with an object that will import submodules in the
growler_ext namespace automatically.
Perhaps unfortunately, because of this there is no way I know of to allow the
``import growler.ext.my_extension`` syntax, as this skips the importer object and raises an
import error.
Users *must* use the ``from growler.ext import ...`` syntax instead.

The best practice for developers to add their middleware to growler is now to put their code in
the python module growler_ext/my_extension.
This will allow your code to be imported by others via ``from growler.ext import my_extension``
or the combination of ``from growler import ext`` and ``ext.my_extension``.


An example of an extension is the `indexer <https://github.com/pyGrowler/growler-indexer>`__
which hosts an automatically generated index of a filesystem directory.
It should implement the best practices of how to write extensions.

More
----

As it stands, Growler is single threaded, and not tested very well. Any submissions or comments
would be appreciated.

The name Growler comes from the `beer bottle
<https://en.wikipedia.org/wiki/Growler_%28jug%29>`__ keeping in line with the theme of giving
python micro-web-frameworks fluid container names.

License
-------

Growler is licensed under `Apache 2.0 <http://www.apache.org/licenses/LICENSE-2.0.html>`__.
