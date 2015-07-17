#
# growler/middleware/session.py
#
"""
A standard 'Session' class which holds data about consecutive calls from a
browser to the server.
"""

import asyncio
import uuid


class Session(object):
    """
    Session middleware!
    """
    _data = {}

    def __init__(self, storage, values={}):
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

    def get(self, name, default=None):
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
        print("[SessionStorage]")

    def save(self, sess):
        raise NotImplementedError


class DefaultSessionStorage(SessionStorage):
    """
    The growler default session storage uses a standard python dict to store
    all sessions ids and variables. The application must use a cookie parser
    (for example, growler.middleware.CookieParser()) BEFORE using the
    DefaultSessionStorage.
    .. code: python
        app.use(CookieParser())
        app.use(DefaultSessionStorage())
    """
    def __init__(self, session_id_name='qid'):
        """

        """
        super().__init__()
        self.session_id_name = session_id_name
        self._sessions = {}

    def __call__(self, req, res):
        """
        The middleware action. Adds a session member to the req object and the
        session id to the resoponse object.
        """
        qid = self.session_id_name
        try:
            sid = req.cookies[qid].value
        except KeyError:
            sid = req.cookies[qid] = uuid.uuid4()

        res.cookies[qid] = sid

        print("[DefaultSessionStorage] ", sid)
        if sid not in self._sessions:
            self._sessions[sid] = {'id': sid}
        req.session = Session(self, self._sessions[sid])

    def save(self, sess):
        # print ("[DefaultSessionStorage::save] saving", sess.id)
        self._sessions[sess.id] = sess._data
