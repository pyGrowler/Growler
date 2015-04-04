#
# growler/mw/__init__.py
#
"""
Alternantive abbreviated name for the growler.middleware package. This is a
virtual namespace that others may extend by adding 'growler.md' to the
namespace_packages keyword in their setup.py's setup() function.
"""

from pkg_resources import declare_namespace

declare_namespace('growler.mw')
