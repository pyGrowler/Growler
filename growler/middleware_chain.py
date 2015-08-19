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
                                                     'mask',
                                                     'is_errorhandler',
                                                     'is_subchain',
                                                     ])

    def __init__(self):
        self.mw_list = []

    def __call__(self, method, path):
        """
        Generator yielding the middleware which matches the provided path.

        :param path: url path of the request.
        :type path: str
        """
        error_handler_stack = []
        err = None
        for mw in self.mw_list:
            method_matches = method & mw.mask
            path_matches = path.startswith(mw.path)

            if not (method_matches and path_matches):
                continue

            if mw.is_subchain:
                subchain = mw.func(method, path[len(mw.path):])
                for sub_mw in subchain:
                    err = yield sub_mw.func
                    if err:
                        sub_mw.send(err)

            elif mw.is_errorhandler:
                error_handler_stack.append(mw.func)

            else:
                err = yield mw.func

            if err:
                break

        if err:
            for errhandler in reversed(error_handler_stack):
                new_error = yield errhandler
                if new_error:
                    pass

    def add(self, method_mask, path, func):
        """
        Add a function to the middleware chain, listening on func
        """
        is_err = len(signature(func).parameters) == 3
        is_subchain = isinstance(func, MiddlewareChain)
        tup = self.MiddlewareTuple(func=func,
                                   mask=method_mask,
                                   path=path,
                                   is_errorhandler=is_err,
                                   is_subchain=is_subchain,)
        self.mw_list.append(tup)

    def __contains__(self, func):
        return any(mw.func is func for mw in self.mw_list)

    def last_router(self):
        from router import Router
        if not isinstance(self.mw_list[-1].func, Router):
            self.add(0xFFF, '/', Router())
        return self.mw_list[-1].func
