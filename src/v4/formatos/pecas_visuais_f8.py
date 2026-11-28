"""F8 — entrada OPT-IN de peças SVG locais com SHA, autoria e geometria.

Não faz pesquisa nem importa imagem remota. Um desenho interno testável NÃO é
referência visual industrial validada. A estética e a publicação permanecem
bloqueadas até conferência humana e direitos de um asset externo real.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).with_name("referencias_visuais_f8")
MANIFEST = ROOT / "manifesto.json"
NS = "http://www.w3.org/2000/svg"
SHAPES = {"rect", "path", "circle", "line", "ellipse"}
ALLOWED = {
    "rect": {"x", "y", "width", "height", "rx", "ry", "fill", "stroke", "stroke-width", "opacity"},
    "path": {"d", "fill", "stroke", "stroke-width", "stroke-linecap", "stroke-linejoin", "opacity"},
    "circle": {"cx", "cy", "r", "fill", "stroke", "stroke-width", "opacity"},
    "line": {"x1", "y1", "x2", "y2", "stroke", "stroke-width", "stroke-linecap", "opacity"},
    "ellipse": {"cx", "cy", "rx", "ry", "fill", "stroke", "stroke-width", "opacity"},
}
NUMERIC = {"x", "y", "width", "height", "rx", "ry", "cx", "cy", "r",
           "x1", "y1", "x2", "y2", "stroke-width", "opacity"}
COLORS = {"fill", "stroke"}
SHA = re.compile(r"[0-9a-f]{64}\Z")
COLOR = re.compile(r"(?:#[a-fA-F0-9]{6}|none)\Z")
# Somente coordenadas absolutas simples; sem funções CSS, URLs ou extensões.
PATH = re.compile(r"[MLHVZ0-9., +\\-]+\Z")


def fail(msg: str):
    raise ValueError("F8-REFERENCIA-" + msg)


def _num(v, low=0, high=1000):
    if type(v) not in (int, float) or not math.isfinite(v) or not low <= v <= high:
        fail("COORDENADA")
    return float(v)


def _catalogo() -> dict:
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        fail("MANIFESTO")
    if (not isinstance(data, dict) or data.get("schema") != "coringa-visual-references-f8-v1"
            or data.get("publication_approved") is not False
            or data.get("visual_approval") is not False
            or data.get("scope") != "LAB_INTERNO_AUTORAL_SEM_REFERENCIA_INDUSTRIAL_COMPROVADA"
            or not isinstance(data.get("entries"), list)):
        fail("DIREITOS")
    ids = [x.get("id") for x in data["entries"] if isinstance(x, dict)]
    if len(ids) != len(data["entries"]) or len(ids) != len(set(ids)):
        fail("CATALOGO-DUPLICADO")
    return {x["id"]: x for x in data["entries"]}


def _entrada(ref: str, actor: str) -> tuple[dict, bytes]:
    entry = _catalogo().get(ref)
    if not entry or entry.get("actor") != actor or actor != "cylinder":
        fail("ATOR-NAO-CADASTRADO")
    if entry.get("primitive") != "chamber":
        fail("TIPO")
    origin = entry.get("origin")
    rights = entry.get("rights")
    if (not isinstance(origin, dict)
            or origin.get("kind") != "desenho_autoral_interno"
            or not str(origin.get("author") or "").strip()
            or origin.get("external_pixels_copied") is not False
            or origin.get("identity_match_verified") is not False
            or not isinstance(rights, dict)
            or rights.get("status") != "USO_INTERNO_LAB_APENAS"
            or rights.get("external_license_inferred") is not False
            or rights.get("publication_allowed") is not False):
        fail("PROVENIENCIA")
    name = entry.get("asset")
    if (not isinstance(name, str) or not re.fullmatch(r"[a-z0-9_]+\.svg", name)
            or entry.get("sha256") is None or
            not isinstance(entry["sha256"], str) or
            not SHA.fullmatch(entry["sha256"])):
        fail("ARQUIVO")
    file = ROOT / name
    if file.is_symlink() or not file.is_file() or file.stat().st_size > 10000:
        fail("ARQUIVO")
    raw = file.read_bytes()
    if hashlib.sha256(raw).hexdigest() != entry["sha256"]:
        fail("SHA")
    if entry.get("viewbox") != [160, 340] or entry.get("anchors") != {
        "axis_top": [80, 5], "axis_bottom": [80, 336]
    }:
        fail("ANCORAS")
    return entry, raw


def _sanitizar(raw: bytes) -> str:
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper() or len(raw) > 10000:
        fail("SVG-PERIGOSO")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        fail("SVG-XML")
    if (root.tag != "{" + NS + "}svg" or
            set(root.attrib) != {"viewBox", "width", "height"} or
            root.get("viewBox") != "0 0 160 340" or
            root.get("width") != "160" or root.get("height") != "340"):
        fail("SVG-RAIZ")
    if not 1 <= len(root) <= 100 or (root.text or "").strip():
        fail("SVG-CONTEUDO")
    for element in root:
        if not element.tag.startswith("{" + NS + "}"):
            fail("SVG-TAG")
        kind = element.tag[len(NS) + 2:]
        if kind not in SHAPES or len(element) or (element.text or "").strip() or (element.tail or "").strip():
            fail("SVG-TAG")
        if not set(element.attrib).issubset(ALLOWED[kind]):
            fail("SVG-ATRIBUTO")
        for key, value in element.attrib.items():
            if len(value) > 700:
                fail("SVG-VALOR")
            if key in NUMERIC:
                try:
                    number = float(value)
                except ValueError:
                    fail("SVG-NUMERO")
                if not math.isfinite(number) or not 0 <= number <= 1000:
                    fail("SVG-NUMERO")
            elif key in COLORS:
                if not COLOR.fullmatch(value):
                    fail("SVG-COR")
            elif key == "d":
                if not PATH.fullmatch(value):
                    fail("SVG-PATH")
                nums = re.findall(r"(?<![a-zA-Z])(?:\d+(?:\.\d+)?)", value)
                if any(float(n) > 340 for n in nums):
                    fail("SVG-PATH")
            elif key == "stroke-linecap" and value not in ("butt", "round", "square"):
                fail("SVG-TRAÇO")
            elif key == "stroke-linejoin" and value not in ("round", "miter", "bevel"):
                fail("SVG-TRAÇO")
    ET.register_namespace("", NS)
    return "".join(ET.tostring(child, encoding="unicode") for child in root)


def validar_pecas(pieces) -> dict:
    if pieces is None:
        return {}
    if not isinstance(pieces, dict) or set(pieces) not in (set(), {"cylinder"}):
        fail("SELECAO")
    if not pieces:
        return {}
    ref = pieces["cylinder"]
    if ref != "cylinder_shell_f8":
        fail("SELECAO")
    _, raw = _entrada(ref, "cylinder")
    _sanitizar(raw)
    return {"cylinder": ref}


def desenhar_cilindro(pieces, x: float, y: float, width: float, height: float) -> str:
    """Desenha somente a carcaça imóvel no slot, sem tocar no pistão dinâmico.

    Não aceita geometria excedendo o palco do compositor F7.
    """
    chosen = validar_pecas(pieces)
    if "cylinder" not in chosen:
        fail("SEM-SELECAO")
    x, y = _num(x, 0, 540), _num(y, 0, 900)
    width, height = _num(width, 30, 300), _num(height, 30, 450)
    if x + width > 500 or y + height > 835:
        fail("FORA-PALCO")
    _, raw = _entrada(chosen["cylinder"], "cylinder")
    fragment = _sanitizar(raw)
    return (f'<g data-f8-reference="{chosen["cylinder"]}" '
            f'data-visual-identity="PENDENTE" '
            f'transform="translate({x:.4f} {y:.4f}) '
            f'scale({width/160:.7f} {height/340:.7f})">'
            + fragment + "</g>")
