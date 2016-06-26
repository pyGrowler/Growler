#
# growler/middleware/static.py
#

import os
import re
import logging
import mimetypes
from pathlib import Path

log = logging.getLogger(__name__)


class Static:
    """
    Static middleware catches any URI paths which match a filesystem file and
    serves that file.

    This middleware uses the HTTPResponse object's send_file method to
    determine mime type. At this time there is no way to change this without
    subclassing.
    """

    INVALID_PATH = re.compile(r"(:?\.\.)")

    def __init__(self, path):
        """
        Construct Static method.
        Args:
            path (str or list): The directory path to search for files. If
                this is a list, the paths will be path-joined automatically.
        """
        # if list, do a pathjoin
        if isinstance(path, list):
            path = os.path.join(*path)

        # store as pathlib.Path, to avoid unexpected relative
        # path redirection
        self.path = Path(path)

        # ensure that path exists
        if not self.path.is_dir():
            log.error("[Static] No path exists at {}".format(self.path))
            raise Exception("Path '{}' does not exist.".format(self.path))

        log.info("%d Serving static files out of %s" % (id(self), self.path))

    def __call__(self, req, res):
        """
        Middleware handle function. Simply checks if matching path is a file,
        attempts to guess the file type, and sends the file. If the request
        has a reference to the parent path, '..', the request is ignored by this
        object.
        """
        filename = self.path / req.path

        # ignore anything that tries to reference an invalid path, such as
        # /../spam
        if any(map(self.INVALID_PATH.match, filename.parts)):
            return

        if filename.is_file():
            mime = mimetypes.guess_type(str(filename))
            stat = filename.stat()
            etag = "%x-%x" % (stat.st_mtime_ns, stat.st_size)
            res.headers['Etag'] = etag

            if req.headers['If-None-Match'] == etag:
                res.status_code = 304
                res.end()
                return

            res.set_type(mime[0])
            res.send_file(filename)
            log.info("%d Sent %s (%s)" % (id(self), filename, mime[0]))
