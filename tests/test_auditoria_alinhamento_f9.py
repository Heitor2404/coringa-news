"""F9b — não chamar sobreposição de papéis de visão computacional."""
import copy
import json
from xml.etree import ElementTree as ET

import pytest

from src.v4.formatos import referencia_evidencia_f9 as REF
from src.v4.formatos import auditoria_alinhamento_f9 as QA
from src.v4.formatos import render_compressor_conjunto_2d as COMP


def fixture():
    ref=REF.carregar()
    assembly=json.loads(COMP.MANIFESTO_PADRAO.read_text("utf8"))
    svg=COMP.frame_svg(.33,assembly)
    return ref,assembly,svg


def test_referencia_e_motor_sao_escopos_distintos():
    ref, assembly,svg=fixture()
    report=QA.auditar(ref,assembly,svg)
    names={x["referencia_papel"] for x in report["structural_roles_present_not_visual_certified"]}
    assert names=={
        "receiver_horizontal","electric_motor","compressor_head",
        "intake_filter","discharge_pipe","tank_pressure_gauge"}
    assert {x["referencia_papel"] for x in report["variant_specific_absent"]}=={
        "belt_guard","wheel"}
    assert report["declared_actor_overlap"]==6
    assert report["source_image_imported"] is False
    assert report["external_image_identity_verified"] is False
    assert report["industrial_visual_homologated"] is False
    assert report["publication_allowed"] is False
    assert report["comparable_variant"] is False


def test_ocultacao_da_correia_na_referencia_nao_prova_cinematica():
    ref,assembly,svg=fixture()
    hidden=QA.auditar(ref,assembly,svg)["hidden_in_reference"]
    assert any(x["referencia_papel"]=="drive_belt" and
               x["motor_papel_presente"] and
               not x["observavel_na_referencia"] and
               not x["prova_de_movimento_pelo_desenho"] for x in hidden)


def test_role_faltante_ou_svg_alterado_reprova():
    ref,assembly,svg=fixture()
    removed=svg.replace('id="role-receiver_horizontal"','id="removed_receiver_horizontal"')
    with pytest.raises(ValueError,match="F9-ATOR-GEOMETRIA-AUSENTE"):
        QA.auditar(ref,assembly,removed)
    duplicate=svg.replace('id="role-electric_motor"','id="role-receiver_horizontal"')
    with pytest.raises(ValueError,match="F9-ATOR-DUPLICADO"):
        QA.auditar(ref,assembly,duplicate)
    with pytest.raises(ValueError,match="F9-SVG-NAO-RENDERIZADO"):
        QA.auditar(ref,assembly,"<svg>")


def test_criar_quadros_reais_sem_licenca_externa(tmp_path):
    _,assembly,_=fixture()
    file=QA.prancha(assembly,tmp_path)
    assert file.is_file()
    from PIL import Image
    with Image.open(file) as im:
        assert im.size==(1080,2040)
    assert "SEM_REFERENCIA_EXTERNA" in file.name
