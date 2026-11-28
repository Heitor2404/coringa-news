import pytest
from src.v4.formatos.integracao_incremental_e343 import intervalos
def shots():
    return [{'id':'a','start':0,'end':2},{'id':'b','start':2,'end':3},{'id':'c','start':3,'end':4},{'id':'d','start':4,'end':8}]
def test_partition_exact_frame_and_unchanged_ranges():
    p=intervalos(shots(),8,{'a','b','d'})
    assert [(r['start'],r['end'],r['changed']) for r in p]==[(0,90,True),(90,120,False),(120,240,True)]
    assert p[0]['shots']==['a','b']
@pytest.mark.parametrize('fault',['gap','overlap','unknown','fraction','duplicate','end'])
def test_partition_rejects_fault(fault):
    s=shots();d=8;c={'b'}
    if fault=='gap':s[1]['start']=2.1
    if fault=='overlap':s[1]['start']=1.9
    if fault=='unknown':c={'missing'}
    if fault=='fraction':s[0]['end']=2.001;s[1]['start']=2.001
    if fault=='duplicate':s[1]['id']='a'
    if fault=='end':d=9
    with pytest.raises(ValueError):intervalos(s,d,c)
