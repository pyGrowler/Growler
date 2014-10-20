#
# growler/middleware/session.py
#
'''
A standard 'Session' class which holds data about consecutive calls from a browser to the server.
'''

class Session(object):
  
  def __init__(self):
    print ("[Session]")

  