"""Provas contratuais para mecanismos físicos, independentes do tema da pauta.

Não confundem compilação com aprovação estética: o MP4 precisa de inspeção.
"""
import copy
import json
from pathlib import Path

import pytest

from src.v4.formatos import filme_editorial as FILME

ROOT=Path(__file__).resolve().parents[1]
RECEITA=ROOT/'docs/v4/formatos/DEMO_MECANISMOS_FISICOS_20261119.json'


def plano():
    return json.loads(RECEITA.read_text(encoding='utf8'))


def test_dois_mecanismos_diferentes_usam_mesmo_filme_editorial():
    p=plano()
    result=FILME.avaliar(p)
    assert result['pronto'],result['bloqueios']
    assert result['momentos_visuais']>=9
    assert result['visual_approval']=='NAO_FOI_AVALIADO'
    assert [s['mechanism'] for s in p['shots']]==['optical_projection','lock_explainer']
    assert p['publicar'] is False


def test_mecanismos_geram_props_sem_fotos_falsas(tmp_path):
    p=plano()
    out=FILME.preparar(p,tmp_path/'saida',tmp_path/'public')
    assert out['pronto'] and out['shots']==2 and out['midias']==0
    props=json.loads((tmp_path/'saida/props.json').read_text(encoding='utf8'))
    assert props['preview'] is True
    assert props['private_review_only'] is False
    assert all(s['type']=='mechanism' and s['evidence']=='explainer' for s in props['shots'])
    assert all('asset' not in s and 'literal_identity' not in s for s in props['shots'])
    assert 'asml.com' in props['shots'][0]['source']
    assert 'pancanal.com' in props['shots'][1]['source']


@pytest.mark.parametrize('indice', [0,1])
def test_mechanism_rejeita_acao_fora_de_ordem(indice):
    p=plano()
    p['shots'][indice]['cues'][1]['action']='wafer'
    result=FILME.avaliar(p)
    assert any(x['codigo']=='F-MECANISMO-PROCESSO' for x in result['bloqueios'])


def test_recusa_animação_sem_tempo_de_explicacao():
    p=plano()
    p['shots'][0]['cues'][-1]['at']=6.7
    result=FILME.avaliar(p)
    assert any(x['codigo']=='F-MECANISMO-PROCESSO' for x in result['bloqueios'])


def test_recusa_falsa_filmagem_e_ponte_nao_autenticada():
    p=plano()
    p['shots'][0]['evidence']='literal'
    p['shots'][0]['asset']='foto_inventada'
    p['shots'][0]['reference_asset']='video_qualquer'
    codes={x['codigo'] for x in FILME.avaliar(p)['bloqueios']}
    assert 'F-MECANISMO-NÃO-IDENTIFICADO' in codes
    assert 'F-MECANISMO-SEM-ACERVO' in codes
    assert 'F-PONTE-SEM-PROVA' in codes


def test_em_modo_privado_nao_autoriza_publicacao():
    p=plano()
    p['tipo']='FILME_FINAL'
    res=FILME.avaliar(p)
    assert not res['pronto']
    assert any(x['codigo'].startswith('F-PORTAO-') or x['codigo']=='F-VOZ-TESTE-EM-PRODUCAO'
               for x in res['bloqueios'])


def test_nenhum_slide_pillow_novo_para_animacao_fisica():
    # A demonstração é um recurso de FILME, não card gerado de foto estática.
    p=plano()
    assert not p['media']
    assert all('motion_graphic' not in s for s in p['shots'])
    optical=(ROOT/'motor4/remotion/src/formatos/OpticalProjection.tsx').read_text()
    assert '<Beam' in optical and 'REFLEXIVA' in optical
    assert 'CAMADA FOTOSSENSÍVEL' in optical
    # Variante nova reutiliza o mesmo motor de estados; o visual legado segue preservado.
    hydraulic=(ROOT/'motor4/remotion/src/formatos/LockCausal.tsx').read_text()
    assert "visualMode==='editorial'" in hydraulic
    assert 'EditorialCutaway' in hydraulic and 'lock-edit-chamber' in hydraulic
