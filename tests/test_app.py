#
# test_app
#

import asyncio
import pytest
import growler
from growler.middleware import (ResponseTime, Logger)
from mock_classes import (
    MockRequest,
    MockResponse,
    MockProtocol,
)


@pytest.fixture
def app():
    result = growler.application.Application(__name__,
                                             request_class=MockRequest,
                                             response_class=MockResponse,
                                             protocol_factory=MockProtocol,
                                             )
    return result


def test_application_constructor():
    app = growler.application.Application('Test')
    assert app.name == 'Test'


def test_application_saves_config():
    val = 'B'
    app = growler.application.Application('Test', A=val)
    assert app.config['A'] == val



def test_application_enables_x_powered_by(app):
    """ Test application enables x-powered-by by default """
    assert app.enabled('x-powered-by')


def test_application_create_server(app):
    """ Test application enables x-powered-by by default """
    srv = app.create_server()
    assert asyncio.iscoroutine(srv)



def test_app_something(app):
    app.create_server()


if __name__ == '__main__':

    app = growler.App(__name__)

    app.use(Logger())
    app.use(ResponseTime())

    # @app.get("/")
    # def index(req, res):
    #  res.send_text("It Works!")

    app.run()
