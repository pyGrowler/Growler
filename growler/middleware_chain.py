#
# growler/middleware_chain.py
#
"""
"""

import logging
from inspect import signature


class Middleware:
    __slots__ = [
        'func',
        'path',
        'mask',
        'is_errorhandler',
        'is_subchain',
    ]

    def __init__(self, **inits):
        for k, v in inits.items():
            setattr(self, k, v)

    def matches_method(self, method):
        """
        Method to determine if the http method matches this middleware.
        """
        return self.mask & method

    def path_split(self, path):
        """
        Splits a path into the part matching this middleware, and the part
        remaining.
        If path does not exist, it returns a pair of None values.
        """
        if isinstance(self.path, str):
            if path.startswith(self.path):
                return self.path, path[len(self.path):]
            else:
                return None, None
        else:
            match = self.path.match(path)
            if match is not None:
                return match, path[:match.span()[1]]
            else:
                return None, None


class MiddlewareChain:
    """
    Class handling the storage and retreival of growler middleware functions.
    """

    mw_list = None
    log = None

    def __init__(self):
        self.mw_list = []
        self.log = logging.getLogger("%s:%d" % (__name__, id(self)))

    def __call__(self, method, path):
        """
        Generator yielding the middleware which matches the provided path.

        :param path: url path of the request.
        :type path: str
        """
        error_handler_stack = []
        err = None

        # loop through this chain's middleware list
        for mw in self.mw_list:

            # skip if method
            if not mw.matches_method(method):
                continue

            # get the path matching this middleware and the 'rest' of the url
            # (i.e. the part that comes AFTER the match) to be potentially
            # matched later by a subchain
            path_match, rest_url = mw.path_split(path)

            # skip if not a match
            if not path_match:
                continue

            # If a subchain - loop through middleware
            if mw.is_subchain:

                # We need to call sub middleware with only the URL past the
                # matching string
                subpath = '/' + rest_url

                # middleware func is the generator of sub-middleware
                subchain = mw.func(method, subpath)

                # loop through subchain
                for sub_mw in subchain:

                    # Yield the middleware function
                    err = yield sub_mw
                    if err:
                        subchain.send(err)

            elif mw.is_errorhandler:
                error_handler_stack.append(mw.func)

            else:
                # Yield the middleware function
                err = yield mw.func

            if err:
                break

        if err:
            self.log.error(err)
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
        tup = Middleware(func=func,
                         mask=method_mask,
                         path=path,
                         is_errorhandler=is_err,
                         is_subchain=is_subchain,)
        self.mw_list.append(tup)

    def __contains__(self, func):
        """
        Returns whether the function is stored anywhere in the middleware chain
        """
        return any((func is mw.func) or (mw.is_subchain and func in mw.func)
                   for mw in self.mw_list)
