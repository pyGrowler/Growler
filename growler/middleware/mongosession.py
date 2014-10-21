#
# growler/middleware/mongosession.py
#



from . import middleware

from termcolor import colored

import growler
import asyncio

# @middleware
class MongoSession:

  def __init__(self, db_future, db_name = 'growler', collection_name = 'sessions'):
    """
    @type db_future: asyncio.Future
    """
    # yield from db_future

    @asyncio.coroutine
    def setup():
      self.cnx = yield from db_future
      self.sessions = self.cnx[db_name][collection_name]
      print ("Session Setup", self.sessions)

    asyncio.async(setup())

  @asyncio.coroutine
  def __call__(self, req, res, next):
    print ("[MongoSession::()]")
    print ("  Request Quick ID: ", req.cookies['qid'].value)

    sess = yield from self.sessions.find_one({"sid": req.cookies['qid'].value})
    
    # No Session Found
    if sess == {}:
      sess["qid"] = req.cookies['qid'].value
      yield from self.sessions.insert(sess)
