#
# growler/app.py
#

import asyncio

from time import time
from datetime import (datetime, timezone, timedelta)

from .http import (HTTPParser, HTTPError, HTTPRequest, HTTPResonse)

class App(object):
  
  def __init__(self, name, settings = {}, loop = None):
    self.cache = {};

    self._config = {'host':'127.0.0.1'};
    self._config.update(settings)

    self.engines = {};
    self.loop = loop if loop != None else asyncio.get_event_loop()
    self.loop.set_debug(True)

    print(__name__, name)

  @asyncio.coroutine
  def GenerateServerListner(self):
    print('[GenerateServerListner]')
    yield from asyncio.start_server(self.handle_connection, 'localhost', 8000)

  @asyncio.coroutine
  def handle_connection(self, reader, writer, req_class = HTTPRequest, res_class = HTTPResonse):
    print('[handle_connection]', reader, writer, "\n")

    # create the request object
    req = req_class(reader)

    # create the response object
    res = res_class(writer)

    try:
      # process the request
      x = yield from req.process()
      print('x',x)
    except HTTPError as err:
      err.PrintSysMessage()
      print (err)
      
      h = "HTTP/1.1 {} {}\n".format(err.code, err.phrase)
      h += "Date: {}\n".format(datetime.now(timezone(timedelta())).strftime("%a, %d %b %Y %H:%M:%S %Z"))

      body_content = "<h1>{}</h1>".format(err.phrase)
      b = "<!DOCTYPE html>\n<html><head><title>{}</title></head><body>{}</body></html>\n".format(err.phrase, body_content)
      self.send_message(res, h, b)

    return None
    # except Exception as e:
      # print ("ERROR")
      # print (e)
      # res.send('There was an error!')
      # return None
    # return None
    parser = HTTPParser(reader)
    parsed_stream = parser.parse()
    try:
      request_line = next(parsed_stream)
      print("[handle_connection] request_line", request_line)
      headers = yield from parser.parse()
      body = yield from parser.parse()
    except HTTPError as err:
      print ("Error in handle_connection")
      print(err)
      
      h = "HTTP/1.1 {} {}\n".format(err.code, err.phrase)
      h += "Date: {}\n".format(datetime.now(timezone(timedelta())).strftime("%a, %d %b %Y %H:%M:%S %Z"))

      body_content = "<h1>{}</h1>".format(err.phrase)
      b = "<!DOCTYPE html>\n<html><head><title>{}</title></head><body>{}</body></html>\n".format(err.phrase, body_content)
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
    # print("Sending:", msg)
    output.write(msg)
    output.write_eof()

  def get(self, *, path):
    print("GET")
    def _(m):
      print(' ', m)
    return _

  #
  # Dict like configuration access
  #
  def __setitem__(self, key, value):
    print ("Setting", key)
    self._config[key] = value

  def __getitem__(self, key):
    print ("Getting", key)
    return self._config[key]

  def config(self):
    return self._config
