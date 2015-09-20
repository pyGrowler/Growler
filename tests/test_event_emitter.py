#
# tests/test_event_emitter
#

from growler.utils.event_manager import event_emitter


@event_emitter
class EE:

    def foo(self):
        return 0


def test_method_addition():
    e = EE()
    assert hasattr(e, 'on')
    assert hasattr(e, 'emit')
