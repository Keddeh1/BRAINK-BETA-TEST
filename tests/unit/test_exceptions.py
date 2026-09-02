"""Unit tests for exception handling."""

import pytest
from braink.core.exceptions import (
    BrainkException,
    RingAccessException,
    StateTransitionException,
)


class TestExceptions:
    """Tests for custom exceptions."""

    def test_braink_exception_creation(self) -> None:
        """Test creating base exception."""
        exc = BrainkException("test error")
        assert str(exc) == "test error"

    def test_ring_access_exception(self) -> None:
        """Test ring access exception."""
        exc = RingAccessException(
            "Access denied",
            requested_ring=0,
            current_ring=3,
        )
        assert exc.requested_ring == 0
        assert exc.current_ring == 3
        assert "Access denied" in str(exc)

    def test_state_transition_exception(self) -> None:
        """Test state transition exception."""
        exc = StateTransitionException("Invalid transition")
        assert isinstance(exc, BrainkException)
