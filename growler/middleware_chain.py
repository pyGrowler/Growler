#
# growler/middleware_chain.py
#
"""
Provides the MiddlewareChain class, which is used to store structured routing,
and provides an easy interface for request matching.
"""

import logging
import re
from inspect import signature


class MiddlewareNode:
    """
    A class representing a node in the MiddlewareChain. It contains the actual
    middleware function, the path this node is mounted on, and the 'method
    mask' which requests must match to proceed. There are two boolean slots
    which indicate whether this node contains a 'subchain' (is this technically
    a tree?) and if function is an error handler.

    A 'subchain' middleware node has the subtree stored as the func attribute.

    The path attribute should be a regular expression. If it is a string, it is
    escaped and then compiled.


    Keyword Arguments
    -----------------
        Simple mappings to attributes
    """

    __slots__ = [
        'func',
        'path',
        'mask',
        'is_errorhandler',
        'is_subchain',
    ]

    def __init__(self, **inits):
        for k, v in inits.items():
            if k == 'path' and isinstance(v, str):
                v = re.compile(re.escape(v))
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

        Parameters
        ----------
        path : str
            The url to split

        Returns
        -------
        matching_path : str or None
            The beginning of the path which matches this middleware or None if
            it does not match
        remaining_path : str or None
            The 'rest' of the path, following the matching part

        """
        match = self.path.match(path)
        if match is not None:
            return match, path[:match.span()[1]]
        else:
            return None, None


class MiddlewareChain:
    """
    Class handling the storage and retreival of growler middleware functions.
    """

    ROOT_PATTERN = re.compile(re.escape('/'))

    mw_list = None
    log = None

    def __init__(self):
        self.mw_list = []
        self.log = logging.getLogger("%s:%d" % (__name__, id(self)))

    def __call__(self, method, path):
        """
        Generator yielding the middleware which matches the provided path.

        When called with an HTTP method and path, the middleware chain returns
        a generator object that will walk along the chain in a depth-first
        pattern. Any middleware nodes matching both the method code and path
        are yielded.

        The generator keeps any error handlers encountered walking the tree in
        its internal state. If an error occurs during execution of a middleware
        function, the exception should be sent back to the generator via the
        send method: ``mw_chain.send(err)``. The error handlers will be looped
        through in reverse order, so the most specific handler matching method
        and path is called first.

        If an error occurs during the execution of an error handler, it is
        ignored (for now) until a solution is determined.

        Parameters
        ----------
        method : growler.http.HTTPMethod
            The request method which
        path : str
            url path of the request.
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

                    # the subchain had an error - forward error to subchain
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
        Add a function to the middleware chain. This function is returned when
        iterating over the chain with matching method and path.

        Parameters
        ----------
        method_mask : growler.http.HTTPMethod
            A bitwise mask intended to match specific request methods.
        path : str or regex
            An object to compare request urls to
        func : callable
            The function to be yieled from the generator upon a request
            matching the method_mask and path
        """
        is_err = len(signature(func).parameters) == 3
        is_subchain = isinstance(func, MiddlewareChain)
        tup = MiddlewareNode(func=func,
                             mask=method_mask,
                             path=path,
                             is_errorhandler=is_err,
                             is_subchain=is_subchain,)
        self.mw_list.append(tup)

    def __contains__(self, func):
        """
        Returns whether the function is stored anywhere in the middleware
        chain.

        This runs recursively though any subchains.

        Parameters
        ----------
        func : callable
            A function which may be present in the chain

        Returns
        -------
        contains_function : bool
            True if func is a function contained anywhere in the chain.
        """
        return any((func is mw.func) or (mw.is_subchain and func in mw.func)
                   for mw in self.mw_list)

    def count_all(self):
        """
        Returns the total number of middleware in this chain and subchains.
        """
        return sum(x.func.count_all() if x.is_subchain else 1 for x in self)

    def __len__(self):
        """
        Returns the number of middleware contained in the root of this chain.
        To count the number of middleware, included in subchains, use
        count_all()
        """
        return len(self.mw_list)

    def __iter__(self):
        """
        Iterates directly through the middleware chain. Does not enter any
        subchains.
        """
        return iter(self.mw_list)

    def __reversed__(self):
        """
        Iterates directly through the middleware chain, starting from the
        bottom. Does not enter any subchains along the way.
        """
        return reversed(self.mw_list)

    def first(self):
        """
        Returns first element in list.

        Returns
        -------
        MiddlewareNode
            The first middleware in the chain.

        Raises
        ------
        IndexError
            If the chain is empty
        """
        return self.mw_list[0]

    def last(self):
        """
        Returns last element in list.

        Returns
        -------
        MiddlewareNode
            The last middleware stored in the chain.

        Raises
        ------
        IndexError
            If the chain is empty
        """
        return self.mw_list[-1]
