"""Ensaios do laboratório de direção A — NÃO aprovam publicação.

Cenas 2.5D originais e modos independentes eclusa/EUV; testam física,
fonte, interface e isolamento sem confundir CI com qualidade estética.
"""
import json
import math
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/'motor4/remotion/src/formatos/atlas-a-proof.json'
SCENE=ROOT/'motor4/remotion/src/formatos/AtlasAProof.tsx'
SHELL=ROOT/'motor4/remotion/src/formatos/AtlasAStudio.tsx'
R=ROOT/'motor4/remotion/src/Root.tsx'
PROFILES=ROOT/'src/v4/formatos/plataformas.json'


def data():
    return json.loads(CONTRACT.read_text('utf8'))


def smooth(x):
    v=max(0,min(1,x))
    return v*v*(3-2*v)


def test_compartilha_direcao_mas_nao_simula_universalidade():
    c=data()
    assert c['status']=='LAB_PRIVADO_NAO_PUBLICAR'
    assert c['duration']==7.8
    assert c['resolution']==[1080,1920]
    assert c['qa']['publish'] is False
    assert c['qa']['telegram'] is False
    assert c['qa']['narration'] is False
    assert c['qa']['deviceUI']=='NOT_VERIFIED'
    assert set(c['subjects'])=={'lock','euv'}
    assert len(c['subjects']['lock']['events'])==5
    assert len(c['subjects']['euv']['events'])==5
    for subject in c['subjects'].values():
        cues=subject['events']
        assert cues[0]['at']==0
        assert [q['at'] for q in cues]==sorted(set(q['at'] for q in cues))
        assert all(len(q['label'])<=45 for q in cues)
        assert subject['source'].startswith('ESQUEMA ILUSTRATIVO')
    root=R.read_text('utf8')
    assert 'id="ProvaA-Eclusa"' in root
    assert 'id="ProvaA-EUV"' in root
    assert "private_review_only:true" in root
    assert "AtlasAProof" in root
    assert "FilmeEditorial" in root
    # Nenhuma destas famílias foi promovida a capacidade de produção.
    catalog=(ROOT/'src/v4/formatos/catalogo_mecanismos.py').read_text('utf8')
    assert "'atlas_a_proof': Capacidade(" not in catalog


def test_agua_e_navio_nunca_se_separam_ao_subir():
    c=data()['subjects']['lock']
    events={x['action']:x['at'] for x in c['events']}
    assert events['inlet']<events['rise']<events['release']
    initial=959
    at_end=initial-141
    last=initial
    for frame in range(236):
        t=frame/30
        fill=max(0,min(1,(t-events['hook'])/4.9))
        waterY=initial-141*fill
        boatShift=waterY-initial
        hull_marker=950+boatShift
        assert math.isclose(waterY-hull_marker,9,abs_tol=1e-10)
        assert waterY<=last+1e-8
        last=waterY
        if t==0:
            assert fill==0
        if t>=.5:
            assert fill>0
    assert math.isclose(last,at_end,abs_tol=1e-10)
    s=SCENE.read_text('utf8')
    assert 'const fill=clamp01((t-hook)/4.9);' in s
    assert 'const boatShift=waterY-959;' in s
    assert 'const flow=t>=hook&&t<release;' in s
    assert 'M166 878 V1440 H355 V993' in s
    assert 'strokeDashoffset={-t*106}' in s
    assert "gateShift:open*57" in s
    assert 'const s=lockState(t,events)' in s
    # A ação principal fica visível mesmo com margem TOLERÁVEL de ícones.
    # O casco usa 1.28x na largura; só a ponta periférica pode entrar
    # na coluna de botões, e a causa física não pode estar ali.
    assert "scale(1.28 1.05)" in s
    assert "(-40+s.boatTravel)" in s
    xleft=560+(344-560)*1.28-40
    xright=560+(791-560)*1.28-40+20
    assert (xright-780)/(xright-xleft)<.12


def test_euv_reflexivo_conectado_nao_transmissivo_nem_chip_pronto():
    c=data()['subjects']['euv']
    ev={x['action']:x['at'] for x in c['events']}
    assert ev['source']<ev['reticle']<ev['mirrors']<ev['wafer']
    scene=SCENE.read_text('utf8')
    assert 'mask' not in [x['action'] for x in c['events']]
    assert 'M270 725 L535 635' in scene     # luz atinge a face
    assert 'M535 635 L758 787' in scene     # REFLEXÃO (mesmo vértice)
    assert 'M745 819 L587 877' in scene     # espelho a espelho
    assert 'M561 896 L524 951' in scene     # segue ao wafer
    assert 'MÁSCARA REFLEXIVA' in scene or 'máscara é explicada pelo cue' in scene
    assert 'RESINA FOTOSSENSÍVEL' in scene
    assert '>CHIP PRONTO<' not in scene.upper()  # Testar rótulo exibido, não comentário técnico.
    assert 'lente transmissiva' not in scene.lower()
    assert 'Photon d=' in scene
    # Referência documental evita fonte hidráulica no EUV.
    assert 'EUV / ASML' in c['source']
    assert 'PRINCÍPIO HIDRÁULICO' not in c['source']


def test_bbox_sem_miniaturizar_mecanismo_na_intersecao_universal():
    c=data()
    profiles=json.loads(PROFILES.read_text('utf8'))
    h=c['roles']['main_stage']
    assert (h[2]-h[0])>=800
    assert (h[3]-h[1])>=500
    assert c['roles']['side_ui_from_y']==840
    assert h[0]<=100 and h[2]>=900
    assert profiles['ativos_seguros']
    # Texto crítico, não o desenho completo, na intersecção rígida.
    for name in profiles['ativos_seguros']:
        p=profiles['perfis'][name]
        assert 295>=p['topo']
        assert 145>=p['esquerda']
        assert 1240<=1920-p['base']
        # Fonte e caption x < limite de ícones laterais abaixo de y840.
        right=1080-p['direita']['largura']
        assert 146+604<=right
        assert 148+600<=right
    shell=SHELL.read_text('utf8')
    assert 'top:cfg.visual_layout.cue[1]' in shell
    assert 'cfg.visual_layout.cue[0]' in shell
    assert 'top:1210,left:148,width:600' in shell
    assert 'fontSize:53' in shell
    assert 'overflow:' in shell


def test_arte_2_5d_original_sem_assets_terceiros():
    a=SCENE.read_text('utf8')
    b=SHELL.read_text('utf8')
    assert 'a-lock-sky' in b and 'a-euv-backdrop' in b
    assert 'IndustrialBackdrop' in b and 'ABeveledPanel' in b
    assert 'tone="steel"' in b and 'tone="cobalt"' in b
    assert 'Q220 1181' in a  # corte inferior com estratigrafia
    assert 'ABeveledPanel' in a and 'AJoint' in a
    assert 'ABeveledPanel' in b and 'ARivet' in b
    assert 'scale(1.28 1.05)' in a  # cargueiro agora ocupa mais largura
    assert 'a-ship' in a and 'a-euv-steel' in a
    assert 'Array.from({length:3}' in a   # containers montados em camadas
    assert 'clipPath="url(#a-chamber)"' in a
    assert 'clipPath="url(#a-euv-wafer-clip)"' in a
    assert 'PRÉVIA PRIVADA · NÃO PUBLICAR' in b
    for code in (a,b):
        assert 'staticFile(' not in code
        assert '<Img' not in code and '<Image' not in code
        assert 'Kurzgesagt' not in code and 'Vox' not in code
        assert 'https://' not in code
    # Mecanismo persistente dentro de um mesmo quadro visual.
    assert "kind==='lock'" in a
    assert 'AtlasAStudio' in a
