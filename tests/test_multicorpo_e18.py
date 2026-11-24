"""E18–E20: núcleo multicorpo 3D, renderer e lote multi-fornecedor.

Os testes sintéticos rodam sem rede. Os de fonte real exigem
E18_MENAGERIE=<checkout no commit fixado> (o workflow faz o checkout).
"""
import json
import math
import os
from pathlib import Path

import numpy as np
import pytest

mujoco = pytest.importorskip("mujoco")
from src.v4.formatos import multicorpo_e18 as M  # noqa: E402
from src.v4.formatos import raster_e18 as R  # noqa: E402
from src.v4.formatos import filme_e18 as F  # noqa: E402

CAIXA = "0 0 0  1 0 0  1 1 0  0 1 0  0 0 1  1 0 1  1 1 1  0 1 1"


def mjcf(corpo, extra=""):
    return f"""<mujoco><compiler angle="radian" autolimits="true"/>
    <asset><mesh name="cx" vertex="{CAIXA}" scale="0.01 0.01 0.01"/></asset>
    <worldbody>{corpo}</worldbody>{extra}</mujoco>"""


def quatro_barras(com_mola=False, sem_acionador_extra=False):
    """Quatro barras planas: manivela 0,1; acopladora 0,3; balancim 0,25; base 0,3 (m)."""
    mola = 'stiffness="1" springref="3"' if com_mola else ""
    corpo = f"""
    <body name="base"><geom type="mesh" mesh="cx" contype="0" conaffinity="0"/>
      <body name="manivela"><joint name="j1" type="hinge" axis="0 0 1"/>
        <geom type="mesh" mesh="cx" contype="0" conaffinity="0"/>
        <body name="acopladora" pos="0.1 0 0"><joint name="j2" type="hinge" axis="0 0 1"/>
          <geom type="mesh" mesh="cx" contype="0" conaffinity="0"/></body></body>
      <body name="balancim" pos="0.3 0 0"><joint name="j3" type="hinge" axis="0 0 1" {mola} range="-3 3"/>
        <geom type="mesh" mesh="cx" contype="0" conaffinity="0"/></body></body>"""
    # Fechamento: ponta da acopladora (0,3 ao longo de x local) no topo do balancim.
    # Pose de referência montada: resolvida numericamente abaixo antes do uso.
    extra = """<equality><connect body1="acopladora" body2="balancim" anchor="0.3 0 0"/></equality>
    <actuator><motor joint="j1"/></actuator>"""
    return corpo, extra


def montar_quatro_barras():
    """Gera MJCF já montado (q0 coerente) para a geometria acima."""
    # Ângulo da manivela 60°: resolve posição montada analiticamente.
    a, b, c, d = 0.1, 0.3, 0.25, 0.3
    th = math.radians(60)
    A = np.array([a * math.cos(th), a * math.sin(th)])
    O4 = np.array([d, 0.0])
    # Interseção dos círculos |P-A|=b, |P-O4|=c (ramo superior).
    dist = np.linalg.norm(O4 - A)
    x = (dist**2 + b**2 - c**2) / (2 * dist)
    h = math.sqrt(b**2 - x**2)
    u = (O4 - A) / dist
    P = A + x * u + h * np.array([-u[1], u[0]])
    ang_b = math.atan2(*(P - A)[::-1])
    ang_c = math.atan2(*(P - O4)[::-1])
    corpo = f"""
    <body name="base"><geom type="mesh" mesh="cx" contype="0" conaffinity="0"/>
      <body name="manivela" euler="0 0 {th}"><joint name="j1" type="hinge" axis="0 0 1" range="-10 10"/>
        <geom type="mesh" mesh="cx" contype="0" conaffinity="0"/>
        <body name="acopladora" pos="{a} 0 0" euler="0 0 {ang_b - th}"><joint name="j2" type="hinge" axis="0 0 1"/>
          <geom type="mesh" mesh="cx" contype="0" conaffinity="0"/></body></body>
      <body name="balancim" pos="{d} 0 0" euler="0 0 {ang_c}"><joint name="j3" type="hinge" axis="0 0 1"/>
        <geom type="mesh" mesh="cx" contype="0" conaffinity="0"/></body></body>"""
    extra = f"""<equality><connect body1="acopladora" body2="balancim" anchor="{b} 0 0"/></equality>
    <actuator><motor name="m" joint="j1"/></actuator>"""
    return mujoco.MjModel.from_xml_string(mjcf(corpo, extra)), (a, b, c, d, th)


def test_fk_propria_igual_ao_mujoco_em_cadeia_com_hinge_e_slide():
    corpo = """<body name="b1" pos="0.1 0.2 0" quat="0.9 0.1 0.3 0.2"><joint type="hinge" axis="0 1 1" pos="0.02 0 0"/>
      <geom type="mesh" mesh="cx" contype="0" conaffinity="0"/>
      <body name="b2" pos="0 0.3 0.1" euler="0.3 -0.2 1"><joint type="slide" axis="1 0 0"/>
        <joint type="hinge" axis="0 0 1" pos="0 0.05 0"/><geom type="mesh" mesh="cx" contype="0" conaffinity="0"/></body></body>"""
    m = mujoco.MjModel.from_xml_string(mjcf(corpo))
    mont = M.de_mujoco(m)
    rng = np.random.default_rng(3)
    qs = [rng.uniform(-1, 1, m.nq) for _ in range(10)]
    r = M.oraculo_cinematica(m, mont, qs)
    assert r["fk_pos_max_m"] < 1e-12 and r["fk_rot_max"] < 1e-12


def test_quatro_barras_fechado_confere_com_freudenstein():
    m, (a, b, c, d, th0) = montar_quatro_barras()
    mont = M.de_mujoco(m)
    alvos = np.linspace(th0, th0 + 1.2, 25)[:, None]  # ângulo absoluto = q + th0 (q0 = 0)
    traj, _ = M.trajetoria(mont, mont.atuadores, alvos - th0, mont.chaves["qpos0"])
    for (q, info), alvo in zip(traj, alvos[:, 0]):
        assert info["mobilidade"] == 0 and info["residuo"] < 1e-9
        X = mont.poses(q)
        bal = X[mont.indice_corpo("balancim")]
        ang = math.atan2(bal[1, 0], bal[0, 0])
        # Oráculo analítico independente (interseção de círculos, mesmo ramo).
        A = np.array([a * math.cos(alvo), a * math.sin(alvo)])
        O4 = np.array([d, 0.0])
        dist = np.linalg.norm(O4 - A)
        x = (dist**2 + b**2 - c**2) / (2 * dist)
        P = A + x * (O4 - A) / dist + math.sqrt(b**2 - x**2) * np.array([-(O4 - A)[1], (O4 - A)[0]]) / dist
        assert abs(math.atan2(*(P - O4)[::-1]) - ang) < 1e-8
    assert M.oraculo_cinematica(m, mont, [q for q, _ in traj])["igualdade_mujoco_max"] < 1e-9


def test_grau_passivo_sem_mola_e_recusado():
    # Cinco barras (dois GL) com um só atuador e nenhuma mola declarada.
    corpo = """<body name="base"><geom type="mesh" mesh="cx" contype="0" conaffinity="0"/>
      <body name="e1"><joint name="a" type="hinge" axis="0 0 1" range="-3 3"/><geom type="mesh" mesh="cx" contype="0" conaffinity="0"/>
        <body name="e2" pos="0.1 0 0"><joint type="hinge" axis="0 0 1"/><geom type="mesh" mesh="cx" contype="0" conaffinity="0"/></body></body>
      <body name="e3" pos="0.25 0 0"><joint type="hinge" axis="0 0 1"/><geom type="mesh" mesh="cx" contype="0" conaffinity="0"/>
        <body name="e4" pos="0.1 0 0"><joint type="hinge" axis="0 0 1"/><geom type="mesh" mesh="cx" contype="0" conaffinity="0"/></body></body></body>"""
    extra = """<equality><connect body1="e2" body2="e4" anchor="0.0 0.0 0"/></equality><actuator><motor joint="a"/></actuator>"""
    m = mujoco.MjModel.from_xml_string(mjcf(corpo, extra))
    mont = M.de_mujoco(m)
    with pytest.raises(ValueError, match="E18-SUBDETERMINADO"):
        M.Resolvedor(mont, mont.atuadores).resolver([0.05], mont.chaves["qpos0"])


def test_juntas_bola_ou_livre_sao_recusadas():
    m = mujoco.MjModel.from_xml_string(mjcf("""<body><joint type="ball"/><geom type="mesh" mesh="cx"/></body>"""))
    with pytest.raises(ValueError, match="E18-JUNTA_NAO_SUPORTADA"):
        M.de_mujoco(m)


def test_corte_no_primeiro_contato_entre_malhas():
    corpo = """<body name="base"><geom type="mesh" mesh="cx" contype="0" conaffinity="0"/>
      <body name="esq" pos="-0.05 0 0"><joint name="je" type="slide" axis="1 0 0" range="0 0.05"/>
        <geom type="mesh" mesh="cx" contype="0" conaffinity="0"/></body>
      <body name="dir" pos="0.05 0 0"><joint name="jd" type="slide" axis="-1 0 0" range="0 0.05"/>
        <geom type="mesh" mesh="cx" contype="0" conaffinity="0"/></body></body>"""
    extra = """<equality><joint joint1="jd" joint2="je"/></equality>
    <tendon><fixed name="t"><joint joint="je" coef="0.5"/><joint joint="jd" coef="0.5"/></fixed></tendon>
    <actuator><motor tendon="t"/></actuator>"""
    m = mujoco.MjModel.from_xml_string(mjcf(corpo, extra))
    mont = M.de_mujoco(m)
    s = M.Resolvedor(mont, mont.atuadores)
    faixa, cortes, eixo = M.corte_no_contato(mont, s, s.faixa_acionador(0), "esq", "dir", mont.chaves["qpos0"])
    # Caixas de 10 mm, centros a 100 mm: folga inicial 90 mm, contato com 45 mm por lado.
    assert cortes == ["fim"] and abs(faixa[1] - 0.045) < 1e-6
    q, _ = s.resolver([faixa[1]], mont.chaves["qpos0"])
    assert abs(M.folga(mont, q, "esq", "dir", eixo)[0]) < 1e-6


def cinco_barras_mjcf(springref):
    """Cinco barras plano real: pivôs fixos O1=(0,0) e O2=(0,25;0); quatro elos
    de 0,1 m; as pontas de e2 e e4 unidas por pino (connect). Dois GL; um
    atuador em 'a'; mola em 'p'; batente em 'c'. Pose montada analítica."""
    A = np.array([0.1 * math.cos(math.radians(60)), 0.1 * math.sin(math.radians(60))])
    B = np.array([0.25 + 0.1 * math.cos(math.radians(120)), 0.1 * math.sin(math.radians(120))])
    meio, meia = (A + B) / 2, np.linalg.norm(B - A) / 2
    P = meio + math.sqrt(0.01 - meia**2) * np.array([0, 1.0])
    ang = lambda v: math.atan2(v[1], v[0])
    g = '<geom type="mesh" mesh="cx" contype="0" conaffinity="0"/>'
    corpo = f"""<body name="base">{g}
      <body name="e1" euler="0 0 {math.radians(60)}"><joint name="a" type="hinge" axis="0 0 1" armature="0.01" range="-1 1" damping="1"/>{g}
        <body name="e2" pos="0.1 0 0" euler="0 0 {ang(P - A) - math.radians(60)}"><joint name="c" type="hinge" axis="0 0 1" armature="0.01" range="-0.35 0.35" damping="0.05" solreflimit="0.002 1"/>{g}</body></body>
      <body name="e3" pos="0.25 0 0" euler="0 0 {math.radians(120)}"><joint name="p" type="hinge" axis="0 0 1" armature="0.01" range="-1 1" stiffness="0.5" springref="{springref}" damping="0.05"/>{g}
        <body name="e4" pos="0.1 0 0" euler="0 0 {ang(P - B) - math.radians(120)}"><joint name="f" type="hinge" axis="0 0 1" armature="0.01" range="-2 2" damping="0.05"/>{g}</body></body></body>"""
    extra = """<equality><connect body1="e2" body2="e4" anchor="0.1 0 0" solref="0.002 1"/></equality>
    <actuator><position joint="a" kp="200" ctrlrange="-1 1"/></actuator>"""
    # armature: inércia de rotor só para condicionar a simulação-oráculo
    # (corpos sintéticos têm 1 g concentrado no pivô); não afeta a estática.
    return mjcf(corpo, extra)


@pytest.mark.parametrize("springref,batentes", [(0.15, []), (2.6, ["c"])])
def test_mola_com_batente_confere_com_simulacao_mujoco(springref, batentes):
    # a=0,3 seria inviável com |c|≤0,35 (verificado por varredura): alvo 0,1.
    # Mola fraca: equilíbrio interno (mola). Mola forte: o elo 'c' vai ao batente.
    xml = cinco_barras_mjcf(springref)
    m = mujoco.MjModel.from_xml_string(xml)
    mont = M.de_mujoco(m)
    s = M.Resolvedor(mont, mont.atuadores)
    q, info = s.resolver([0.1], mont.chaves["qpos0"])
    assert info["mobilidade"] == 1 and info["residuo"] < 1e-9
    assert s.ultimos_batentes == batentes
    assert info["modo"] == ("quase_estatico_batente" if batentes else "quase_estatico_mola")
    # Oráculo independente: dinâmica do MuJoCo até o repouso.
    sim = M.oraculo_simulacao(mujoco.MjModel.from_xml_string(xml), mont,
                              M.Resolvedor(mont, mont.atuadores), [0.1], segundos=4.0)
    assert sim[0]["max_dif_junta_rad"] < 5e-3
    # Mínimo local: perturbações viáveis não reduzem a energia.
    e = lambda x: float((s.k * (x - s.qs) ** 2).sum())
    for passo in (0.02, -0.02):
        try:
            outro, _ = M.Resolvedor(mont, mont.atuadores).resolver([0.1], q + passo)
        except ValueError:
            continue
        assert e(outro) >= e(q) - 1e-12


def test_hash_adulterado_bloqueia(tmp_path):
    (tmp_path / "m.xml").write_text(mjcf("""<body><joint type="hinge"/><geom type="mesh" mesh="cx"/></body>"""))
    (tmp_path / "LICENSE").write_text("x")
    modelo = dict(xml="m.xml", licenca_arquivo="LICENSE",
                  sha256={"m.xml": "0" * 64, "LICENSE": F.sha256(tmp_path / "LICENSE")})
    with pytest.raises(ValueError, match="E18-FONTE-SHA256"):
        F.carregar(modelo, tmp_path)
    modelo["sha256"]["m.xml"] = F.sha256(tmp_path / "m.xml")
    del modelo["sha256"]["LICENSE"]
    with pytest.raises(ValueError, match="LICENCA_SEM_HASH"):
        F.carregar(modelo, tmp_path)


def test_renderer_cobre_peca_e_respeita_camera_fixa():
    V = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]], float) * .1
    Fc = np.array([[0, 1, 2], [0, 2, 3], [4, 5, 6], [4, 6, 7], [0, 1, 5], [0, 5, 4],
                   [1, 2, 6], [1, 6, 5], [2, 3, 7], [2, 7, 6], [3, 0, 4], [3, 4, 7]], np.int32)
    cam = R.enquadrar(V, np.array([1, 0.4, -0.3]), np.array([0, 0, 1.]), 24, 108, 192, (.1, .2, .9, .7))
    img, info = R.renderizar(cam, [(V, Fc, np.array([.8, .5, .2]), .5)], R.fundo_gradiente(108, 192), chao=0.0)
    assert img.shape == (192, 108, 3) and 0.05 < info["cobertura"] < 0.6
    u, v, _, _ = cam.projetar(V)
    assert u.min() >= 0.1 * 108 - 1 and u.max() <= 0.9 * 108 + 1 and v.min() >= .2 * 192 - 1 and v.max() <= .7 * 192 + 1


def test_manifesto_sem_ramo_por_maquina():
    """O código do filme não pode conter nomes dos modelos do manifesto."""
    man = json.loads(Path("benchmarks/e18_multifornecedor.json").read_text())
    codigo = "".join(Path(f"src/v4/formatos/{n}.py").read_text().lower()
                     for n in ("filme_e18", "multicorpo_e18", "raster_e18"))
    for modelo in man["modelos"]:
        for termo in (modelo["id"], modelo["titulo"].lower(), modelo["xml"].split("/")[0]):
            assert termo.lower() not in codigo
    assert all(len(m["sha256"]) >= 3 and m["licenca_arquivo"] in m["sha256"] for m in man["modelos"])


# ---------------------------------------------------------------- fonte real
RAIZ = os.environ.get("E18_MENAGERIE")
real = pytest.mark.skipif(not RAIZ, reason="E18_MENAGERIE não definido")


@real
def test_fontes_reais_carregam_com_hash_e_fk_igual_ao_mujoco():
    man = json.loads(Path("benchmarks/e18_multifornecedor.json").read_text())
    for modelo in man["modelos"]:
        m, mont, lidos = F.carregar(modelo, RAIZ)
        assert set(lidos) <= set(modelo["sha256"])
        rng = np.random.default_rng(0)
        lo = np.array([j.limite[0] if j.limite else -1 for j in mont.juntas])
        hi = np.array([j.limite[1] if j.limite else 1 for j in mont.juntas])
        r = M.oraculo_cinematica(m, mont, [rng.uniform(lo, hi) for _ in range(8)])
        assert r["fk_pos_max_m"] < 1e-12


@real
def test_robotiq_subatuado_bate_com_simulacao_e_ficha():
    man = json.loads(Path("benchmarks/e18_multifornecedor.json").read_text())
    modelo = next(x for x in man["modelos"] if x["movimento"]["tipo"] == "varredura_atuador"
                  and "2f85" in x["xml"])
    m, mont, _ = F.carregar(modelo, RAIZ)
    cache = {}
    acion, alvos, semente = F.plano_movimento(mont, modelo, cache)
    s = M.Resolvedor(mont, acion)
    q, info = s.resolver([cache["faixa"][0]], semente)
    assert info["mobilidade"] == 2
    abertura = M.folga(mont, q, modelo["medida"]["a"], modelo["medida"]["b"], cache["eixo"])[0] * 1000
    assert abs(abertura - modelo["oraculo"]["valor_mm"]) <= modelo["oraculo"]["tolerancia_mm"]
    sim = M.oraculo_simulacao(mujoco.MjModel.from_xml_path(str(Path(RAIZ) / modelo["xml"])), mont,
                              M.Resolvedor(mont, acion), [0.2, 0.4])
    assert max(r["max_dif_junta_rad"] for r in sim) < 1e-3


@real
def test_ur5e_confere_com_tabela_dh_oficial():
    man = json.loads(Path("benchmarks/e18_multifornecedor.json").read_text())
    modelo = next(x for x in man["modelos"] if x["oraculo"]["tipo"] == "dh")
    _, mont, _ = F.carregar(modelo, RAIZ)
    r = F.oraculo_dh(mont, modelo["oraculo"])
    assert r["erro_max_mm"] <= modelo["oraculo"]["tolerancia_mm"]
    # Controle negativo: a3 trocado por 10 mm a mais tem de ser detectado.
    errado = dict(modelo["oraculo"], a=[0, -0.425, -0.4022, 0, 0, 0])
    assert F.oraculo_dh(mont, errado)["erro_max_mm"] > 5
