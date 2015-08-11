#
# growler/http/parser.py
#

import re
import sys
from urllib.parse import (unquote, urlparse, parse_qs)

from .methods import (
    HTTPMethod,
    string_to_method as Gen_HTTP_Method
)

from growler.http.errors import (
    HTTPErrorNotImplemented,
    HTTPErrorBadRequest,
    HTTPErrorInvalidHeader,
    HTTPErrorVersionNotSupported,
)

INVALID_CHAR_REGEX = re.compile('[\x00-\x1F\x7F(),/:;<=>?@\[\]{} \t\\\\\"]')

MAX_REQUEST_LENGTH = 1024 ** 2  # 1 MB
MAX_REQUEST_LINE_LENGTH = 8 * 1024  # 8 KB


class Parser:
    """
    New version of the Growler HTTPParser class. Responsible for interpreting
    the reqests made by the client and creating a request object.

    Current implementation accepts both LF and CRLF line endings, discovered
    while processing the first line. Each header is read in one at a time.

    Upon finding an error the Parser will throw a 'BadHTTPRequest' exception.
    """

    def __init__(self, parent):
        """
        Construct a Parser object.

        :param queue asyncio.queue: The queue in which to put parsed items.
            This is assumed to be read from the responder which created it.
        """
        self.parent = parent
        self.EOL_TOKEN = None
        self._buffer = []
        self.encoding = 'utf-8'
        self.HTTP_VERSION = None
        self._header_buffer = None
        self.headers = dict()

        self.needs_request_line = True
        self.needs_headers = True

        self.request_length = 0
        self.body_buffer = None

    def consume(self, data):
        """
        Consumes data provided by the responder.

        If headers have finished being read in, this returns asyncio.Future
        which will contain the body. Else it returns None.
        """
        self.request_length += len(data)

        if self.request_length > MAX_REQUEST_LENGTH:
            raise HTTPErrorBadRequest

        # if no newline - store in buffer
        if self.find_newline(data) == -1:
            self._buffer.append(data)
            return

        lines = b''.join(self._buffer + [data]).split(self.EOL_TOKEN)

        # The last element was NOT a complete line, put back in the buffer
        last_line = lines.pop()

        # last line didn't terminate - store back in buffer. Else, clear buffer
        if not data.endswith(self.EOL_TOKEN):
            self._buffer = [last_line]
        else:
            self._buffer.clear()

        # process request line (first line in 'lines')
        if self.needs_request_line:
            try:
                self.parse_request_line(lines.pop(0).decode())
            except UnicodeDecodeError:
                raise HTTPErrorBadRequest

            self.parent.set_request_line(self.method,
                                         self.parsed_url,
                                         self.version)
            self.needs_request_line = False

        if not lines:
            return

        # process headers
        if self.needs_headers:
            self.store_headers_from_lines(lines)

            # nothing was left in buffer - we have finished headers
            if not self._header_buffer:
                self.parent.headers = self.headers
                self.needs_headers = False

        # return None if we have not stored the body, else return the body
        return self.body_buffer

    def parse_request_line(self, req_line):
        """
        Splits the request line given into three components. Ensures that the
        version and method are valid for this server, and uses the urllib.parse
        function to parse the request URI.

        @return Tuple of (method, parsed_url, version)
        """
        try:
            method, request_uri, version = req_line.split()
        except ValueError:
            raise HTTPErrorBadRequest()

        if version not in ('HTTP/1.1', 'HTTP/1.0'):
            raise HTTPErrorVersionNotSupported()

        try:
            self.method = Gen_HTTP_Method[method]
        except KeyError:
            # Method not found
            err = "Unknown HTTP Method '{}'".format(method)
            raise HTTPErrorNotImplemented(err)

        # save 'method' to self and get the correct function to finish
        # processing
        num_str = version[version.find('/')+1:]
        self.HTTP_VERSION = tuple(num_str.split('.'))
        self.version_number = float(num_str)
        self.version = version

        self._process_headers = {
            HTTPMethod.GET: self.process_get_headers,
            HTTPMethod.POST: self.process_post_headers
        }.get(self.method, None)

        self.original_url = request_uri
        self.parsed_url = urlparse(request_uri)
        self.path = unquote(self.parsed_url.path)
        self.query = parse_qs(self.parsed_url.query)
        self.parent.parsed_query = self.query
        return self.method, self.parsed_url, version

    def _flush_header_buffer(self):
        """
        Stores the _header_buffer into the self.headers. Then Nonifies the
        _header_buffer.
        """
        self.headers[self._header_buffer['key']] = self._header_buffer['value']
        self._header_buffer = None

    def find_newline(self, string):
        """
        Finds an End-Of-Line character in the string. If this has not been
        determined, simply look for the \n, then check if there was an \r
        before it. If not found, return -1.
        Edgecase: If buffers end with '\r' and string starts with '\n' return
                  -2
        """
        if isinstance(string, str):
            string = string.encode()

        # we have not processed the first line yet
        if self.EOL_TOKEN is None:
            token = self.determine_newline_from_string(string)
            if token is None:
                return -1
            else:
                self.EOL_TOKEN = token
            position = string.find(self.EOL_TOKEN)
            if position == -1:
                position = -2
            return position

        return string.find(self.EOL_TOKEN)

    def determine_newline_from_string(self, string):
        """
        Looks for a newline character in bytestring parameter 'string'.
        Currently only looks for chars '\r\n', '\n'. If '\n' is found in the
        first position of the string, and there is at least one string in the
        _buffer member, this will check if the last character in last element
        of the buffer is '\r'.
        """
        line_end_pos = string.find(b'\n')
        if line_end_pos == 0:
            prev_char = self._buffer[-1][-1] if len(self._buffer) > 0 else b''
        elif line_end_pos != -1:
            prev_char = string[line_end_pos-1]
        else:
            return None

        return b'\r\n' if (prev_char is b'\r'[0]) else b'\n'

    def store_headers_from_lines(self, lines):
        """
        Takes the list of lines and gets a header from each string, storing
        first into the buffer, then checks for continuation of the header. If
        there is no continuing header - place the header into self.headers and
        continue parsing.
        """
        for lineno, line in enumerate(lines):
            # we are done parsing headers!
            if line is b'':
                self._flush_header_buffer()
                self.body_buffer = b''.join(lines[lineno:])
                break

            try:
                line = line.decode(self.encoding)
            except UnicodeDecodeError:
                raise HTTPErrorBadRequest

            if line.startswith((' ', '\t')):
                if self._header_buffer is None:
                    raise HTTPErrorInvalidHeader
                line = line.strip()
                val = self._header_buffer['value']
                if isinstance(val, str):
                    self._header_buffer['value'] = [val, line]
                else:
                    self._header_buffer['value'] += [line]
                continue

            if self._header_buffer:
                self._flush_header_buffer()

            self._header_buffer = self.header_from_line(line)

    def join_and_clear_buffer(self, data=b''):
        result = b''.join(self._buffer + [data])
        self._buffer.clear()
        return result

    @classmethod
    def header_from_line(cls, line):
        """
        Takes a string and attempts to build a key-value pair for the header
        object. Header names are checked for validity. In the event that the
        string can not be split on a ':' char, a HTTPErrorBadRequest exception
        is raised. The keys are stored as UPPER case.
        """
        try:
            key, value = map(str.strip, line.split(':', 1))
        except ValueError:
            # rederr = colored('ERROR', 'red')
            rederr = 'ERROR'
            err_str = "{} parsing headers. Input '{}'".format(rederr, line)
            print(err_str, file=sys.stderr)
            raise HTTPErrorInvalidHeader

        if cls.is_invalid_header_name(key):
            raise HTTPErrorInvalidHeader

        key = key.upper()
        return {'key': key, 'value': value}

    @classmethod
    def is_invalid_header_name(cls, string):
        """
        Returns true if the string passes the regex checking for invalid
        header-key characters
        """
        return string == '' or bool(INVALID_CHAR_REGEX.search(string))

    def process_get_headers(self, data):
        """
        Called upon receiving a GET HTTP request to do specific 'GET' things to
        the list of headers.
        """
        pass

    def process_post_headers(self, data):
        """
        Called upon receiving a POST HTTP request to do specific 'POST' things
        to the headers.
        """
        pass
