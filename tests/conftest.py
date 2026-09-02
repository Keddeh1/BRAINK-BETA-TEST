"""Pytest configuration and shared fixtures."""

import pytest
from braink.core.rings import Ring, RingLevel
from braink.domain.engine import DomainEngine
from braink.runtime.executor import RuntimeExecutor


@pytest.fixture
def ring_0() -> Ring:
    """Fixture providing Ring 0 instance."""
    return Ring(RingLevel.RING_0, memory_base=0x00000000, memory_size=0x10000000)


@pytest.fixture
def ring_1() -> Ring:
    """Fixture providing Ring 1 instance."""
    return Ring(RingLevel.RING_1, memory_base=0x10000000, memory_size=0x10000000)


@pytest.fixture
def domain_engine() -> DomainEngine:
    """Fixture providing initialized domain engine."""
    engine = DomainEngine()
    engine.initialize()
    return engine


@pytest.fixture
def executor_ring_0(ring_0: Ring) -> RuntimeExecutor:
    """Fixture providing executor for Ring 0."""
    return RuntimeExecutor(ring_0)
