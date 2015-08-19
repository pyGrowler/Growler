#
# growler/middleware_chain.py
#
"""
"""

from inspect import signature
from collections import namedtuple

MiddlewareTuple = namedtuple('MiddlewareTuple', ['func',
                                                 'path',
                                                 'mask',
                                                 'is_errorhandler',
                                                 'is_subchain',
                                                 ])


class MiddlewareChain:
    """
    Class handling the storage and retreival of growler middleware functions.
    """

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
            if not callable(mw.func):
                continue

            method_matches = method & mw.mask
            path_matches = path.startswith(mw.path)    \
                           if isinstance(mw.path, str) \
                           else mw.path.match(path)

            if not (method_matches and path_matches):
                continue

            if mw.is_subchain:
                post_match_idx = len(mw.path)                 \
                                 if isinstance(mw.path, str)  \
                                 else len(path_matches.string)
                subchain = mw.func(method, path[post_match_idx:])

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
        tup = MiddlewareTuple(func=func,
                              mask=method_mask,
                              path=path,
                              is_errorhandler=is_err,
                              is_subchain=is_subchain,)
        self.mw_list.append(tup)

    def __contains__(self, func):
        return any((func is mw.func) or
                   (isinstance(mw.func, MiddlewareChain) and func in mw.func)
                   for mw in self.mw_list)
