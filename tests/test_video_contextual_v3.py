"""Regressões V3→V4: audiovisual REAL, direitos pendentes, ROI e sem prova falsa.

Roteiro V2 escolhe REFERENTE, catálogo separado escolhe vídeo; jamais
atribuir filmagem de laboratório a fabricante, evento ou mecanismo diferente.
"""
import copy
import json
from pathlib import Path

import pytest

from src.v4.formatos import ponte_biblioteca
from src.v4.formatos import video_contextual_v3 as VIDEO
from src.v4.formatos import diretor_hibrido as H

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/v4/formatos'


def plano():
    return json.loads((BASE/'QA_ROTEIRO_V2_HIBRIDO_NIST_20261120.json').read_text('utf8'))


def ficha():
    return json.loads((BASE/'VIDEO_CURADO_PRIVADO_NIST_20261120.json').read_text('utf8'))


def catalogo(v=None):
    return VIDEO.catalogo_com_video(ponte_biblioteca.catalogo(),
                                   v or ficha(),requer_arquivo=False)


def codigo(exc):
    return {x['codigo'] for x in exc.value.bloqueios}


def test_roteiro_tres_formatos_sem_nomear_asset_ou_renderer():
    p=plano()
    assert all('asset' not in s and 'mechanism' not in s
               for s in p['roteiro']['cenas'])
    z=H.planejar(p,catalogo())
    a,b,c=z['plano']['shots']
    assert [s['type'] for s in (a,b,c)]==['photo','video','mechanism']
    assert [a['start'],a['end'],b['start'],b['end'],c['start'],c['end']]==[
        0,3.0,3.0,5.6,5.6,12.5]
    assert b['evidence']=='representative'
    assert b['lead']=='VÍDEO REAL · REGISTRO CONTEXTUAL'
    assert b['headline']=='NIST NANOFAB'
    assert b['source_in_seconds']==58.15
    assert len(b['video_framing']['pontos'])==3
    assert b['video_framing']['pontos'][1]['fonte_s']==59.3
    assert c['mechanism']=='auto'
    assert z['plano']['media'][b['asset']]['license']=='REVIEW_PENDING'
    assert z['plano']['media'][b['asset']]['rights_status']=='REVIEW_PENDING'
    assert z['plano']['publicar'] is False
    assert z['plano']['duracao']==12.5


def test_fonte_so_pode_ser_incorporada_com_sha_real():
    v=ficha()
    assert VIDEO.validar_clip(v['videos'][0],requer_arquivo=False)['width']==1360
    v['videos'][0]['sha256_origem']='f'*64
    # Metadata diferente pode planejar, mas a etapa REAL deve revalidar
    # o mesmo original; não há aprovação de SHA sem ler os bytes reais.
    c=catalogo(v)
    assert c['itens'][-1]['sha256_origem']=='f'*64
    assert c['itens'][-1]['publicar'] is False


def test_video_nao_pode_dizer_que_demonstra_outro_evento():
    v=ficha()
    v['videos'][0]['comprova_outro_evento']=True
    with pytest.raises(ValueError,match='FATO'):
        catalogo(v)


def test_video_sem_licenca_confirmada_fica_privado_e_nao_publica():
    v=ficha()
    v['videos'][0]['licenca']='Public domain'
    with pytest.raises(ValueError,match='DIREITOS'):
        catalogo(v)
    p=plano()
    p['publicar']=True
    with pytest.raises(H.MontagemHibridaBloqueada) as e:
        H.planejar(p,catalogo())
    assert 'H-PUBLICACAO' in codigo(e)


def test_video_sem_roi_verificada_nao_entra_automaticamente():
    v=ficha()
    v['videos'][0]['janela']['roi']=[]
    with pytest.raises(ValueError,match='ROI'):
        catalogo(v)


def test_duas_pessoas_ou_pessoa_mais_maquina_nao_viram_apenas_um_rosto():
    from src.v4.formatos import filme_editorial as FILME
    p=H.planejar(plano(),catalogo())
    clip=p['plano']['shots'][1]
    metadata=p['plano']['media'][clip['asset']]
    escolha=FILME.resolver_relacao_video(clip,metadata,(1360,720))
    assert escolha['layout']=='cena_integral'
    assert escolha['framing_positions']==[]
    assert sorted(escolha['elementos_protegidos'])==[
        'estacao_com_monitor','pesquisador']


def test_rejeita_relacao_com_bbox_fora_do_original():
    v=ficha()
    v['videos'][0]['janela']['roi'][0]['elementos'][1]['bbox']=[-.1,.2,.38,.84]
    with pytest.raises(ValueError,match='ROI'):
        catalogo(v)


def test_relacao_proxima_e_recortavel_nao_precisa_gerar_letterbox():
    from src.v4.formatos import filme_editorial as FILME
    p=H.planejar(plano(),catalogo())
    clip=p['plano']['shots'][1]
    metadata=p['plano']['media'][clip['asset']]
    d=clip['video_framing']
    for frame in d['pontos']:
        frame['elementos']=[
            {'nome':'pessoa','bbox':[.46,.15,.56,.87]},
            {'nome':'estacao','bbox':[.36,.18,.46,.84]},
        ]
    escolha=FILME.resolver_relacao_video(clip,metadata,(1360,720))
    assert escolha['layout']=='recorte_relacional_seguro'
    assert len(escolha['framing_positions'])==3


def test_cena_com_mais_tempo_que_original_nao_deve_ser_estendida():
    p=plano()
    p['roteiro']['cenas'][1]['duracao_s']=3.7
    with pytest.raises(H.MontagemHibridaBloqueada) as e:
        H.planejar(p,catalogo())
    assert 'H-VIDEO-JANELA' in codigo(e)


def test_contexto_video_sem_catalogo_nao_cria_plano_vazio():
    with pytest.raises(H.MontagemHibridaBloqueada) as e:
        H.planejar(plano(),ponte_biblioteca.catalogo())
    assert 'R-SEM-REGISTRO' in codigo(e)


def test_arquivo_que_nao_foi_ingerido_nao_vira_confirmado(tmp_path,monkeypatch):
    p=tmp_path/'stage_documental'
    p.mkdir()
    original=p/'nist_nanofab_users_2017.mp4'
    original.write_bytes(b'midias falsas sem origem')
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError,match='SHA'):
        VIDEO.catalogo_com_video(ponte_biblioteca.catalogo(),ficha(),
                                 requer_arquivo=True)


def test_video_de_fonte_externa_invalida_bloqueado():
    v=ficha()
    v['videos'][0]['provedor']='externo_aleatorio'
    with pytest.raises(ValueError,match='ORIGEM'):
        catalogo(v)
