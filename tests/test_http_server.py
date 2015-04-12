#
# tests/test_http_server.py
#

import pytest
from growler.http.server import HTTPServer


def test_random_port():
    # assume there will be a free port we could bind to in range [10000,11000)
    for x in range(10000, 11000):
        port = HTTPServer.get_random_port((x, x+1))
        if port is not None:
            assert port == x
            break


def test_bad_port_range():
    # assume there will be a free port we could bind to in range [10000,11000)
    port = HTTPServer.get_random_port((10001, 10000))
    assert port is None


def test_server_constructor_default():
    server = HTTPServer()


def test_server_constructor_port():
    server = HTTPServer(port='80')
    assert server.port == 80


def test_server_constructor_port_range():
    server = HTTPServer(port=(5000, 7000))
    assert server.port in range(5000, 7000)


def test_server_constructor_host():
    hostname = '127.0.0.1'
    server = HTTPServer(host='127.0.0.1')
    assert server.host == '127.0.0.1'


def test_server_constructor_socket():
    us = '/run/sock'
    server = HTTPServer(sockfile=us)
    assert server.unix_socket == us
    server.port = 70
    assert server.port is 70
    with pytest.raises(KeyError):
        server.unix_socket

# test_random_port()
