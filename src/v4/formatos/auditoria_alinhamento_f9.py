"""F9b — auditoria estrutural de correspondência, NÃO comparação visual por VLM.

Compara atores declarados na referência de outro AUTOR com os papéis no
SVG real do compressor existente. Distingue presença estrutural, papel
oculto e diferença de VARIANTE. Não converte arte externa em geometria.
"""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import cairosvg
from PIL import Image, ImageDraw, ImageFont

from src.v4.formatos import referencia_evidencia_f9 as REF
from src.v4.formatos import render_compressor_conjunto_2d as COMP

# Apenas equivalências SEMÂNTICAS. Sem inferir de pixels da ilustração.
ALIASES = {"tank_pressure_gauge": "receiver_gauge"}
REFERENCE_SPECIFIC = {"belt_guard", "wheel"}
SVG_NS = "{http://www.w3.org/2000/svg}"


def auditar(reference:dict, assembly:dict, svg:str) -> dict:
    REF.validar(reference)
    COMP.validar_plano(assembly)
    try:
        root=ET.fromstring(svg)
    except ET.ParseError as exc:
        raise ValueError("F9-SVG-NAO-RENDERIZADO") from exc
    roles=[n.get("id")[5:] for n in root.iter()
           if n.get("id","").startswith("role-")]
    if len(roles)!=len(set(roles)):
        raise ValueError("F9-ATOR-DUPLICADO")
    actual=set(roles)
    by_role={x["papel"] for x in assembly["pecas"]}
    if not actual.issuperset(by_role):
        raise ValueError("F9-ATOR-GEOMETRIA-AUSENTE")
    supported=[]
    variant=[]
    unknown=[]
    for visible in reference["claims"]["visible_parts"]:
        role=visible["role"]
        target=ALIASES.get(role,role)
        row={"referencia_papel":role,"motor_papel":target,
             "estado":"PAPEL_DECLARADO_NAO_PROVA_SEMELHANCA_VISUAL"}
        if target in actual:
            supported.append(row)
        elif role in REFERENCE_SPECIFIC:
            row["estado"]="VARIANTE_PORTATIL_NAO_PRESENTE_NO_MOTOR_ATUAL"
            variant.append(row)
        else:
            row["estado"]="PAPEL_VISIVEL_NAO_IMPLEMENTADO"
            unknown.append(row)
    hidden=[]
    for role in reference["claims"]["hidden_parts"]:
        hidden.append({
            "referencia_papel":role,
            "observavel_na_referencia":False,
            "motor_papel_presente":role in actual,
            "prova_de_movimento_pelo_desenho":False,
        })
    return {
        "schema":"coringa-f9-align-report-v1",
        "reference_id":reference["id"],
        "reference_type":reference["reference_type"],
        "source_url":reference["source"]["page"],
        "source_image_imported":False,
        "structural_roles_present_not_visual_certified":supported,
        "variant_specific_absent":variant,
        "missing_general_roles":unknown,
        "hidden_in_reference":hidden,
        "candidates_count":len(reference["claims"]["visible_parts"]),
        "declared_actor_overlap":len(supported),
        "comparable_variant":False if variant else None,
        "source_process_type":"portable_single_stage",
        "target_process_type":"workshop_belt_driven_tank_horizontal",
        "external_image_identity_verified":False,
        "physics_derived_from_external_pixels":False,
        "industrial_visual_homologated":False,
        "publication_allowed":False,
        "conclusion":"REVISAO_HUMANA_PENDENTE_DIFERENCAS_DE_VARIANTE",
    }


def prancha(assembly:dict, out:Path):
    """Quatro quadros VERDADEIROS do motor local; não contém imagem externa."""
    COMP.validar_plano(assembly)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    snapshots=[]
    for p in (.03,.27,.61,.94):
        svg=COMP.frame_svg(p,assembly,camera_causal=False,realce_causal=False)
        with Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode()))) as im:
            snapshots.append(im.convert("RGB").copy())
    board=Image.new("RGB",(1080,2040),"#e6f0f4")
    d=ImageDraw.Draw(board)
    for i,photo in enumerate(snapshots):
        board.paste(photo,((i%2)*540,45+(i//2)*960))
    d.rectangle((0,0,1080,44),fill="#123043")
    d.text((24,14),"F9 — QUADROS REAIS DA MAQUINA ATUAL (SEM FONTE EXTERNA)",
           fill="#ffffff",font=REF._fonte(17))
    d.text((24,1985),"Aparencia didatica AUTORAL | Referencia Commons ainda nao incorporada",
           fill="#35566a",font=REF._fonte(17))
    p=out/"MAQUINA_EXISTENTE_4_FASES_SEM_REFERENCIA_EXTERNA.jpg"
    board.save(p,quality=89)
    return p


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--saida",type=Path,required=True)
    args=p.parse_args(argv)
    reference=REF.carregar()
    assembly=json.loads(COMP.MANIFESTO_PADRAO.read_text(encoding="utf8"))
    svg=COMP.frame_svg(.33,assembly,camera_causal=False)
    report=auditar(reference,assembly,svg)
    args.saida.mkdir(parents=True,exist_ok=True)
    prancha(assembly,args.saida)
    (args.saida/"AUDITORIA_SEMANTICA_F9.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
    print(json.dumps(report,ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
