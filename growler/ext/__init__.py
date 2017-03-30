#
# growler/ext/__init__.py
#
"""
Virtual namespace for other pacakges to extend the growler server
"""

import sys
import pkg_resources

# load all items in 'growler.ext' and add to local namespace
for obj in pkg_resources.iter_entry_points(group='growler.ext'):
   locals()[obj.name] = obj.load()

# clean local namespace
del pkg_resources
del sys
