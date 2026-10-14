"""Security regression: all privilege transitions, including RuntimeExecutor and DomainEngine."""
import pytest

from braink.core.rings import Ring, RingLevel
from braink.core.exceptions import RingAccessException
from braink.runtime.executor import RuntimeExecutor
from braink.domain.engine import DomainEngine


@pytest.mark.parametrize("source", list(RingLevel))
@pytest.mark.parametrize("target", list(RingLevel))
def test_ring_matrix(source, target):
    # 0 is highest privilege. Only equal or less-privileged targets are allowed.
    assert Ring(source).can_access(target) is (source.value <= target.value)


@pytest.mark.parametrize("source", list(RingLevel))
@pytest.mark.parametrize("target", list(RingLevel))
def test_runtime_executor_enforces_matrix(source, target):
    executor = RuntimeExecutor(Ring(source))
    observed = []
    def effect():
        observed.append("executed")
        return "ok"
    if source.value <= target.value:
        assert executor.execute(effect, target_ring=target) == "ok"
        assert observed == ["executed"]
    else:
        with pytest.raises(RingAccessException):
            executor.execute(effect, target_ring=target)
        assert observed == []


@pytest.mark.parametrize("source", list(RingLevel))
@pytest.mark.parametrize("target", list(RingLevel))
def test_domain_transition_enforces_matrix(source, target):
    domain = DomainEngine()
    domain.initialize()
    assert domain.validate_transition(source, target) is (source.value <= target.value)


def test_ring_three_cannot_invoke_ring_zero():
    called = []
    executor = RuntimeExecutor(Ring(RingLevel.RING_3))
    with pytest.raises(RingAccessException):
        executor.execute(lambda: called.append(True), target_ring=RingLevel.RING_0)
    assert called == []
