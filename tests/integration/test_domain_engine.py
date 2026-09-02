"""Integration tests for domain engine."""

import pytest
from braink.domain.engine import DomainEngine
from braink.core.rings import RingLevel
from braink.core.exceptions import EngineExecutionException


class TestDomainEngine:
    """Tests for domain engine."""

    def test_engine_initialization(self) -> None:
        """Test engine initialization."""
        engine = DomainEngine()
        assert not engine.is_initialized
        engine.initialize()
        assert engine.is_initialized

    def test_get_ring_after_init(self, domain_engine: DomainEngine) -> None:
        """Test retrieving rings after initialization."""
        ring_0 = domain_engine.get_ring(RingLevel.RING_0)
        assert ring_0.level == RingLevel.RING_0

        ring_3 = domain_engine.get_ring(RingLevel.RING_3)
        assert ring_3.level == RingLevel.RING_3

    def test_get_ring_before_init(self) -> None:
        """Test that getting ring before init raises exception."""
        engine = DomainEngine()
        with pytest.raises(EngineExecutionException):
            engine.get_ring(RingLevel.RING_0)

    def test_validate_transition(
        self,
        domain_engine: DomainEngine,
    ) -> None:
        """Test ring transition validation."""
        # Ring 0 can access Ring 1
        assert domain_engine.validate_transition(RingLevel.RING_0, RingLevel.RING_1)

        # Ring 1 cannot access Ring 0
        assert not domain_engine.validate_transition(RingLevel.RING_1, RingLevel.RING_0)
