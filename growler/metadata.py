#
# metadata.py
#
"""Project Metadata"""

package = 'growler'
project = 'A New Web Framework'
project_no_spaces = project.replace(' ', '')

version_info = (0, 1, 5)
version = '.'.join(map(str, version_info))
version_name = ''.join((project, 'version', version))


author = "Andrew Kubera"
author_email = "andrew.kubera@gmail.com"
copyright = "Copyright 2014, Andrew Kubera"

license = 'Apache v2.0'
