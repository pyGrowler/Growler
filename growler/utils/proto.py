#
# growler/utils/proto.py
#

from collections import namedtuple


BoundFunction = namedtuple("BoundFunction", 'func')


class PrototypeMeta(type):
    pass


class PrototypeObject(metaclass=PrototypeMeta):
    """
    Class mimicking the prototypal inheritance pattern found in other
    programming languages.
    Objects of this class may inherit attributes from another object
    by setting the other object to ``__proto__``.
    For example, executing ``b.__proto__ = a``, if ``b`` is a
    PrototypeObject, will allow all attributes of a to be accessible
    from b.

    To avoid type/class confusion, it is recommended to use the
    :meth:`create` method to create inherited objects rather than
    'linking' the prototypes after construction.

    The ``bind`` method allows any function to be dynamically added as
    a method to the object.
    Note that the first argument (i.e. the ``self`` argument) will be
    the object calling the method, not necessarily the object the
    function was bound to.
    This option is there
    """

    __proto__ = object()
    __methods__ = None

    @classmethod
    def create(cls, obj):
        """
        Create a new prototype object with the argument as the source
        prototype.

        .. Note:

            This does not `initialize` the newly created object any
            more than setting its prototype.
            Calling the __init__ method is usually unnecessary as all
            initialization data should be in the original prototype
            object already.

            If required, call __init__ explicitly:

            >>> proto_obj = MyProtoObj(1, 2, 3)
            >>> obj = MyProtoObj.create(proto_obj)
            >>> obj.__init__(1, 2, 3)

        """
        self = cls.__new__(cls)
        self.__proto__ = obj
        return self

    def bind(self, func):
        """
        Take a function and create a bound method
        """
        if self.__methods__ is None:
            self.__methods__ = {}
        self.__methods__[func.__name__] = BoundFunction(func)

    def has_own_property(self, attr):
        """
        Returns if the property
        """
        try:
            object.__getattribute__(self, attr)
        except AttributeError:
            return False
        else:
            return True

    def __getattr__(self, attr):
        """
        Called by python when an attribute is not found.
        This will call the __getprotoattr__ to search the chain.

        If a BoundFunction is found, it gets bound to 'self' and the
        resulting method is returned.
        """
        result = self.__getprotoattr__(attr)
        if isinstance(result, BoundFunction):
            result = result.func.__get__(self)
        return result

    def __getprotoattr__(self, attr):
        """
        Recursively search through object's prototype-chain,
        """
        # first check our own object's bound methods
        if self.__methods__ and attr in self.__methods__:
            return self.__methods__[attr]

        # do 'standard' attribute check in prototype
        try:
            return object.__getattribute__(self.__proto__, attr)
        except AttributeError:
            pass

        # recursively call __getprotoattr__ for prototype
        try:
            return self.__proto__.__getprotoattr__(attr)
        except AttributeError:
            raise AttributeError("{!r} object has no attribute {!r}".format(
                self.__class__.__name__,
                attr))

    def __setattr__(self, attr, value):
        # special handling of bound __method__ objects
        if self.__methods__ and attr in self.__methods__:
            del self.__methods__[attr]
        object.__setattr__(self, attr, value)

    def __delattr__(self, attr):
        """
        Remove the attribute from this object.
        If attribute exists in prototype, this has no effect.

        The __proto__ and __methods__ attributes are protected
        and must not be deleted.
        """
        # cannot delete the prototype!
        if attr in ('__proto__', '__methods__'):
            raise RuntimeError(
                "Attempted to delete {} from PrototypeObject".format(attr)
            )

        try:
            object.__delattr__(self, attr)
        except AttributeError:
            if not hasattr(self.__proto__, attr):
                raise
