import json,re
from pathlib import Path
from src.v4.formatos import cena_declarativa_e202 as C, diretor_visual_e202 as D

def test_palco_amplo_consistente():
    ts=Path('motor4/remotion/src/formatos/SceneGraphCoreE201.ts').read_text()
    for name,box in [('BOX_V2',C.CAIXA),('CAPTION_V2',C.LEGENDA)]:
        assert list(box)==json.loads(re.search(name+r'=(\[[^\]]+\])',ts)[1])
    assert (C.CAIXA[2]-C.CAIXA[0])>=1000
    assert (C.CAIXA[3]-C.CAIXA[1])>=900
    assert C.LEGENDA[3]<C.CAIXA[1]

def test_primeiro_quadro_e_palco():
    fx=json.loads(Path('tests/dados/e202_cena_sintetica.json').read_text())
    sg=D.filme({'plano':fx['plano']},fx['caso'])['props']['shots'][0]['scene_graph']
    assert any(a['layer']=='essencial' and a['states'][0]['opacity']>.9 for a in sg['actors'])
