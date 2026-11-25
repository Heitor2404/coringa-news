import json,pytest
from pathlib import Path
from scripts.qa_adquirir_pretriagem_e272 import selecionados

def test_preview_selection_matches_exact_hash_page_and_obligation():
    spec=json.loads(Path('benchmarks/e254/documentario.json').read_text())
    choices=json.loads(Path('benchmarks/e265/pretriagem_selecionada.json').read_text())
    x=choices['selecao'][0];choices['selecao']=[x]
    a={**x,'estado':'PRETRIAGEM_PENDENTE','publicar':False,'source_id':1}
    report={'publicar':False,'necessidades':[{'id':x['id'],'amostras':[a]}]}
    assert len(selecionados(spec,report,choices))==1
    with pytest.raises(ValueError):selecionados(spec,report,{**choices,'selecao':[{**x,'preview_sha256':'0'*64}]})
    with pytest.raises(ValueError):selecionados(spec,report,{**choices,'selecao':[{**x,'mostrar':'other'}]})


def test_observed_preview_selection_checks_scope_and_sheet(tmp_path):
    import hashlib
    from src.v4.pretriagem_documental import escolhas_observadas
    from src.v4.formatos import diretor_visual_e202 as D,reuso_documental as RE
    spec=json.loads(Path('benchmarks/e254/documentario.json').read_text())
    old=json.loads(Path('benchmarks/e265/pretriagem_selecionada.json').read_text())
    x=old['selecao'][0];case=next(c for c in spec['cases'] if c['id']==old['case'])
    n=next(n for n in D.triagem_documental(case['necessidades'],case['fatos'],progressivo=True) if n['id']==x['id'])
    (tmp_path/'sheet.jpg').write_bytes(b'test-sheet')
    a={**x,'estado':'PRETRIAGEM_PENDENTE','publicar':False,'source_id':1,'folha':'sheet.jpg'}
    report={'publicar':False,'necessidades':[{'id':x['id'],'amostras':[a]}]}
    o={**a,'escopo':RE.escopo(n),'folha_sha256':hashlib.sha256(b'test-sheet').hexdigest(),'origem':'INSPECAO_ASSISTIDA','observacao':'Referente visivel na amostra.','decisao':'PRIORIZAR_AQUISICAO'}
    obs={'case':case['id'],'publicar':False,'direitos_aprovados':False,'observacoes':[o]}
    result=escolhas_observadas(spec,report,obs,tmp_path)
    assert len(selecionados(spec,report,result))==1
    assert not escolhas_observadas(spec,report,{**obs,'observacoes':[{**o,'decisao':'NAO_PRIORIZAR'}]},tmp_path)['selecao']
    with pytest.raises(ValueError,match='E278-ESCOPO'):escolhas_observadas(spec,report,{**obs,'observacoes':[{**o,'escopo':{}}]},tmp_path)
    (tmp_path/'sheet.jpg').write_bytes(b'changed')
    with pytest.raises(ValueError,match='E278-FOLHA'):escolhas_observadas(spec,report,obs,tmp_path)
