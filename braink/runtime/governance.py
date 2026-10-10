"""Governed literals and deterministic warrant arithmetic.

Owner source: Governance, Control, and Substantive Architecture Analysis,
8 October 2026. Local oscillator references never redefine the jitter literal.
Arithmetic results do not certify signatures, consensus, storage, or hardware.
"""

JITTER_LITERAL = "0.297"
Q32_SCALE = 1 << 32
# floor(2**32 * ln(level)), for the owner's discrete warrant domain.
# Generated with 70-digit decimal precision; no runtime floating-point logarithms.
WARRANT_LOG_Q32 = (None, 0, 2977044471, 4718503850, 5954088943)


def consilience_sum(levels):
    """Return Q32.32 sum, retaining input levels and absorbing zero separately.

    Zero has no finite logarithm. Level one contributes zero to the arithmetic,
    but remains visible in the inputs; it is never promoted to peer verification.
    Per-term floor error is below 2**-32, and aggregate error grows with terms.
    """
    if type(levels) not in (list, tuple) or not 0 < len(levels) <= 4096:
        raise ValueError("bounded nonempty warrant sequence required")
    if any(type(level) is not int or not 0 <= level <= 4 for level in levels):
        raise ValueError("warrant levels must be integers from zero through four")
    absorbing_zero = 0 in levels
    total = None if absorbing_zero else sum(WARRANT_LOG_Q32[level] for level in levels)
    if total is not None and not -(1 << 63) <= total < (1 << 63):
        raise OverflowError("signed Q32.32 overflow")
    return {"input_levels": list(levels), "sum_q32": total,
            "absorbing_zero": absorbing_zero, "scale": Q32_SCALE}
