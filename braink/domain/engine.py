"""Domain Engine implementation.

Handles domain-level validation, state management, and orchestration.
"""

from typing import Dict, Any
from braink.core.rings import Ring, RingLevel, RingState
from braink.core.exceptions import EngineExecutionException


class DomainEngine:
    """Manages domain-level operations and validations."""

    def __init__(self) -> None:
        """Initialize the domain engine."""
        self._rings: Dict[RingLevel, Ring] = {}
        self._initialized = False

    def initialize(self) -> None:
        """Initialize domain engine with default ring configuration.

        Raises:
            EngineExecutionException: If initialization fails
        """
        try:
            # Initialize rings with default memory layout
            self._rings[RingLevel.RING_0] = Ring(
                RingLevel.RING_0,
                memory_base=0x00000000,
                memory_size=0x10000000,
            )
            self._rings[RingLevel.RING_1] = Ring(
                RingLevel.RING_1,
                memory_base=0x10000000,
                memory_size=0x10000000,
            )
            self._rings[RingLevel.RING_2] = Ring(
                RingLevel.RING_2,
                memory_base=0x20000000,
                memory_size=0x10000000,
            )
            self._rings[RingLevel.RING_3] = Ring(
                RingLevel.RING_3,
                memory_base=0x30000000,
                memory_size=0x10000000,
            )
            self._initialized = True
        except Exception as e:
            raise EngineExecutionException(
                f"Failed to initialize domain engine: {str(e)}"
            ) from e

    @property
    def is_initialized(self) -> bool:
        """Check if engine is initialized."""
        return self._initialized

    def get_ring(self, level: RingLevel) -> Ring:
        """Get a ring by level.

        Args:
            level: Ring level to retrieve

        Returns:
            Ring instance at specified level

        Raises:
            EngineExecutionException: If ring not found
        """
        if not self._initialized:
            raise EngineExecutionException("Engine not initialized")

        if level not in self._rings:
            raise EngineExecutionException(f"Ring {level.name} not found")

        return self._rings[level]

    def validate_transition(
        self,
        from_ring: RingLevel,
        to_ring: RingLevel,
    ) -> bool:
        """Validate that a ring transition is allowed.

        Args:
            from_ring: Source ring level
            to_ring: Target ring level

        Returns:
            True if transition is valid
        """
        if not self._initialized:
            return False

        source = self._rings.get(from_ring)
        if source is None:
            return False

        return source.can_access(to_ring)
