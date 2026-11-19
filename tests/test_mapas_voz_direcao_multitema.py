"""Mapas, narração natural e direção: mesmas regras para três assuntos distintos."""
import json
from pathlib import Path
import pytest

from src.v4.formatos import filme_editorial as F
from src.v4.formatos import contrato_visual_comum as C
from src.v4.formatos import direcao_eventos as D
from src.v4.formatos.tempo_natural import retemporizar

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'docs/v4/formatos/qa_mapas_eventos_tres_temas.json'


def plano():
    return json.loads(PATH.read_text(encoding='utf8'))


def codigo(p):
    return {x['codigo'] for x in F.avaliar(p)['bloqueios']}


def test_um_mesmo_compositor_para_taiwan_venezuela_e_suez():
    p=plano()
    assert F.avaliar(p)['pronto'],F.avaliar(p)['bloqueios']
    assert len(p['shots'])==3
    assert {x['map']['country_id'] for x in p['shots']}=={'158','862','818'}
    assert [x['direcao_evento']['intencao'] for x in p['shots']]==[
        'localizar','localizar','trajeto']
    c=C.auditar(p)
    assert c['estrutura_declarada_ok']
    assert c['total_compromissos']==3
    assert c['provas_resolvidas_no_plano']==3
    assert c['prova_visual']=='NAO_INSPECIONADA'
    assert c['aprovacao_humana']=='PENDENTE'


@pytest.mark.parametrize('idx', [0,1,2])
def test_mapa_sem_pin_verificado_e_bloqueado_qualquer_tema(idx):
    p=plano()
    p['shots'][idx]['map']['points']=[]
    assert 'F-MAPA-NAO-COMPROVADO' in codigo(p)


def test_roteiro_de_navio_sem_rota_nao_deve_ser_mapa_de_trajeto():
    p=plano()
    del p['shots'][2]['map']['route']
    assert 'F-MAPA-NAO-COMPROVADO' in codigo(p)


def test_traçado_geografico_invalido_nunca_e_inventado_pelo_renderer():
    p=plano()
    p['shots'][2]['map']['route']['coords']=[[32.45,95],[200,30]]
    assert 'F-MAPA-NAO-COMPROVADO' in codigo(p)


def test_mapa_e_esquema_nao_pode_ser_rotulado_como_filmagem_real():
    p=plano()
    p['shots'][0]['evidence']='literal'
    p['shots'][0]['literal_identity']='filmagem real de Taiwan'
    assert 'F-MAPA-EVIDENCIA' in codigo(p)


def test_diretor_nao_usa_foto_parada_para_demonstrar_acao():
    p=plano()
    p['shots'][0]['type']='photo'
    p['shots'][0]['direcao_evento']['intencao']='demonstrar_acao'
    assert 'D-RECURSO-INCOMPATIVEL' in codigo(p)


def test_diretor_exige_fato_novo_em_vez_de_repetir_promessa_do_plano_anterior():
    p=plano()
    p['shots'][1]['direcao_evento']['fato_id']='taiwan_localizacao'
    assert 'D-FATO-REPETIDO' in codigo(p)


def test_narracao_ajusta_duracao_de_imagem_sem_acelerar_voz():
    p=plano()
    out=retemporizar(p,[2.0,2.7,3.1])
    assert out['sincronia_voz']['tempo_audio']==1.
    assert out['duracao']!=p['duracao']
    assert all(s['voice_tempo']==1 for s in out['shots'])
    assert all(s['end']-s['start']<=3.8 for s in out['shots'])
    assert all(abs(s['start']-out['shots'][i-1]['end'])<.001
               for i,s in enumerate(out['shots']) if i)
    assert F.avaliar(out)['pronto'],F.avaliar(out)['bloqueios']
    assert p['shots'][0]['end']==3.0  # função não muta entrada


def test_voz_longa_deve_abrir_novo_plano_em_vez_de_atempo():
    p=plano()
    with pytest.raises(ValueError,match='NÃO aplicar atempo'):
        retemporizar(p,[2.,4.2,3.])


def test_nao_reescrever_o_tempo_de_uma_simulacao_causal():
    p=plano()
    p['shots'][1]['type']='mechanism'
    with pytest.raises(ValueError,match='causal'):
        retemporizar(p,[2.4,3.1,2.6])


def test_barra_global_unica_na_composicao_nao_no_plano():
    s=(ROOT/'motor4/remotion/src/formatos/FilmeEditorial.tsx').read_text(encoding='utf-8')
    assert s.count('data-testid="filme-progresso-global"')==1
    assert '100*clamp(t/Math.max(.01,duracao))' in s
    assert '100*p' not in s
