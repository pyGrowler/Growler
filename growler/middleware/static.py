#
# growler/middleware/static.py
#

import os
import mimetypes
import logging

log = logging.getLogger(__name__)


class Static():
    """
    Static middleware catches any uri paths which match a filesystem file and
    serves that file.

    :param path: The directory path to search for files. If this is a list, the
                 paths will be path-joined automatically.
    :type path: str/list
    """

    def __init__(self, path):
        # if list, do a pathjoin
        if isinstance(path, list):
            path = os.path.join(*path)

        # store as the computed absolute path, to avoid unexpected relative
        # path redirection
        self.path = os.path.abspath(path)

        # ensure that path exists
        if not os.path.isdir(self.path):
            log.error("[Static] No path exists at {}".format(self.path))
            raise Exception("Path '{}' does not exist.".format(self.path))

        log.info("%d Serving static files out of %s" % (id(self), self.path))

    def __call__(self, req, res):
        """
        Middleware handle function. Simply checks if matching path is a file,
        attempts to guess the file type, and sends the file.
        """
        filename = self.path + req.path
        if os.path.isfile(filename):
            mime = mimetypes.guess_type(filename)
            res.set_type(mime[0])
            res.send_file(filename)
            log.info("%d Sent %s (%s)" % (id(self), filename, mime[0]))
