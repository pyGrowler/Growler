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

    Class responsible for interpreting the reqests made by the client. This is
    where the actual implementation of the HTTP occurs.

    The parser object is created by the client's GrowlerHTTPResponder upon
    construction. When data is passed to the responder's on_data method, the
    consume method of the parser is called. If the data does not contain the
    complete header, nor finishes the header, consume returns None, otherwise
    the remaining data (the body/beginning of body) is returned as encoded
    bytes.

    Most users do not need to interact with the parser. The default respnoder
    class (GrowlerHTTPResponder) accepts a parser_factor method which is called
    to create the parser. This should make it easy to use a custom parser.

    Current implementation accepts both LF and CRLF line endings, discovered
    while processing the first line. Each header is read in one at a time, as
    they come in over the wire.

    Upon finding an error the Parser will throw a 'BadHTTPRequest' exception.

    Parameters
    ----------
    parent : growler.HTTPResponder
        The 'parent' responder which will forward client data to the parser,
        and the parser will send parsed data back.
    """

    def __init__(self, parent):
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

        # create the parser generator 'object'
        self._http_parser = self._http_parser()
        self._http_parser.send(None)

    def consume(self, data):
        """
        Consumes data provided by the responder.

        If headers have finished being read in, the buffer containing the
        avaiable body is returned (as bytes); note that the body might be
        incomplete and more data will come in via the asynchronous transport.
        If there is no body, the empty bytes object is returned (b'').

        If headers have NOT finished, None is returned.

        Parameters
        ----------
        data : bytes
            data to be parsed

        Raises
        ------
        BadHTTPRequest
            When any unexpected values are encountered in the data
        """
        body = self._http_parser.send(data)
        return body

    def _http_parser(self):
        """
        Meat of the parsing algorithm. This is a generator that data is 'sent'
        to by the consume method. Using the generator type allows state to be
        maintained despite not having all data. It is assumed that this is more
        efficient than checking state (headers parsed, EOL found, etc) on every
        consume call, but I'm not going to check this.
        """

        buffer = bytearray()

        # first, find first EOL (i.e. get request line)
        while self.EOL_TOKEN is None:

            # use yield to have data sent to us - store in buffer
            buffer += yield
            if len(buffer) > MAX_REQUEST_LENGTH:
                raise HTTPErrorBadRequest("Max request length exceeded")
            self.EOL_TOKEN = self.determine_newline(buffer)

        # we now have the newline character - get request line + any header
        # lines, last element remains the buffer
        req_line, *header_lines, buffer = buffer.split(self.EOL_TOKEN)

        # save raw_request_line (as str)
        try:
            self.raw_request_line = req_line.decode()
        except UnicodeDecodeError:
            raise HTTPErrorBadRequest

        self.parse_request_line(self.raw_request_line)

        # header parser is the algorithm for parsing... headers
        header_parser = self._header_parser_lines()
        header_parser.send(None)

        body_data = None

        while body_data is None:
            # send header lines to header_parser generator
            for hkey, hval in header_parser.send(header_lines):
                if hkey is None:
                    body_data = self.EOL_TOKEN.join(hval) + buffer
                    break
                self.headers[hkey] = hval
            else:  # if no break
                buffer += yield
                *header_lines, buffer = buffer.split(self.EOL_TOKEN)
        yield body_data

    def _header_parser_lines(self):
        """
        Same behavior as _header_parser, but accepts a list of lines, rather
        than one line at a time.
        """

        outgoing_list, lines = [], []

        # init loop - get sent a non-empty list of lines
        while len(lines) == 0:
            lines = yield outgoing_list

        line = lines.pop(0)

        while line != b'':

            # get key-value from line
            key, value = self.header_key_value(line)
            key = key.upper()

            # ensure there is a following line
            while len(lines) == 0:
                lines = yield outgoing_list
                outgoing_list = []

            # if next line is a continuation - do stuff
            if lines[0].startswith((b' ', b'\t')):
                value = [value]
                while lines[0].startswith((b' ', b'\t')):
                    value += [lines.pop(0).strip().decode()]

                    while len(lines) == 0:
                        lines = yield outgoing_list
                        outgoing_list = []

            # at this point we know next line is NOT continuation line, so we
            # can add key/value to next result
            outgoing_list.append((key, value))
            line = lines.pop(0)

        outgoing_list.append((None, lines))
        yield outgoing_list

    def parse_request_line(self, req_line):
        """
        Splits the request line given into three components. Ensures that the
        version and method are valid for this server, and uses the urllib.parse
        function to parse the request URI.

        Note
        ----
        This method has the additional side effect of updating all request line
        related attributes of the parser.

        Returns
        -------
        request_tuple : tuple
            Tuple containing the parsed (method, parsed_url, version)

        Raises
        ------
        HTTPErrorBadRequest
            If request line is invalid
        HTTPErrorNotImplemented
            If HTTP method is not recognized
        HTTPErrorVersionNotSupported
            If HTTP version is not recognized
        """
        try:
            self.method_str, self.original_url, self.version = req_line.split()
        except ValueError:
            raise HTTPErrorBadRequest()

        if self.version not in ('HTTP/1.1', 'HTTP/1.0'):
            raise HTTPErrorVersionNotSupported()

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
        r"""
        Looks for a newline character in bytestring parameter 'data'.
        Currently only looks for strings '\r\n', '\n'. If '\n' is found at the
        first position of the string, this raises an exception.

        Parameters
        ----------
        data : bytes
            The data to be searched

        Returns
        -------
        None : If no-newline is found
        One of '\n', '\r\n', whichever is found first
        """
        line_end_pos = data.find(b'\n')

        if line_end_pos == -1:
            return None
        elif line_end_pos == 0:
            return b'\n'

        prev_char = data[line_end_pos - 1]

        return b'\r\n' if (prev_char is b'\r'[0]) else b'\n'

    def header_key_value(self, line):
        """
        Takes a byte string and attempts to decode and build a key-value pair
        for the header. Header names are checked for validity. In the event
        that the string can not be split on a ':' char, an
        HTTPErrorInvalidHeader exception is raised.
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
        header-key characters
        """
        return header == '' or bool(INVALID_CHAR_REGEX.search(header))

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
