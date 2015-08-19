#
# growler/middleware_chain.py
#
"""
"""

from inspect import signature
from collections import namedtuple


class MiddlewareChain:
    """
    Class handling the storage and retreival of growler middleware functions.
    """

    MiddlewareTuple = namedtuple('MiddlewareTuple', ['func',
                                                     'path',
                                                     'err',
                                                     'mask',
                                                     ])

    def __init__(self):
        self.mw_list = []

    def __call__(self, method, path):
        """
        Generator yielding the middleware which matches the provided path.

        :param path: url path of the request.
        :type path: str
        """
        for mw in self.mw_list:
            if (method & mw.mask) and (path.startswith(mw.path)):
                yield mw.func

    def add(self, method_mask, path, func):
        """
        Add a function to the middleware chain, listening on func
        """
        is_err = len(signature(func).parameters) == 3
        tup = self.MiddlewareTuple(func=func,
                                   mask=method_mask,
                                   path=path,
                                   err=is_err,)
        self.mw_list.append(tup)

    def __contains__(self, func):
        return any(mw.func is func for mw in self.mw_list)

    def last_router(self):
        from router import Router
        if not isinstance(self.mw_list[-1].func, Router):
            self.add(0xFFF, '/', Router())
        return self.mw_list[-1].func
