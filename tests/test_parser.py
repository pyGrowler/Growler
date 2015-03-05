#
# tests/test_parser.py
#

import growler

import asyncio
# from pytest_localserver import http
import urllib.request

import threading

import socket


def setup_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app = growler.App("ParserTest", loop=loop)
    app.get('/', lambda req, res: res.send_text("ItWorks"))
    app.run()


threading.Thread(target=setup_server).start()


def pytest_configure(config):
    from pprint import pprint
    print("[pytest_configure]")
    pprint(config)


def test_bad_request():
    from time import sleep
    sleep(2)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 8000))
    s.sendall(b'Get BLAHBLAHBLAH H\n\n')
    print(s.recv(4096))
    print("======")
    # s.listen(1)
    print(s)
    cnx = urllib.request.urlopen('http://:')
    print(cnx.read(100).decode('utf-8'))
    # print (cnx)
    # loop.stop()

test_bad_request()
