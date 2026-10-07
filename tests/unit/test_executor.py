from concurrent.futures import ThreadPoolExecutor
import pytest
from braink.runtime.executor import RuntimeExecutor
from braink.core.rings import Ring,RingLevel
from braink.core.exceptions import RingAccessException

def test_denied_access_never_calls_operation():
 executor=RuntimeExecutor(Ring(RingLevel.RING_3));calls=[]
 with pytest.raises(RingAccessException):executor.execute(lambda:calls.append(1),target_ring=RingLevel.RING_0)
 assert not calls and executor.operation_count==0

def test_success_counts_under_concurrency():
 executor=RuntimeExecutor(Ring(RingLevel.RING_1))
 with ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(lambda i:executor.execute(lambda n:n+1,i,target_ring=RingLevel.RING_2),range(128)))
 assert results==list(range(1,129)) and executor.operation_count==128

def test_failed_operation_not_counted():
 executor=RuntimeExecutor(Ring(RingLevel.RING_1))
 with pytest.raises(RuntimeError):executor.execute(lambda:1/0)
 assert executor.operation_count==0
