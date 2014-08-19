#
# growler/__init__.py
#

import asyncio

from .app import App 


def create_http_server(callback = None, loop = None):
  loop = loop or asyncio.get_event_loop()

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

  return http_server(callback, loop)

def run_forever(loop = None):
  loop = loop or asyncio.get_event_loop()
  try:
    loop.run_forever()
  except KeyboardInterrupt:
    print("Keyboard induced termination : Exiting")
  finally:
    loop.close()
