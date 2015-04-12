#
# growler/http/Error.py
#

import sys


class HTTPError(Exception):
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

    def __init__(self, code=None, phrase=None, ex=None):
        """
        Construct an http error, if code or phrase not defined, use default.
        """
        self.phrase = phrase or self.msg
        self.code = code or self.code
        Exception.__init__(self, self.phrase)
        self.sys_exception = ex
        self.traceback = sys.exc_info()[2]

    def PrintSysMessage(self, printraceback=True):
        if self.sys_exception:
            print(self.sys_exception)
        if printraceback and self.traceback:
            print(self.traceback)

    @classmethod
    def get_from_code(cls, code):
        return {
            400: HTTPErrorBadRequest,
            401: HTTPErrorUnauthorized,
            402: HTTPErrorPaymentRequired,
            403: HTTPErrorForbidden,
            404: HTTPErrorNotFound,
            410: HTTPErrorGone
            }(code, None)


class HTTPErrorBadRequest(HTTPError):
    code = 400
    msg = "Bad Request"


class HTTPErrorUnauthorized(HTTPError):
    code = 401
    msg = "Unauthorized"


class HTTPErrorPaymentRequired(HTTPError):
    code = 402
    msg = "Payment Required"


# HTTPErrorForbidden = HTTPError.__init__({}, 403, "Forbidden")
class HTTPErrorForbidden(HTTPError):
    code = 403
    msg = "Forbidden"


class HTTPErrorNotFound(HTTPError):
    code = 405
    msg = "Not Found"


class HTTPErrorGone(HTTPError):
    code = 410
    msg = "Gone"


class HTTPErrorRequestTooLarge(HTTPError):
    code = 414
    msg = "Request-URI Too Large"


class HTTPErrorUnsupportedMediaType(HTTPError):
    code = 415
    msg = "Unsupported Media Type"


class HTTPErrorInternalServerError(HTTPError):
    code = 500
    msg = "Internal Server Error"


class HTTPErrorNotImplemented(HTTPError):
    code = 501
    msg = "Method Not Implemented"


class HTTPErrorVersionNotSupported(HTTPError):
    msg = "Version not supported"
    code = 505


__all__ = [
    'HTTPError',
    'HTTPErrorInternalServerError',
    'HTTPErrorBadRequest',
    'HTTPErrorUnauthorized',
    'HTTPErrorPaymentRequired',
    'HTTPErrorForbidden',
    'HTTPErrorNotFound',
    'HTTPErrorGone',
    'HTTPErrorRequestTooLarge',
    'HTTPErrorUnsupportedMediaType',
    'HTTPErrorInternalServerError',
    'HTTPErrorNotImplemented',
    'HTTPErrorVersionNotSupported',
]
