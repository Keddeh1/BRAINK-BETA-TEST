"""Custom exceptions for BRAINK components."""


class BrainkException(Exception):
    """Base exception for all BRAINK errors."""

    pass


class RingAccessException(BrainkException):
    """Raised when unauthorized ring-level access is attempted."""

    def __init__(
        self,
        message: str,
        requested_ring: int,
        current_ring: int,
    ) -> None:
        """Initialize RingAccessException.

        Args:
            message: Human-readable error message
            requested_ring: Ring level being accessed
            current_ring: Current ring level privilege
        """
        self.requested_ring = requested_ring
        self.current_ring = current_ring
        super().__init__(message)


class StateTransitionException(BrainkException):
    """Raised when an invalid state transition is attempted."""

    pass


class EngineExecutionException(BrainkException):
    """Raised when engine execution fails."""

    pass
