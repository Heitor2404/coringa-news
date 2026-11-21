"""Regressão física da prova 2D: geometria, continuidade e segurança.

O teste não homologa estilo nem aprova publicação. Os vídeos gerados no
CI precisam de revisão humana em várias fases e em celular real.
"""
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CFG=ROOT/'motor4/remotion/src/formatos/lever2d-contract.json'
SCENE=ROOT/'motor4/remotion/src/formatos/LeverMechanism2D.tsx'
CORE=ROOT/'motor4/remotion/src/formatos/Mechanism2DCore.ts'
ROOT_TSX=ROOT/'motor4/remotion/src/Root.tsx'


def contract():
    return json.loads(CFG.read_text(encoding='utf8'))


def _rotate(pivot,pt,ang):
    rad=math.radians(ang)
    dx,dy=pt[0]-pivot[0],pt[1]-pivot[1]
    return (pivot[0]+dx*math.cos(rad)-dy*math.sin(rad),
            pivot[1]+dx*math.sin(rad)+dy*math.cos(rad))


def _ease(v):
    v=max(0,min(1,v))
    return v*v*(3-2*v)


def test_prova_tem_cinco_fases_fisicas_sem_montagem_por_assunto():
    d=contract()
    cues=d['cues']
    assert d['status']=='PRIVATE_VISUAL_PROBE_NOT_PRODUCTION'
    assert d['qa']['publication']=='BLOCKED'
    assert 8.5<=d['duration']<=9.5
    assert [e['action'] for e in cues]==[
        'introduce','load','effort','actuate','explain']
    assert [e['at'] for e in cues]==sorted(set(e['at'] for e in cues))
    assert all(len(x['label'])<55 and x['label'].strip() for x in cues)
    root=ROOT_TSX.read_text(encoding='utf8')
    assert 'id="ProvaMecanismo2D"' in root
    assert 'private_review_only:true' in root
    catalog=(ROOT/'src/v4/formatos/catalogo_mecanismos.py').read_text()
    assert "'lever_2d': Capacidade(" not in catalog  # Ainda não homologado.


def test_mesma_rotacao_governa_carga_esforco_e_extremidades():
    d=contract()['geometry']
    pivot=d['pivot']
    lx=d['loadX']
    ex=d['effortX']
    assert d['beamStartX']<=lx<pivot[0]<ex<=d['beamEndX']
    assert (ex-pivot[0])/(pivot[0]-lx)>1.5
    p0=_rotate(pivot,(lx,pivot[1]),0)
    q0=_rotate(pivot,(ex,pivot[1]),0)
    prev_load=p0[1]
    prev_effort=q0[1]
    for i in range(1,181):
        ang=d['maxTiltDeg']*_ease(i/180)
        l=_rotate(pivot,(lx,pivot[1]),ang)
        e=_rotate(pivot,(ex,pivot[1]),ang)
        # 1a classe: aplicar força longa para baixo eleva o braço curto.
        assert l[1]<=prev_load+1e-7
        assert e[1]>=prev_effort-1e-7
        prev_load,prev_effort=l[1],e[1]
        # Pivô indeformável: distâncias radiais iguais em todos os frames.
        assert math.isclose(math.dist(l,pivot),pivot[0]-lx,rel_tol=1e-12)
        assert math.isclose(math.dist(e,pivot),ex-pivot[0],rel_tol=1e-12)
    assert prev_load<p0[1]-30
    assert prev_effort>q0[1]+75
    s=SCENE.read_text(encoding='utf8')
    core=CORE.read_text(encoding='utf8')
    assert "rotateAbout(pivot,{x:cfg.loadX,y:pivot.y},tilt)" in s
    assert "rotateAbout(pivot,{x:cfg.effortX,y:pivot.y},tilt)" in s
    assert "tilt=cfg.maxTiltDeg*move" in s
    assert "return {\n    x:pivot.x+dx*Math.cos(angle)-dy*Math.sin(angle)" in core


def test_nao_esconde_pecas_essenciais_na_ui_antes_dos_icones():
    c=contract()
    g=c['geometry']
    assert c['qa']['rightIconsStartY']==840
    assert c['qa']['criticalSafe']==[150,300,770,1240]
    max_angle=g['maxTiltDeg']
    pivot=g['pivot']
    for i in range(61):
        ang=max_angle*i/60
        lx,ly=_rotate(pivot,(g['loadX'],pivot[1]),ang)
        ex,ey=_rotate(pivot,(g['effortX'],pivot[1]),ang)
        # A caixinha se mantém visível, inclusive no fim da elevação.
        assert lx-g['loadWidth']/2>=120
        assert ly-g['beamThickness']/2-g['loadHeight']>=510
        assert ex<=960
        assert ey+g['beamThickness']/2+c['qa']['minimumClearanceBeforeIcons']<=840
    scene=SCENE.read_text(encoding='utf8')
    assert 'left:156,top:1095,width:600' in scene
    assert 'left:156,top:1220,width:603' in scene
    assert 'left:156,top:378,width:670' in scene
    assert 'PROVA VISUAL PRIVADA · NÃO PUBLICAR' in scene
    assert 'data-safe-role="mechanism-actors"' in scene
    assert 'M190 885' not in scene  # Medição não cruza mais o suporte.
    assert '<Label x={878} y={539}' in scene  # A força acompanha a ponta longa.
    assert 'y={1008}' in scene and '>APOIO</Label>' in scene
    assert "const loadTopIn=crateY-(1-loaded)*35" in scene
    assert "stageTransform=" not in scene  # Stage declarativo, sem transform hardcoded no JSX.
    assert 'transform={stageTransform}' in scene
    assert 'strokeDasharray="12 16"' in scene  # Posição inicial da barra permanece rastreável.
    assert "stroke={p.teal} strokeWidth=\"8\"" in scene
    assert "stroke={p.effort} strokeWidth=\"8\"" in scene





def test_ampliacao_de_atores_sem_amputacao_em_todas_as_fases():
    g=contract()['geometry']
    stage=contract()['qa']['actorStage']
    assert stage['scaleX']>1 and stage['scaleY']>1
    assert g['loadWidth']>=140 and g['loadHeight']>=120
    assert g['beamEndX']-g['beamStartX']>=790
    cx,cy=stage['origin']
    transform_x=lambda x:cx+(x-cx)*stage['scaleX']
    transform_y=lambda y:cy+(y-cy)*stage['scaleY']
    # Toda a progressão, incluindo peso no alto e ponta longa embaixo.
    for i in range(121):
        angle=g['maxTiltDeg']*i/120
        x,y=_rotate(g['pivot'],(g['loadX'],g['pivot'][1]),angle)
        rx,ry=_rotate(g['pivot'],(g['effortX'],g['pivot'][1]),angle)
        left=transform_x(x-g['loadWidth']/2)
        top=transform_y(y-g['beamThickness']/2-g['loadHeight'])
        bottom=transform_y(ry+g['beamThickness']/2+contract()['qa']['minimumClearanceBeforeIcons'])
        assert left>=120,(i,left)
        assert top>=490,(i,top)
        assert transform_x(rx)<=960,(i,transform_x(rx))
        assert bottom<840,(i,bottom)
    # A área ocupada por atores essenciais cresceu em vez de encolher.
    w=(g['beamEndX']-g['beamStartX'])*stage['scaleX']
    assert w>830


def test_estetica_da_prova_e_limpa_e_original_sem_importar_assets_da_referencia():
    s=SCENE.read_text(encoding='utf8')
    assert "variant='paper'" in s
    assert "graphite:" in s
    assert 'MECÂNICA · 2D' in s
    assert 'LeverMechanism2D' in s
    assert 'pattern id=' not in s
    assert 'feTurbulence' not in s
    assert 'Image' not in s
    assert '<Img' not in s
    assert 'The Efficient Engineer' not in s
    assert '3Blue1Brown' not in s
    assert "s.active.label" in s
    # Os rótulos mudam, mas os atores permanecem no mesmo componente.
    assert 'const crateY=loadPoint.y-cfg.beamThickness/2-cfg.loadHeight' in s
    assert 'const rightY=effortPoint.y' in s
