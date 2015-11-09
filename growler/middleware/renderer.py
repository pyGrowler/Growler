#
# growler/middleware/renderer.py
#

import os
import logging

log = logging.getLogger(__name__)


class Renderer():
    """
    A growler-middleware class for changing template files into html (or any
    file format) to send back to the client.

    A renderer is created with the template directory and name of rendering
        engine as parameters.

    Upon being called in the middleware chain, the __call__ method will add a
    'render' function
    """

    render_engine_map = dict()

    def __init__(self, path, engine):
        """
        Construct a renderer.

        :param path: The directory containing the templates to render. If this
            is a list, it is automatically concatenated by os.path.join.

        :param engine: The rendering engine or the string key for the type of
            engine, details should be found in the documentation for that
            engine.
        """
        if isinstance(path, list):
            path = os.path.join(*path)

        self.path = os.path.abspath(path)

        if not os.path.exists(self.path):
            log.error("%d No path at %s" % (id(self), self.path))
            raise Exception("Path '{}' does not exist.".format(self.path))

        log.info("%d files located in %s" % (id(self), self.path))

        if isinstance(engine, str):
            engine = self.render_engine_map.get(engine, None)

        if engine is None:
            raise Exception("[Renderer] No valid rendering engine provided.")

        self.engine = engine(self)

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

        def _render(template, obj={}):
            res.locals.update(obj)
            filename = self._find_file(template)
            html = self.engine(filename, res)
            res.send_html(html)

        res.locals = {}
        res.render = _render

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


class StringRenderer(Renderer):

    def __init__(self, view_directory, extensions=None):
        self.extensions = (['.html.tmpl']
                            if extensions is None
                            else extensions)
        self.path = view_directory

    def render_file(self, filename, render_obj, **kwargs):
        txt = self.file_text(filename)
        obj = copy(render_obj)
        obj.update(kwargs)
        return txt.format(**obj)

    def file_text(self, filename):
        with open(filename, 'r') as file:
            return file.read()


# register the renderer
Renderer.render_engine_map['string'] = StringRenderer
