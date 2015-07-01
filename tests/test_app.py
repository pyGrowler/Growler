#
# test_app
#

import growler

from growler.middleware import (ResponseTime, Logger)


def test_Success():
    assert True


def test_application_constructor():
    app = growler.application.Application('Test')
    assert app.name == 'Test'


if __name__ == '__main__':

    app = growler.App(__name__)

    app.use(Logger())
    app.use(ResponseTime())

    # @app.get("/")
    # def index(req, res):
    #  res.send_text("It Works!")

    app.run()
