#
# growler/middleware/renderer.py
#

import logging
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
        Should be called via `res.render(...)`.

        This sends the response to the client and will therefore finish the
        growler application chain. An error is raised if no template could be
        found.

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
            filename = engine.find_template_filename(template)
            if filename:
                if obj:
                    self.res.locals.update(obj)
                html = engine.render_source(filename, self.res.locals)
                self.res.send_html(html)
                break
        else:
            raise ValueError("Could not find a template with name '%s'" % template)

    def add_engine(self, engine):
        """
        Add an engine to the engines
        """
        self.engines.append(engine)


class RenderEngine:
    """
    Class used to render templates.

    Upon being called in the middleware chain, the __call__ method will
    add a 'render' function to the res object.

    To create your own RenderEngine, you must subclass this class and
    implement the render_source method.

    When requesting to render the view, the user may use or may not
    specify the file extension to use.
    The member `default_file_extensions` should be a list of file
    extensions (including leading '.') that will be added to the end
    any template names requested.
    No search is performed if there is no such member.

    If the template name does not follow a typical template_name.extension
    format, you can implement your own by overloading the
    find_template_filename method.

    It is **not** recommended to change the behavior of the __call__
    method, which may modify the res object in a manner all other
    RenderEngines are dependent.

    Attributes:
        path (pathlib.Path): The directory containing the view files this
            renderer will find.
    """

    def __init__(self, path):
        """
        Constructor

        Args:
            path (str): Top level directory to search for template files - the
                path must exist and the path must be a directory.

        Raises:
            FileNotFoundError: If the provided path does not exists.
            NotADirectoryError: If the path is not a directory.
        """
        self.path = Path(path).resolve()

        if not self.path.is_dir():
            log.warning("path given to render engine is not a directory")
            raise NotADirectoryError("path '%s' is not a directory" % path)

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
        res.render.add_engine(self)

    def find_template_filename(self, template_name):
        """
        Searches for a file matching the given template name.

        If found, this method returns the pathlib.Path object of the found
        template file.

        Args:
            template_name (str): Name of the template, with or without a file
                extension.

        Returns:
            pathlib.Path: Path to the matching filename.
        """

        def next_file():
            filename = self.path / template_name
            yield filename
            try:
                exts = self.default_file_extensions
            except AttributeError:
                return

            strfilename = str(filename)
            for ext in exts:
                yield Path(strfilename + ext)

        for filename in next_file():
            if filename.is_file():
                return filename

    def render_source(self, filename, obj):
        """
        Render the template file found at filename.

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

    default_file_extensions = [
        '.html.tmpl',
    ]

    def render_source(self, filename, obj=None):
        txt = self.file_text(str(self.path.joinpath(filename)))
        if obj is None:
            return txt
        else:
            return txt.format(**obj)

    def file_text(self, filename):
        with open(filename, 'r') as file:
            return file.read()


# register the renderer
Renderer.render_engine_map['string'] = StringRenderer
