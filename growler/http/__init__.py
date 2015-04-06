#
# growler/http/__init__.py
#
"""
Sub-package dealing with HTTP implementation. In this pacakge we have the
asyncio protocol, server, parser, and request and response objects.
"""

from .parser import HTTPParser
from .request import HTTPRequest
from .Response import HTTPResponse
from .Error import *
from .server import create_server

from http.server import BaseHTTPRequestHandler

import mimetypes

mimetypes.init()


__all__ = ['HTTPRequest', 'HTTPResponse', 'HTTPParser', 'HTTPError']
__all__.extend(Error.__all__)


KB = 1024
MB = KB ** 2
GB = KB ** 3

MAX_REQUEST_LENGTH = 4 * KB
MAX_POST_LENGTH = 2 * MB

# MAX_REQUEST_LENGTH = 96

# End of line and end of header
EOL = "\r\n"
# EOL = "\n"
HEADER_DELIM = EOL * 2

RESPONSES = BaseHTTPRequestHandler.responses

HTTPCodes = {
  200 : "OK",
  301 : "Moved Permanently",
  302 : "Found"
}
