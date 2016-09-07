=======
Growler
=======

master
  |travis-master| |coveralls-master| ' |version-master|

dev
  |travis-dev| |coveralls-dev|

Growler is a web framework built atop asyncio, the asynchronous library described in `PEP
3156`_ and added to the standard library in python 3.4.
It takes a cue from the `Connect`_ & `Express`_ frameworks in the `nodejs`_ ecosystem, using a
single application object and series of middleware to process HTTP requests.
The custom chain of middleware provides an easy way to implement complex applications.

Installation
------------

Growler is installable via pip:

.. code:: bash

    $ pip install growler

The source can be downloaded/cloned from github at http://github.com/pyGrowler/Growler.

Extras
~~~~~~

The pip utility allows packages to provide optional requirements, so features may be installed
only upon request.
This meshes well with the minimal nature of the Growler project: don't install anything the
user doesn't need.
That being said, there are (will be) community packages that are *blessed* by the growler
developers (after ensuring they work as expected and are well tested with each version of
growler) that will be available as extras directly from the growler package.

For example, if you want to use the popular `mako`_ html
template engine, you can add support easily by adding it to the list of optionals:

.. code:: bash

    $ pip install growler[mako]

This will automatically install the mako-growler packge, or growler-mako, or whatever it is
named - you don't care, it's right there, and it works! Very easy!

The goal here is to provide a super simple method for adding middleware packages that the user
can be sure works with that version of growler (i.e. has been tested), and has the blessing of
the growler developer(s).

The coolest thing would be to describe your web stack via this command, so if you want mako,
coffeescript, and some postgres ORM, your install command would look like
:code:`growler[mako,coffee,pgorm]`; anybody could look at that string and get the birds-eye
view of your project.

When multiple extras are available, they will be listed here.

Usage
-----

The core of the framework is the ``growler.App`` class, which links the asyncio server to your
project's middleware.
Middeware can be any callable or coroutine.
The App object creates a request and a response object when a client connects and passes the
pair to this middleware chain.
Note: The middleware are processed in the *same order* they are specified - this could cause
unexpected behavior (errors) if a developer is not careful, so be careful!
The middleware can manipulate the request and response, adding features or checking state.
If any respond to the client, the middleware chain is finished.
This stream/filter model makes it very easy to modularize and extend web applications with many
features, backed by the power of python.

Example Usage
-------------

.. code:: python

    import asyncio

    from growler import App
    from growler.middleware import (Logger, Static, StringRenderer)

    loop = asyncio.get_event_loop()

    # Construct our application with name GrowlerServer
    app = App('GrowlerServer', loop=loop)

    # Add some growler middleware to the application
    app.use(Logger())
    app.use(Static(path='public'))
    app.use(StringRenderer("views/"))

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
at this point), and a reference to the event loop.
Requests are passed to some middleware provided by the Grower package: Logger, Static, and
StringRenderer.
Logger simply prints the ip address of the connecting client to stdout.
Static will check a request url path against files in views/, if one of the files match, the
file type is determined, proper content-type header is set, and the file content is sent.
Renderer adds the 'render' method to the response object, allowing any following function to
call res.render('/filename'), where filename exists in the "views" directory.

Decorators are used to add endpoints to the application, so requests with path matching '/'
will call ``index(req, res)`` and requests matching '/hello' will call ``hello_world(req,
res)``.
Because 'app.get' is used, only HTTP ``GET`` requests will match these endpoints.
Other HTTP 'verbs' (post, put, delete, etc) are available as well as 'all', which matches any
method.
Verb methods must match a path in full.

The 'use' method takes an optional path parameter (e.g.
``app.use(Static("public"), '/static'))``, which calls the middleware anytime the request path
*begins* with the parameter.

The asyncio package provides a Server class which does the low-level socket handling for the
developer, this is how your application should be hosted.
Calling ``app.create_server(...)`` creates an asyncio Server object with the event loop given
in app's constructor, and the app as the target for incomming connections; this is the
recommended way to setup a server.
You can't do much with the server directly, so after creation the event loop must be given
control of the thread
The easiest way to do this is to use ``loop.run_forever()`` after ``app.create_server(...)``.
Or do it in one line with ``app.create_server_and_run_forever(...)``.

Extensions
----------

Growler introduces the virtual namespace ``growler_ext`` to which other projects may add their
own growler-specific code.
Of course, these packages may be imported in the standard way, but Growler provides an
autoloading feature via the growler.ext module (note the '.' in place of '_') which will
automatically import any packages found in the growler_ext namespace.
This not only provides a standard interface for extensions, but allows for different
implementations of an interface to be chosen by the environment, rather than hard-coded in.
It also can reduce the number of import statements at the beginning of the file.
This specialized importer may be imported as a standalone module:

.. code:: python

    from growler import App, ext

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
Users **must** use the ``from growler.ext import ...`` syntax instead.

The best practice for developers to add their middleware to growler is now to put their code in
the python module growler_ext/my_extension.
This will allow your code to be imported by others via ``from growler.ext import my_extension``
or the combination of ``from growler import ext`` and ``ext.my_extension``.

An example of an extension is the `indexer`_ packge, which hosts an automatically generated
index of a filesystem directory.
It should implement the best practices of how to write extensions.

More
----

As it stands, Growler is single threaded, partially implemented, and not fully tested.
Any submissions, comments, and issues are greatly appreciated, but I request that you please
follow the Growler `contributing`_ guide.

The name Growler comes from the `beer bottle`_ keeping in line with the theme of giving
python micro-web-frameworks fluid container names.

License
-------

Growler is licensed under `Apache 2.0`_.


.. _PEP 3156: https://www.python.org/dev/peps/pep-3156/
.. _NodeJS: https://nodejs.org
.. _express: http://expressjs.com
.. _connect: https://github.com/senchalabs/connect
.. _indexer: https://github.com/pyGrowler/growler-indexer
.. _beer bottle: https://en.wikipedia.org/wiki/Growler_%28jug%29
.. _Apache 2.0: http://www.apache.org/licenses/LICENSE-2.0.html
.. _mako: http://www.makotemplates.org/
.. _contributing: https://github.com/pyGrowler/Growler/blob/dev/CONTRIBUTING.rst


.. |version-master| image:: https://img.shields.io/pypi/v/growler.svg
                    :target: https://pypi.python.org/pypi/growler/
                    :alt: Latest PyPI version


.. |travis-master| image:: https://travis-ci.org/pyGrowler/Growler.svg?branch=master
                   :target: https://travis-ci.org/pyGrowler/Growler/branches?branch=master
                   :alt: Testing Report (Master Branch)

.. |travis-dev| image:: https://travis-ci.org/pyGrowler/Growler.svg?branch=dev
                :target: https://travis-ci.org/pyGrowler/Growler/branches?branch=dev
                :alt: Testing Report (Development Branch)

.. |coveralls-master| image:: https://coveralls.io/repos/github/pyGrowler/Growler/badge.svg?branch=master
                      :target: https://coveralls.io/github/pyGrowler/Growler?branch=master
                      :alt: Coverage Report (Master Branch)

.. |coveralls-dev| image:: https://coveralls.io/repos/github/pyGrowler/Growler/badge.svg?branch=dev
                   :target: https://coveralls.io/github/pyGrowler/Growler?branch=dev
                   :alt: Coverage Report (Development Branch)
