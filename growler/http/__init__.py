#
# growler/__init__.py
#

from .Parser import HTTPParser
from .Request import HTTPRequest
from .Response import HTTPResponse
from .Error import *

__all__ = ['HTTPRequest', 'HTTPResponse', 'HTTPParser', 'HTTPError']
__all__.extend(Error.__all__)

import mimetypes

mimetypes.init()

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

HTTPCodes = {
  200 : "OK",
  301 : "Moved Permanently",
  302 : "Found"
}
