#
# growler/ext/__init__.py
#
"""
Virtual namespace for other pacakges to extend the growler server
"""

import sys


class GrowlerExtensionImporter:

    def __getattr__(cls):
        pass

sys.modules[__name__] = GrowlerExtensionImporter(__name__)
