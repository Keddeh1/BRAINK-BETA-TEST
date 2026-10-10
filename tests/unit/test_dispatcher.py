import pytest
from braink.domain.dispatcher import WorkModule,WorkModuleDispatcher,ModuleType,DispatchState
from braink.core.rings import Ring,RingLevel

def module(identity='sample',dependencies=None):
    return WorkModule(identity,ModuleType.SERVICE,'sample','local qualification',{}, {},dependencies or [],'fixture',[])

def test_real_execution_and_duplicate_rejection():
    calls=[];d=WorkModuleDispatcher({'fixture':lambda data:(calls.append(data),{'value':data['value']+1})[1]});m=module();d.register_module(m)
    d.dispatch('1',m,{'value':3});r=d.execute_dispatch('1')
    assert r.state==DispatchState.COMPLETED and r.output_data=={'value':4} and len(calls)==1
    assert d.execute_dispatch('1') is None
    with pytest.raises(ValueError):d.dispatch('1',m,{})
    with pytest.raises(ValueError):d.register_module(m)

def test_unregistered_and_unbound():
    d=WorkModuleDispatcher();m=module()
    with pytest.raises(ValueError):d.dispatch('1',m,{})
    d.register_module(m);d.dispatch('1',m,{})
    assert d.execute_dispatch('1').state==DispatchState.FAILED
    assert d.get_dispatch_status('1')['output_data'] is None

@pytest.mark.parametrize('fn',[lambda data:1,lambda data:(_ for _ in ()).throw(RuntimeError('SECRET'))])
def test_failed_output_or_executor(fn):
    d=WorkModuleDispatcher({'fixture':fn});m=module();d.register_module(m);d.dispatch('1',m,{})
    r=d.execute_dispatch('1');assert r.state==DispatchState.FAILED and 'SECRET' not in r.error

def test_dependencies():
    calls=[];d=WorkModuleDispatcher({'fixture':lambda data:(calls.append(1),{})[1]});a=module('a');b=module('b',['a'])
    d.register_module(a);d.register_module(b);d.dispatch('b-early',b,{})
    assert d.execute_dispatch('b-early').state==DispatchState.FAILED and not calls
    d.dispatch('a',a,{});d.execute_dispatch('a');d.dispatch('b',b,{})
    assert d.execute_dispatch('b').state==DispatchState.COMPLETED

def test_all_ring_pairs():
    for source in RingLevel:
        for target in RingLevel:assert Ring(source).can_access(target)==(source<=target)
