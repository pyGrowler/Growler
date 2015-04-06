#
# growler/http/Parser.py
#

import asyncio

from termcolor import colored

from .Error import (HTTPErrorBadRequest)

MAX_REQUEST_LENGTH = 4096  # 4KB
# from urllib.parse import (quote, parse_qs)


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
    def read_next_header(self):
        """
        A coroutine to generate headers. It uses read_next_line to get headers
        line by line - allowing a quick response to invalid requests.
        """
        # No buffer has been saved - get the next line
        if self._header_buffer is None:
            line = yield from self.read_next_line()
        # if there was a header saved, use that (and clear the buffer)
        else:
            line, self._header_buffer = self._header_buffer, None

        # end of the headers - 'None' will end an iteration
        if line == '':
            return None

        # TODO: warn better than a print statement
        if line[0] == ' ':
            print("WARNING: Header leads with whitespace")

        next_line = yield from self.read_next_line()

        # if next_line starts with a space, append this line to the previous
        while next_line != '' and next_line[0] == ' ':
            line += next_line
            next_line = yield from self.read_next_line()

        # next_line is now the beginning of the 'next_header', while 'line'
        #  is the current header
        self._header_buffer = next_line

        try:
            key, value = map(str.strip, line.split(":", 1))
        except ValueError as e:
            err_str = "ERROR parsing headers. Input '{}'".format(line)
            print(colored(err_str, 'red'))
            raise HTTPBadRequest(e)

        return {'key': key, 'value': value}

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
        req_lst = req_line.split()
        return req_lst
