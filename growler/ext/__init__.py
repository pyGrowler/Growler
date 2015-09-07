#
# growler/ext/__init__.py
#
"""
Virtual namespace for other pacakges to extend the growler server
"""

import sys


class GrowlerExtensionImporter:

    def __getattr__(cls, module_name):
        """
        Get the 'attribute' of growler.ext, which looks for the module in the
        python virtual namespace growler_ext
        """
        pass

sys.modules[__name__] = GrowlerExtensionImporter(__name__)
