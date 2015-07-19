#!/usr/bin/env python3
#
# Ex2 - Lonely Server
#

import asyncio

import growler


# Small function to handle requests from server
#
# This is typically a growler.App object, which handles the middleware chain
# and routing to endpoints.
#
@asyncio.coroutine
def handle_request(req, res):
    print("connection made by:", req)
    res.close()


http_server = growler.create_server(handle_request)
http_server.listen()
http_server.run_forever()
