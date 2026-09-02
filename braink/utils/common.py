"""Common utility functions."""

from typing import Any


def format_memory_address(address: int, width: int = 16) -> str:
    """Format a memory address for display.

    Args:
        address: Memory address as integer
        width: Number of hex digits to display

    Returns:
        Formatted address string
    """
    return f"0x{address:0{width}x}"


def validate_ring_level(value: int) -> bool:
    """Validate that value is a valid ring level (0-3).

    Args:
        value: Ring level value to validate

    Returns:
        True if valid, False otherwise
    """
    return 0 <= value <= 3
