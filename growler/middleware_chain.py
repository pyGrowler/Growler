#
# growler/middleware_chain.py
#
"""
Provides the MiddlewareChain class, which is used to store structured routing, and provides an
easy interface for request matching.
"""

import logging
import re
from inspect import signature


class MiddlewareNode:
    """
    A class representing a node in the MiddlewareChain.
    It contains the actual middleware function, the path this node is mounted on, and the
    'method mask' which requests must match to proceed.
    There are two boolean slots which indicate whether this node contains a 'subchain' (i.e.
    another MiddlewareChain stored in func) and if function should be treated as an error
    handler rather than standard middleware.

    A 'subchain' middleware node has the subtree stored as the func attribute.
    """

    IGNORE_TRAILING_SLASH = True

    __slots__ = [
        'func',
        'path',
        'mask',
        'is_errorhandler',
        'is_subchain',
    ]

    def __init__(self, **inits):
        """
        The path attribute should be a regular expression.
        If it is a string, it is escaped and then compiled.

        Keyword Args:
            path (String or regex): A regex to be matched upon connection
                Simple mappings to attributes
        """
        for k, v in inits.items():
            if k == 'path' and isinstance(v, str):
                v = self.path_to_regex(v)
            setattr(self, k, v)

    @staticmethod
    def path_to_regex(path):
        """
        Static method wich handles the conversion of a string to the regex that will be tested
        against the incoming request paths.
        """
        # last_slash = '' if path.endswith('/') else '/'
        esc_path = re.escape(path)
        return re.compile(esc_path)

    def matches_method(self, method):
        """
        Method to determine if the http method matches this middleware.
        """
        return self.mask & method

    def path_split(self, path):
        """
        Splits a path into the part matching this middleware and the part remaining.
        If path does not exist, it returns a pair of None values.
        If the regex matches the entire pair, the second item in returned tuple is None.

        Args:
            path (str): The url to split

        Returns:
            Tuple
            matching_path (str or None): The beginning of the path which matches this
                middleware or None if it does not match
            remaining_path (str or None): The 'rest' of the path, following the matching part
        """

        match = self.path.match(path)
        if match is None:
            return None, None

        # split string at position
        the_rest = path[match.end():]

        # ensure we split at a '/' character
        if the_rest:
            if match.group().endswith('/'):
                pass
            elif the_rest.startswith('/'):
                pass
            else:
                return None, None

        if self.IGNORE_TRAILING_SLASH and the_rest == '/':
            the_rest = ''

        return match, the_rest


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

        When called with an HTTP method and path, the middleware chain returns a generator
        object that will walk along the chain in a depth-first pattern. Any middleware nodes
        matching both the method code and path are yielded.

        The generator keeps any error handlers encountered walking the tree in its internal
        state. If an error occurs during execution of a middleware function, the exception
        should be sent back to the generator via the throw method: ``mw_chain.throw(err)``. The
        error handlers will be looped through in reverse order, so the most specific handler
        matching method and path is called first.

        If an error occurs during the execution of an error handler, it is ignored (for now)
        until a solution is determined.

        Args:
            method (growler.http.HTTPMethod): The request method which
            path (str): URL path of the request.

        Yields:
            Callable or Coroutine: The next middleware object that matches the incoming request

        TODO:
            What to do when the error handler raises a new error?
        """
        error_handler_stack = []

        # loop through all middleware matching the request
        matching_middleware = self.find_matching_middleware(method, path)
        for mw, path_match, rest_url in matching_middleware:

            # If a subchain - loop through middleware
            if mw.is_subchain:

                # We need to call sub middleware with only the URL past the
                # matching string
                subpath = '/' + rest_url

                # middleware func is the generator of sub-middleware
                subchain = mw.func(method, subpath)

                # loop through subchain
                yield from self.iterate_subchain(subchain)

            # add to list of error handlers
            elif mw.is_errorhandler:
                error_handler_stack.append(mw.func)

            # Found a matching request! yield result function
            else:
                try:
                    # Yield the middleware function back to application
                    yield mw.func

                # exception means application threw something back at us
                except Exception as err:
                    # Yielding None here returns execution to the caller,
                    # allowing it to request error handling middleware from us
                    yield None
                    # redirect all other requests to the handle_error loop
                    yield from self.handle_error(err, error_handler_stack)
                    break

    def find_matching_middleware(self, method, path):
        """
        Iterator handling the matching of middleware against a method+path
        pair. Yields the middleware, and the
        """
        for mw in self.mw_list:
            if not mw.matches_method(method):
                continue

            # get the path matching this middleware and the 'rest' of the url
            # (i.e. the part that comes AFTER the match) to be potentially
            # matched later by a subchain
            path_match, rest_url = mw.path_split(path)
            if self.should_skip_middleware(mw, path_match, rest_url):
                continue

            yield mw, path_match, rest_url

    def iterate_subchain(self, chain):
        """
        A coroutine used by __call__ to forward all requests to a
        subchain.
        """
        for mw in chain:
            try:
                yield mw
            except Exception as err:
                yield chain.throw(err)

    def handle_error(self, error, err_handlers):
        self.log.error(error)
        for errhandler in reversed(err_handlers):
            try:
                yield errhandler
            except Exception:  # except Exception as new_error:
                yield None

    def should_skip_middleware(self, middleware, matching, rest):
        """
        Method used to determine if middleware should be called.
        Returns True (should skip) only if matching evaluates to False (no match), otherwise
        the standard MiddlewareChain returns any matching request.
        The Router overrides this and the *entire* request must be matched to warrant yielding
        a function.
        This method was factored out of __call__ so it may be overriden with cust logic without
        reimplementing the whole __call__ method.
        """
        return bool(not matching)

    def add(self, method_mask, path, func):
        """
        Add a function to the middleware chain.
        This function is returned when iterating over the chain with matching method and path.

        Args:
            method_mask (growler.http.HTTPMethod): A bitwise mask intended to match specific
                request methods.
            path (str or regex): An object with which to compare request urls
            func (callable): The function to be yieled from the generator upon a request
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
        Returns whether the function is stored anywhere in the middleware chain.

        This runs recursively though any subchains.

        Args:
            func (callable): A function which may be present in the chain

        Returns:
            bool: True if func is a function contained anywhere in the chain.
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
        To count the number of middleware, included in subchains, use count_all().
        """
        return len(self.mw_list)

    def __iter__(self):
        """
        Iterates directly through the middleware chain. Does not enter any subchains.
        """
        return iter(self.mw_list)

    def __reversed__(self):
        """
        Iterates directly through the middleware chain, starting from the bottom.
        Does not enter any subchains along the way.
        """
        return reversed(self.mw_list)

    def first(self):
        """
        Returns first element in list.

        Returns:
            MiddlewareNode: The first middleware in the chain.

        Raises:
            IndexError: If the chain is empty
        """
        return self.mw_list[0]

    def last(self):
        """
        Returns last element in list.

        Returns:
            MiddlewareNode: The last middleware stored in the chain.

        Raises:
            IndexError: If the chain is empty
        """
        return self.mw_list[-1]
