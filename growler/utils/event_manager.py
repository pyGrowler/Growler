#
# growler/utils/event_emitter.py
#


def event_emitter(_cls=None, events=None):

    def _event_emitter(cls):

        def on_event(self, ):
            pass

        if (events is not None) or ('*' in events):

            cls.on = lambda event_name: print(self_)

        return cls

    if _cls is None:
        return _event_emitter
    else:
        return _event_emitter(_cls)


def emits(pre=None, *, post=None):
    pass
