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
