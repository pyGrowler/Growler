#!/usr/bin/env python3
#
# Ex2 - Lonely Server
#

import asyncio
import growler


app = growler.App("Example2")

# Small function to handle requests from server
@app.get("/")
@asyncio.coroutine
def handle_request(req, res):
    print("connection made by:", req)
    yield from asyncio.sleep(2)
    res.send_text('')

app.create_server_and_run_forever(host='127.0.0.1', port=8000)
