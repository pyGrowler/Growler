#
# growler/mw/__init__.py
#
"""
Alternantive abbreviated name for the growler.middleware package. This is a
virtual namespace that others may extend by adding 'growler.md' to the
namespace_packages keyword in their setup.py's setup() function.
"""

import sys
import growler.ext

importer = growler.ext.__class__()
importer.__path__ = 'growler.mw'
importer.__mods__ = {}

sys.modules[__name__] = importer
