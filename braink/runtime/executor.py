"""Runtime Executor - Executes operations within ring contexts."""

from typing import Any, Callable, Optional
from braink.core.rings import Ring, RingLevel
from braink.core.exceptions import RingAccessException


class RuntimeExecutor:
    """Executes operations within ring privilege contexts."""

    def __init__(self, current_ring: Ring) -> None:
        """Initialize executor for a ring.

        Args:
            current_ring: Ring to execute within
        """
        self.current_ring = current_ring
        self._operation_count = 0

    def execute(
        self,
        operation: Callable[..., Any],
        *args: Any,
        target_ring: Optional[RingLevel] = None,
        **kwargs: Any,
    ) -> Any:
        """Execute an operation within ring context.

        Args:
            operation: Callable to execute
            *args: Positional arguments for operation
            target_ring: Ring level required for operation (None = current ring)
            **kwargs: Keyword arguments for operation

        Returns:
            Result of operation execution

        Raises:
            RingAccessException: If insufficient privilege to execute
        """
        # Validate ring access if target specified
        if target_ring is not None:
            if not self.current_ring.can_access(target_ring):
                raise RingAccessException(
                    f"Ring {self.current_ring.level.name} cannot access "
                    f"Ring {target_ring.name}",
                    requested_ring=target_ring.value,
                    current_ring=self.current_ring.level.value,
                )

        try:
            result = operation(*args, **kwargs)
            self._operation_count += 1
            return result
        except RingAccessException:
            raise
        except Exception as e:
            raise RuntimeError(f"Operation execution failed: {str(e)}") from e

    @property
    def operation_count(self) -> int:
        """Get total operations executed."""
        return self._operation_count
