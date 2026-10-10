"""Canonical Q32.32 logarithms for explicitly assigned warrant levels.

No evidence level is inferred or upgraded here. Level zero is not logarithmable.
For n positive inputs the aggregate floor error is < n / 2**32.
"""
SCALE = 1 << 32
MAX_SIGNED = (1 << 63) - 1
LOG_Q32 = {1: 0, 2: 2977044471, 3: 4718503850, 4: 5954088943}


def aggregate(levels):
    result = 0
    count = 0
    for level in levels:
        if type(level) is not int or level not in LOG_Q32:
            raise ValueError('An explicit positive warrant level 1..4 is required; log(0) is undefined')
        term = LOG_Q32[level]
        if result > MAX_SIGNED - term:
            raise OverflowError('Signed Q32.32 accumulator exceeded')
        result += term
        count += 1
    return {'raw_q32': result, 'scale': SCALE, 'terms': count,
            'floor_error_upper_bound': {'numerator':count,'denominator':SCALE},
            'qualification':'Arithmetic aggregation does not establish warrant or consensus'}
