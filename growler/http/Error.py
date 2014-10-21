#
# growler/http/Error.py
#


import sys

__all__ = ['HTTPError', 'HTTPErrorInternalServerError', 'HTTPErrorBadRequest', 'HTTPErrorUnauthorized', 'HTTPErrorPaymentRequired', 'HTTPErrorForbidden', 'HTTPErrorNotFound', 'HTTPErrorGone', 'HTTPErrorRequestTooLarge', 'HTTPErrorUnsupportedMediaType', 'HTTPErrorInternalServerError', 'HTTPErrorNotImplemented', 'HTTPErrorVersionNotSupported']

class HTTPError(Exception):

  def __init__(self, phrase, code, ex = None):
    print ("[HTTPError]")
    Exception.__init__(self, phrase)
    self.code = code
    self.phrase = phrase
    self.sys_exception = ex
    self.traceback = sys.exc_info()[2]

  def PrintSysMessage(self, printraceback = True):
    if self.sys_exception:
      print(self.sys_exception)
    if printraceback and self.traceback:
      print (self.traceback)
      # for line in self.traceback:
        # print (line)

  def GetFromCode(self, code):
    return {400: HTTPErrorBadRequest,
            401: HTTPErrorUnauthorized,
            402: HTTPErrorPaymentRequired,
            403: HTTPErrorForbidden,
            404: HTTPErrorNotFound,
            410: HTTPErrorGone}(code, None)

class HTTPErrorBadRequest(HTTPError):
  def __init__(self, ex = None):
    HTTPError.__init__(self, "Bad Request", 400, ex)

class HTTPErrorUnauthorized(HTTPError):
  def __init__(self):
    HTTPError.__init__(self, "Unauthorized", 401)

class HTTPErrorPaymentRequired(HTTPError):
  def __init__(self):
    HTTPError.__init__(self, "Payment Required", 402)

class HTTPErrorForbidden(HTTPError):
  def __init__(self):
    HTTPError.__init__(self, "Forbidden", 403)

class HTTPErrorNotFound(HTTPError):
  def __init__(self):
    HTTPError.__init__(self, "Not Found", 404)

class HTTPErrorGone(HTTPError):
  def __init__(self):
    HTTPError.__init__(self, "Gone", 410)

class HTTPErrorRequestTooLarge(HTTPError):
  def __init__(self):
    HTTPError.__init__(self, "Request-URI Too Large", 414)

class HTTPErrorUnsupportedMediaType(HTTPError):
  def __init__(self):
    HTTPError.__init__(self, "Unsupported Media Type", 415)

class HTTPErrorInternalServerError(HTTPError):
  def __init__(self):
    HTTPError.__init__(self, "Internal Server Error", 500)

class HTTPErrorNotImplemented(HTTPError):
  def __init__(self):
    HTTPError.__init__(self, "Method Not Implemented", 501)

class HTTPErrorVersionNotSupported(HTTPError):
  def __init__(self):
    HTTPError.__init__(self, "Version not supported", 505)
