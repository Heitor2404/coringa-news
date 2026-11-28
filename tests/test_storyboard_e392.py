import copy,json
from pathlib import Path
import pytest
from scripts.qa_storyboard_e392 import compile_board,FAMILY,ACTIONS
from src.v4.formatos import grafo_causal as G,camera_causal_svg as C
def sample():
    return {'sequence':json.loads(Path('benchmarks/e391/sequence.json').read_text()),'private_review_only':True,'duracao':428/30,'captions':[]}
def test_existing_graph_and_camera_drive_four_boards():
    p=sample();out=compile_board(p)
    assert out['graph']==G.montar(FAMILY,ACTIONS,momentos=tuple(s['at'] for s in p['sequence']['states'][1:]))
    assert out['boards'][0]['state']['reservoir.material']=='initial'
    assert out['boards'][1]['state']['reservoir.material']=='reduced'
    assert out['boards'][2]['state']['roof.position']=='lowered'
    assert out['boards'][3]['state']['crater.depth']=='deeper'
    assert len({tuple(x['camera'].values()) for x in out['boards']})==1
    assert not out['publish'] and not out['physical_simulation']
def test_cannot_reuse_mechanical_physics_or_fake_source():
    p=sample();p['sequence']['sourceSha']='a'*64
    with pytest.raises(ValueError,match='E392-SOURCE'):compile_board(p)
    with pytest.raises(G.GrafoInvalido):G.montar(FAMILY,('open','fill','equalize'))
    with pytest.raises(ValueError):C.calcular(FAMILY,'rise',4,3,14)
