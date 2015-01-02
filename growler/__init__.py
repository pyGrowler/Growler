#
# growler/__init__.py
#
#   Copyright (c) 2014 Andrew Kubera <andrew.kubera@gmail.com>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
"""
Growler is an http(s) server designed around the asyncio python module which
imitates Nodejs's express framework, allowing easy creation of complex websites
using a middleware-based configuration.
"""

from importlib.machinery import SourceFileLoader
from os import path

metadata = SourceFileLoader("metadata", path.join(path.dirname(__file__),"metadata.py")).load_module()

__version__ = metadata.version
__author__ = metadata.author
__date__ = "Oct 21, 2014"
__copyright__ = metadata.copyright
__license__ = metadata.license

import asyncio
import ssl

from copy import copy

from .app import App
from .http import *
from .router import Router

DEFAULT_HTTP_OPTS = {'backlog': 100}


class http_proto(asyncio.Protocol):
  """Growler implementation of HTTP"""

  def connection_made(self, transport):
    """@type transport: asyncio.Transport"""
    self.transport = transport
    self.hostname = transport.get_extra_info('peername')
    self.socket = transport.get_extra_info('socket')
    print('HTTP connection from {}'.format(self.hostname))
    transport.write("data")

  def data_received(self, data):
    """@type data: bytes"""
    print('data received: {}'.format(data.decode()))
    self.transport.write(data)

    # close the socket
    self.transport.close()

class http_server(object):
  """HTTP Server"""

  def __init__(self, cb, loop, ssl = None, message="Creating HTTP server"):
    """
    @type loop: asyncio.BaseEventLoop
    @type ssl: ssl.SSLContext
    """
    print (message)
    self.callback = cb
    self.loop = loop
    self.ssl = ssl

  def listen(self, host, port):
    """ """
    self.coro = self.loop.create_server(http_proto, host, port, ssl=self.ssl)
    self.srv = self.loop.run_until_complete(self.coro)
    # print('securing with',self.private_key, self.public_key)
    # sock = ssl.wrap_socket(self.srv.sockets[0], self.private_key, self.public_key)
    print('serving on {}'.format(self.srv.sockets[0].getsockname()))
    print(' sock {}'.format(self.srv.sockets[0]))
    # print(' sock {}'.format(self.srv.sockets[0]))
    # print(' sock {} ({})'.format(sock, sock == self.srv.sockets[0]))

def create_http_server(options = {}, callback = None, loop = None):
  """Creates an http 'server' object which may listen on multiple ports."""
  loop = loop or asyncio.get_event_loop()

  opts = copy(DEFAULT_HTTP_OPTS)
  opts.update(options)

  return http_server(callback, loop)

def create_https_server(options, callback = None, loop = None):
  """Creates an https 'server' object which may listen on multiple ports."""
  loop = loop or asyncio.get_event_loop()
  priv = options['key']
  pub = options['cert'] if 'cert' in options.keys() else None

  sslctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
  if pub == None:
    sslctx.load_cert_chain(certfile=priv)
  else:
    sslctx.load_cert_chain(certfile=pub, keyfile=priv)

  return http_server(callback, loop, sslctx, "Creating HTTPS server")

def run_forever(loop = None):
  loop = loop or asyncio.get_event_loop()
  try:
    loop.run_forever()
  except KeyboardInterrupt:
    print("Keyboard induced termination : Exiting")
  finally:
    loop.close()

__all__ = ["App", "Router", "run_forever", "create_http_server", "create_https_server", "http_server", "https_server"]


