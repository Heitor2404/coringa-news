"""O diretor usa vídeo de ação real só quando fato e etapas correspondem.

A inspeção assistida permite PRÉVIA, nunca aprovação editorial ou comercial.
"""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from src.v4.formatos import video_acao_real as A
from src.v4.formatos import diretor_hibrido as H
from src.v4.formatos import filme_editorial as F
from src.v4.formatos import ponte_biblioteca as PB

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'docs/v4/formatos'


def manifesto():
    return json.loads((D/'VIDEO_ACAO_OBSERVADA_NASA_20261120.json').read_text())


def plano():
    return json.loads((D/'QA_ROTEIRO_V2_ACAO_CURIOSITY_20261120.json').read_text())


def catalogo(x=None):
    return A.catalogo_com_acoes(PB.catalogo(),x or manifesto(),bytes_obrigatorios=False)


def codigos(v):
    return {x['codigo'] for x in v['bloqueios']}


def test_filmagem_substitui_mecanismo_quando_acao_real_e_o_mesmo_fato():
    p=plano()
    assert 'shots' not in p
    assert not any('asset' in c or 'mechanism' in c
                   for c in p['roteiro']['cenas'])
    out=H.planejar(p,catalogo())
    f=out['plano']
    assert f['duracao']==4.8
    assert len(f['shots'])==1
    c=f['shots'][0]
    assert c['type']=='video'
    assert c['evidence']=='literal'
    assert c['source_in_seconds']==4.5
    assert c['video_framing']['modo']=='fonte_integral'
    assert c['progressao_visual']['tipo']=='acao_observada'
    assert len(c['progressao_visual']['eventos'])==3
    assert len(f['media'])==1
    assert F.avaliar(f)['pronto'],F.avaliar(f)['bloqueios']
    assert f['publicar'] is False
    assert out['proveniencia']['aprovacao_editorial'] is False


def test_nao_aceita_video_real_de_outro_evento_mesmo_que_tema_seja_igual():
    p=plano()
    p['roteiro']['cenas'][0]['acontecimento']['id']='outro_rover_ou_acontecimento'
    with pytest.raises(H.MontagemHibridaBloqueada) as v:
        H.planejar(p,catalogo())
    assert 'R-SEM-MECANISMO' in {x['codigo'] for x in v.value.bloqueios}


def test_nao_aceita_video_que_nao_cobre_uma_das_acoes():
    p=plano()
    p['roteiro']['cenas'][0]['acontecimento']['dados']['acoes_necessarias']=[
        'ferramenta_sobre_rocha','braco_retrai','pedra_solta_visivelmente'
    ]
    with pytest.raises(H.MontagemHibridaBloqueada) as e:
        H.planejar(p,catalogo())
    assert 'R-SEM-MECANISMO' in {x['codigo'] for x in e.value.bloqueios}


def test_video_sem_original_rejeitado_na_etapa_de_bytes(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(A.ProvaInvalida,match='VA-ARQUIVO'):
        A.catalogo_com_acoes(PB.catalogo(),manifesto(),bytes_obrigatorios=True)


def test_tempos_da_fonte_precisam_ser_exatos():
    m=manifesto()
    m['videos'][0]['janela']['eventos'][1]['fonte_s']=52
    with pytest.raises(A.ProvaInvalida,match='VA-TEMPO'):
        catalogo(m)


def test_exige_identidade_do_original_e_modo_sequencia_condensada():
    m=manifesto()
    m['videos'][0]['temporalidade']='TEMPO_REAL_CONTINUO'
    with pytest.raises(A.ProvaInvalida,match='VA-TEMPO'):
        catalogo(m)
    m=manifesto()
    m['videos'][0]['pagina']='https://www.tsmc.com/recording'
    with pytest.raises(A.ProvaInvalida,match='VA-ORIGEM'):
        catalogo(m)


def test_prova_de_licenca_nao_pode_ser_fabricada():
    m=manifesto()
    m['videos'][0]['licenca']='CC0'
    with pytest.raises(A.ProvaInvalida,match='VA-PORTAO'):
        catalogo(m)
    m=manifesto()
    m['videos'][0]['direitos_revisados']=True
    with pytest.raises(A.ProvaInvalida,match='VA-PORTAO'):
        catalogo(m)


def test_anotacao_assistida_nao_e_homologacao_humana():
    m=manifesto()
    m['videos'][0]['inspecao_status']='HOMOLOGADO_HUMANAMENTE'
    with pytest.raises(A.ProvaInvalida,match='VA-INSPECAO'):
        catalogo(m)


def test_roteiro_com_duracao_diferente_nao_acelera_video():
    p=plano()
    p['roteiro']['cenas'][0]['duracao_s']=2.8
    with pytest.raises(A.ProvaInvalida,match='VA-NARRACAO'):
        H.planejar(p,catalogo())


def test_controle_de_fontes_nist_contextual_nao_vira_prova_fisica():
    p=plano()
    with pytest.raises(H.MontagemHibridaBloqueada) as e:
        H.planejar(p,PB.catalogo())
    assert 'R-SEM-MECANISMO' in {x['codigo'] for x in e.value.bloqueios}


def test_recorte_temporal_inteiro_deve_exibir_original_sem_crop():
    p=H.planejar(plano(),catalogo())['plano']
    c=p['shots'][0]
    meta=p['media'][c['asset']]
    assert F.proteger_fonte_integral(c,meta,(1024,1024))=='quadro_integral'
    bad=copy.deepcopy(c)
    bad['video_zoom']=1.8
    with pytest.raises(ValueError,match='F-ROI-ZOOM'):
        F.proteger_fonte_integral(bad,meta,(1024,1024))


def test_fonte_de_acao_sem_anotacoes_unicas_bloqueia():
    m=manifesto()
    m['videos'][0]['janela']['eventos'][1]['acao_id']='braco_afastado'
    with pytest.raises(A.ProvaInvalida,match='VA-ACAOINCORRETA'):
        catalogo(m)
