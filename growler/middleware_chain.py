#
# growler/middleware_chain.py
#
"""
"""


class MiddlewareChain:
    """
    Class handling the storage and retreival of growler middleware functions.
    """

    def __call__(self, path):
        """
        Generator yielding the middleware which is matches the path provided.

        :param path: url path of the request.
        :type path: str
        """

    def add(self, method, path, func):
        """
        Add a function to the middleware chain, listening on func
        """
