"""F7 — prova de reuso físico/desenho fora da hidráulica.

Duas cenas mudam curso e razão de polias sem trocar compositor; compressor
e Otto consomem o MESMO núcleo, sem trocar física dos gases.
"""
from __future__ import annotations
import copy,io,json,math,re
from pathlib import Path
import cairosvg,pytest
from PIL import Image,ImageChops,ImageStat

from src.v4.formatos import (
    cinematica_biela_manivela as K,
    compressor_pv_core as CO,
    compositor_cinematico_parametrico_2d as M,
    primitivas_fisicas_parametricas as P,
    render_compressor_conjunto_2d as CP,
    render_reconstrucao_causal_2d as OT,
    camera_causal_svg as CAM,
    grafo_causal as G,
)

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/"src/v4/formatos/cenas_parametricas"
SRC=ROOT/"docs/v4/formatos/reference_first"

def presets():
    return (M.carregar(D/"biela_manivela_curso_curto.json"),
            M.carregar(D/"biela_manivela_curso_longo.json"))

def raster(xml):
    with Image.open(io.BytesIO(cairosvg.svg2png(bytestring=xml.encode()))) as img:
        return img.convert("RGB").copy()

def diff(a,b,roi):
    return sum(ImageStat.Stat(ImageChops.difference(
        a.crop(roi),b.crop(roi))).mean)/3


def test_nucleo_compartilhado_reproduz_formula_analitica_pistao():
    for r,L in ((42,135),(64,190),(46,175),(64,186)):
        for i in range(361):
            theta=i*2*math.pi/360
            p=K.calcular(theta,r,L,300,715)
            dx=r*math.sin(theta)
            py=715-r*math.cos(theta)-math.sqrt(L*L-dx*dx)
            assert math.isclose(p.crank_x,300+dx,abs_tol=1e-10)
            assert math.isclose(p.piston_y,py,abs_tol=1e-10)
            assert math.isclose(p.comprimento_observado,L,abs_tol=1e-10)
        assert math.isclose(K.calcular(0,r,L,300,715).piston_y,715-r-L)
        assert math.isclose(K.calcular(math.pi,r,L,300,715).piston_y,715+r-L)


def test_regressao_core_compressor_e_otto_mesmas_coordenadas():
    spec=CP.AssemblyLayout().spec()
    measured=json.loads((SRC/"otto_48f_measured_motion.json").read_text("utf8"))
    for fraction in (.001,.125,.273,.500,.625,.875,.999):
        s=CO.estado(fraction,spec)
        p=K.calcular(s.angulo,spec.raio,spec.biela,spec.eixo_x,spec.eixo_y)
        assert math.isclose(s.pistao_y,p.piston_y,abs_tol=1e-7)
        assert math.isclose(s.crank_y,p.crank_y,abs_tol=1e-7)
        assert math.isclose(s.crank_x,p.crank_x,abs_tol=1e-7)
        o=OT.pose(fraction,measured)
        assert math.isclose(o["rod_distance"],o["rod_nominal"],abs_tol=1e-7)
        assert math.isfinite(o["piston_y"])


def test_duas_montagens_um_so_compositor_e_mesma_api_de_pecas():
    a,b=presets()
    assert a["id"]!=b["id"]
    assert a["crank"]["radius"]!=b["crank"]["radius"]
    assert a["crank"]["rod"]!=b["crank"]["rod"]
    assert a["motor"]["pulley"]==b["motor"]["pulley"]
    assert a["physics"]==b["physics"]
    assert sorted(P.verificar_reuso())==[
        "conduit","fluid_body","gate","piston","reservoir","rotor",
        "transmission","valve"]
    assert M.validar(a)["graph"]["publicar"] is False
    assert M.validar(b)["graph"]["publicar"] is False
    assert G.montar(M.FAMILY,("curso_descendente","curso_ascendente"))["estado_final"]["piston.position"]=="upper"


@pytest.mark.parametrize("idx",[0,1])
def test_216_quadros_cinematica_biela_junta_correia_sem_escorregamento(idx):
    scene=presets()[idx]
    dur=scene["duration_s"]
    angles=[]
    for i in range(217):
        s=M.estado(scene,dur*i/216)
        p=s["rig"]
        angles.append(p.angulo_rad)
        assert math.isclose(p.comprimento_observado,scene["crank"]["rod"],abs_tol=1e-8)
        assert math.isclose(s["motor_angle_rad"],
             p.angulo_rad*scene["crank"]["wheel"]/scene["motor"]["pulley"],
             abs_tol=1e-8)
        assert scene["crank"]["cx"]==p.piston_x
    assert angles==sorted(angles)
    assert math.isclose(M.estado(scene,0)["rig"].piston_y,
                        M.estado(scene,dur)["rig"].piston_y,abs_tol=1e-7)
    assert M.estado(scene,dur/2)["rig"].piston_y>M.estado(scene,0)["rig"].piston_y
    assert M.estado(scene,0)["stroke"]==2*scene["crank"]["radius"]


def test_pose_camera_mesma_ao_longo_de_ambas_montagens():
    for scene in presets():
        trans=set()
        for i in range(32):
            t=i*scene["duration_s"]/32
            svg=M.frame_svg(scene,t)
            m=re.search(r'id="machine-stage" transform="([^"]+)"',svg)
            assert m,svg[:200]
            trans.add(m.group(1))
            assert svg.count('data-visual-identity="PENDENTE"')==6
        assert len(trans)==1
        for action in ("curso_descendente","curso_ascendente"):
            pose=CAM.calcular(M.FAMILY,action,scene["duration_s"]*.75,0,scene["duration_s"])
            assert CAM.verificar_pose(M.FAMILY,pose)


@pytest.mark.parametrize("idx",[0,1])
def test_cena_real_tem_pistao_movendo_sem_cartoes_ou_camera_nervosa(idx):
    scene=presets()[idx]
    first=M.frame_svg(scene,.04)
    middle=M.frame_svg(scene,scene["duration_s"]*.5)
    last=M.frame_svg(scene,scene["duration_s"]*.99)
    assert all(f'id="role-{key}"' in first for key in M.ACTORS)
    assert len(set(M.ACTORS))==6
    assert "<svg" in first and "BIELA E MANIVELA" in first
    a,b,c=[raster(s) for s in (first,middle,last)]
    assert a.size==b.size==c.size==(540,960)
    assert diff(a,b,(63,303,475,820))>7
    assert diff(a,c,(63,303,475,820))>2
    assert diff(a,b,(0,0,540,55))==0
    assert diff(a,b,(0,906,446,959))==0
    # Contador discreto muda de 01/02 para 02/02. O rodape nao se move.
    assert "01/02" in first and "02/02" in middle


def test_kits_corretamente_bloqueiam_geometria_impossivel():
    for args in [(100,700,30,105,700,70),(100,700,30,150,700,70)]:
        with pytest.raises(ValueError,match="F-PRIMITIVA-CORREIA-SEM-TANGENCIA"):
            P.transmissao_correia(*args)
    with pytest.raises(ValueError,match="F-PRIMITIVA-PISTAO"):
        P.pistao(490,450,120,70)
    with pytest.raises(ValueError,match="F-CINEMATICA"):
        K.calcular(.1,150,100,300,715)
    with pytest.raises(ValueError,match="F-CINEMATICA"):
        K.angulo_motor(.1,60,0)
    with pytest.raises(ValueError):
        P.rotor(300,715,70,math.nan)
    with pytest.raises(ValueError):
        P.biela(200,470,200,470)
    assert "rotate(" in P.rotor(300,715,64,90,raios=5)


def test_falhar_fechado_em_componentes_adulterados_e_licenca_presumida():
    a,_=presets()
    edits=[
      (lambda x:x.update({"publish":True}),"F-COMP-MEC-NAO-HOMOLOGADO"),
      (lambda x:x["legal"].update({"external_media_used":True}),"F-COMP-MEC-FISICA"),
      (lambda x:x["source"].update({"external_license_inferred":True}),"F-COMP-MEC-FISICA"),
      (lambda x:x["crank"].update({"radius":160}),"F-COMP-MEC-PARAMETRO"),
      (lambda x:x["crank"].update({"rod":45}),"F-COMP-MEC-PARAMETRO"),
      (lambda x:x["motor"].update({"cx":285}),"F-COMP-MEC-PARAMETRO"),
      (lambda x:x["phases"][1].update({"action":"fake"}),"F-COMP-MEC-FASE"),
      (lambda x:x["actors"].pop(),"F-COMP-MEC-ATOR"),
    ]
    for change,expected in edits:
        case=copy.deepcopy(a)
        change(case)
        with pytest.raises(ValueError,match=expected):
            M.validar(case)


def test_identidade_visual_ainda_pendente_e_nao_producao():
    for scene in presets():
        svg=M.frame_svg(scene,3)
        assert "data-visual-identity=\"PENDENTE\"" in svg
        assert "PROVA PRIVADA" in svg
        assert "FilmeEditorial" not in svg
        assert "LockCausalCycle" not in svg
        assert scene["publish"] is False
        assert scene["visual_approval"] is False
