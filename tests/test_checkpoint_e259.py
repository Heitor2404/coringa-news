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


def test_historical_lead_without_lexical_overlap_is_only_a_candidate():
    from scripts import recuperar_checkpoints_documentais as R
    from src.v4.formatos import reuso_documental as RE
    n={'id':'n','sujeito':'ice','mostrar':'glacier surface','fatos':['f'],'necessidade':'registro','evidencia_visual':'estatica','consultas_en':['glacier']}
    h={'escopo':RE.escopo(n),'sha256':'a'*64,'pagina':'https://example.org/a','tipo':'foto','relatorio':'old','necessidade_anterior':'other','estado':'PISTA_HISTORICA_PENDENTE','publicar':False,'direitos_aprovados':False}
    n['candidatos_historicos']=[h]
    row={'sha256':'a'*64,'url_pagina':h['pagina'],'tipo':'foto','titulo':'IMG001'}
    assert R.relevances(row,[n])=={'n':2}
    assert R.relevances(row,[{**n,'mostrar':'different'}])=={}
    assert R.relevances({**row,'url_pagina':'https://example.org/b'},[n])=={}
    assert R.relevances(row,[{**n,'evidencia_visual':'movimento'}])=={}

def test_discovery_can_use_previous_review_not_metadata():
    from scripts import recuperar_checkpoints_documentais as R
    n={'id':'new','sujeito':'ice','mostrar':'glacier surface','fatos':['newfact'],'necessidade':'registro','evidencia_visual':'estatica','consultas_en':['glacier surface']}
    q={'publicar':False,'sha256_origem':'a'*64,'necessidade_id':'old','mostrar':'glacier surface','pixels_sha256':'b'*64,'revisao_id':'r'}
    d={'estado':'PERTINENTE_PRIVADO','publicar':False,'direitos_aprovados':False,'revisao_id':'r'}
    row={'tipo':'foto','titulo':'IMG001','sha256':'a'*64,'analises':{'x':{'publicar':False,'direitos_aprovados':False,'revisao':q,'decisao':d,'escopo_pesquisa':{**n,'id':'old'}}}}
    assert R.relevances(row,[n])=={'new':1.8}
    assert R.relevances(row,[{**n,'evidencia_visual':'movimento'}])=={}

def test_exact_scope_review_precedes_historical_and_lexical_even_if_not_preferred():
    from scripts import recuperar_checkpoints_documentais as R
    rows=[({'a':2},'old',{'name':'old-a'}),({'a':3},'new',{'name':'new-a'}),({'b':2},'old',{'name':'old-b'}),({'a':3},'new',{'name':'alternative-a'})]
    ordered=R.priorizar(rows)
    assert [x[2]['name'] for x in ordered][:2]==['new-a','alternative-a']
    n={'id':'n','sujeito':'ice','mostrar':'glacier surface','fatos':['f'],'necessidade':'registro','evidencia_visual':'estatica'}
    q={'publicar':False,'sha256_origem':'a'*64,'necessidade_id':'n','mostrar':n['mostrar'],'pixels_sha256':'b'*64,'revisao_id':'r'}
    d={'estado':'PERTINENTE_PRIVADO','publicar':False,'direitos_aprovados':False,'revisao_id':'r'}
    row={'tipo':'foto','titulo':'IMG001','sha256':'a'*64,'analises':{'x':{'publicar':False,'direitos_aprovados':False,'revisao':q,'decisao':d,'escopo_pesquisa':n}}}
    assert R.relevances(row,[n])=={'n':3}
    assert R.relevances(row,[{**n,'fatos':['changed']}])=={'n':1.8}
