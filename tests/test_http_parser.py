#
# tests/test_http_parser.py
#

import growler

from growler.http.parser import Parser

import asyncio
# from pytest_localserver import http
import urllib.request

import threading

import socket

def pytest_configure(config):
    from pprint import pprint
    print("[pytest_configure]")
    pprint(config)

def test_parse_request_line():
    data = b"""GET /path HTTP/1.1\r\nhost: nowhere.com\r\n"""
    (reqest_line, following) = Parser.parse_request_line(b)
    parser.

def test_bad_request():
    parser = Parser()

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

# test_bad_request()
