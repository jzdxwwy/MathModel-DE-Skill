import pytest
from tools.runtime.v09c_contracts import ContractBlocked, validate_binding
from tools.runtime.expression_adapter import optimize, sensitivity, monte_carlo

def test_missing_inputs_blocked():
    with pytest.raises(ContractBlocked): validate_binding('optimization', {'variables':['x'], 'bounds':[[0,1]]})

def test_optimization():
    r=optimize({'objective_expression':'(x-3)^2','variables':['x'],'bounds':[[0,10]],'initial_point':[1]})
    assert abs(r['x'][0]-3)<1e-5

def test_sensitivity():
    r=sensitivity({'objective_expression':'2*x+y','base':{'x':1,'y':1},'grid':[0.5,1,1.5]})
    assert r['ranking']['x']>r['ranking']['y']

def test_monte_carlo_seed():
    b={'event_expression':'x-1','variables':['x'],'distributions':{'x':{'name':'normal','mean':0,'std':1}},'n':1000,'seed':7}
    assert monte_carlo(b)==monte_carlo(b)

def test_graph_contract():
    validate_binding('shortest_path',{'data_path':'edges.csv','source':'A','target':'Z','directed':False})
