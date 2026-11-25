"""E237 offline contracts; not evidence of downloaded imagery or semantic autonomy."""
import json
from pathlib import Path
import pytest
from scripts import qa_atlas_multiscale as G
from src.v4.formatos import diretor_visual_e202 as D

CASES=json.loads(Path('benchmarks/e236/regioes.json').read_text())['cases']

@pytest.mark.parametrize('caso',CASES,ids=[c['id'] for c in CASES])
def test_plan_and_acquire_once(caso,monkeypatch):
    plans=G.escalas(caso['atlas']['roi'],caso['delta'])
    assert plans and len(plans)<=3
    assert all(0<p['tiles']<=100 for p in plans)
    assert all(p['dataset']==('bmng' if p['zoom']<=8 else 's2_2016') for p in plans)
    assert any(p['dataset']=='s2_2016' for p in plans)
    calls=[]
    def acquire(name,bbox,z,dataset):
        calls.append((name,z,dataset))
        return {'nome':name,'dataset':dataset}
    monkeypatch.setattr(G.R,'registrar_base_regional',acquire)
    data=G.adquirir_bases(caso)
    assert len(calls)==len(plans)
    monkeypatch.setattr(G.E,'mapplan',lambda ch,span:{'duracao':span})
    monkeypatch.setattr(G.DE,'plano_entrada_geografica',lambda p,**kw:(p,kw))
    for span in (1.4,3.,5.5,8.):
        ch,p,report=G.resolver(caso,data,span)
        assert p['duracao']==span
        assert report['bases']==data['bases']
        assert report['roi_destino']==caso['atlas']['roi']
        assert ch['atlas']['raster']==data['bases'][0]['nome']
    assert len(calls)==len(plans)

def test_invalid_pin_refused_before_acquisition(monkeypatch):
    c={**CASES[0],'atlas':{**CASES[0]['atlas'],'lonlat':[0,0]}}
    monkeypatch.setattr(G.R,'registrar_base_regional',lambda *a:pytest.fail('network'))
    with pytest.raises(ValueError,match='GEO-MARCADOR'):
        G.adquirir_bases(c)

@pytest.mark.parametrize('objective,resource',[
    ('localizacao','regiao'),('relevo','elevação_verificada'),
    ('rota','trajeto_verificado'),('territorio','limites_verificados'),
    ('comparacao','escala_comparavel')])
def test_director_requests_evidence_not_ready_map(objective,resource):
    n={'id':'m','sujeito':'região natural','mostrar':'relação espacial',
       'necessidade':'territorio','fatos':['f1'],'objetivo_geografico':objective}
    r=D.triagem_documental([n],[{'id':'f1'}],{'itens':[],'reprovados':[]})[0]
    g=r['solicitacao_atlas']
    assert resource in g['recursos_candidatos'] and g['verificar_epoca']
    assert not g['pronto_para_render'] and not r['pronto_para_render']

def test_real_record_has_no_geographic_request():
    n={'id':'r','sujeito':'animal','mostrar':'ação real','necessidade':'registro','fatos':['f1']}
    r=D.triagem_documental([n],[{'id':'f1'}],{'itens':[],'reprovados':[]})[0]
    assert 'solicitacao_atlas' not in r and r['modalidade_proposta']=='registro_real'
