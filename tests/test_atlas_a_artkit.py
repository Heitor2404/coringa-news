"""Contrato de desenho A multiassunto (ainda não é homologação em app).
Garante ausência de colisões no plano autorado e ações no primeiro segundo.
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/'motor4/remotion/src/formatos/atlas-a-proof.json'
KIT=ROOT/'motor4/remotion/src/formatos/AtlasAArtKit.tsx'
SCENE=ROOT/'motor4/remotion/src/formatos/AtlasAProof.tsx'
STUDIO=ROOT/'motor4/remotion/src/formatos/AtlasAStudio.tsx'

def overlap(a,b):
    return max(0,min(a[0]+a[2],b[0]+b[2])-max(a[0],b[0])) * max(
        0,min(a[1]+a[3],b[1]+b[3])-max(a[1],b[1]))

def test_uma_linguagem_material_em_ambas_as_familias():
    k=KIT.read_text(encoding='utf8')
    a=SCENE.read_text(encoding='utf8')
    b=STUDIO.read_text(encoding='utf8')
    for primitive in ('ABeveledPanel','ARivet','AJoint'):
        assert f'export const {primitive}' in k
    for primitive in ('ABeveledPanel','ARivet','AJoint'):
        assert primitive in a
    assert 'ABeveledPanel' in b
    assert 'IndustrialBackdrop' in b
    assert 'src/formatos/AtlasAArtKit' not in a  # relativo ao renderizador, não src duro

def test_editorial_nao_encobre_rotulos_renderizados_por_contrato():
    d=json.loads(CONTRACT.read_text(encoding='utf8'))
    z=d['visual_layout']
    title, cue, source=z['title'],z['cue'],z['source']
    assert overlap(title,cue)==0
    assert overlap(cue,source)==0
    assert cue[1]+cue[3]<578  # antes da ótica/máquina principal
    for family,labels in z['labels'].items():
        assert family in d['subjects']
        for label in labels:
            assert overlap(cue,label)==0, (family,label)
            assert overlap(source,label)==0, (family,label)
    assert "cfg.visual_layout.cue[1]" in STUDIO.read_text(encoding='utf8')
    assert 'top:1090,left:146,width:604' not in STUDIO.read_text(encoding='utf8')

def test_gancho_agora_tem_evento_visual_correspondente():
    d=json.loads(CONTRACT.read_text(encoding='utf8'))
    a=SCENE.read_text(encoding='utf8')
    assert d['subjects']['lock']['events'][0]['action']=='hook'
    assert d['subjects']['euv']['events'][0]['action']=='hook'
    assert "const fill=clamp01((t-hook)/4.9);" in a
    assert "const source=progress(t,a('hook'),1.0);" in a
    assert 'A ÁGUA JÁ MOVE O NAVIO' in d['subjects']['lock']['events'][0]['label']
    assert 'A LUZ COMEÇA O PERCURSO' in d['subjects']['euv']['events'][0]['label']
    assert 'M270 725 L535 635' in a
    assert 'M535 635 L758 787' in a
    assert "M390 1035 L405 1312" in a  # suporte de wafer ligado
