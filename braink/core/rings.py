"""Ring Architecture core definitions.

Implements the KEX_SEED Ring Architecture with 4 privilege levels (0-3).
"""

from enum import IntEnum
from typing import Optional


class RingLevel(IntEnum):
    """Ring privilege levels in the KEX_SEED architecture."""

    RING_0 = 0  # Highest privilege - core security kernel
    RING_1 = 1  # Domain engine privilege
    RING_2 = 2  # Runtime engine privilege
    RING_3 = 3  # User application privilege (lowest)


class RingState:
    """Immutable representation of a ring's execution state."""

    def __init__(
        self,
        ring_level: RingLevel,
        cycle_count: int = 0,
        memory_base: int = 0,
        memory_limit: int = 0,
    ) -> None:
        """Initialize ring state.

        Args:
            ring_level: Current ring privilege level
            cycle_count: CPU cycles executed
            memory_base: Base address for ring memory
            memory_limit: Upper memory limit for ring
        """
        self._ring_level = ring_level
        self._cycle_count = cycle_count
        self._memory_base = memory_base
        self._memory_limit = memory_limit

    @property
    def ring_level(self) -> RingLevel:
        """Get current ring level."""
        return self._ring_level

    @property
    def cycle_count(self) -> int:
        """Get total cycles executed."""
        return self._cycle_count

    @property
    def memory_base(self) -> int:
        """Get memory base address."""
        return self._memory_base

    @property
    def memory_limit(self) -> int:
        """Get memory upper limit."""
        return self._memory_limit

    def __repr__(self) -> str:
        """String representation of ring state."""
        return (
            f"RingState("
            f"ring={self._ring_level.name}, "
            f"cycles={self._cycle_count}, "
            f"mem=[{self._memory_base:#x}, {self._memory_limit:#x})"
            f")"
        )


class Ring:
    """Represents a single ring in the KEX_SEED architecture."""

    def __init__(
        self,
        level: RingLevel,
        memory_base: int = 0,
        memory_size: int = 0,
    ) -> None:
        """Initialize a ring.

        Args:
            level: Ring privilege level
            memory_base: Base address for this ring's memory
            memory_size: Size of memory allocated to this ring
        """
        self.level = level
        self.memory_base = memory_base
        self.memory_limit = memory_base + memory_size
        self._state = RingState(
            ring_level=level,
            memory_base=memory_base,
            memory_limit=self.memory_limit,
        )

    @property
    def state(self) -> RingState:
        """Get current ring state (immutable)."""
        return self._state

    def can_access(self, target_ring: RingLevel) -> bool:
        """Check if this ring can access a target ring.

        Lower ring numbers (higher privilege) can generally access higher
        numbered rings (lower privilege). Access from higher to lower requires
        explicit permission validation.

        Args:
            target_ring: Target ring level to access

        Returns:
            True if access is allowed, False otherwise
        """
        # Ring 0 can access all rings
        if self.level == RingLevel.RING_0:
            return True

        # Higher numbered rings (lower privilege) cannot access lower rings
        return self.level >= target_ring

    def __repr__(self) -> str:
        """String representation of ring."""
        return f"Ring({self.level.name}, mem=[{self.memory_base:#x}, {self.memory_limit:#x}))"
