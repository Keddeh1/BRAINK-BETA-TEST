"""Unit tests for ring architecture."""

import pytest
from braink.core.rings import Ring, RingLevel, RingState


class TestRingLevel:
    """Tests for RingLevel enum."""

    def test_ring_level_values(self) -> None:
        """Test that ring levels have correct values."""
        assert RingLevel.RING_0.value == 0
        assert RingLevel.RING_1.value == 1
        assert RingLevel.RING_2.value == 2
        assert RingLevel.RING_3.value == 3


class TestRingState:
    """Tests for RingState."""

    def test_ring_state_creation(self) -> None:
        """Test creating a ring state."""
        state = RingState(
            ring_level=RingLevel.RING_0,
            cycle_count=100,
            memory_base=0x00000000,
            memory_limit=0x10000000,
        )
        assert state.ring_level == RingLevel.RING_0
        assert state.cycle_count == 100
        assert state.memory_base == 0x00000000
        assert state.memory_limit == 0x10000000

    def test_ring_state_immutable(self, ring_0: Ring) -> None:
        """Test that ring state is effectively immutable."""
        state = ring_0.state
        assert state.ring_level == RingLevel.RING_0


class TestRing:
    """Tests for Ring class."""

    def test_ring_creation(self) -> None:
        """Test creating a ring."""
        ring = Ring(RingLevel.RING_0, memory_base=0x00000000, memory_size=0x1000)
        assert ring.level == RingLevel.RING_0
        assert ring.memory_base == 0x00000000
        assert ring.memory_limit == 0x1000

    def test_ring_0_can_access_all(self, ring_0: Ring) -> None:
        """Test that Ring 0 can access all rings."""
        assert ring_0.can_access(RingLevel.RING_0)
        assert ring_0.can_access(RingLevel.RING_1)
        assert ring_0.can_access(RingLevel.RING_2)
        assert ring_0.can_access(RingLevel.RING_3)

    def test_ring_access_hierarchy(self, ring_1: Ring) -> None:
        """Test ring access hierarchy."""
        # Ring 1 can access itself and higher numbered rings
        assert ring_1.can_access(RingLevel.RING_1)
        assert ring_1.can_access(RingLevel.RING_2)
        assert ring_1.can_access(RingLevel.RING_3)
        # But not Ring 0
        assert not ring_1.can_access(RingLevel.RING_0)
