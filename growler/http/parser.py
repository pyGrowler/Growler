#
# growler/http/Parser.py
#

import asyncio
import re

from urllib.parse import (unquote, urlparse, parse_qs)
from termcolor import colored

from growler.http.Error import (
    HTTPErrorNotImplemented,
    HTTPErrorBadRequest,
    HTTPErrorVersionNotSupported,
)

INVALID_CHAR_REGEX = '[\x00-\x1F\x7F()<>@,;:\[\]={} \t\\\\\"]'
contains_invalid_char = re.compile(INVALID_CHAR_REGEX).search

MAX_REQUEST_LENGTH = 4096  # 4KB
# from urllib.parse import (quote, parse_qs)


class Parser:
    """
    New version of the Growler HTTPParser class. Responsible for interpreting
    the reqests made by the client and creating a request object.
    """

    def __init__(self, queue):
        """
        Construct a Parser object.

        @param queue asyncio.queue: The queue in which to put parsed items.
            This is assumed to be read from the responder which created it.
        """
        self.queue = queue
        self.EOL_TOKEN = None
        self._buffer = []
        self.encoding = 'utf-8'
        self.HTTP_VERSION = None
        self._header_buffer = None
        self.headers = dict()

        self.needs_request_line = True
        self.needs_headers = True

    def consume(self, data):
        try:
            data = data.decode(self.encoding)
        except UnicodeDecodeError:
            raise HTTPErrorBadRequest

        print("[Parser::consume] {}".format(data.encode()))

        if self._find_newline(data) == -1:
            self._buffer.append(data)
            return

        lines = ''.join(self._buffer + [data]).split(self.EOL_TOKEN)

        # The last element was NOT a complete line, put back in the buffer
        last_line = lines.pop()

        if not data.endswith(self.EOL_TOKEN):
            self._buffer = [last_line]
        else:
            self._buffer.clear()

        # process request line
        if self.needs_request_line:
            self.parse_request_line(lines.pop(0))
            self.queue.put_nowait({
                'method': self.method,
                'version': self.version,
                'url': self.parsed_url
            })
            self.needs_request_line = False

        # process headers
        if lines and self.needs_headers:
            print("LINES",lines)
            self.store_headers_from_lines(lines)

            # nothing was left in buffer - we have finished headers
            if not self._header_buffer:
                self.queue.put_nowait(self.headers)
                self.needs_headers = False


    def parse_request_line(self, req_line):
        """
        Simply splits the request line into three components.
        TODO: Check that there are 3 and validate the method/path/version
        """
        try:
            method, request_uri, version = req_line.split()
        except ValueError:
            raise HTTPErrorBadRequest()

        if version not in ('HTTP/1.1', 'HTTP/1.0'):
            raise HTTPErrorVersionNotSupported()

        # save 'method' to self and get the correct function to finish
        # processing
        num_str = version[version.find('/')+1:]
        self.HTTP_VERSION = tuple(num_str.split('.'))
        self.version_number = float(num_str)
        self.version = version
        self.method = method
        self._process_headers = {
          "GET": self.process_get_headers,
          "POST": self.process_post_headers
        }.get(method, None)

        # Method not found
        if self._process_headers is None:
            err = "Unknown HTTP Method '{}'".format(method)
            raise HTTPErrorNotImplemented(err)

        self.original_url = request_uri
        self.parsed_url = urlparse(request_uri)
        self.path = unquote(self.parsed_url.path)
        self.query = parse_qs(self.parsed_url.query)

        return method, self.parsed_url, version

    def _acquire_header_buffer(self):
        self.headers[self._header_buffer['key']] = self._header_buffer['value']
        self._header_buffer = None

    def _find_newline(self, string):
        # we have not processed the first line yet
        if self.EOL_TOKEN is None:
            line_end_pos = string.find('\n')
            if line_end_pos != -1:
                prev_char = string[line_end_pos-1]
                self.EOL_TOKEN = '\r\n' if prev_char is '\r' else '\n'
            else:
                return -1
        return string.find(self.EOL_TOKEN)

    def store_headers_from_lines(self, lines):
        empty_line = False
        for line in lines:
            print("LINE: '{}'".format(line))
            # we are done parsing headers!
            if line is '':
                self._acquire_header_buffer()
                break
                # empty_line = True
                # continue
            empty_line = False

            if line.startswith((' ', '\t')):
                line = line.strip()
                val = self.header_buffer['value']
                if isinstance(val, str):
                    self.header_buffer['value'] = [val, line]
                else:
                    self.header_buffer['value'] += [line]
                continue

            if self._header_buffer:
                self._acquire_header_buffer()

            self._header_buffer = self.header_from_line(line)

    @classmethod
    def header_from_line(cls, line):
        try:
            key, value = map(str.strip, line.split(':', 1))
        except ValueError as e:
            err_str = "ERROR parsing headers. Input '{}'".format(line)
            print(colored(err_str, 'red'))
            raise HTTPErrorBadRequest(msg=e)

        if contains_invalid_char(key):
            raise HTTPErrorBadRequest

        key = key.upper()
        return {'key': key, 'value': value}

    def process_get_headers(self, data):
        pass

    def process_post_headers(self, data):
        pass


class HTTPParser(object):
    """
    Growler's implementation of an HTTP parsing class. An HTTPRequest object
    uses this to read data from the stream and extract HTTP parameters,
    headers, and body. The important functions are coroutines
    'read_next_header' and 'read_body'.

    Current implementation accepts both LF and CRLF line endings, discovered
    while processing the first line. Each header is read in one at a time.
    """
    def __init__(self, req, instream=None):
        """
        Create a Growler HTTP Parser.

        @param req: The HTTPRequest with the stream to build
        @type req: growler.HTTPRequest

        @param instream: The stream to read. If None, use the stream from the
            req
        @type instream: asyncio.StreamReader
        """
        self._stream = req._stream if not instream else instream
        self._req = req
        self._buffer = ''
        self.EOL_TOKEN = None
        self.read_buffer = ''
        self.bytes_read = 0
        self.max_read_size = MAX_REQUEST_LENGTH
        self.max_bytes_read = MAX_REQUEST_LENGTH
        self.data_future = asyncio.Future()
        self._header_buffer = None

    @asyncio.coroutine
    def _read_data(self):
        """
        Reads in a block of data (at most self.max_read_size bytes) and returns
        the decoded string.
        """
        data = yield from self._stream.read(self.max_read_size)
        self.bytes_read += len(data)
        return data.decode()

    @asyncio.coroutine
    def read_next_line(self, line_future=None):
        """
        Returns a single line read from the stream. If the EOL char has not
        been determined, it will wait for '\n' and set EOL to either LF or
        CRLF. This returns a single line, and stores the rest of the read in
        data in self._buffer

        @param line_future: A future to save the line to, if requested, else
                it is returned
        @type line_future: asyncio.Future
        """
        # Keep reading data until a newline is found
        while self.EOL_TOKEN is None:
            next_str = yield from self._read_data()
            line_end_pos = next_str.find('\n')
            self._buffer += next_str
            if line_end_pos != -1:
                if next_str[line_end_pos-1] == '\r':
                    self.EOL_TOKEN = '\r\n'
                else:
                    self.EOL_TOKEN = '\n'

        line_ends_at = self._buffer.find(self.EOL_TOKEN)

        while line_ends_at == -1:
            self._buffer += yield from self._read_data()
            line_ends_at = self._buffer.find(self.EOL_TOKEN)

        # split!
        line, self._buffer = self._buffer.split(self.EOL_TOKEN, 1)

        # yield from asyncio.sleep(0.75) # artificial delay
        return line

    @asyncio.coroutine
    def read_body(self):
        """
        Finishes reading the request. This method expects content-length to be
        defined in self.headers, and will read that many bytes from the stream.
        """
        # There is no body - return None
        if self.headers['content-length'] == 0:
            return None

        # Get length of whatever is already read into the buffer
        bytes_read = len(self._buffer)
        if self.headers['content-length'] < bytes_read:
            err_str = "Body too large. Expecting {} bytes received {}".format(
                self.headers['content-length'],
                bytes_read)
            raise HTTPErrorBadRequest(err_str)

        self.max_read_size = self.headers['content-length'] - bytes_read

        while self.max_read_size != 0:
            next_str = yield from self._read_data()
            bytes_read += len(next_str)
            self.max_read_size = self.headers['content-length'] - bytes_read
            self._buffer += next_str

        res, self._buffer = self._buffer, ''
        return res

    def parse_request_line(self, req_line):
        """
        Simply splits the request line into three components.
        TODO: Check that there are 3 and validate the method/path/version
        """
        req_lst = req_line.split("\n")
        return req_lst
