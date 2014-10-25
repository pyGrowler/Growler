#
# growler/http.py
#


import growler

from .Parser import HTTPParser
from .Request import HTTPRequest
from .Response import HTTPResponse
from .Error import *

__all__ = ['HTTPRequest', 'HTTPResponse', 'HTTPParser', 'HTTPError']
__all__.extend(Error.__all__)

import asyncio
import sys
import json
from pprint import PrettyPrinter

import mimetypes

mimetypes.init()

KB = 1024
MB = KB ** 2

MAX_REQUEST_LENGTH = 4096 # 4KB
MAX_POST_LENGTH = 2 * 1024**3 # 2MB

# MAX_REQUEST_LENGTH = 96

# End of line and end of header
# EOL = "\r\n"
EOL = "\n"
HEADER_DELIM = EOL * 2

HTTPCodes = {
  200 : "OK",
  301 : "Moved Permanently",
  302 : "Found"
}
