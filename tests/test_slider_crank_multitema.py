"""Regressões independentes de assunto para o rig slider-crank.

A física, os eventos, geometria e limites de enquadramento devem passar
com DOIS conjuntos de dados sem ajustes de TSX por vídeo. CI nao aprova arte.
"""
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'motor4/remotion/src/formatos/slider-crank-proofs.json'
RIG=ROOT/'motor4/remotion/src/formatos/SliderCrankRig.ts'
DRAW=ROOT/'motor4/remotion/src/formatos/SliderCrankProof.tsx'
COMP=ROOT/'motor4/remotion/src/Root.tsx'
PLATFORMS=ROOT/'src/v4/formatos/plataformas.json'


def get():
    return json.loads(DATA.read_text('utf8'))


def state(t,geom):
    r=geom['radius'];length=geom['rodLength']
    theta=2*math.pi*min(1,max(0,t/(8.4-.38)))
    dx=r*math.sin(theta)
    cx=geom['centerX'];cy=geom['centerY']
    py=cy-r*math.cos(theta)-math.sqrt(length*length-dx*dx)
    return (cx,py),(cx+dx,cy-r*math.cos(theta)),theta


def test_duas_maquinas_mesmo_rig_uma_unica_composicao():
    d=get()
    assert d['status']=='PRIVATE_MOTION_PROOF_NOT_PUBLIC'
    assert d['duration']==8.4 and d['resolution']==[1080,1920]
    assert d['qa']['publish'] is False and d['qa']['telegram'] is False
    assert d['qa']['narration'] is False
    assert d['qa']['visualApproval']=='PENDING'
    assert set(d['models'])=={'motor','compressor'}
    assert d['models']['motor']['driver']=='pressure'
    assert d['models']['compressor']['driver']=='shaft'
    assert d['models']['motor']['ports'] is False
    assert d['models']['compressor']['ports'] is True
    assert d['models']['motor']['geometry']!=d['models']['compressor']['geometry']
    txt=DRAW.read_text('utf8')
    assert '(specs.models as unknown as Record<string,Model>)[kind]' in txt
    assert 'rigState(theta,g)' in txt
    assert 'const stage=Math.max' in txt
    assert "if(kind==='motor')" not in txt
    assert "if(kind==='compressor')" not in txt
    root=COMP.read_text('utf8')
    assert 'id="ProvaA-Pistao"' in root
    assert 'id="ProvaA-Compressor"' in root
    assert 'SliderCrankProof' in root
    assert 'FilmeEditorial' in root
    # Não promover a produção sem inspeção visual.
    catalog=(ROOT/'src/v4/formatos/catalogo_mecanismos.py').read_text('utf8')
    assert "'slider_crank': Capacidade" not in catalog


def test_biela_e_pinos_sempre_conectados_e_pistao_sem_movimento_lateral():
    for model in get()['models'].values():
        g=model['geometry']
        r=g['radius'];L=g['rodLength']
        assert 2*r<L*1.15  # curso cabe em proporção de máquina plausível
        assert r>0 and L>r
        for i in range(254):
            p,c,theta=state(i/30,g)
            assert abs(math.dist(p,c)-L)<1e-8
            assert p[0]==g['centerX']
            assert abs(math.dist(c,(g['centerX'],g['centerY']))-r)<1e-8
            y0=g['centerY']-r-L
            assert y0-1e-8<=p[1]<=y0+2*r+1e-8
            # Faixa vertical observável do pistão e volante, sem cortar ação.
            top=p[1]-g['pistonHeight']*.69
            assert 603<=top<=800
            assert g['centerY']+140<1170
        p0,c0,_=state(0,g)
        p180,c180,_=state((8.4-.38)/2,g)
        assert math.isclose(p180[1]-p0[1],2*r,abs_tol=1e-6)


def test_ciclo_progressivo_por_acontecimento_nao_por_titulo():
    for model in get()['models'].values():
        beats=model['steps']
        assert len(beats)==4 and beats[0]['at']==0
        assert [x['at'] for x in beats]==sorted(set(x['at'] for x in beats))
        assert beats[-1]['at']<8.4
        assert all(x['detail'].strip() and len(x['detail'])<65 for x in beats)
        assert all(x['focus'] in ('piston','rod','crank','intake','outlet')
                   for x in beats)
        assert model['title'][0].strip() and model['title'][1].strip()


def test_zonas_criticas_na_intersecao_das_plataformas():
    platforms=json.loads(PLATFORMS.read_text('utf8'))
    for name in platforms['ativos_seguros']:
        z=platforms['perfis'][name]
        assert z['topo']<=295
        assert z['base']<=672
        assert z['direita']['de_y']>=840
        assert 1080-z['direita']['largura']>=780
        assert 1920-z['base']>=1248
    s=DRAW.read_text('utf8')
    # Brand + textos essenciais ficam antes da coluna lateral e da UI inferior.
    assert 'x="135" y="295"' in s
    assert 'x="129" y="1174"' in s
    assert 'x={153} y={1238}' in s
    assert 'x={654} y={ptop+57}' in s
    assert 'x={716} y={573}' in s
    assert '<SVGText x={540} y={1847}' in s  # apenas marca 'preview'


def test_visual_nao_e_contagem_de_pixel_ou_copia_de_imagem():
    rig=RIG.read_text('utf8')
    scene=DRAW.read_text('utf8')
    assert 'Math.sqrt(g.rodLength*g.rodLength-dx*dx)' in rig
    assert 'Math.sin(theta)' in rig and 'Math.cos(theta)' in rig
    assert 'private_review_only' in scene
    assert 'NÃO PUBLICAR' in scene or 'NÃO PUBLICAR' in get()['status']
    assert '<Cutaway t={t}' in scene
    assert 'strokeDashoffset={-t*55}' in scene
    assert '.png' not in scene and '<image' not in scene
