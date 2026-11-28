"""Structural integration using a versioned real image and a synthetic review
response. These tests do not assert semantic correctness or editorial approval."""
import json,shutil
from pathlib import Path
from copy import deepcopy
from PIL import Image
from src.v3.pacote_biblioteca import sha
from src.v4.formatos import ponte_cobertura_filme as P,revisao_documental as R,filme_editorial as F
from src.v4.formatos import revelacao_documental_e327 as E

def test_general_bridge_reuses_exact_photo_review_without_extra_calls(tmp_path,monkeypatch):
    src=Path(__file__).resolve().parents[1]/'tests/midia/foto_horizontal_roraima.jpg'
    meta=json.loads(src.with_suffix('.json').read_text())
    monkeypatch.chdir(tmp_path)
    p=Path('stage_documental/test.jpg');p.parent.mkdir();shutil.copyfile(src,p)
    h=sha(p)
    n={'id':'n','fatos':['f'],'mostrar':'Região específica da imagem','sujeito':'Paisagem','papel_visual':'detalhe','evidencia_visual':'estatica','exigir_evidencia_direta':True}
    c={'fonte':'commons','source_id':'fixture','tipo':'foto','pagina':meta['pagina'],'credito':meta['autor']+' · '+meta['licenca'],'licenca':meta['licenca'],'local_source':str(p),'aquisicao':{'sha256':h,'width':1800,'height':1200,'duration_s':None}}
    calls=[]
    def response(prompt,images):
        calls.append(prompt)
        assert 'rotulo_detalhe' in prompt
        return {'veredito':'pertinente','natureza_visual':'registro_compativel','inspecao':'Resposta sintética de QA para testar o vínculo com a região da imagem.',
            'rotulo_detalhe':'REGIÃO DE TESTE','evidencia_direta':{'classe':'direta','detalhe':'Região de teste para o contrato de detalhe visual.','escala':'xy_0_1000','bbox':{'esquerda':350,'topo':200,'direita':530,'base':340}}}
    with Image.open(p) as im:
        im.thumbnail((1280,1280));c['revisao']=R.revisar_foto({'expected_sha256':h},im,n,response)
    c['decisao']=R.decidir(n,c,c['revisao'],tipo='foto')
    case={'tema':'Prova estrutural','chapters':[{'title':'Contexto','needs':['n']}]}
    report={'publish':False,'triagem':[n],'cobertura':[{'necessidade_id':'n','estado':'CANDIDATO_PRIVADO_REVISADO','selecionado':['commons','fixture'],'rodadas':[{'pesquisa':{'candidatos':[c]}}]}]}
    chosen,gate=P.preparar_cobertura(report,case,minimo_s=1.4)
    assert gate['pronto_para_tts']
    plan=P.plano(case,chosen,[108]);s=plan['shots'][0]
    assert s['static_fact_reveal']['label']=='REGIÃO DE TESTE' and 'photo_roi_candidate' not in s
    assert s['static_fact_reveal']['detail_zoom'] is True
    assert plan['revelacoes_documentais'][0]['tempo']=='METADE_DA_CENA_NAO_ANCORA_DE_FALA'
    assert not plan['revelacoes_documentais'][0]['aprovacao_editorial'] and len(calls)==1
    F.preparar(plan,Path('out'),Path('public'),fragmento_misto=True)
    props=json.loads(Path('out/props.json').read_text())
    assert props['shots'][0]['documentary_static_reveal']['detail_zoom'] is True
    for k,value in [('pixels_sha256','b'*64),('mostrar','outra necessidade'),('revisao_id','c'*64)]:
        bad=deepcopy(chosen);bad['n']['candidate']['revisao'][k]=value
        out=P.plano(case,bad,[108]);assert 'static_fact_reveal' not in out['shots'][0]
    old=deepcopy(chosen);old['n']['candidate']['revisao']['resposta'].pop('rotulo_detalhe')
    assert 'static_fact_reveal' not in P.plano(case,old,[108])['shots'][0]
    wrong=deepcopy(chosen);wrong['n']['candidate']['revisao']['resposta']['rotulo_detalhe']='Paisagem'
    assert 'static_fact_reveal' not in P.plano(case,wrong,[108])['shots'][0]
    short=P.plano(case,chosen,[60]);assert not short['revelacoes_documentais']
    from src.v4.formatos.direcao_short_e306 import diagnosticar
    assert not diagnosticar(plan)['pronto_para_analise_visual']
