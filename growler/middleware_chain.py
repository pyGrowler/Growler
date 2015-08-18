#
# growler/middleware_chain.py
#
"""
"""


class MiddlewareChain:
    """
    Class handling the storage and retreival of growler middleware functions.
    """

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
        self.mw_list.append((func,))

    def __contains__(self, func):
        for mw in self.mw_list:
            if func == mw[0]:
                return True
        return False
