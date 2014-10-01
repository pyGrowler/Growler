
import growler

from growler.middleware import (ResponseTime, Logger)

app = growler.App(__name__)

app.use(Logger())
app.use(ResponseTime())

@app.get("/")
def index(req, res, next):
  res.send_text("It Works!")

app.run()
