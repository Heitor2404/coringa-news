"""Testes de integração V2 registro contextual real + mecanismo autoral.

Somente QA privada; internet substituída por fonte mockada nos testes locais.
A origem deve vir do catálogo, o arquivo deve bater com o SHA da fonte.
"""
from __future__ import annotations

import copy
import hashlib
import io
import json
from pathlib import Path

import pytest
from PIL import Image

from src.v4.formatos import diretor_hibrido as H

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/v4/formatos'


def fixture():
    return json.loads((DOC/'QA_ROTEIRO_V2_TAIWAN_20261120.json').read_text('utf8'))


def two():
    p=fixture()
    p['roteiro']['cenas']=p['roteiro']['cenas'][:2]
    p['titulo']='Teste de cena híbrida privada sem asset selecionado'
    return p


def real_library():
    return json.loads((ROOT/'src/v4/biblioteca_comprovada.json').read_text('utf8'))


def generate_mock():
    buffer=io.BytesIO()
    Image.new('RGB',(960,700),(19,57,78)).save(buffer,format='JPEG',quality=90)
    return buffer.getvalue()


def catalogo_mock():
    img=generate_mock()
    lib=real_library()
    for it in lib['itens']:
        if it['id']=='commons:TSMC_Fab_18_May_2025.jpg':
            it['sha256_origem']=hashlib.sha256(img).hexdigest()
            break
    return lib,img


def codes(exc):
    return {x['codigo'] for x in exc.value.bloqueios}


def test_montagem_sem_escolher_foto_ou_animacao_reusa_catalogos():
    p=two()
    assert all('asset' not in s and 'mechanism' not in s and 'cues' not in s
               for s in p['roteiro']['cenas'])
    result=H.planejar(p,real_library())
    scene=result['plano']['shots']
    assert [x['type'] for x in scene]==['photo','mechanism']
    assert scene[0]['evidence']=='representative'
    assert scene[0]['direcao_evento']['intencao']=='explicar_contexto'
    assert scene[0]['headline']=='TSMC FAB 18'
    assert not scene[0]['headline'].lower().startswith('mostrar ')
    assert scene[0]['subject']=='Foto de arquivo · 2025'
    assert scene[0]['cues'][0]['label']=='FOTOGRAFIA · 2025'
    assert scene[1]['mechanism']=='auto'
    assert [x['action'] for x in scene[1]['cues']]==['source','reticle','projection','wafer']
    assert result['plano']['duracao']==9.9
    assert len(result['plano']['media'])==1
    asset=next(iter(result['plano']['media'].values()))
    assert asset['expected_sha256']==next(
        x['sha256_origem'] for x in real_library()['itens'] if 'TSMC_Fab_18' in x['id'])
    assert asset['url'].startswith('https://thumb.wikimedia.org/')
    assert result['proveniencia']['estado']=='PLANEJADO_SEM_BYTES'
    assert result['plano']['publicar'] is False
    assert p.get('shots') is None


def test_renderer_reprovado_bloqueia_hibrido_antes_de_download(tmp_path):
    lib,img=catalogo_mock()
    calls=[]
    with pytest.raises(ValueError,match='A-ROTA-BLOQUEADA'):
        H.preparar(two(),tmp_path/'run',tmp_path/'public',
                   downloader=lambda url:calls.append(url) or img,biblioteca=lib)
    assert not calls
    assert not (tmp_path/'run/proveniencia_hibrida.json').exists()


def test_bytes_autenticados_somente_apos_verificar_SHA(tmp_path):
    # The photo's SHA contract is independent of the rejected renderer.
    from src.v4.formatos import filme_editorial as F
    img=generate_mock()
    p=H.planejar(two(),catalogo_mock()[0])['plano']
    p['shots']=p['shots'][:1]
    p['duracao']=p['shots'][0]['end']
    result=F.preparar(p,tmp_path/'run',tmp_path/'public',downloader=lambda url:img,fragmento_misto=True)
    assert result['pronto']
    props=json.loads((tmp_path/'run/props.json').read_text('utf8'))
    assert props['private_review_only'] and [x['type'] for x in props['shots']]==['photo']
    assert len(list((tmp_path/'public/film_editorial').glob('*.jpg')))==1


def test_mismatch_bytes_bloqueia_sem_arquivo_aprovado(tmp_path):
    from src.v4.formatos import filme_editorial as F
    lib,img=catalogo_mock()
    p=H.planejar(two(),lib)['plano']
    p['shots']=p['shots'][:1];p['duracao']=p['shots'][0]['end']
    with pytest.raises(ValueError,match='hash da origem mudou'):
        F.preparar(p,tmp_path/'run',tmp_path/'public',downloader=lambda url:img+b'changed!',fragmento_misto=True)
    assert not (tmp_path/'run/props.json').exists()


def test_filme_integral_nao_inventa_registro_de_terremoto():
    with pytest.raises(H.MontagemHibridaBloqueada) as e:
        H.planejar(fixture(),real_library())
    assert 'R-SEM-REGISTRO' in codes(e)
    assert e.value.relatorio['total_cenas']==3


def test_outro_fenomeno_sem_renderer_nao_finge_transicao_ou_render():
    p=json.loads((DOC/'QA_ROTEIRO_V2_OXIDACAO_20261120.json').read_text('utf8'))
    with pytest.raises(H.MontagemHibridaBloqueada) as e:
        H.planejar(p,real_library())
    assert 'R-SEM-MECANISMO' in codes(e)


def test_nao_reutiliza_catalogo_de_fonte_sem_prova_licenca():
    p=two()
    lib=real_library()
    for it in lib['itens']:
        if 'TSMC_Fab_18' in it['id']:
            it['prova'].pop('licenca_confirmada_pela_API',None)
    with pytest.raises(H.MontagemHibridaBloqueada) as e:
        H.planejar(p,lib)
    assert 'H-MIDIA-SEM-PROVENIENCIA' in codes(e)


def test_nao_aceita_publicacao_ou_mecanismo_forcado():
    p=two()
    p['publicar']=True
    with pytest.raises(H.MontagemHibridaBloqueada) as e:
        H.planejar(p,real_library())
    assert 'H-PUBLICACAO' in codes(e)
    p=two()
    p['roteiro']['cenas'][1]['acontecimento']['capacidade']='optical_projection'
    with pytest.raises(H.MontagemHibridaBloqueada) as e:
        H.planejar(p,real_library())
    assert 'R-RECURSO-PREDEFINIDO' in codes(e)


def test_registro_historico_requer_curadoria_identidade_mesmo_com_candidato():
    p=two()
    p['roteiro']['cenas'][0]['acontecimento']['tipo']='evento_historico'
    with pytest.raises(H.MontagemHibridaBloqueada) as e:
        H.planejar(p,real_library())
    assert 'H-REGISTRO-ESPECIFICO' in codes(e)
