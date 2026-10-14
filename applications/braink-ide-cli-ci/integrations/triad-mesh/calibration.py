"""Measured latency windows and non-destructive acceptance evaluation."""
from collections import deque
import math
import threading


class Measurements:
    def __init__(self, window=512, p99_budget_ns=15_000_000):
        if type(window) is not int or window<1 or type(p99_budget_ns) is not int or p99_budget_ns<1:
            raise ValueError('Positive sample window and explicit latency budget required')
        self.window=deque(maxlen=window);self.p99s=deque(maxlen=16)
        self.budget=p99_budget_ns;self.lock=threading.Lock()

    def observe(self, elapsed_ns):
        if type(elapsed_ns) is not int or elapsed_ns<0:raise ValueError('Measured nanoseconds required')
        with self.lock:
            self.window.append(elapsed_ns)
            ordered=sorted(self.window);p99=ordered[(99*len(ordered)+99)//100-1]
            self.p99s.append(p99)
            return {'samples':len(ordered),'p99_ns':p99,'p99_budget_ns':self.budget,
                    'moving_mean_p99_ns':sum(self.p99s)//len(self.p99s),
                    'latency_acceptance':'PASS' if p99<self.budget else 'EXCEEDED',
                    'disk_io_saturation':None,'hardware_thread_contention':None,
                    'tolerance_index':None,'calibration_state':'HARDWARE_BASELINE_NOT_BOUND',
                    'effect':'diagnostic only; no transport shutdown',
                    'da_registrar':{'state':'UNASSESSED','affects_braink_admission':False}}
