"""F8 — prova da ponte entre arquivo vetorial, direitos, hash e montagem F7."""
from __future__ import annotations

import copy
import io
import json
from pathlib import Path

import cairosvg
import pytest
from PIL import Image, ImageChops, ImageStat

from src.v4.formatos import (
    pecas_visuais_f8 as V,
    compositor_cinematico_parametrico_2d as M,
)

ROOT = Path(__file__).resolve().parents[1]
SCENE = ROOT / "src/v4/formatos/cenas_parametricas/biela_manivela_curso_curto.json"
REF = {"cylinder": "cylinder_shell_f8"}


def _scene():
    return M.carregar(SCENE)


def _img(svg):
    with Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode("utf8")))) as im:
        return im.convert("RGB").copy()


def _tmp_reference(monkeypatch, tmp_path):
    manifest = json.loads(V.MANIFEST.read_text("utf8"))
    src = V.ROOT / "cylinder_shell_f8.svg"
    tmp = tmp_path / "refs"
    tmp.mkdir()
    (tmp / src.name).write_bytes(src.read_bytes())
    (tmp / "manifesto.json").write_text(json.dumps(manifest), encoding="utf8")
    monkeypatch.setattr(V, "ROOT", tmp)
    monkeypatch.setattr(V, "MANIFEST", tmp / "manifesto.json")
    return tmp, manifest


def test_gates_do_asset_com_hash_proveniencia_e_ancoras():
    data = V._catalogo()
    assert len(data) == 1
    ref = data["cylinder_shell_f8"]
    assert ref["origin"]["kind"] == "desenho_autoral_interno"
    assert ref["origin"]["external_pixels_copied"] is False
    assert ref["origin"]["identity_match_verified"] is False
    assert ref["rights"]["publication_allowed"] is False
    assert V.validar_pecas(REF) == REF
    assert V.validar_pecas(None) == {}
    markup = V.desenhar_cilindro(REF, 230, 340, 160, 320)
    assert 'data-f8-reference="cylinder_shell_f8"' in markup
    assert 'data-visual-identity="PENDENTE"' in markup
    assert "<rect" in markup
    assert "scale(" in markup


@pytest.mark.parametrize("invalid", [
    {"flywheel": "cylinder_shell_f8"},
    {"cylinder": "not_registered"},
    {"cylinder": "cylinder_shell_f8", "motor_pulley": "cylinder_shell_f8"},
    ["cylinder_shell_f8"],
    "cylinder_shell_f8",
])
def test_pecas_desconhecidas_bloqueiam_sem_fallback(invalid):
    with pytest.raises(ValueError, match="F8-REFERENCIA-SELECAO"):
        V.validar_pecas(invalid)


def test_svg_externo_perigoso_e_texto_ativo_rejeitados():
    original = (V.ROOT / "cylinder_shell_f8.svg").read_bytes()
    malicious = [
        original.replace(b"<rect ", b'<rect onload="alert(1)" ', 1),
        original.replace(b"<rect ", b'<rect style="fill:url(https://evil)" ', 1),
        original.replace(b"</svg>", b'<foreignObject width="10" height="10"/></svg>'),
        original.replace(b"</svg>", b'<image href="https://evil/pixel"/></svg>'),
        b"<!DOCTYPE svg [<!ENTITY xxe SYSTEM 'file:///tmp/a'>]>" + original,
        original.replace(b'fill="#456F85"', b'fill="url(#filter)"'),
        original.replace(b'viewBox="0 0 160 340"', b'viewBox="0 0 900 340"'),
    ]
    for raw in malicious:
        with pytest.raises(ValueError, match="F8-REFERENCIA-"):
            V._sanitizar(raw)


def test_adulteracao_arquivo_hash_e_direitos_bloqueia(monkeypatch, tmp_path):
    directory, manifest = _tmp_reference(monkeypatch, tmp_path)
    path = directory / "cylinder_shell_f8.svg"
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="F8-REFERENCIA-SHA"):
        V.validar_pecas(REF)
    path.write_bytes((Path(__file__).resolve().parents[1] /
        "src/v4/formatos/referencias_visuais_f8/cylinder_shell_f8.svg").read_bytes())
    for key, value in [
        ("origin", {"kind": "importado_da_web", "author": "?"}),
        ("rights", {"publication_allowed": True}),
    ]:
        altered = copy.deepcopy(manifest)
        altered["entries"][0][key] = value
        (directory / "manifesto.json").write_text(json.dumps(altered), encoding="utf8")
        with pytest.raises(ValueError, match="F8-REFERENCIA-PROVENIENCIA"):
            V.validar_pecas(REF)


def test_f7_default_preservado_e_f8_substitui_apenas_carcaca():
    scene = _scene()
    old = M.frame_svg(scene, 2.2)
    with_part = copy.deepcopy(scene)
    with_part["visual_parts"] = REF
    M.validar(with_part)
    new = M.frame_svg(with_part, 2.2)
    assert new != old
    assert "data-f8-reference" not in old
    assert 'data-f8-reference="cylinder_shell_f8"' in new
    assert all(f'id="role-{actor}"' in new for actor in M.ACTORS)
    assert old.count('data-visual-identity="PENDENTE"') == 6
    assert new.count('data-visual-identity="PENDENTE"') == 7
    assert 'id="machine-stage" transform="' in new
    a, b = _img(old), _img(new)
    assert a.size == b.size == (540, 960)
    physical = ImageChops.difference(a.crop((210, 332, 418, 680)),
                                     b.crop((210, 332, 418, 680)))
    assert sum(ImageStat.Stat(physical).mean)/3 > 0.3
    # Header, captions and footer remain pixel identical.
    for region in ((0, 0, 540, 207), (0, 910, 540, 960)):
        assert ImageChops.difference(a.crop(region), b.crop(region)).getbbox() is None


def test_referencia_nao_muda_cinematica_nem_camera():
    scene = _scene()
    custom = copy.deepcopy(scene)
    custom["visual_parts"] = REF
    for t in (0.1, 2.3, 4.6, 7.9):
        s0 = M.estado(scene, t)
        s1 = M.estado(custom, t)
        assert s0["rig"] == s1["rig"]
        assert s0["motor_angle_rad"] == s1["motor_angle_rad"]
        assert M.frame_svg(custom, t).count("data-f8-reference") == 1
    assert custom["publish"] is False and custom["visual_approval"] is False


def test_cena_nao_pode_publicar_ou_selecionar_referencia_enganosa():
    scene = _scene()
    scene["visual_parts"] = {"cylinder": "cylinder_shell_f8"}
    scene["publish"] = True
    with pytest.raises(ValueError, match="F-COMP-MEC-NAO-HOMOLOGADO"):
        M.validar(scene)
    scene["publish"] = False
    scene["visual_parts"] = {"flywheel": "cylinder_shell_f8"}
    with pytest.raises(ValueError, match="F8-REFERENCIA-SELECAO"):
        M.validar(scene)
