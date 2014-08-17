#
# growler/app.py
#

import asyncio

from time import time
from datetime import datetime

from .http import (HTTPParser, HTTPError)

class App(object):
  
  def __init__(self, name, loop = None):
    self.cache = {};
    self.settings = {};
    self.engines = {};
    self.loop = loop if loop != None else asyncio.get_event_loop()

    print(__name__, name)

  @asyncio.coroutine
  def GenerateServerListner(self):
    print('[GenerateServerListner]')
    yield from asyncio.start_server(self.handle_connection, 'localhost', 8000)

  @asyncio.coroutine
  def handle_connection(self, reader, writer):
    print('handle_connection', reader, writer)
    print()
    # while not reader.at_eof():
    #   line = yield from reader.readline()
    # for line in 
    # line = 
    # print("LINE",line)
    # print(dir(reader))
    # yield from ['1','2']

    parser = HTTPParser()
    try:
      headers = yield from parser.parse(reader)
    except HTTPError as err:
      print ("Error in parser.parse")
      print(err)
      
      h = "HTTP/1.1 {} {}\n".format(err.code, err.message)
      h += "Date: {}\n".format(datetime.now().strftime("%a, %d %b %Y %H:%M:%S %Z"))
    
      body_content = "<h1>{}</h1>".format(err.message)
      b = "<!DOCTYPE html>\n<html><head><title>{}</title></head><body>{}</body></html>".format(err.message, body_content)
      self.send_message(writer, h, b)
      return None

    self.send_message(writer, "", "")
    return None
      
  def run(self):
    self.loop.run_until_complete(self.GenerateServerListner())
    try:
      self.loop.run_forever()
    finally:
      print("Run Forever Ended!")
      self.loop.close()

  # WARNING : This is hiding io, something we want to AVOID!
  def send_message(self, output, header, body):
    msg = "{}\r\n\r\n{}".format(header, body)
    print("Sending:", msg)
    output.write(bytes(msg, 'latin-1'))
    output.write_eof()

  def get(self, *, path):
    print("GET")
    def _(m):
      print(' ', m)
    return _

