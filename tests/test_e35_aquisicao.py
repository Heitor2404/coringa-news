"""E35 — descoberta → geometria → juntas → solver, sem fonte externa.

Genebras sintéticos (n = 5 e 6, diferentes do benchmark n = 4) são gerados em
CadQuery a partir da geometria clássica, exportados em STEP e passam pelo
MESMO leitor/inferência/solver. Casos adversariais: folga grande, peças fora
de posição, entrada não ortogonal, licenças e unidades.
"""
import json
import math
import re
from pathlib import Path

import numpy as np
import pytest

cq = pytest.importorskip("cadquery")

from src.v4.formatos import brep_e35 as B
from src.v4.formatos import fontes_e35 as Fo
from src.v4.formatos import inferencia_e35 as I
from src.v4.formatos import oraculos_e35 as O
from src.v4.formatos import pares_e35 as P
from src.v4.formatos import pipeline_e35 as PL


def genebra_step(tmp, n, a=40.0, pino=3.0, folga=0.3, deslocar=(0, 0), c_fator=1.0):
    """Estrela de n rasgos radiais + roda motora com pino; geometria clássica."""
    c = a / math.sin(math.pi / n) * c_fator
    b = math.sqrt(max(c * c - a * a, 1.0))
    w = 2 * pino + folga
    r_in = c - a - pino
    estrela = cq.Workplane("XY").circle(b).circle(2.5).extrude(6)
    for k in range(n):
        ang = 360.0 * k / n
        corte = (cq.Workplane("XY").center((r_in + b + 5) / 2, 0).rect(b + 5 - r_in, w).extrude(6)
                 .rotate((0, 0, 0), (0, 0, 1), ang))
        estrela = estrela.cut(corte)
    estrela = estrela.translate((-c + deslocar[0], deslocar[1], 6))
    motora = (cq.Workplane("XY").circle(a + pino + 4).circle(2.5).extrude(6)
              .union(cq.Workplane("XY").center(-a, 0).circle(pino).extrude(12)))
    asm = cq.Assembly().add(estrela, name="peca_a").add(motora, name="peca_b")
    caminho = Path(tmp) / f"g{n}.step"
    asm.save(str(caminho))
    return caminho


def _pipeline_local(caminho, classes):
    r, leitura, ctr = PL.analisar_arquivo(caminho, "genebra", classes["genebra"])
    return r, leitura, ctr


@pytest.fixture(scope="module")
def classes():
    return O.carregar_classes()


@pytest.mark.parametrize("n", [5, 6])
def test_genebra_sintetico_n_rasgos_avanco_e_repouso(tmp_path, classes, n):
    r, leitura, ctr = _pipeline_local(genebra_step(tmp_path, n), classes)
    assert r["estagio"] == "PRONTO_PARA_SOLVER", r
    assert r["assinatura"]["n"] == n
    assert all(j["evidencia"] == "derivado+hipotese" for j in ctr["juntas"])
    assert ctr["hipoteses"][0]["codigo"] == "SUPORTE_IMPLICITO"
    mont = I.montagem(leitura, ctr)
    pares = [P.ParPinoRasgo(mont, p, ctr) for p in ctr["pares"]]
    entrada, info = PL.escolher_entrada(leitura, ctr, mont, pares, 13)
    assert leitura["corpos"][entrada].nome.startswith("peca_b")   # quem tem o pino
    alvos = [[x] for x in np.linspace(0, 2 * math.pi, 181)]
    traj, _ = P.trajetoria(mont, {"entrada": {entrada: 1.0}}, pares, alvos, np.zeros(mont.nq))
    assert max(i["residuo"] for _, i in traj) < 1e-9
    o = O.genebra_classico(mont, traj, pares[0], ctr, r["assinatura"])
    assert abs(o["avanco_por_volta_graus"] - 360.0 / n) < 1e-6
    # repouso amostrado em 181 quadros: resolução de 1/180 de volta
    assert abs(o["fracao_repouso"] - o["fracao_repouso_esperada"]) <= 2 / 181
    assert o["relacao_engate_erro_max_graus"] < 1e-9
    inter = O.interferencia_brep(leitura, mont, [q for q, _ in traj], range(0, 181, 12))
    assert inter["pior"]["volume_mm3"] < 1e-6      # projeto sintético com folga: zero interferência


def test_pecas_fora_de_posicao_nao_formam_par(tmp_path, classes):
    r, _, _ = _pipeline_local(genebra_step(tmp_path, 4, deslocar=(150, 30)), classes)
    assert r["estagio"] == "PARES" and r["motivo"] == "NENHUM_PAR_PINO_RASGO"


def test_folga_excessiva_nao_e_rasgo_do_pino(tmp_path, classes):
    r, _, _ = _pipeline_local(genebra_step(tmp_path, 4, folga=3.0), classes)
    assert r["estagio"] == "PARES"


def test_entrada_nao_ortogonal_reprova_assinatura(tmp_path, classes):
    r, _, _ = _pipeline_local(genebra_step(tmp_path, 4, c_fator=0.97), classes)
    assert r["estagio"] == "ASSINATURA_DA_CLASSE" and r["motivo"] == "ASSINATURA_FORA_DA_TOLERANCIA"


def test_licencas_gratuito_nao_e_comercial():
    assert Fo.classificar_licenca("")["classe"] == "sem_licenca"
    nc = Fo.classificar_licenca("Attribution-NonCommercial 4.0 International https://creativecommons.org/licenses/by-nc/4.0/")
    assert nc["classe"] == "nao_comercial" and nc["uso_comercial"] == "PROIBIDO"
    sa = Fo.classificar_licenca("Attribution-ShareAlike 4.0 creativecommons.org/licenses/by-sa/4.0")
    assert sa["classe"] == "reciproca"
    mit = Fo.classificar_licenca("MIT License\nPermission is hereby granted, free of charge, to any person")
    assert mit["spdx"] == "MIT" and "interpretação" in mit["nota"]
    assert Fo.classificar_licenca("Todos os direitos reservados")["classe"] == "sem_licenca"
    assert Fo.triagem(dict(licenca=nc, arquivos=[dict(tipo="STEP")], identidade_textual=dict(pontuacao=1)))[1] \
        == "LICENCA_NAO_COMERCIAL"


def test_unidade_do_arquivo():
    assert B.unidade_comprimento("SI_UNIT(.MILLI.,.METRE.) SI_UNIT($,.METRE.)")["fator_metro"] == 1e-3
    assert B.unidade_comprimento("CONVERSION_BASED_UNIT('INCH',#5)")["fator_metro"] == 0.0254
    with pytest.raises(ValueError, match="UNIDADE_AMBIGUA"):
        B.unidade_comprimento("SI_UNIT(.MILLI.,.METRE.) SI_UNIT(.CENTI.,.METRE.)")


def test_terceiros_por_nome_de_produto():
    for nome in ("M3x10 - 91290A115", "W684AX50ZZ Ball", "EBM-Papst 255 H", "CUI DEVICES AMT encoder"):
        assert Fo.TERCEIRO.search(nome), nome
    for nome in ("Star wheel", "Rotor (R = 4.15 - N = 12)", "Output shaft v126"):
        assert not Fo.TERCEIRO.search(nome), nome


def test_classe_pela_consulta(classes):
    assert O.classe_da_consulta("geneva mechanism CAD", classes) == "genebra"
    assert O.classe_da_consulta("cycloidal drive CAD", classes) == "cicloidal"
    assert O.classe_da_consulta("turbina eólica", classes) is None


def test_sem_nome_de_equipamento_ou_fonte_no_codigo():
    proibidos = re.compile(r"ajahidny|geez0x1|sakethgg|promakina|bhimanimahatale|star wheel|drive wheel", re.I)
    for m in ("brep_e35", "inferencia_e35", "pares_e35", "fontes_e35", "oraculos_e35", "pipeline_e35"):
        texto = Path(f"src/v4/formatos/{m}.py").read_text()
        assert not proibidos.search(texto), m
