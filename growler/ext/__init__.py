#
# growler/ext/__init__.py
#
"""
Virtual namespace for other pacakges to extend the growler server
"""

from pkg_resources import declare_namespace

declare_namespace('growler.ext')
