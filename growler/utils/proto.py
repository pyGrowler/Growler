#
# growler/utils/proto.py
#


class PrototypeMeta(type):
    pass


class PrototypeObject(metaclass=PrototypeMeta):
    """
    Class mimicking the prototypal inheritance pattern found in other
    programming languages.
    Objects of this class may inherit attributes from another object. And
    """

    __proto__ = object()

    @classmethod
    def create(cls, obj):
        """
        Create a new prototype object with the argument as the source
        prototype.
        """
        self = cls.__new__(cls)
        self.__proto__ = obj
        return self

    def has_own_property(self, attr):
        """
        Returns if the property
        """
        try:
            object.__getattribute__(self, attr)
        except AttributeError:
            return False
        return True

    def __getattr__(self, attr):
        """
        Return
        """
        try:
            return getattr(self.__proto__, attr)
        except AttributeError:
            raise AttributeError("{!r} object has no attribute {!r}".format(
                self.__class__.__name__,
                attr))

    def __delattr__(self, attr):
        """
        """
        # cannot delete the prototype!
        if attr == '__proto__':
            return
        try:
            object.__delattr__(self, attr)
        except AttributeError:
            if not hasattr(self.__proto__, attr):
                raise
