#
# growler/http/methods.py
#
# flake8: noqa
#

import enum


class HTTPMethod(enum.IntEnum):
    ALL    = 0b011111
    GET    = 0b000001
    POST   = 0b000010
    DELETE = 0b000100
    PUT    = 0b001000
    HEAD   = 0b010000


string_to_method = {
    "GET": HTTPMethod.GET,
    "POST": HTTPMethod.POST,
    "DELETE": HTTPMethod.DELETE,
    "PUT": HTTPMethod.PUT,
    "HEAD": HTTPMethod.HEAD,
}


method_to_string = dict((v,k) for k, v in string_to_method.items())
