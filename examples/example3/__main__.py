#!/usr/bin/env python3
#
# Example2 - DefaultSession
#

import os
import asyncio

from growler import App
from growler.router import routerclass

@routerclass
class QuickRoute:

    def __init__(self, param):
        """
        Construct a QuickRoute object
        """
        self.param = param

    @asyncio.coroutine
    def get_root(self, req, res):
        """
        /
        return the root of the object
        """
        res.send_json({'param': self.param})

app = App("Example3")

app.use(QuickRoute('Helloo'), '/')

app.create_server_and_run_forever(port=8080, host='127.0.0.1')
