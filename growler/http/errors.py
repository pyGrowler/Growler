#
# growler/http/errors.py
#
"""
Custom Exception subclasses relating to specific http errors.
"""

import sys
from urllib.error import HTTPError as UrllibHttpError
from growler.http import HttpStatus
from growler.utils.metaclasses import ItemizedMeta


class HTTPError(UrllibHttpError, metaclass=ItemizedMeta):
    """
    Generic HTTP Exception.

    Must be constructed with a code number, may be given an optional phrase.
    It is recommended to use one of the subclasses which is defined below.
    A helper function exists to get the appropriate error from a code:
        raise HTTPError.get_from_code(404)
        raise HTTPErrorNotFound()
    """

    _msg = None
    code = 0
    code_to_error = dict()

    def __init__(self, url=None, code=None, phrase=None, msg=None, ex=None):
        """
        Construct an http error, if code or phrase not defined, use default.
        """
        super().__init__(url, code or self.status.value, msg or self.msg, None, None)
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

    @property
    def msg(self):
        return self._msg or self.status.phrase

    @msg.setter
    def msg(self, value):
        self._msg = str(value)

    @classmethod
    def _getitem_(cls, key):
        if isinstance(key, int):
            # key by code
            err = cls.get_from_code(key)
            if err is not None:
                return err
        elif isinstance(key, str):
            # key by phrase
            for error in cls.code_to_error.values():
                if error.status.phrase == key:
                    return error
        raise HTTPErrorInvalidHttpError


class HTTPErrorBadRequest(HTTPError):
    status = HttpStatus.BAD_REQUEST


class HTTPErrorInvalidHeader(HTTPErrorBadRequest):
    msg = "Bad Request (Invalid Header Name)"


class HTTPErrorUnauthorized(HTTPError):
    status = HttpStatus.UNAUTHORIZED


class HTTPErrorPaymentRequired(HTTPError):
    status = HttpStatus.PAYMENT_REQUIRED


class HTTPErrorForbidden(HTTPError):
    status = HttpStatus.FORBIDDEN


class HTTPErrorNotFound(HTTPError):
    status = HttpStatus.NOT_FOUND


class HTTPErrorMethodNotAllowed(HTTPError):
    status = HttpStatus.METHOD_NOT_ALLOWED


class HTTPErrorNotAcceptable(HTTPError):
    status = HttpStatus.NOT_ACCEPTABLE


class HTTPErrorProxyAuthenticationRequired(HTTPError):
    status = HttpStatus.PROXY_AUTHENTICATION_REQUIRED


class HTTPErrorRequestTimeout(HTTPError):
    status = HttpStatus.REQUEST_TIMEOUT


class HTTPErrorConflict(HTTPError):
    status = HttpStatus.CONFLICT


class HTTPErrorGone(HTTPError):
    status = HttpStatus.GONE


class HTTPErrorLengthRequired(HTTPError):
    status = HttpStatus.LENGTH_REQUIRED


class HTTPErrorPreconditionFailed(HTTPError):
    status = HttpStatus.PRECONDITION_FAILED


class HTTPErrorRequestEntityTooLarge(HTTPError):
    status = HttpStatus.REQUEST_ENTITY_TOO_LARGE


class HTTPErrorRequestUriTooLarge(HTTPError):
    status = HttpStatus.REQUEST_URI_TOO_LONG


class HTTPErrorUnsupportedMediaType(HTTPError):
    status = HttpStatus.UNSUPPORTED_MEDIA_TYPE


class HTTPErrorRequestedRangeNotSatisfiable(HTTPError):
    status = HttpStatus.REQUESTED_RANGE_NOT_SATISFIABLE


class HTTPErrorExpectationFailed(HTTPError):
    status = HttpStatus.EXPECTATION_FAILED


class HTTPErrorUnprocessableEntity(HTTPError):
    status = HttpStatus.UNPROCESSABLE_ENTITY


class HTTPErrorLocked(HTTPError):
    status = HttpStatus.LOCKED


class HTTPErrorFailedDependency(HTTPError):
    status = HttpStatus.FAILED_DEPENDENCY


class HTTPErrorUpgradeRequired(HTTPError):
    status = HttpStatus.UPGRADE_REQUIRED


class HTTPErrorPreconditionRequired(HTTPError):
    status = HttpStatus.PRECONDITION_REQUIRED


class HTTPErrorTooManyRequests(HTTPError):
    status = HttpStatus.TOO_MANY_REQUESTS


class HTTPErrorRequestHeaderFieldsTooLarge(HTTPError):
    status = HttpStatus.REQUEST_HEADER_FIELDS_TOO_LARGE


class HTTPErrorInternalServerError(HTTPError):
    status = HttpStatus.INTERNAL_SERVER_ERROR


class HTTPErrorInvalidHttpError(HTTPErrorInternalServerError):
    msg = "Server attempted to raise invalid HTTP error"


class HTTPErrorNotImplemented(HTTPError):
    status = HttpStatus.NOT_IMPLEMENTED


class HTTPErrorBadGateway(HTTPError):
    status = HttpStatus.BAD_GATEWAY


class HTTPErrorServiceUnavailable(HTTPError):
    status = HttpStatus.SERVICE_UNAVAILABLE


class HTTPErrorGatewayTimeout(HTTPError):
    status = HttpStatus.GATEWAY_TIMEOUT


class HTTPErrorVersionNotSupported(HTTPError):
    status = HttpStatus.HTTP_VERSION_NOT_SUPPORTED


class HTTPErrorVariantAlsoNegotiates(HTTPError):
    status = HttpStatus.VARIANT_ALSO_NEGOTIATES


class HTTPErrorInsufficientStorage(HTTPError):
    status = HttpStatus.INSUFFICIENT_STORAGE


class HTTPErrorLoopDetected(HTTPError):
    status = HttpStatus.LOOP_DETECTED


class HTTPErrorNotExtended(HTTPError):
    status = HttpStatus.NOT_EXTENDED


class HTTPErrorNetworkAuthenticationRequired(HTTPError):
    status = HttpStatus.NETWORK_AUTHENTICATION_REQUIRED


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
    414: HTTPErrorRequestUriTooLarge,
    415: HTTPErrorUnsupportedMediaType,
    416: HTTPErrorRequestedRangeNotSatisfiable,
    417: HTTPErrorExpectationFailed,
    422: HTTPErrorUnprocessableEntity,
    423: HTTPErrorLocked,
    424: HTTPErrorFailedDependency,
    426: HTTPErrorUpgradeRequired,
    428: HTTPErrorPreconditionRequired,
    429: HTTPErrorTooManyRequests,
    431: HTTPErrorRequestHeaderFieldsTooLarge,

    500: HTTPErrorInternalServerError,
    501: HTTPErrorNotImplemented,
    502: HTTPErrorBadGateway,
    503: HTTPErrorServiceUnavailable,
    504: HTTPErrorGatewayTimeout,
    505: HTTPErrorVersionNotSupported,
    506: HTTPErrorVariantAlsoNegotiates,
    507: HTTPErrorInsufficientStorage,
    508: HTTPErrorLoopDetected,
    510: HTTPErrorNotExtended,
    511: HTTPErrorNetworkAuthenticationRequired,
}

__all__ = [
    # generic error
    'HTTPError',

    #  -- 4XX errors
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
    'HTTPErrorRequestUriTooLarge',
    'HTTPErrorUnsupportedMediaType',
    'HTTPErrorRequestedRangeNotSatisfiable',
    'HTTPErrorExpectationFailed',
    'HTTPErrorUnprocessableEntity',
    'HTTPErrorLocked',
    'HTTPErrorFailedDependency',
    'HTTPErrorUpgradeRequired',
    'HTTPErrorPreconditionRequired',
    'HTTPErrorTooManyRequests',
    'HTTPErrorRequestHeaderFieldsTooLarge',

    #  -- 5XX errors
    'HTTPErrorInternalServerError',
    'HTTPErrorNotImplemented',
    'HTTPErrorBadGateway',
    'HTTPErrorServiceUnavailable',
    'HTTPErrorGatewayTimeout',
    'HTTPErrorVersionNotSupported',
    'HTTPErrorVariantAlsoNegotiates',
    'HTTPErrorInsufficientStorage',
    'HTTPErrorLoopDetected',
    'HTTPErrorNotExtended',
    'HTTPErrorNetworkAuthenticationRequired',

    # -- derived errors
    'HTTPErrorInvalidHeader',
    'HTTPErrorInvalidHttpError',
]
