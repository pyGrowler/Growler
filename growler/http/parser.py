#
# growler/http/parser.py
#

import re
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

INVALID_CHAR_REGEX = re.compile('[\x00-\x1F\x7F\(\),/:;<=>?@\[\]\{\} \t\\\\\"]')

MAX_REQUEST_LENGTH = 1024 ** 2  # 1 MB
MAX_REQUEST_LINE_LENGTH = 8 * 1024  # 8 KB


class Parser:
    """
    Class responsible for interpreting the reqests made by the client.
    This is where the actual implementation of the HTTP occurs.

    The parser object is created by the client's GrowlerHTTPResponder
    upon construction. When data is passed to the responder's on_data
    method, the consume method of the parser is called. If the data
    does not contain the complete header, nor finishes the header,
    consume returns None, otherwise the remaining data (the body or
    beginning of body) is returned as encoded bytes.

    Most users do not need to interact with the parser. The default
    respnoder class (GrowlerHTTPResponder) accepts a parser_factor
    method which is called to create the parser. This should make it
    easy to use a custom parser.

    Current implementation accepts both LF and CRLF line endings,
    discovered while processing the first line. Each header is read in
    one at a time, as they come in over the wire.

    Upon finding an error the Parser will throw a 'BadHTTPRequest'
    exception.
    """
    EOL_TOKEN = None
    HTTP_VERSION = None

    def __init__(self, parent):
        """
        Construct HTTP parser.

        Parameters:
            parent (growler.HTTPResponder): The 'parent' responder which
                will forward client data to the parser, and the parser will
                send parsed data back to this object.
        """
        self.parent = parent
        self._buffer = bytearray()

        self.encoding = 'utf-8'
        self.headers = dict()

        # create the parser generator 'object'
        self._http_parser = self._http_parser()
        self._http_parser.send(None)

    def consume(self, data):
        """
        Consumes data provided by the responder.

        If headers have finished being read in, the buffer containing
        the avaiable body is returned (as bytes); note that the body
        might be incomplete and more data will come in via the
        asynchronous transport.
        If there is no body, the empty bytes object is returned (b'').

        If headers have NOT finished, None is returned.

        Parameters:
            data (bytes): Data to be parsed

        Raises:
            BadHTTPRequest: When any unexpected values are encountered
                in the data
        """
        body = self._http_parser.send(data)
        return body

    def _http_parser(self):
        """
        Meat of the parsing algorithm. This is a generator that data is
        'sent' to by the consume method. Using the generator type allows
        state to be maintained despite not having all data. It is assumed
        that this is more efficient than checking state (headers parsed,
        EOL found, etc) on every consume call, but I'm not going to check
        this.

        Yields:
            None: Indicates headers have not been completed and the
                parser is expecting more bytes to be sent to it (via
                'send()')
            bytes: The (potentially incomplete) body data. This signifies
                the parser has completed parsing HTTP headers (stored in
                parser.headers) and should no longer be sent any data.
        """
        # first, find first EOL (i.e. get request line)
        yield from self._receive_eol_token()

        # split the request line and headers (modifies buffer)
        yield from self._parse_and_store_req_line(self.EOL_TOKEN)

        # completes when all headers have been processed and stored
        yield from self._parse_and_store_headers()

        # we send back the rest of the body
        yield self._buffer

    def _receive_eol_token(self):
        """
        A simple coroutine that is sent data until the first end of line
        (EOL) token is found. This sets the EOL_TOKEN member of the parser
        and pushes all data into the buffer.
        """
        while self.EOL_TOKEN is None:
            # use yield to have data sent to us - store in buffer
            self._buffer += yield
            if len(self._buffer) > MAX_REQUEST_LENGTH:
                raise HTTPErrorBadRequest("Max request length exceeded")
            self.EOL_TOKEN = self.determine_newline(self._buffer)

    def _parse_and_store_req_line(self, eol):
        """
        """
        yield from self._receive_eol_token()
        req_line, _, self._buffer = self._buffer.partition(eol)
        # req_line, header_lines = self._split_req_headers()
        # save raw_request_line (as str)
        self._store_request_line(req_line)
        # return; yield

    def _parse_and_store_headers(self):
        """
        Coroutine used retrieve header data and parse each header until
        the body is found.
        """

        HEADER_END = self.EOL_TOKEN * 2

        header_storage = self._store_header()
        header_storage.send(None)
        headers = []

        for header_line in self._next_header_line():
            if header_line is None:
                self._buffer += yield
                continue
            else:
                header_storage.send(header_line)

        self.headers = header_storage.send(None)

    def _store_header(self):
        """
        Logic & state behind storing headers. This is a coroutine that
        should be sent header lines in the usual fashion. Sending it
        None will indicate there are no more lines, and the dictionary
        of headers will be returned.
        """
        key, value = None, None
        headers = []
        header_line = yield
        while header_line is not None:
            if not header_line.startswith((b' ', b'\t')):
                if key:
                    headers.append((key, value))
                key, value = self.split_header_key_value(header_line)
                key = key.upper()
            else:
                next_val = header_line.strip().decode()
                if isinstance(value, list):
                    value.append(next_val)
                else:
                    value = [value, next_val]
            header_line = yield

        if key is not None:
            headers.append((key, value))

        yield dict(headers)


    def _next_header_line(self):
        """
        Non-destructive buffer processor returning all lines (defined
        by self.EOL_TOKEN) in self._buffer. If end of buffer is reached,
        None is yielded and it is expected that more bytes will be
        appended to the buffer by the caller.

        Upon finding an empty header, this method trims the buffer to
        the start of the body
        """
        eol = self.EOL_TOKEN
        eol_length = len(eol)
        start = 0
        end = self._buffer.find(eol)

        # if start == end, foudn empty header - stop iterating
        while start != end:

            # end of line was found
            if end != -1:
                yield self._buffer[start:end]
                start = end + eol_length
            # end of line was not found - request more buffer data
            else:
                yield None

            # find next end of line
            end = self._buffer.find(eol, start)

        # trim buffer
        del self._buffer[:end + eol_length]

    def _store_request_line(self, req_line):
        """
        Splits the request line given into three components.
        Ensures that the version and method are valid for this server,
        and uses the urllib.parse function to parse the request URI.

        Note:
            This method has the additional side effect of updating all
            request line related attributes of the parser.

        Returns:
            tuple: Tuple containing the parsed (method, parsed_url,
                version)

        Raises:
            HTTPErrorBadRequest: If request line is invalid
            HTTPErrorNotImplemented: If HTTP method is not recognized
            HTTPErrorVersionNotSupported: If HTTP version is not
                recognized.
        """
        if not isinstance(req_line, str):
            try:
                req_line = self.raw_request_line = req_line.decode()
            except UnicodeDecodeError:
                raise HTTPErrorBadRequest

        try:
            self.method_str, self.original_url, self.version = req_line.split()
        except ValueError:
            raise HTTPErrorBadRequest()

        if self.version not in ('HTTP/1.1', 'HTTP/1.0'):
            raise HTTPErrorVersionNotSupported(self.version)

        # allow lowercase methodname?
        # self.method_str = self.method_str.upper()

        # save 'method' and get the correct function to finish processing
        try:
            self.method = Gen_HTTP_Method[self.method_str]
        except KeyError:
            # Method not found
            err = "Unknown HTTP Method '{}'".format(self.method_str)
            raise HTTPErrorNotImplemented(err)

        self._process_headers = {
            HTTPMethod.GET: self.process_get_headers,
            HTTPMethod.POST: self.process_post_headers
        }.get(self.method, lambda data: True)

        _, num_str = self.version.split('/', 1)
        self.HTTP_VERSION = tuple(num_str.split('.'))
        self.version_number = float(num_str)

        self.parsed_url = urlparse(self.original_url)
        self.path = unquote(self.parsed_url.path)
        self.query = parse_qs(self.parsed_url.query)

        return self.method, self.parsed_url, self.version

    @staticmethod
    def determine_newline(data):
        """
        Looks for a newline character in bytestring parameter 'data'.
        Currently only looks for strings '\r\n', '\n'. If '\n' is
        found at the first position of the string, this raises an
        exception.

        Parameters:
            data (bytes): The data to be searched

        Returns:
            None: If no-newline is found
            One of '\n', '\r\n': whichever is found first
        """
        line_end_pos = data.find(b'\n')

        if line_end_pos == -1:
            return None
        elif line_end_pos == 0:
            return b'\n'

        prev_char = data[line_end_pos - 1]

        return b'\r\n' if (prev_char is b'\r'[0]) else b'\n'

    def split_header_key_value(self, line):
        """
        Takes a byte string and attempts to decode and build a key-value
        pair for the header. Header names are checked for validity. In
        the event that the string can not be split on a ':' char, an
        HTTPErrorInvalidHeader exception is raised.

        Parameters:
            line (bytes): header bytes which will be automatically
                decoded and split between key + value.

        Returns:
            tuple of 2 strs: key + value

        Raises:
            HTTPErrorInvalidHeader: The string cannot be split on a ':'
                character or the header key is an invalid HTTP header
                name.
        """
        try:
            line = line.decode()
            key, value = map(str.strip, line.split(':', 1))
        except ValueError:
            raise HTTPErrorInvalidHeader

        if self.is_invalid_header_name(key):
            raise HTTPErrorInvalidHeader

        return key, value

    @staticmethod
    def is_invalid_header_name(header):
        """
        Returns true if the string passes the regex checking for invalid
        header-key characters.

        Returns:
            bool: True if header is empty or matches the module's
                INVALID_CHAR_REGEX regex objec.
        """
        return header == '' or bool(INVALID_CHAR_REGEX.search(header))

    def process_get_headers(self, data):
        """
        Called upon receiving a GET HTTP request to do specific 'GET'
        things to the list of headers.
        Currently does nothing.
        """
        pass

    def process_post_headers(self, data):
        """
        Called upon receiving a POST HTTP request to do specific 'POST'
        things to the headers.
        Currently does nothing.
        """
        pass
