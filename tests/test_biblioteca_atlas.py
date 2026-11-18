"""Contrato offline da biblioteca ATLAS: referências reais, sem tocar no render."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "src/v4/formatos/biblioteca_atlas/catalogo.json"
CAT = json.loads(BASE.read_text(encoding="utf-8"))
FMT = json.loads((ROOT / CAT["fontes"]["composicoes"]).read_text(encoding="utf-8"))
MIDIAS = json.loads((ROOT / CAT["fontes"]["midias"]).read_text(encoding="utf-8"))
RASTER_ROOT = ROOT / CAT["fontes"]["rasters"]


def test_catalogo_nao_e_producao_nem_duplica_midias():
    assert CAT["formato"] == "atlas"
    assert CAT["status"] == "prototipo_nao_ativo"
    assert "itens" not in CAT["acervo"]
    assert CAT["acervo"]["confirmados_com_metadados"] == len(MIDIAS["itens"])
    assert all(a.get("id") and a.get("licenca") and a.get("credito") and a.get("mostra")
               for a in MIDIAS["itens"])


def test_todas_as_bases_cartograficas_existem_e_tem_licenca():
    ids = set()
    for item in CAT["cartografia"]:
        assert item["id"] not in ids
        ids.add(item["id"])
        name = item["raster"]
        info = json.loads((RASTER_ROOT / f"{name}.json").read_text(encoding="utf-8"))
        assert info["nome"] == name
        assert (RASTER_ROOT / info["arquivo"]).is_file()
        assert info["sha256"] and info.get("atribuicao")
        assert info.get("fonte", {}).get("licenca") or info.get("dataset") == "ne2_raster"


def test_composicoes_e_movimentos_ja_autorizados():
    atlas = FMT["formatos"]["atlas"]
    for item in CAT["composicoes"]:
        ref = item["ref"]
        assert ref.startswith("atlas.")
        assert ref in FMT["composicoes"]
        assert FMT["composicoes"][ref]["formato"] == "atlas"
    for item in CAT["movimentos"]:
        base = item["base"]
        assert base in ("rotas", "destaques") or base in atlas["componentes"] or base in atlas["clipes"]


def test_pacotes_nao_sao_aprovados_por_antecipacao():
    mapas = {x["id"] for x in CAT["cartografia"]}
    comp = {x["id"] for x in CAT["composicoes"]}
    for tema in CAT["pacotes_tematicos"]:
        assert not tema["usar_em_producao"], f"{tema['id']} não foi homologado"
        assert set(tema["mapas"]) <= mapas
        assert set(tema["composicoes"]) <= comp
        if tema.get("base"):
            assert (ROOT / tema["base"]).is_file()
        assert tema.get("pendencias"), "tema sem necessidades de validação"


def test_biblioteca_nao_importada_no_motor_atlas():
    for p in (ROOT / "src/v4/formatos").glob("*.py"):
        assert "biblioteca_atlas" not in p.read_text(encoding="utf-8"), p
