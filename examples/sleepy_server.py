#!/usr/bin/env python3
#
# examples/sleepy_server.py
#
"""
Example growler server which uses a coroutine middleware
"""

import asyncio
import growler


app = growler.App("Example2")


# Small function to handle requests from server
@app.get("/")
async def handle_request(req, res):
    sleep_for = 2
    print("Sleeping for %d seconds" % (sleep_for))
    await asyncio.sleep(sleep_for)
    res.send_text('It Works!')


app.create_server_and_run_forever(host='127.0.0.1', port=8000)
