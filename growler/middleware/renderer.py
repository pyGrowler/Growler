#
# growler/middleware/renderer.py
#


import asyncio
import os

class Renderer():
  """
    Loads templates
  """
  def __init__(self, path, engine):
    self.path = os.path.abspath(path)
    if not os.path.exists(self.path):
      print ("[Renderer] Error:", "No path exists at {}".format(self.path))
      raise Exception("Path '{}' does not exist.".format(self.path))
    print ("[Renderer] Template files located in {}".format(self.path))

    if isinstance(engine, str):
      engine = render_engine_map.get(engine, None)

    if engine == None:
      raise Exception("[Renderer] No valid rendering engine provided.")

    self.engine = engine(self)

  @asyncio.coroutine
  def __call__(self, req, res):

    def _render(template, obj = {}, cb = None):
      print ("[Renderer::_render]", template)
      res.locals.update(obj)
      filename = self._find_file(template)
      print ("[HTML]")
      html = self.engine(filename, res)
      res.send_html(html)

    res.locals = {}
    res.render = _render

  def _find_file(self, fname):
    filename = os.path.join(self.path, fname)
    if not os.path.isfile(filename):
      filename += self.engine.default_file_extension()
      if not os.path.isfile(filename):
        raise Exception("No File found {}.".format(fname))
    print ("[Renderer::_find_file]", filename)
    return filename

import pyjade
import mako

class MakoRenderer():

  def __init__(self, source):
    from mako.template import Template
    self._render = Template
    print ("[MakoRenderer]")

  def __call__(self, filename, res):
    print ("[MakoRenderer] CALL", filename)
    tmpl = self._render(filename= filename)
    html = tmpl.render()
    return html

  def default_file_extension(self):
    return ".mako"

class JadeRenderer():

  def __init__(self, source):
    print ("[JadeRenderer]")
    # from pyjade.ext import mako
    from pyjade.ext.mako import preprocessor as mako_preprocessor
    from mako.template import Template

    self._render = Template
    self._engine = mako
    self._preprocessor = mako_preprocessor

  def default_file_extension(self):
    return ".jade"

  def __call__(self, filename, res):
    print ("[JadeRenderer] ::", filename)
    tmpl = self._render(filename= filename, preprocessor= self._preprocessor)
    html = tmpl.render(**res.locals)
    return html

render_engine_map = {
  "mako" : MakoRenderer,
  "jade" : JadeRenderer
}

