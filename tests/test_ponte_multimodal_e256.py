import json,hashlib
from pathlib import Path
import pytest
from src.v4.formatos import ponte_cobertura_filme as P,revisao_documental as R
from src.v4 import acervo_v4 as A

def test_actual_extent_response_e255():
    e={'classe':'direta','detalhe':'extensa rede de fendas visíveis por toda a superfície',
       'escala':'0_1000','bbox':{'esquerda':0,'topo':180,'delta_x':1000,'delta_y':820}}
    assert R.normalizar_evidencia_direta(e)['bbox']==[0,.18,1,1]
    e['bbox']['delta_y']=821
    assert R.normalizar_evidencia_direta(e) is None
    e['bbox']['delta_y']=820
    e['bbox']['direita']=1000
    assert R.normalizar_evidencia_direta(e) is None

def test_alternative_query_reaches_primary_video_provider():
    calls=[]
    def providers(t):
        assert t=='video'
        return [(k,lambda q,k=k:calls.append((k,q)) or []) for k in ('primary','second','third','fourth')]
    n={'id':'n','necessidade':'registro','evidencia_visual':'movimento','pesquisa':{'consultas_en':['first query','alternative query']}}
    A.pesquisar_cobertura(n,fontes=providers,max_buscas=4)
    assert ('primary','first query') in calls and ('primary','alternative query') in calls and len(calls)==4

def test_map_requires_proof_and_binding(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    n={'id':'n','necessidade':'territorio','sujeito':'região','mostrar':'localização','fatos':['f']}
    report={'publish':False,'triagem':[n],'cobertura':[{'necessidade_id':'n','estado':'DELEGAR_ATLAS'}]}
    case={'tema':'fixture','chapters':[{'title':'local','needs':['n']}]}
    assert not P.preparar_cobertura(report,case,minimo_s=5)[1]['pronto_para_tts']
    # Synthetic contract test only: no claim of cartographic rendering.
    p=Path('stage_atlas/test');p.mkdir(parents=True);clip=p/'map.mp4';clip.write_bytes(b'fixture')
    digest=hashlib.sha256(clip.read_bytes()).hexdigest()
    proof=p/'proof.json';proof.write_text(json.dumps({'renderer':'ATLAS/Formato/PalcoMapa/MapLibre',
        'status':'PRONTO_PARA_REVISAO_HUMANA','aprovacao_humana':'PENDENTE','publicado':False,
        'video_sha256':digest,'duracao_s':5.5,'mapeamento':{'rasters_ativos':[{'atribuicao':'Natural Earth'}],'roi':[0,0,1,1]},'quadros_reais':[{}]}))
    m={'necessidade_id':'n','fatos':['f'],'mostrar':'localização','origem':'CURADORIA_GEOGRAFICA_VERIFICADA',
       'local_source':str(clip),'atlas_proof':str(proof),'expected_sha256':digest}
    chosen,gate=P.preparar_cobertura(report,case,atlas={'n':m},minimo_s=5)
    assert gate['pronto_para_tts'] and chosen['n']['cap']==5.5
    plan=P.plano(case,chosen,[165])
    assert plan['shots'][0]['type']=='atlas_map' and not plan['publicar']
    with pytest.raises(ValueError):P.plano(case,chosen,[120])
    clip.write_bytes(b'changed')
    assert not P.preparar_cobertura(report,case,atlas={'n':m},minimo_s=5)[1]['pronto_para_tts']
