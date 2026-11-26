import pytest
from scripts import qa_documentario_geografia_e219 as E

def test_binding_rejects_wrong_fact_hash_or_overlap():
    cut=dict(chapter='A',speech='FRAGMENTOS',source='s',label='fonte',sha256='h',
             window_start=7,window_duration=3.8,observed='sample',review_ref='sheet')
    media={'s':dict(label='fonte',expected_sha256='h',duration_s=30)}
    words=[dict(w='FRAGMENTOS',s=0,e=2)]
    assert E.corte_revisado(cut,media,words,'A',0,2,{})==(media['s'],7)
    with pytest.raises(ValueError,match='FALA'):
        E.corte_revisado(cut,media,[dict(w='EVACUACAO',s=0,e=2)],'A',0,2,{})
    with pytest.raises(ValueError,match='VINCULO'):
        E.corte_revisado({**cut,'sha256':'other'},media,words,'A',0,2,{})
    with pytest.raises(ValueError,match='REPETICAO'):
        E.corte_revisado(cut,media,words,'A',0,2,{'h':[(8,10)]})
    with pytest.raises(ValueError,match='JANELA'):
        E.corte_revisado(cut,media,words,'A',0,4,{})
