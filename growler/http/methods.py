#
# growler/http/methods.py
#


import enum


class HTTPMethod(enum.Enum):
    ALL = 0x0
    GET = 0x1
    POST = 0x2
    DELETE = 0x4
    PUT = 0x8


string_to_method = {
    "GET": HTTPMethod.GET,
    "POST": HTTPMethod.POST,
    "DELETE": HTTPMethod.DELETE,
    "PUT": HTTPMethod.PUT,
}
