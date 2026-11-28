"""F5: contrato de peças reais compartilhado por 3 renderizadores 2D.

Prova que nenhum role essencial falta no SVG gerado; texto da fonte
não é licença de copiar imagem nem evidência de similaridade visual.
"""
from __future__ import annotations
import copy,io,json,re
from pathlib import Path
from xml.etree import ElementTree as ET
import cairosvg,pytest
from PIL import Image,ImageChops,ImageStat
from src.v4.formatos import biblioteca_componentes_fisicos as B
from src.v4.formatos import grafo_causal as G
from src.v4.formatos import camera_causal_svg as C
from src.v4.formatos import render_compressor_conjunto_2d as P
from src.v4.formatos import render_reconstrucao_causal_2d as O
from src.v4.formatos import render_eclusa_hidraulica_2d as L

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'docs/v4/formatos/reference_first'


def renderers():
    manifest=json.loads(P.MANIFESTO_PADRAO.read_text('utf8'))
    motion=json.loads((DATA/'otto_48f_measured_motion.json').read_text('utf8'))
    scene=json.loads((DATA/'otto_48f_causal_reviewed_scene.json').read_text('utf8'))
    return {
        'compressor_oficina_pv':[
            P.frame_svg(.1,manifest,camera_causal=True),
            P.frame_svg(.75,manifest,camera_causal=True)],
        'otto_4t_reference':[
            O.svg_frame(motion,scene,.10,camera_causal=True),
            O.svg_frame(motion,scene,.70,camera_causal=True)],
        'lock_cycle_standalone':[
            L.frame_svg(4.15),L.frame_svg(7.50)],
    }


def raster(svg):
    with Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode()))) as im:
        return im.convert('RGB').copy()


def changes(a,b,region):
    diff=ImageChops.difference(a.crop(region),b.crop(region))
    return sum(ImageStat.Stat(diff).mean)/3.


def test_contrato_e_tres_fontes_tecnicas_nao_sao_licencas_visuais():
    summary=B.validar()
    assert summary['atores']==29
    assert summary['familias']==3
    assert summary['tipos']==13
    assert len(summary['tipos_entre_familias'])>=5
    assert summary['fonte_tecnica_nao_licenca_visual'] is True
    assert summary['publicar'] is False
    for fam in B.CATALOGO['families'].values():
        assert fam['rights']['source_pixel_copied'] is False
        assert fam['rights']['source_page_is_media_license'] is False
        assert fam['rights']['republication_approved'] is False
        assert 'identity_reference' in fam
    for source in B.CATALOGO['evidence_sources'].values():
        assert source['url'].startswith('https://')
        assert source['does_not_establish']


def test_todos_29_atores_existem_em_svg_real_com_papel_e_fonte():
    for family,frames in renderers().items():
        expected=B.CATALOGO['families'][family]['actor_role_mapping']
        source=B.CATALOGO['families'][family]['technical_source']
        for svg in frames:
            root=ET.fromstring(svg)
            assert root.tag.endswith('svg')
            seen={}
            for node in root.iter():
                id_=node.attrib.get('id','')
                if id_.startswith('role-'):
                    assert id_ not in seen
                    seen[id_]=node.attrib
            assert all('role-'+x['id'] in seen for x in expected)
            for actor in expected:
                attrs=seen['role-'+actor['id']]
                assert attrs['data-primitive']==actor['primitive']
                assert attrs['data-source-tech']==source
                assert attrs['data-visual-identity']=='PENDENTE'
                assert actor['id'] in C.CAMERAS['familias'][family]['roles']
            assert 'data-visual-identity="APROVADO"' not in svg
            assert 'data-primitive=' in svg


def test_uma_ausencia_em_qualquer_familia_bloqueia_svg():
    for family,frames in renderers().items():
        role=B.CATALOGO['families'][family]['actor_role_mapping'][0]['id']
        svg=frames[0].replace(f'id="role-{role}"',f'id="role-inexistente_{role}"')
        with pytest.raises(ValueError,match='F-BIBLIOTECA-ATOR-SEM-DESENHO'):
            B.etiquetar_svg(family,svg)


def test_papel_duplicado_bloqueia_ainda_que_peca_exista():
    svg=renderers()['lock_cycle_standalone'][0]
    invalid=svg.replace('id="role-water"','id="role-water" id="role-water"')
    with pytest.raises(ValueError,match='F-BIBLIOTECA-ATOR-DUPLICADO-SVG'):
        B.etiquetar_svg('lock_cycle_standalone',invalid)


def test_manifesto_nao_pode_aprovar_imagem_ou_licenca_automaticamente():
    for mutate,pattern in [
        (lambda db:db.update({'published':True}),'F-BIBLIOTECA-SEM-GATE'),
        (lambda db:db.update({'visual_approval':True}),'F-BIBLIOTECA-SEM-GATE'),
        (lambda db:db['families']['lock_cycle_standalone']['rights'].update(
            {'source_pixel_copied':True}),'F-BIBLIOTECA-DIREITOS'),
        (lambda db:db['families']['otto_4t_reference']['actor_role_mapping'].pop(),
            'F-BIBLIOTECA-ATOR-AUSENTE'),
        (lambda db:db['evidence_sources']['usace_lock_operation'].update(
            {'url':'file:///tmp/bad.png'}),'F-BIBLIOTECA-FONTE'),
        (lambda db:db['families']['compressor_oficina_pv'].update(
            {'technical_source':'url_unverified'}),'F-BIBLIOTECA-SEM-FONTE'),
        (lambda db:db['families']['otto_4t_reference'].update(
            {'event_ids':['hello']}),'F-BIBLIOTECA-EVENTO'),
    ]:
        obj=copy.deepcopy(B.CATALOGO)
        mutate(obj)
        with pytest.raises(ValueError,match=pattern):
            B.validar(obj)


def test_fichas_compiladas_têm_geometrias_com_origem_e_relacoes():
    for family in B.CATALOGO['families']:
        ficha=B.fichas(family)
        assert ficha['visual_proven'] is False
        assert ficha['publish'] is False
        assert ficha['identity_state']
        assert ficha['relations']==G.GRAFOS[family]['relacoes']
        assert len(ficha['components'])==len(G.GRAFOS[family]['atores'])
        for obj in ficha['components']:
            assert len(obj['bbox'])==4
            assert obj['primitive'] in B.CATALOGO['primitive_types']


def test_pixels_mudam_nos_atores_fisicos_em_tres_familias():
    # Checagem de mudança de pixel: APENAS detector de cena estática.
    # Não confundir com prova que a física foi compreendida ou fonte fiel.
    regions={
        'compressor_oficina_pv':(220,330,398,775),
        'otto_4t_reference':(178,295,364,764),
        'lock_cycle_standalone':(157,385,387,779)
    }
    for family,frames in renderers().items():
        a,b=[raster(s) for s in frames]
        assert a.size==b.size==(540,960)
        delta=changes(a,b,regions[family])
        assert delta>1.1,(family,delta)
        assert changes(a,b,(0,0,540,27))==0,(family,'header background')
    assert len({x for x in B.CATALOGO['primitive_types']})==13


def test_componentes_ainda_nao_podem_ser_criados_por_nome_desconhecido():
    with pytest.raises(ValueError,match='F-BIBLIOTECA-FAMILIA-DESCONHECIDA'):
        B.fichas('compressor_de_algum_texto_aleatorio')
    with pytest.raises(ValueError,match='F-BIBLIOTECA-FAMILIA-DESCONHECIDA'):
        B.etiquetar_svg('tema_novo','<svg></svg>')
