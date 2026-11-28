"""Destaque por relação causal: físico, discreto e sem câmera móvel.

Compara SVGs reais, preservando compositor e física quando desligado.
"""
from __future__ import annotations
import copy,io,json,re
from pathlib import Path
import cairosvg,pytest
from PIL import Image,ImageChops,ImageStat
from src.v4.formatos import realce_causal_svg as R
from src.v4.formatos import grafo_causal as G
from src.v4.formatos import render_compressor_conjunto_2d as P
from src.v4.formatos import render_reconstrucao_causal_2d as O
from src.v4.formatos import camera_causal_svg as C
from src.v4.formatos.compressor_pv_core import limites_fases

DIR=Path(__file__).resolve().parents[1]/'docs/v4/formatos/reference_first'

def _manifest():
    return json.loads(P.MANIFESTO_PADRAO.read_text('utf8'))

def _otto():
    return (json.loads((DIR/'otto_48f_measured_motion.json').read_text('utf8')),
            json.loads((DIR/'otto_48f_causal_reviewed_scene.json').read_text('utf8')))

def _rgb(svg):
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode()))).convert('RGB')

def _delta(a,b,roi):
    return sum(ImageStat.Stat(ImageChops.difference(a.crop(roi),b.crop(roi))).mean)/3

def _sem_linhas_vazias(svg):
    # Unica diferenca ignorada: a linha em branco após retirar camada SVG.
    # Nenhuma alteracao de tags, coords, estilo ou fisica e permitida.
    return "\\n".join(line.rstrip() for line in svg.splitlines() if line.strip())



def test_duas_familias_contem_rotas_verdadeiras_do_grafo():
    for fam in ('compressor_oficina_pv','otto_4t_reference'):
        cap=G.GRAFOS[fam]
        causal=G.montar(fam,tuple(e['acao'] for e in cap['eventos']))
        for action,spec in R.REGISTRO['familias'][fam].items():
            event=next(e for e in causal['eventos'] if e['acao']==action)
            assert spec['edge'] in [
                [r['from'],r['type'],r['to']] for r in event['relacoes_em_foco']]
            assert spec['kind'] in ('flow','outline')
            assert spec['color'].startswith('#')
        assert C.CAMERAS['familias'][fam]['politica_camera']=='plano_geral_travado'
    # Sem duplicar efeito de ignição, porque já existe faísca física.
    assert 'ignicao_expansao' not in R.REGISTRO['familias']['otto_4t_reference']


def test_realce_de_fluxo_so_com_admissao_ou_saida_fisicas():
    for fam,act,relation in [
        ('compressor_oficina_pv','ADMISSAO_AR','intake_filter'),
        ('compressor_oficina_pv','DESCARGA_PRESSURIZADA','discharge_pipe'),
        ('otto_4t_reference','admissao_mistura','intake_flow'),
        ('otto_4t_reference','escape_gases','outlet_valve')]:
        svg=R.renderizar(fam,act,.5,fisica_confirma=True)
        assert 'id="causal-emphasis"' in svg
        assert 'stroke-dasharray="11 17"' in svg
        assert 'data-event=' in svg and relation in [
            x['id'] for x in G.GRAFOS[fam]['atores']]
        assert '<rect' not in svg
        assert '<text' not in svg
        with pytest.raises(ValueError,match='F-REALCE-SEM-EVIDENCIA-FISICA'):
            R.renderizar(fam,act,.5,fisica_confirma=False)


def test_realce_de_pistao_acompanha_bbox_dinamica():
    a=R.renderizar('compressor_oficina_pv','COMPRESSAO_AR',.5,
                  dinamicos={'piston_cutaway':(252,488,86,60)})
    b=R.renderizar('compressor_oficina_pv','COMPRESSAO_AR',.5,
                  dinamicos={'piston_cutaway':(252,560,86,60)})
    assert 'y="488.00"' in a and 'y="560.00"' in b
    assert '<rect' in a and 'fill="none"' in a
    c=R.renderizar('otto_4t_reference','compressao_mistura',.5,
                  dinamicos={'piston':(188,430,158,95)})
    assert 'x="188.00"' in c
    with pytest.raises(ValueError,match='F-REALCE-SEM-PECA-MOVEL'):
        R.renderizar('otto_4t_reference','compressao_mistura',.5)
    with pytest.raises(ValueError,match='F-REALCE-FORA-DA-MAQUINA'):
        R.renderizar('otto_4t_reference','compressao_mistura',.5,
                    dinamicos={'piston':(188,920,158,95)})


def test_ciclo_compressor_preserva_camera_fisica_e_titulos():
    manifest=_manifest()
    spans=limites_fases(P.AssemblyLayout().spec())
    for action,range_ in spans.items():
        t=(range_['de']+range_['ate'])/2
        base=P.frame_svg(t,manifest,camera_causal=True)
        new=P.frame_svg(t,manifest,camera_causal=True,realce_causal=True)
        assert 'id="causal-emphasis"' not in base
        assert 'id="causal-emphasis"' in new
        a,b=_rgb(base),_rgb(new)
        assert a.size==b.size==(540,960)
        assert _delta(a,b,(0,0,540,238))==0
        assert _delta(a,b,(0,903,540,960))==0
        assert _delta(a,b,(75,255,485,850))>0.02
        # A unica diferença no XML deve ser o grupo de realce.
        assert _sem_linhas_vazias(re.sub(
            r'    <g id="causal-emphasis".*?</g>','',new,
            flags=re.DOTALL))==_sem_linhas_vazias(base)


def test_otto_sem_pulsar_camera_e_sem_duplicar_faisca():
    mov,scene=_otto()
    beats=scene['ciclo'];total=mov['quadros']
    for i,beat in enumerate(beats):
        end=beats[i+1]['quadro_inicio'] if i+1<len(beats) else total
        t=(beat['quadro_inicio']+end)/(2*total)
        before=O.svg_frame(mov,scene,t,camera_causal=True)
        after=O.svg_frame(mov,scene,t,camera_causal=True,realce_causal=True)
        a,b=_rgb(before),_rgb(after)
        assert a.size==b.size==(540,960)
        assert _delta(a,b,(0,0,540,238))==0
        if beat['tipo']=='ignicao_expansao':
            assert 'id="causal-emphasis"' not in after
            assert before==after
        else:
            assert 'id="causal-emphasis"' in after
            assert _delta(a,b,(30,247,510,905))>0.02
            assert _sem_linhas_vazias(re.sub(
                r'    <g id="causal-emphasis".*?</g>','',after,
                flags=re.DOTALL))==_sem_linhas_vazias(before)


def test_sem_efeito_em_estados_sem_evidencia_ou_ativos():
    assert R.renderizar('otto_4t_reference','ignicao_expansao',.5)==''
    with pytest.raises(ValueError,match='F-REALCE-ACAO-NAO-CADASTRADA'):
        R.renderizar('compressor_oficina_pv','efeito_aleatorio',.5)
    with pytest.raises(ValueError,match='F-REALCE-SEM-GRAFO'):
        R.renderizar('tema_aleatorio','a',.5)


def test_entradas_maliciosas_sao_bloqueadas(monkeypatch):
    for value in (-.01,1.01,float('nan'),float('inf')):
        with pytest.raises(ValueError,match='F-REALCE-TEMPO-INVALIDO'):
            R.renderizar('compressor_oficina_pv','ADMISSAO_AR',value)
    temp=copy.deepcopy(R.REGISTRO)
    temp['familias']['compressor_oficina_pv']['ADMISSAO_AR']['edge']=[
        'intake_filter','feeds','receiver_horizontal']
    monkeypatch.setattr(R,'REGISTRO',temp)
    with pytest.raises(ValueError,match='F-REALCE-SEM-RELACAO-CAUSAL'):
        R.renderizar('compressor_oficina_pv','ADMISSAO_AR',.4)


def test_opt_in_deixa_renderizadores_originais_intocados():
    manifest=_manifest()
    for t in (.04,.29,.58,.96):
        x=P.frame_svg(t,manifest)
        y=P.frame_svg(t,manifest,realce_causal=False)
        assert x==y
    assert R.REGISTRO['publicar'] is False
