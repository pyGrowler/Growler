#
# growler/middleware/renderer.py
#

import os
import logging
from copy import copy
from pathlib import Path

log = logging.getLogger(__name__)


class Renderer:
    """
    Renderer is a helper class designed to provide a common interface for
    rendering html (or potentially any file format) from templates files. It is
    important to note that Renderer itself is not middleware, but an extension
    given to 'res' objects by the actually middleware, RendererEngines.

    The expected behavior of a RendererEngine middleware is to add a Renderer
    object to res (if it is not already present) at res.render, and add the
    engine to this object.

    The Renderer is callable, so expected usage is as simple as
    `res.render('tmplate_file')`. The renderer will intelligently find the
    appropriate file and engine pair, and send the results to the client.

    To add custom templating functionality, look to subclass the RendererEngine
    class, and leave the renderer class alone.
    """

    render_engine_map = dict()

    def __init__(self, res):
        """
        Constructor

        Args:
            res (HttpResponse): The response which owns this renderer
        """
        self.res = res
        self.engines = []

    def __call__(self, template, obj=None):
        """
        Should be called via `res.render(...)`

        This sends the response to the client and will therefore finish the
        growler application chain.

        Args:
            template (str): The name of the template to render. If there is no
                file extension, each engine will search for files matching its
                own designated extension.
            obj (dict): A dictionary containing the 'local namespace' of the
                rendering environment.

        Raises:
            ValueError: If no template could be found with the provided name.
        """
        for engine in self.engines:
            filename = engine.find_filename(template)
            if filename:
                if obj:
                    self.res.locals.update(obj)
                html = engine.render_source(filename, self.res.locals)
                self.res.send(html)
                break
        else:
            raise Exception()

    def _find_file(self, fname):
        """
        Looks for the file with filename 'fname'
        """

        def next_file():
            filename = os.path.join(self.path, fname)
            yield filename
            yield filename + self.engine.default_file_extension

        for filename in next_file():
            if not os.path.isfile(filename):
                continue
            return filename

        raise Exception("No file found provided name '{}'.".format(fname))

    def add_engine(self, engine):
        """
        Add an engine to the engines
        """
        self.engines.append(engine)


class RenderEngine:
    """
    Class used to render templates.

    Upon being called in the middleware chain, the __call__ method will add a
    'render' function.
    """

    def __init__(self, path):
        """
        Constructor

        Args:
            path (str): Top level directory to search for template files.
        """
        if isinstance(path, Path):
            self.path = path.resolve()
        else:
            self.path = Path(path).resolve()

        if not self.path.is_dir():
            log.warning("path given to render engine is not a directory")

    def __call__(self, req, res):
        """
        The action of this middleware upon client request. The response is
        given a member 'locals' which house the local variables for use in the
        template, and a new method 'render' which takes a template file name
        (relative to the template directory given to the Render's constructor),
        a dict which will update any values in res.locals. After the engine
        runs on this file, the resulting html is sent to the client
        automatically, ending the res/req chain.
        """
        if not hasattr(res, 'render'):
            res.render = Renderer(res)
            res.locals = {}

        res.renderer.add_engine(self)

    def find_filename(self, filename):
        """
        Finds a filename

        Args:
            filename (str): Path to the template file

        Returns:
            str: Path a filename
        """
        raise NotImplementedError()

    def render_source(self, filename, obj):
        """
        Render the filename

        Args:
            filename (str): Path to the template file
            obj (dict): Dictionary of data to pass to templating engine

        Returns:
            str: The rendererd file
        """
        raise NotImplementedError()


class StringRenderer(RenderEngine):
    """
    A renderer that uses the basic str.format method to generate html pages.

    Given a view directory that contains *.html.tmpl template files, this will
    add the 'render' method to the middleware response object. When this
    method is called with a filename and dictionary, the file is read in as a
    string then .format is called with the contents of the dictionary.
    """

    default_file_extension = '.html.tmpl'

    def render_file(self, filename, render_obj={}, **kwargs):
        txt = self.file_text(str(self.path.joinpath(filename)))
        obj = copy(render_obj)
        obj.update(kwargs)
        return txt.format(**obj)

    def file_text(self, filename):
        with open(filename, 'r') as file:
            return file.read()

    def __call__(self, filename, res):
        with open(filename, 'r') as file:
            s = file.read()
        return s.format(**res.locals)


# register the renderer
Renderer.render_engine_map['string'] = StringRenderer
