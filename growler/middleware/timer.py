#
# growler/python/timer.py
#

from datetime import datetime


class Timer:
    """Times the response generation"""

    def __init__(self, option={}):
        pass

    def __call__(self, req, res):
        START = datetime.now()

        def _on_end():
            print(" [ONEND]")
            END = datetime.now()
            print(" -- timer {}".format(END - START))
        res.on_send_end(_on_end)
