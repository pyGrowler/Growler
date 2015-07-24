#
# growler/middleware/auth.py
#


class Auth():
    """
    Authentication middleware used to log users or validate services.
    """

    def __init__(self):
        print("[Auth]")

    def __call__(self):
        """
        """
        return self.do_authentication

    def do_authentication(self, req, res):
        """
        Unimplemented middleware to be overloaded by subclasses
        """
        raise NotImplementedError
