"""E41 — agrupamento rígido, suportes, rolamentos e pares superiores.

Montagens sintéticas com relações CONHECIDAS por construção (fixtures_e41).
Nenhuma fonte externa: o benchmark real (cicloidal da E35) roda no workflow.
"""
import math
import re
import sys
from pathlib import Path

import numpy as np
import pytest

cq = pytest.importorskip("cadquery")
sys.path.insert(0, str(Path(__file__).parent))
from fixtures_e41 import disco_lobulado, eixo_em_mancais, placas_dois_pinos  # noqa: E402

from src.v4.formatos import brep_e35 as B  # noqa: E402
from src.v4.formatos import inferencia_e35 as I  # noqa: E402
from src.v4.formatos import lobulos_e41 as LB  # noqa: E402
from src.v4.formatos import transmissao_e41 as TR  # noqa: E402
from src.v4.formatos import vinculos_e41 as V  # noqa: E402


def _nomes(L, ids):
    return sorted(L["corpos"][i].nome for i in ids)


def test_eixo_em_mancais_grupo_rigido_por_fixador_e_rolamentos(tmp_path):
    L = B.ler(eixo_em_mancais(tmp_path), tesselar=False)
    an = V.analisar(L)
    rigidos = [m for m in an["grupos"].values() if len(m) > 1]
    assert [_nomes(L, m) for m in rigidos] == [["eixo", "flange", "parafuso_0", "parafuso_1"]]
    assert len(an["rolamentos"]) == 2 and all(r["residuo_circulo_mm"] < 1e-9 for r in an["rolamentos"])
    tipos = sorted({j["tipo"] for j in an["juntas"]})
    assert tipos == ["ajuste", "rolamento"]
    assert an["sem_vinculo"] == []
    # o eixo com colar encostado no flange NÃO é fixador (ajuste nominal, sem rosca)
    assert any(L["corpos"][p["corpo"]].nome == "eixo" for p in an["possiveis_fixadores"])


def test_dois_pinos_rigidez_derivada_um_pino_nao(tmp_path):
    L = B.ler(placas_dois_pinos(tmp_path, pinos=2, apoio_solto=True, coaxial_com_folga=True), tesselar=False)
    an = V.analisar(L)
    assert [_nomes(L, m) for m in an["grupos"].values() if len(m) > 1] == [["base", "topo"]]
    assert any(r["tipo"] == "sem_movimento_relativo" for r in an["rigidas"])
    assert _nomes(L, an["sem_vinculo"]) == ["apoiado", "coaxial_solto"]   # contato/coaxialidade ≠ vínculo
    L1 = B.ler(placas_dois_pinos(tmp_path, pinos=1), tesselar=False)
    an1 = V.analisar(L1)
    assert all(len(m) == 1 for m in an1["grupos"].values())              # um eixo só: placas giram


def test_poda_prefere_rolamento_e_linha_angular(tmp_path):
    L = B.ler(eixo_em_mancais(tmp_path), tesselar=False)
    an = V.analisar(L)
    uf = V.uniao_de(an)
    base = next(i for i, c in enumerate(L["corpos"]) if c.nome == "carcaca")
    eixo = next(i for i, c in enumerate(L["corpos"]) if c.nome == "eixo")
    mont0, idx, _, uf = TR.montar(L, an, base)
    mont, livres, cong = TR.podar(mont0, [idx[uf.achar(eixo)]])
    assert len(livres) == 1 and livres[0].startswith("rolamento") and cong
    d = np.array([0, 0, 1.0])
    r = TR.linha_angular(mont, idx[uf.achar(eixo)], d)
    traj, _ = TR.trajetoria(mont, r, np.zeros((0, mont.nq)), [0.0, 1.0, 2.0])
    assert abs(r @ traj[-1][0] - 2.0) < 1e-9 and traj[-1][1]["mobilidade"] == 0


@pytest.mark.parametrize("falso,fase,aceito", [(False, 0.0, True), (False, math.pi / 9, False),
                                               (True, 0.0, False), (True, math.pi / 9, False)])
def test_par_lobulado_so_aceita_perfil_conjugado(tmp_path, falso, fase, aceito):
    f = disco_lobulado(tmp_path, falso=falso, fase=fase)
    L = B.ler(f, tesselar=False)
    C = L["corpos"]
    conj = next(c for c in LB.conjuntos_cilindricos(C) if c["n"] == 10)
    k = next(i for i, c in enumerate(C) if c.nome.startswith("disco"))
    r = LB.par_lobulado(B.solidos(f, [k])[k], I.eixo_proprio(C[k]), conj, 72)
    assert r["lobulos"] == 9 and abs(r["razao_derivada"] + 1 / 9) < 1e-12
    assert r["aceito"] is aceito
    if aceito:
        assert r["teste_razao_derivada"]["penetracao_max_mm"] <= LB.PEN_MAX
        assert all(a["penetracao_max_mm"] > 10 * LB.PEN_MAX for a in r["alternativas"])


def test_criterios_nao_flexibilizados():
    assert LB.PEN_MAX == 0.02 and LB.FOLGA_CONTATO == 0.25
    assert V.TOL_AJUSTE == 0.05 and V.TOL_EIXO == 0.02


def test_sem_nome_de_equipamento_no_codigo_e41():
    proibidos = re.compile(r"geez0x1|cycloid|cicloid|rotor|w684|kaydon|6705|robotiq|geneva", re.I)
    for m in ("vinculos_e41", "lobulos_e41", "transmissao_e41"):
        assert not proibidos.search(Path(f"src/v4/formatos/{m}.py").read_text()), m
