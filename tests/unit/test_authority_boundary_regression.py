"""Regressions for ring authorization requiring explicit caller review."""
import pytest
from braink.core.rings import Ring, RingLevel
from braink.core.exceptions import RingAccessException
from braink.runtime.executor import RuntimeExecutor
from braink.domain.engine import DomainEngine

@pytest.mark.parametrize("source", list(RingLevel))
@pytest.mark.parametrize("target", list(RingLevel))
def test_no_side_effect_on_unauthorized_transition(source, target):
    calls = []
    executor = RuntimeExecutor(Ring(source))
    def action():
        calls.append("effect")
    if source > target:
        with pytest.raises(RingAccessException):
            executor.execute(action, target_ring=target)
        assert calls == []
        assert executor.operation_count == 0
    else:
        executor.execute(action, target_ring=target)
        assert calls == ["effect"]
        assert executor.operation_count == 1

def test_domain_uninitialized_fails_closed():
    assert not DomainEngine().validate_transition(RingLevel.RING_3, RingLevel.RING_0)

@pytest.mark.parametrize("source", list(RingLevel))
def test_unprivileged_to_core_denied(source):
    assert Ring(source).can_access(RingLevel.RING_0) is (source == RingLevel.RING_0)
