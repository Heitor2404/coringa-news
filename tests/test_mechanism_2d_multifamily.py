"""Contrato multiassunto de duas provas vetoriais 2D independentes.

Não simula acurácia de render em aplicativos reais e não habilita publicação.
"""
import json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CFG=ROOT/'motor4/remotion/src/formatos/mechanisms2d-probes.json'
SRC=ROOT/'motor4/remotion/src/formatos/Mechanism2DOtherModels.tsx'
SHELL=ROOT/'motor4/remotion/src/formatos/Mechanism2DPaperStudio.tsx'
CORE=ROOT/'motor4/remotion/src/formatos/Mechanism2DCore.ts'
ROOT_TSX=ROOT/'motor4/remotion/src/Root.tsx'


def plan():
    return json.loads(CFG.read_text('utf8'))


def test_paper_is_a_reusable_visual_contract_not_two_separate_templates():
    p=plan()
    assert p['palette']=='paper'
    assert p['status']=='PRIVATE_QA_NOT_PRODUCTION'
    assert p['qa']['publicar'] is False
    assert p['qa']['telegram'] is False
    assert set(p['demo'])=={'pulley','gears'}
    assert all(7<=v['duration']<=10 for v in p['demo'].values())
    assert all([c['at'] for c in v['cues']] == sorted(set(c['at'] for c in v['cues']))
               for v in p['demo'].values())
    s=SRC.read_text('utf8')
    assert "PaperLayout title={a.headline" in s
    assert 'eventAt(t,cues,cues[0])' in s
    assert "if(kind==='pulley')" not in s  # Escolha de geometria não reescreve layout.
    assert 'gearState(t)' in s and 'pulleyState(t)' in s
    assert 'gearOutline(' in s
    shell=SHELL.read_text('utf8')
    assert 'Coringa' not in shell  # Logo textual com grafia real.
    assert 'CORINGA <span' in shell
    assert "PAPER.bg" in shell
    assert 'feTurbulence' not in shell
    assert 'pattern id=' not in shell
    assert '<Img' not in shell and 'backgroundImage' not in shell
    assert 'PRÉVIA PRIVADA · NÃO PUBLICAR' in shell
    root=ROOT_TSX.read_text('utf8')
    assert 'id="ProvaPolia2D"' in root
    assert 'id="ProvaEngrenagens2D"' in root
    assert "kind:'pulley',private_review_only:true" in root
    assert "kind:'gears',private_review_only:true" in root
    catalog=(ROOT/'src/v4/formatos/catalogo_mecanismos.py').read_text('utf8')
    assert "'pulley_2d': Capacidade(" not in catalog
    assert "'gears_2d': Capacidade(" not in catalog


def test_polia_fixa_transmite_deslocamentos_iguais_e_nao_multiplica_forca():
    p=plan()['demo']['pulley']
    g=p['geometry']
    assert [c['action'] for c in p['cues']]==[
        'assembly','load','pull','lift','result']
    assert g['freeX']==g['center'][0]-g['radius']
    assert g['loadX']==g['center'][0]+g['radius']
    assert g['maxTravel']>=125
    x_free=g['freeX']
    x_load=g['loadX']
    assert 150<x_free<x_load<770
    lengths=[]
    for n in range(101):
        t=n/100*g['maxTravel']
        free_y=g['freeEndInitialY']+t
        load_y=g['loadTopInitialY']-t
        lengths.append((free_y-g['center'][1])+(load_y-g['center'][1]))
        assert free_y>=g['center'][1]
        assert load_y>=g['center'][1]+g['radius']*.65
        assert load_y+24+g['loadHeight']<=1083
        assert (x_load+g['loadWidth']/2)<770
        # O peso NÃO pode encostar ou atravessar a roldana no topo.
        # Geometria circular real, em 101 momentos e não só nos keyframes.
        block_top=load_y+24
        dx_left=x_load-g['loadWidth']/2
        cy=g['center'][1]
        if block_top<cy+g['radius']:
            dy=block_top-cy
            circle_right=g['center'][0]+math.sqrt(
                max(0,g['radius']**2-dy**2))
            assert dx_left>=circle_right+12,(t,dx_left,circle_right)
    assert max(lengths)-min(lengths)<1e-7
    s=SRC.read_text('utf8')
    assert 'wheelRotation:travel/g.radius*180/Math.PI' in s
    assert 'freeEndY:g.freeEndInitialY+travel' in s
    assert 'loadTopY:g.loadTopInitialY-travel' in s
    assert "' A '+r+" in s  # arco da corda montado dinamicamente no mesmo path
    assert 'POLIA FIXA MUDA A DIREÇÃO DA FORÇA' in json.dumps(p,ensure_ascii=False)


def test_engrenagens_mesma_velocidade_tangencial_sentidos_opostos():
    g=plan()['demo']['gears']['geometry']
    d,e=g['driverCenter'],g['drivenCenter']
    assert d[1]==e[1]
    assert math.isclose(e[0]-d[0],g['driverRadius']+g['drivenRadius'])
    ratio=g['driverTeeth']/g['drivenTeeth']
    assert .45<ratio<.85
    assert abs(g['driverRadius']/g['drivenRadius']-ratio)<.01
    for angle in [0,15,60,125,205,370,g['driverTurnDegrees']]:
        output=-angle*ratio
        assert output<=0<=angle
        assert math.isclose(abs(output/angle),ratio) if angle else output==0
    s=SRC.read_text('utf8')
    assert 'outputRotation=-(rotation*g.driverTeeth/g.drivenTeeth)' in s
    assert 'st.ratio.toFixed(1)' in s
    assert 'gearOutline(x,y,r,teeth)' in s
    assert "stroke={PAPER.teal}" in s
    # Parte grande pode chegar em x>770 somente na altura acima dos
    # botões; dentro da faixa y>=840 sua largura respeita a zona central.
    cx,cy=e
    radius=g['drivenRadius']*1.025
    assert cy+radius<1093
    if cy+radius>840:
        right_at_icons=cx+math.sqrt(radius**2-(840-cy)**2)
        assert right_at_icons<=770


def test_zero_assets_copiados_e_visual_original():
    src=SRC.read_text('utf8')
    assert 'the efficient engineer' not in src.lower()
    assert '3blue1brown' not in src.lower()
    assert 'staticFile(' not in src
    assert 'render 3d' not in src.lower()
    assert 'FECHAR' not in src
    assert CORE.is_file()
