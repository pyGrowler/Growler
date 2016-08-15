#
# growler/middleware/session.py
#
"""
The standard growler session module which contains code for setting up
a typical client 'Session', allowing client data to be saved on the
server.

The Middleware ``SessionStorage`` should be added to the application
chain somewhere before the main web routes.
The typical action of the SessionStorage middleware is to add a
``session`` object to the request.
This object provides an abstraction around the backend storage system.

The default session storage object uses an 'sid' cookie field to identify
the client's session.
(Note that non-secure connections could lead to session hijacking!)
To use cookies, the author must ensure that the cookie middleware is loaded
BEFORE the session middleware.
In other words there will be a lurking AttributeError if req.cookies does
not exist when the middleware chain meets SessionStorage.

As stated, the session object attached to the request abstracts the
fetching of data from the backend system.
The default implementation of this object is found in the class Session,
which simply uses a python dictionary as the backend storage system.
It is not recommended that the default session class be used in production.
Other solutions (yet to be developed) that use a persistent data backend
should be used, but idealy the interfaces (session objects) will be identical.
The interface should match the dictionary interface.
To ensure this it is recommended to subclass the abstract base class
`collections.abc.MutableMapping` which ensures that all the get/set/del item
methods are implemented as expected.

"""

import uuid
import asyncio
import logging
from abc import abstractmethod
from collections.abc import MutableMapping

logger = logging.getLogger(__name__)

class Session(MutableMapping):
    """
    Session data
    """

    def __init__(self, storage, values=None):
        self._data = {} if values is None else values
        self._store = storage

    def __getitem__(self, name):
        return self._data.__getitem__(name)

    def __setitem__(self, name, value):
        return self._data.__setitem__(name, value)

    def __delitem__(self, name):
        return self._data.__delitem__(name)

    def __len__(self):
        return self._data.__len__()

#   def __getattr__(self, name):
#     print ("[__getattr__]:", name)
#     return object.__getattribute__(self, '_data')[name]
#     return self._data[name]

#   def __setattr__(self, name, value):
#     print ("[__setattr__]:", name,value)
#     #self[name] = value
#     self._data[name] = value

    def get(self, name, default=None):
        return self._data.get(name, default)

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


class SessionStorage:

    @abstractmethod
    def save(self, sess):
        raise NotImplementedError


class DefaultSessionStorage(SessionStorage):
    """
    The growler default session storage uses a standard python dict to store
    all sessions ids and variables. The application must use a cookie parser
    (for example, growler.middleware.CookieParser()) BEFORE using the
    DefaultSessionStorage.

    >>> app.use(CookieParser())
    >>> app.use(DefaultSessionStorage())
    """

    def __init__(self, session_id_name='qid'):
        """
        Construct a session storage object using the parameter as the
        unique session key.
        """
        super().__init__()
        self.session_id_name = session_id_name
        self._sessions = {}

    def __call__(self, req, res):
        """
        The middleware action. Adds a session member to the req object
        and the session id to the response object.
        """
        qid = self.session_id_name
        try:
            sid = req.cookies[qid].value
        except KeyError:
            sid = req.cookies[qid] = uuid.uuid4()

        res.cookies[qid] = sid

        logger.debug("[DefaultSessionStorage] %s" % sid)
        if sid not in self._sessions:
            self._sessions[sid] = {'id': sid}
        req.session = Session(self, self._sessions[sid])

    def save(self, sess):
        logger.debug("[DefaultSessionStorage::save] saving %s" % sess.id)
        self._sessions[sess.id] = sess._data
