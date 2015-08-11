#
# growler/http/__init__.py
#
# flake8: noqa
#
"""
Sub-package dealing with HTTP implementation. In this pacakge we have the
asyncio protocol, server, parser, and request and response objects.
"""

from .parser import Parser
from .request import HTTPRequest
from .response import HTTPResponse
from .protocol import GrowlerHTTPProtocol
from .errors import __all__ as http_errors
from .status import Status
from .methods import HTTPMethod

from http.server import BaseHTTPRequestHandler

import mimetypes


mimetypes.init()

__all__ = [
    'HTTPRequest',
    'HTTPResponse',
    'HTTPParser',
    'GrowlerHTTPProtocol',
]

__all__.extend(http_errors)

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

HTTPStatusPhrase = Status.Phrase
