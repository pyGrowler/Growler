
import asyncio
import uvloop

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

from growler import App


app = App()


@app.get("/")
def index(req, res):
    res.send_text("uvloop runs!")


app.create_server_and_run_forever(
    host='0.0.0.0',
    port=8008,
)


