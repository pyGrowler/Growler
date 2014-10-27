#
# growler/middleware/session.py
#
'''
A standard 'Session' class which holds data about consecutive calls from a browser to the server.
'''

import asyncio

class Session(object):

  _data = {}

  def __init__(self, storage, values = {}):
    self._data = values
    self._store = storage

  def __getitem__(self, name):
    return self._data[name]

  def __setitem__(self, name, value):
    self._data[name] = value
 
#   def __delitem__(self, name):
#     del self._data[name]

#   def __getattr__(self, name):
#     print ("[__getattr__]:", name)
#     return object.__getattribute__(self, '_data')[name]
#     return self._data[name]

#   def __setattr__(self, name, value):
#     print ("[__setattr__]:", name,value)
#     #self[name] = value
#     self._data[name] = value

  def get(self, name, default = None):
    return self._data[name] if name in self._data else default

#     return object.__getitem__(self, '_data')['name']
#   def __set__(self, name, value):
#     print ("+++ Seting ",name,vlaue)
#     self._data[name] = value
# 
#   def iteritems(self):
#     return self._data.iteritems()
# 
#   def keys(self):
#     return self._data.keys()
# 
#   def items(self):
#     return self._data.items()
# 
#   def iterkeys(self):
#     return self._data.iterkeys()
# 
#   def iteritems(self):
#     return self._data.iteritems()
# 
  def __iter__(self):
    return self._data.__iter__()
# 
#   def __contains__(self, key):
#     return key in self._data
# 
#   def __dict__(self):
#     print ("DICT")

  @asyncio.coroutine
  def save(self):
    yield from self._store.save(self)


class SessionStorage(object):

  def __init__(self, **kwargs):
    print ("[SessionStorage]")

  @asyncio.coroutine
  def save(self, sess):
    raise NotImplementedError

class DefaultSessionStorage(SessionStorage):

  def __init__(self):
    super().__init__()
    # print("[DefaultSessionStorage]")
    self._sessions = {}

  @asyncio.coroutine
  def __call__(self, req, res):
    """The middleware action"""
    sid = req.cookies['qid'].value
    print ("[DefaultSessionStorage] ", sid)
    if not sid in self._sessions:
      self._sessions[sid] = {'id': sid}
    req.session = Session(self, self._sessions[sid])

  @asyncio.coroutine
  def save(self, sess):
    # print ("[DefaultSessionStorage::save] saving", sess.id)
    self._sessions[sess.id] = sess._data
