"""Regressao: o fundo/arte pode ultrapassar safe zone textual; foco nao.
Nova familia visual 3D continua PRIVADA, usa a mesma fisica para 2 temas.
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
POL=ROOT/'motor4/remotion/src/formatos/editorial-safe-roles-v2.json'
SRC=ROOT/'motor4/remotion/src/formatos/CinematicCutaway3D.tsx'
RIG=ROOT/'motor4/remotion/src/formatos/SliderCrankRig.ts'
ROOT_TS=ROOT/'motor4/remotion/src/Root.tsx'
DATA=ROOT/'motor4/remotion/src/formatos/slider-crank-proofs.json'


def test_nao_restringe_o_ator_ao_retangulo_de_texto():
    d=json.loads(POL.read_text('utf8'))
    roles=d['roles']
    assert roles['visual_full_bleed']['rect']==[0,0,1080,1920]
    assert roles['visual_full_bleed']['may_appear_under_ui'] is True
    assert roles['essential_text']['may_appear_under_ui'] is False
    text=roles['essential_text']['rect']
    assert 270<text[1]<300 and text[3]<=1248
    assert text[2]-text[0]>600
    assert roles['visual_primary_action']['preferred_center_x'][1]<=780
    assert roles['visual_primary_action']['preferred_center_y'][1]<1248

def test_direcao_nova_e_3d_nao_recolor_2d():
    s=SRC.read_text('utf8')
    assert "ThreeCanvas" in s and "Rod a={pi} b={cr}" in s
    assert "angleAt(t,duration-.38)" in s
    assert "rigState(theta,cfg)" in s
    assert "boxGeometry" in s and "cylinderGeometry" in s
    assert "model.driver==='pressure'" in s
    assert "model.ports&&" in s
    assert "if(kind==='motor')" not in s
    assert "if(kind==='compressor')" not in s
    assert "SliderCrankProof" not in s
    root=ROOT_TS.read_text('utf8')
    assert 'id="Prova3D-Pistao"' in root and 'id="Prova3D-Compressor"' in root
    assert "FilmeEditorial" in root
    catalog=(ROOT/'src/v4/formatos/catalogo_mecanismos.py').read_text('utf8')
    assert "'cinematic_cutaway_3d': Capacidade(" not in catalog

def test_nenhuma_correcao_de_geometria_por_episodio():
    src=SRC.read_text('utf8')
    data=json.loads(DATA.read_text('utf8'))
    assert data['models']['motor']['geometry']!=data['models']['compressor']['geometry']
    assert 'const model=(configs.models as unknown as Record<string,Model>)[kind]' in src
    assert "const pi=new Vector3" in src and "const cr=new Vector3" in src
    assert 'Rod a={pi} b={cr}' in src
    assert data['qa']['visualApproval']=="PENDING"
