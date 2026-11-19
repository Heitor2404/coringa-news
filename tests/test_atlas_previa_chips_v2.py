"""Ponte editorial: o primeiro roteiro chips V2 deve resolver tempos e layouts OFFLINE.
Nao confunde teste sintetico de tempo com audio aprovado; Gemini só no workflow privado.
"""
import json
import re
from pathlib import Path

from src.v4.formatos import plano as P

RAIZ = Path(__file__).resolve().parents[1]
ARQ = RAIZ / "src/v4/formatos/planos/reuso/atlas_chips_v2_prova_25s.json"


def _palavras(texto):
    texto = re.findall(r"[\wÀ-ÿº]+", texto)
    return [{"w": x.upper(), "s": round(i / 2.55, 3), "e": round((i + 1) / 2.55, 3)}
            for i, x in enumerate(texto)]


def test_tempo_sintetico_e_contracto_chips_v2():
    pl = json.loads(ARQ.read_text(encoding="utf-8"))
    assert pl["abertura_tipo"] == "prova_real"
    assert pl["beats"][0]["composicao"] == "atlas.prova"
    assert pl["narracao"]["texto"].lower().count("noventa") == 0
    pal = _palavras(pl["narracao"]["texto"])
    resolvido = P.resolver_tempos(pl, pal)
    assert 20 <= resolvido["duracao"] <= 30
    assert resolvido["beats"][0]["camadas"][0]["p"]["rotulo_t"] < 3
    assert all(isinstance(L["t0"], (int, float)) for b in resolvido["beats"] for L in b["camadas"])
    erros = [v for v in P.validar(resolvido) if v["gravidade"] == "erro"]
    if erros:
        print("ATLAS_V2_VALIDATION_ERRORS=" + json.dumps(erros, ensure_ascii=False))
    assert not erros, erros[:30]


def test_fotos_chips_vem_do_catalogo_com_hash_real():
    pl = json.loads(ARQ.read_text(encoding="utf-8"))
    refs = [x["p"]["asset"] for b in pl["beats"] for x in b["camadas"]
            if x["componente"] == "atlas.provaVisual"]
    bib = json.loads((RAIZ / "src/v4/biblioteca_comprovada.json").read_text(encoding="utf-8"))
    by_id = {x["id"]: x for x in bib["itens"]}
    assert len(refs) == 2 and len(set(refs)) == 2
    for x in refs:
        reg = by_id[x]
        assert reg["licenca"] == "CC BY 4.0"
        assert len(reg["sha256_origem"]) == 64
        assert reg["prova"]["midia_corresponde"] is True
        assert reg["prova"]["confirmacao_humana"] is None
    assert "não mostra produção interna" in by_id[refs[0]]["mostra"]
    assert "sem identificação" in by_id[refs[1]]["mostra"]
