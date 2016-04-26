#
# growler/ext/__init__.py
#
"""
Virtual namespace for other pacakges to extend the growler server
"""

import sys
from importlib import (
    import_module,
)


class GrowlerExtensionImporter:

    __path__ = 'growler.ext'
    __name__ = 'GrowlerExtensionImporter'
    __mods__ = {}

    def __getattr__(self, module_name):
        """
        Get the 'attribute' of growler.ext, which looks for the module in the
        python virtual namespace growler_ext
        """
        try:
            result = self.__mods__[module_name]
        except KeyError:
            # import the 'real' module
            result = import_module('growler_ext.' + module_name)

            # store alias in sys.modules
            alias_mod_name = 'growler.ext.' + module_name
            sys.modules[alias_mod_name] = result

            # cache in this object
            self.__mods__[module_name] = result

        return result

sys.modules[__name__] = GrowlerExtensionImporter()
