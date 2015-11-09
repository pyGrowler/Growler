#
# growler/ext/__init__.py
#
"""
Virtual namespace for other pacakges to extend the growler server
"""

import sys
from importlib import (
    import_module,
    # invalidate_caches,
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
        if module_name in self.__mods__:
            return self.__mods__[module_name]

        # invalidate_caches()

        real_mod_path = 'growler_ext.' + module_name
        tmp_module = import_module(real_mod_path)

        module_path = 'growler.ext.' + module_name

        sys.modules[module_path] = tmp_module
        self.__mods__[module_name] = tmp_module

        return tmp_module

sys.modules[__name__] = GrowlerExtensionImporter()
