#
# growler/__init__.py
#

import asyncio

from .app import App 
from .router import Router
from .middleware import (middleware)

import ssl

class http_proto(asyncio.Protocol):

  def connection_made(self, transport):
      print('HTTP connection from {}'.format(transport.get_extra_info('peername')))
      self.transport = transport

  def data_received(self, data):
      print('data received: {}'.format(data.decode()))
      self.transport.write(data)

      # close the socket
      self.transport.close()

class http_server():
  def __init__(self, cb, loop, ssl = None, message="Creating HTTP server"):
    print (message)
    self.callback = cb
    self.loop = loop
    self.ssl = ssl

  def listen(self, host, port):
    self.coro = self.loop.create_server(http_proto, host, port, ssl=self.ssl)
    self.srv = self.loop.run_until_complete(self.coro)
    # print('securing with',self.private_key, self.public_key)
    # sock = ssl.wrap_socket(self.srv.sockets[0], self.private_key, self.public_key)
    print('serving on {}'.format(self.srv.sockets[0].getsockname()))
    print(' sock {}'.format(self.srv.sockets[0]))
    # print(' sock {}'.format(self.srv.sockets[0]))
    # print(' sock {} ({})'.format(sock, sock == self.srv.sockets[0]))

def create_http_server(callback = None, loop = None):
  loop = loop or asyncio.get_event_loop()

  return http_server(callback, loop)

def create_https_server(options, callback = None, loop = None):
  loop = loop or asyncio.get_event_loop()
  if not 'cert' in options.keys():
    priv = options['key']
  else:
    priv, pub = options['key'], options['cert']

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


