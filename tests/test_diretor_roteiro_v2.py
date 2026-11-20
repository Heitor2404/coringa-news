"""Roteiro V2 → forma V3 → catálogo V4 → preflight FilmeEditorial.

Conferimos três tipos de evidência com o MESMO diretor e outro tema
sem renderer. O sistema NÃO inventa imagem, vídeo nem ação física.
"""
import copy
import json
from pathlib import Path

from src.v4.formatos import diretor_roteiro as R
from src.v4.formatos import filme_editorial as F

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/v4/formatos'


def load(name):
    return json.loads((DOC/name).read_text('utf8'))


def codes(p):
    return {x['codigo'] for x in F.avaliar(p)['bloqueios']}


def test_cadeia_dos_chips_escolhe_candidato_foto_mecanismo_e_bloqueia_registro_sem_prova():
    p=load('QA_ROTEIRO_V2_TAIWAN_20261120.json')
    rel=R.analisar(p)
    assert rel['pronto_para_render'] is False
    assert rel['status']=='BLOQUEADO'
    assert rel['total_cenas']==3
    a,b,c=rel['decisoes']
    assert a['forma_v3']=='registro'
    assert a['estado']=='CANDIDATO_DOCUMENTAL_SEM_BYTES'
    assert any('TSMC_Fab_18' in it['asset_id'] for it in a['candidatos'])
    assert 'R-ASSET-NAO-REVALIDADO' in {x['codigo'] for x in a['bloqueios']}
    assert b['forma_v3']=='esquema'
    assert b['estado']=='CAPACIDADE_TECNICA_DISPONIVEL'
    assert b['capacidade']=='optical_projection'
    assert b['prova_factual_verificada'] is False
    assert c['estado']=='BLOQUEADO'
    assert c['candidatos']==[]
    assert 'R-SEM-REGISTRO' in {x['codigo'] for x in c['bloqueios']}
    assert not F.avaliar(p)['pronto']
    assert 'R-ASSET-NAO-REVALIDADO' in codes(p)
    assert rel['publicar'] is False and rel['telegram'] is False


def test_acontecimento_v2_isolado_vira_render_por_rotas_existentes(tmp_path):
    p=load('QA_ROTEIRO_V2_EUV_20261120.json')
    assert 'shots' not in p and 'eventos_diretor' not in p
    assert not any('capacidade' in c['acontecimento'] for c in p['roteiro']['cenas'])
    res=R.expandir_preview(p)
    assert len(res['shots'])==1
    assert res['shots'][0]['mechanism']=='auto'
    assert [c['action'] for c in res['shots'][0]['cues']]==[
        'source','reticle','projection','wafer']
    assert F.avaliar(p)['pronto'],F.avaliar(p)['bloqueios']
    q=F.preparar(p,tmp_path/'prova',tmp_path/'public')
    assert q['pronto']
    props=json.loads((tmp_path/'prova/props.json').read_text('utf8'))
    assert props['shots'][0]['mechanism']=='optical_projection'
    assert props['duracao']==6.9
    assert not p.get('shots')  # nenhuma mutação da pauta fonte


def test_fenomeno_inedito_sem_renderer_gera_bloqueio_nao_cartao():
    p=load('QA_ROTEIRO_V2_OXIDACAO_20261120.json')
    rel=R.analisar(p)
    assert rel['decisoes'][0]['tipo_v2']=='transformacao'
    assert rel['decisoes'][0]['forma_v3']=='esquema'
    assert rel['decisoes'][0]['capacidade'] is None
    assert 'R-SEM-MECANISMO' in {e['codigo'] for e in rel['bloqueios']}
    assert not F.avaliar(p)['pronto']


def test_sem_acontecimento_v2_nao_adivinha_pela_fala():
    p=load('QA_ROTEIRO_V2_EUV_20261120.json')
    del p['roteiro']['cenas'][0]['acontecimento']
    assert 'R-ACONTECIMENTO-AUSENTE' in {x['codigo'] for x in R.analisar(p)['bloqueios']}
    assert 'R-ACONTECIMENTO-AUSENTE' in codes(p)


def test_nao_deixar_recurso_manualmente_escolhido_passar_como_auto():
    p=load('QA_ROTEIRO_V2_EUV_20261120.json')
    p['roteiro']['cenas'][0]['acontecimento']['capacidade']='optical_projection'
    assert 'R-RECURSO-PREDEFINIDO' in {x['codigo'] for x in R.analisar(p)['bloqueios']}
    assert not F.avaliar(p)['pronto']


def test_midia_sem_bytes_nao_prova_acao_no_interior():
    p=load('QA_ROTEIRO_V2_TAIWAN_20261120.json')
    p['roteiro']['cenas'][0]['acontecimento']['acao']='fabricar wafers no interior'
    p['roteiro']['cenas'][0]['acontecimento']['mostrar']='interior fabricando wafers'
    r=R.analisar(p)
    assert r['decisoes'][0]['candidatos']  # mesmo local gera só candidato
    assert r['decisoes'][0]['estado']=='CANDIDATO_DOCUMENTAL_SEM_BYTES'
    assert r['pronto_para_render'] is False


def test_reprova_tentativa_de_publicar_e_fonte_ausente():
    p=load('QA_ROTEIRO_V2_EUV_20261120.json')
    p['publicar']=True
    assert 'R-SEM-GATE' in {x['codigo'] for x in R.analisar(p)['bloqueios']}
    p=load('QA_ROTEIRO_V2_EUV_20261120.json')
    del p['roteiro']['cenas'][0]['acontecimento']['fonte']
    assert 'R-FONTE-NAO-DECLARADA' in {x['codigo'] for x in R.analisar(p)['bloqueios']}


def test_biblioteca_falsa_ou_pouca_evidencia_nao_autoriza_midia():
    p=load('QA_ROTEIRO_V2_TAIWAN_20261120.json')
    artificial={'itens':[{'id':'falso','natureza':'foto','titulo':'TSMC Fab 18',
                         'mostra':'Fábrica exterior','credito':'x','licenca':'CC BY 4.0',
                         'sha256_origem':'a'*64,'prova':{'midia_corresponde':False}}],
                'reprovados':[]}
    r=R.analisar(p,artificial)
    assert r['decisoes'][0]['candidatos']==[]
    assert 'R-SEM-REGISTRO' in {x['codigo'] for x in r['bloqueios']}


def test_original_legado_sem_chave_roteiro_continua_igual():
    p=load('DEMO_DIRETOR_EVENTOS_20261120.json')
    assert R.expandir_preview(p) is p
    assert F.avaliar(p)['pronto']
