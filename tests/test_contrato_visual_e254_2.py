import pytest
from src.v4.formatos import revisao_documental as R
from src import acervo

# Exact coordinate arrays from E254's recovered review report.
BOXES=[[0,500,1000,760],[373,270,1000,1000],[266,258,906,948],
       [561,352,999,996],[502,507,990,976],[331,273,353,303],
       [0,0,1000,1000],[294,303,1000,1000],[0,0,1000,1000],
       [236,251,677,561],[331,418,902,908]]
def decision(box,verdict='pertinente',nature='registro_compativel',classe='direta',**extra):
    n={'id':'n','exigir_evidencia_direta':True,'evidencia_visual':'estatica'}
    c={'aquisicao':{'sha256':'a'*64}}
    r={'sha256_origem':'a'*64,'necessidade_id':'n','revisao_id':'r',
       'resposta':{'veredito':verdict,'natureza_visual':nature,'evidencia_direta':
        {'classe':classe,'detalhe':'Componente concreto descrito pelo revisor visual','bbox':box,**extra}}}
    return R.decidir(n,c,r,tipo='foto')

@pytest.mark.parametrize('box',BOXES)
def test_replay_e254_scale(box):
    d=decision(box)
    assert d['estado']=='PERTINENTE_PRIVADO'
    assert d['evidencia_direta_normalizada']['bbox']==[x/1000 for x in box]
    assert not d['evidencia_direta_normalizada']['enquadramento_verificado']
    assert not d['direitos_aprovados'] and not d['publicar']

@pytest.mark.parametrize('box',[[0,0,1001,1000],[500,0,300,1000],[0,.5,1000,1000],
                                  [False,0,1000,1000],[0,0,float('nan'),1],None])
def test_bad_box(box):
    assert decision(box)['estado']=='INSUFICIENTE'

def test_explicit_named_axes_and_semantics():
    box={'esquerda':100,'topo':200,'direita':800,'base':900}
    d=decision(box,escala='xy_0_1000')
    assert d['evidencia_direta_normalizada']['bbox']==[.1,.2,.8,.9]
    assert decision(box)['estado']=='INSUFICIENTE'
    assert decision(box,escala='xy_0_1')['estado']=='INSUFICIENTE'
    assert decision(BOXES[0],verdict='contexto')['motivo']=='SEM_PERTINENCIA'
    assert decision(BOXES[0],classe='contextual')['estado']=='INSUFICIENTE'
    assert decision(BOXES[0],nature='ilustracao')['estado']=='INSUFICIENTE'

def test_rank_file_before_unrelated_category(monkeypatch):
    monkeypatch.setattr(acervo,'_busca_commons',lambda q,n,**kwargs:['File:relevant'])
    monkeypatch.setattr(acervo,'_categoria_commons',lambda q,n,**kwargs:['File:garlic','File:partial'])
    def info(titles,source,*,preview_width,estrito):
        assert preview_width == 1400 and estrito
        assert titles[0]=='File:relevant'
        return [{'titulo':'Garlic in garden'},{'titulo':'Glacier crevasses aerial'},
                {'titulo':'Mountain glacier','categories':'Glaciers'}]
    monkeypatch.setattr(acervo,'_commons_infos',info)
    assert [c['titulo'] for c in acervo.f_commons_documental('glacier crevasses aerial')]==['Glacier crevasses aerial','Mountain glacier']


def test_commons_documental_reports_provider_error_and_keeps_partial_alternative(monkeypatch):
    from requests import Timeout
    def failed(*args, **kw):
        raise Timeout('provider')
    monkeypatch.setattr(acervo, '_get', failed)
    with pytest.raises(Timeout):
        acervo.f_commons_documental('chamber condensation')
    monkeypatch.setattr(acervo, '_categoria_commons', lambda *a, **k: ['File:Chamber'])
    monkeypatch.setattr(acervo, '_commons_infos', lambda titles, *a, **kw: [{'titulo': 'Chamber'}])
    assert acervo.f_commons_documental('chamber')[0]['titulo'] == 'Chamber'
