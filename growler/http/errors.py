#
# growler/http/errors.py
#
"""
Custom Exception subclasses relating to specific http errors.
"""

import sys
from urllib.error import HTTPError as UrllibHttpError


class HTTPError(UrllibHttpError):
    """
    Generic HTTP Exception.

    Must be constructed with a code number, may be given an optional phrase.
    It is recommended to use one of the subclasses which is defined below.
    A helper function exists to get the appropriate error from a code:
        raise HTTPError.get_from_code(404)
        raise HTTPErrorNotFound()
    """

    msg = ''
    code = 0
    code_to_error = dict()

    def __init__(self, url=None, code=None, phrase=None, msg=None, ex=None):
        """
        Construct an http error, if code or phrase not defined, use default.
        """
        super().__init__(url, code or self.code, msg or self.msg, None, None)
        self.phrase = phrase or self.msg
        self.sys_exception = ex
        self.traceback = sys.exc_info()[2]

    def PrintSysMessage(self, printraceback=True):
        if self.sys_exception:
            print(self.sys_exception)
        if printraceback and self.traceback:
            print(self.traceback)

    @classmethod
    def get_from_code(cls, code):
        """
        A simple way of getting the Exception class of an http error from http
        error code.
        """
        return cls.code_to_error.get(code)


class HTTPErrorBadRequest(HTTPError):
    code = 400
    msg = "Bad Request"


class HTTPErrorInvalidHeader(HTTPErrorBadRequest):
    msg = "Bad Request (Invalid Header Name)"


class HTTPErrorUnauthorized(HTTPError):
    code = 401
    msg = "Unauthorized"


class HTTPErrorPaymentRequired(HTTPError):
    code = 402
    msg = "Payment Required"


class HTTPErrorForbidden(HTTPError):
    code = 403
    msg = "Forbidden"


class HTTPErrorNotFound(HTTPError):
    code = 404
    msg = "Not Found"


class HTTPErrorMethodNotAllowed(HTTPError):
    code = 405
    msg = "Method Not Allowed"


class HTTPErrorNotAcceptable(HTTPError):
    code = 406
    msg = "Not Acceptable"


class HTTPErrorProxyAuthenticationRequired(HTTPError):
    code = 407
    msg = "Proxy Authentication Required"


class HTTPErrorRequestTimeout(HTTPError):
    code = 408
    msg = "Request Timeout"


class HTTPErrorConflict(HTTPError):
    code = 409
    msg = "Conflict"


class HTTPErrorGone(HTTPError):
    code = 410
    msg = "Gone"


class HTTPErrorLengthRequired(HTTPError):
    code = 411
    msg = "Length Required"


class HTTPErrorPreconditionFailed(HTTPError):
    code = 412
    msg = "Precondition Failed"


class HTTPErrorRequestEntityTooLarge(HTTPError):
    code = 413
    msg = "Request Entity Too Large"


class HTTPErrorRequestTooLarge(HTTPError):
    code = 414
    msg = "Request URI Too Large"


class HTTPErrorUnsupportedMediaType(HTTPError):
    code = 415
    msg = "Unsupported Media Type"


class HTTPErrorTooManyRequests(HTTPError):
    code = 429
    msg = "Too Many Requests"


class HTTPErrorInternalServerError(HTTPError):
    code = 500
    msg = "Internal Server Error"


class HTTPErrorNotImplemented(HTTPError):
    code = 501
    msg = "Method Not Implemented"


class HTTPErrorVersionNotSupported(HTTPError):
    msg = "Version not supported"
    code = 505

HTTPError.code_to_error = {
    400: HTTPErrorBadRequest,
    401: HTTPErrorUnauthorized,
    402: HTTPErrorPaymentRequired,
    403: HTTPErrorForbidden,
    404: HTTPErrorNotFound,
    405: HTTPErrorMethodNotAllowed,
    406: HTTPErrorNotAcceptable,
    407: HTTPErrorProxyAuthenticationRequired,
    408: HTTPErrorRequestTimeout,
    409: HTTPErrorConflict,
    410: HTTPErrorGone,
    411: HTTPErrorLengthRequired,
    412: HTTPErrorPreconditionFailed,
    413: HTTPErrorRequestEntityTooLarge,
    414: HTTPErrorRequestTooLarge,
}

__all__ = [
    'HTTPError',
    'HTTPErrorInternalServerError',
    'HTTPErrorBadRequest',
    'HTTPErrorUnauthorized',
    'HTTPErrorPaymentRequired',
    'HTTPErrorForbidden',
    'HTTPErrorNotFound',
    'HTTPErrorMethodNotAllowed',
    'HTTPErrorNotAcceptable',
    'HTTPErrorProxyAuthenticationRequired',
    'HTTPErrorRequestTimeout',
    'HTTPErrorConflict',
    'HTTPErrorGone',
    'HTTPErrorLengthRequired',
    'HTTPErrorPreconditionFailed',
    'HTTPErrorRequestEntityTooLarge',
    'HTTPErrorRequestTooLarge',
    'HTTPErrorUnsupportedMediaType',
    'HTTPErrorInternalServerError',
    'HTTPErrorNotImplemented',
    'HTTPErrorVersionNotSupported',
]
