#
# growler/middleware_chain.py
#
"""
"""

from collections import namedtuple


class MiddlewareChain:
    """
    Class handling the storage and retreival of growler middleware functions.
    """

    middleware_tuple = namedtuple('middleware', ['func', 'path'])

    def __init__(self):
        self.mw_list = []

    def __call__(self, path):
        """
        Generator yielding the middleware which is matches the path provided.

        :param path: url path of the request.
        :type path: str
        """

    def add(self, method_mask, path, func):
        """
        Add a function to the middleware chain, listening on func
        """
        self.mw_list.append(self.middleware_tuple(func=func,
                                                  path=path,))

    def __contains__(self, func):
        for mw in self.mw_list:
            if func is mw.func:
                return True
        return False
