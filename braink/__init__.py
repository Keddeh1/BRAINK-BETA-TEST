"""BRAINK - KEX_SEED Ring Architecture Implementation.

This package provides the core implementation of the KEX_SEED Ring Architecture
(Ring 0..3) and the Domain/Runtime Engines.
"""

__version__ = "0.1.0"
__author__ = "Keddeh1"
__license__ = "MIT"

# Core exports
from braink.core.rings import (
    Ring,
    RingLevel,
    RingState,
)
from braink.core.exceptions import (
    BrainkException,
    RingAccessException,
)

__all__ = [
    "Ring",
    "RingLevel",
    "RingState",
    "BrainkException",
    "RingAccessException",
]
