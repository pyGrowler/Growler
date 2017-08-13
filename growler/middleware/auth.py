#
# growler/middleware/auth.py
#
import logging

logger = logging.getLogger(__name__)


class Auth:
    """
    Authentication middleware used to log users or validate services.
    """

    def __init__(self):
        self.log = logger.getChild("id=%x" % id(self))

    def __call__(self):
        """
        """
        return self.do_authentication

    def do_authentication(self, req, res):
        """
        Unimplemented middleware to be overloaded by subclasses
        """
        raise NotImplementedError
