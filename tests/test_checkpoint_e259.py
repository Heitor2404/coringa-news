import hashlib,zipfile
import pytest
from src.v3 import pacote_biblioteca as P

def test_checkpoint_zip_flat_contract(tmp_path):
    z=tmp_path/'ok.zip'
    with zipfile.ZipFile(z,'w') as f:
        f.writestr('index.json','{}')
        f.writestr('manifesto.jsonl','{}')
        f.writestr('a'*64+'.webm',b'fixture')
    h=P.sha(z);dest=P.extrair_checkpoint(z,tmp_path/'safe',expected_sha256=h)
    assert (dest/('a'*64+'.webm')).read_bytes()==b'fixture'
    with pytest.raises(ValueError,match='E259-ZIP-SHA'):
        P.extrair_checkpoint(z,tmp_path/'wrong',expected_sha256='0'*64)

def test_checkpoint_zip_never_extracts_arbitrary_path(tmp_path):
    z=tmp_path/'bad.zip'
    with zipfile.ZipFile(z,'w') as f:
        f.writestr('index.json','{}');f.writestr('manifesto.jsonl','{}')
        f.writestr('../escape',b'unsafe')
    with pytest.raises(ValueError,match='E259-ZIP-NOME'):
        P.extrair_checkpoint(z,tmp_path/'bad',expected_sha256=P.sha(z))
    assert not (tmp_path/'escape').exists() and not (tmp_path/'bad').exists()


def test_checkpoint_discovery_paginates_past_recent_diagnostics(monkeypatch):
    from scripts import recuperar_checkpoints_documentais as R
    calls=[]
    def api(path):
        calls.append(path)
        return [{'tag_name':str(i)} for i in range(20)] if path.endswith('page=1') else [{'tag_name':'older'}]
    monkeypatch.setattr(R,'api',api)
    assert R.listar_releases(60)[-1]['tag_name']=='older'
    assert len(calls)==2


def test_checkpoint_order_reserves_best_candidate_per_need():
    from scripts import recuperar_checkpoints_documentais as R
    rows=[({'a':1},'tag',{'name':'a1'}),({'a':.9},'tag',{'name':'a2'}),({'b':.4},'tag',{'name':'b1'})]
    assert [x[2]['name'] for x in R.priorizar(rows)]==['a1','b1','a2']
    n=[{'id':'a','necessidade':'registro','evidencia_visual':'movimento','consultas_en':['glacier']}, {'id':'b','necessidade':'registro','evidencia_visual':'estatica','consultas_en':['glacier']}]
    assert R.relevances({'tipo':'foto','titulo':'glacier'},n)=={'b':1}
