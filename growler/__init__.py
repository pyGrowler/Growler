#
# growler/__init__.py
#

import asyncio

from .app import App 

import ssl



class http_proto(asyncio.Protocol):

  def connection_made(self, transport):
      peername = transport.get_extra_info('peername')
      print('connection from {}'.format(peername))
      self.transport = transport

  def data_received(self, data):
      print('data received: {}'.format(data.decode()))
      self.transport.write(data)

      # close the socket
      self.transport.close()      

class https_proto(http_proto):

  def connection_made(self, transport):
    peername = transport.get_extra_info('peername')
    print('HTTPS connection from {}'.format(peername))
    print('transport', transport)
    sock = transport.get_extra_info('socket')
    print('socket', sock)    
    self.transport = transport

def create_http_server(callback = None, loop = None):
  loop = loop or asyncio.get_event_loop()

  class http_server():
    def __init__(self, cb, loop):
      asyncio.Protocol.__init__(self)
      print ("Creating http server")
      self.callback = cb
      self.loop = loop

    def listen(self, host, port):
      self.coro = self.loop.create_server(http_proto, host, port)
      self.srv = self.loop.run_until_complete(self.coro)
      print('serving on {}'.format(self.srv.sockets[0].getsockname()))
      print(' sock {}'.format(self.srv.sockets[0]))

  return http_server(callback, loop)

def create_https_server(options, callback = None, loop = None):
  loop = loop or asyncio.get_event_loop()
  priv, pub = options['key'], options['cert']

  class https_server():
    def __init__(self, priv, pub, cb, loop):
      asyncio.Protocol.__init__(self)
      print ("Creating https server")
      self.sslctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
      if pub == None:
        self.sslctx.load_cert_chain(certfile=priv)
      else:
        self.sslctx.load_cert_chain(certfile=pub, keyfile=priv)
      self.private_key = priv
      self.public_key = pub
      self.callback = cb
      self.loop = loop

    def listen(self, host, port):
      self.coro = self.loop.create_server(https_proto, host, port, ssl=self.sslctx)
      self.srv = self.loop.run_until_complete(self.coro)
      # print('securing with',self.private_key, self.public_key)
      # sock = ssl.wrap_socket(self.srv.sockets[0], self.private_key, self.public_key)
      print('serving on {}'.format(self.srv.sockets[0].getsockname()))
      # print(' sock {}'.format(self.srv.sockets[0]))
      # print(' sock {} ({})'.format(sock, sock == self.srv.sockets[0]))

  return https_server(priv, pub, callback, loop)

def run_forever(loop = None):
  loop = loop or asyncio.get_event_loop()
  try:
    loop.run_forever()
  except KeyboardInterrupt:
    print("Keyboard induced termination : Exiting")
  finally:
    loop.close()
