#
# growler/utils/metaclasses.py
#
"""
A place to put metaclasses used throughout the project
"""


class ItemizedMeta(type):
    """
    Adds the item access (square brackets) methods to the
    class. This forwards __getitem__, __setitem__, and __delitem__
    to the classmethods _getitem_, _setitem_, and _delitem_.
    """

    def __getitem__(cls, key):
        return cls._getitem_(key)

    def __setitem__(cls, key, val):
        return cls._setitem_(key, val)

    def __delitem__(cls, key):
        return cls._delitem_(key)
