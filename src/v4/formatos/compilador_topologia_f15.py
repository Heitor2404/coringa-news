"""F15 — compilador de topologia para os DOIS núcleos mecânicos do LAB.

Não é classificador de texto, LLM, VLM, pesquisa de imagem nem CAD.
Seleciona UMA família por isomorfismo exato de grafo tipado, com nomes de
atores arbitrários; verifica fonte de física e lista exata de eventos
executáveis; constrói cena PARAMÉTRICA validada pelo compositor original.
Papel novo, borda extra, física desconhecida ou autorização falsa => BLOQUEIO.
Produção e catalogo_mecanismos.py não são usados/alterados.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
import re
from pathlib import Path

from src.v4.formatos import compositor_cinematico_parametrico_2d as CRANK
from src.v4.formatos import compositor_engrenagens_f14 as GEARS

SCHEMA = "coringa-topology-request-f15-v1"
PLAN_SCHEMA = "coringa-topology-compiled-f15-v1"
SCENES = Path(__file__).with_name("cenas_parametricas")
IDENT = re.compile(r"^[a-z][a-z0-9_]{0,39}$")
NODE_KINDS = frozenset(("rotor", "belt", "rod", "piston", "chamber", "spur_gear"))
LINK_KINDS = frozenset(("drives", "transmits_to", "hinged_to", "slides_in", "meshes_with"))

REGISTRY = {
    "slider_crank_parametrico": {
        "roles": {
            "motor_pulley":"rotor", "drive_belt":"belt", "flywheel":"rotor",
            "connecting_rod":"rod", "piston":"piston", "cylinder":"chamber",
        },
        "edges": (
            ("motor_pulley","drive_belt","drives"),
            ("drive_belt","flywheel","transmits_to"),
            ("flywheel","connecting_rod","hinged_to"),
            ("connecting_rod","piston","hinged_to"),
            ("piston","cylinder","slides_in"),
        ),
        "events": ("curso_descendente","curso_ascendente"),
        "params":frozenset(("crank_radius_px","rod_length_px",
                            "wheel_radius_px","motor_pulley_radius_px")),
        "source":{
            "type":"internal_kernel",
            "locator":"src/v4/formatos/cinematica_biela_manivela.py",
            "external_pixels_copied":False,
            "source_is_image_license":False,
        },
        "baseline":"biela_manivela_curso_curto.json",
        "renderer":"compositor_cinematico_parametrico_2d",
    },
    "external_spur_gear_reduction": {
        "roles":{"input_gear":"spur_gear","output_gear":"spur_gear"},
        "edges":(("input_gear","output_gear","meshes_with"),),
        "events":("engagement","reduction"),
        "params":frozenset(("z_input","z_output","module_px",
                            "input_x_px","center_y_px","driver_revolutions")),
        "source":{
            "type":"technical_equations",
            "locator":"https://khkgears.net/new/gear_knowledge/gear_technical_reference/calculation_gear_dimensions.html",
            "external_pixels_copied":False,
            "source_is_image_license":False,
        },
        "baseline":"redutor_engrenagens_18x36.json",
        "renderer":"compositor_engrenagens_f14",
    },
}

def blocked(code):
    raise ValueError("F15-BLOQUEADO-"+code)

def valid_id(value):
    if not isinstance(value,str) or not IDENT.fullmatch(value):
        blocked("ID")
    return value

def valid_text(value):
    if (not isinstance(value,str) or not 4<=len(value)<=62
            or any(x in value for x in "<>&\n\r")):
        blocked("TEXTO")
    return value

def number(value,lo,hi):
    import math
    if type(value) not in (int,float) or not math.isfinite(value) or not lo<=value<=hi:
        blocked("PARAMETRO")
    return value

def _validate_request(request):
    if not isinstance(request,dict) or set(request)!={
       "schema","id","title","subtitle","graph","required_events",
       "parameters","evidence","publish","visual_approval",
    } or request["schema"]!=SCHEMA or request["publish"] is not False or request["visual_approval"] is not False:
        blocked("CONTRATO")
    valid_id(request["id"]); valid_text(request["title"]); valid_text(request["subtitle"])
    graph=request["graph"]
    if not isinstance(graph,dict) or set(graph)!={"nodes","edges"}:
        blocked("GRAFO")
    nodes,edges=graph["nodes"],graph["edges"]
    if (not isinstance(nodes,list) or not 2<=len(nodes)<=12 or
        not isinstance(edges,list) or not 1<=len(edges)<=24):
        blocked("GRAFO")
    by={}
    for node in nodes:
        if not isinstance(node,dict) or set(node)!={"id","kind"}:
            blocked("NO")
        node_id=valid_id(node["id"])
        if node_id in by or node["kind"] not in NODE_KINDS:
            blocked("NO_DUPLICADO_OU_DESCONHECIDO")
        by[node_id]=node["kind"]
    actual=[]
    for edge in edges:
        if not isinstance(edge,dict) or set(edge)!={"from","to","joint"}:
            blocked("ARESTAS")
        src,dst,joint=edge["from"],edge["to"],edge["joint"]
        if src not in by or dst not in by or src==dst or joint not in LINK_KINDS:
            blocked("ARESTA_INVALIDA")
        actual.append((src,dst,joint))
    if len(actual)!=len(set(actual)):
        blocked("ARESTA_DUPLICADA")
    events=request["required_events"]
    if (not isinstance(events,list) or not 1<=len(events)<=8 or
        any(not isinstance(x,str) or not IDENT.fullmatch(x) for x in events)
        or len(events)!=len(set(events))):
        blocked("EVENTOS")
    if not isinstance(request["parameters"],dict) or not isinstance(request["evidence"],dict):
        blocked("PARAMETROS_OU_FONTE")
    return by,set(actual)

def _match_family(by,actual,record):
    roles=record["roles"]
    if len(by)!=len(roles) or sorted(by.values())!=sorted(roles.values()):
        return []
    # Isomorfismo tipado exato, determinístico, jamais pontuação textual.
    role_ids=tuple(roles)
    candidates=[[node for node,kind in by.items() if kind==roles[role]]
                for role in role_ids]
    solutions=[]
    for permutation in itertools.product(*candidates):
        if len(set(permutation))!=len(permutation):
            continue
        mapping=dict(zip(role_ids,permutation))
        expected={(mapping[src],mapping[dst],joint) for src,dst,joint in record["edges"]}
        if expected==actual:
            solutions.append(mapping)
    return solutions

def identify(request):
    """Sem fallback ao primeiro modelo; prova do grafo EXATO."""
    by,actual=_validate_request(request)
    matches=[]
    for family,record in REGISTRY.items():
        for roles in _match_family(by,actual,record):
            matches.append((family,record,roles))
    if not matches:
        blocked("TOPOLOGIA_NAO_SUPORTADA")
    if len(matches)!=1:
        blocked("TOPOLOGIA_AMBIGUA")
    family,record,roles=matches[0]
    if request["required_events"]!=list(record["events"]):
        blocked("EVENTOS_NAO_IMPLEMENTADOS")
    if set(request["parameters"])!=record["params"]:
        blocked("PARAMETROS_NAO_DISPONIVEIS")
    if request["evidence"]!=record["source"]:
        blocked("FONTE_NAO_VERIFICADA_OU_DIREITOS")
    return family,record,roles

def compile_request(request):
    family,record,roles=identify(request)
    # Base curada só fornece aparência, cronologia e contratos editoriais.
    # Números de DINÂMICA do pedido substituem a base, validados pelo kernel.
    if family=="slider_crank_parametrico":
        original=CRANK.carregar(SCENES/record["baseline"])
        scene=copy.deepcopy(original)
        p=request["parameters"]
        scene["crank"]["radius"]=number(p["crank_radius_px"],20,85)
        scene["crank"]["rod"]=number(p["rod_length_px"],115,280)
        scene["crank"]["wheel"]=number(p["wheel_radius_px"],55,94)
        scene["motor"]["pulley"]=number(p["motor_pulley_radius_px"],21,40)
        scene["visual_parts"]=None
        scene["id"]=request["id"]
        scene["title"]=request["title"]
        scene["subtitle"]=request["subtitle"]
        CRANK.validar(scene)
        # A fase real está no kernel; essa montagem não "aprende" roteiro livre.
        preview=CRANK.frame_svg(scene,2.6,transmissao_animada=True,
                              enquadramento_mobile="hero_lateral_f13")
        if 'id="role-piston"' not in preview:
            blocked("ATOR_NAO_RENDERIZAVEL")
    else:
        original=GEARS.load(SCENES/record["baseline"])
        scene=copy.deepcopy(original)
        p=request["parameters"]
        for key in ("z_input","z_output","driver_revolutions"):
            if type(p[key]) is not int:
                blocked("PARAMETRO_INTEIRO")
        scene["gears"]={
            "z1":p["z_input"],
            "z2":p["z_output"],
            "module":number(p["module_px"],3,7),
            "input_x":number(p["input_x_px"],100,235),
            "center_y":number(p["center_y_px"],350,650),
        }
        scene["driver_revolutions"]=p["driver_revolutions"]
        scene["id"]=request["id"]
        scene["title"]=request["title"]
        scene["subtitle"]=request["subtitle"]
        GEARS.validate(scene)
        if 'id="role-input_gear"' not in GEARS.frame(scene,2.6):
            blocked("ATOR_NAO_RENDERIZAVEL")
    if scene["publish"] is not False or scene["visual_approval"] is not False:
        blocked("PUBLICACAO")
    # Nunca incluir um "aprovado industrial" inventado no plano.
    canonical=json.dumps(request,sort_keys=True,ensure_ascii=False,separators=(",",":"))
    return {
        "schema":PLAN_SCHEMA,
        "status":"TOPOLOGIA_VALIDADA_RENDER_PRIVADO_POSSIVEL",
        "compiled_family":family,
        "renderer":record["renderer"],
        "role_binding":roles,
        "graph_sha256":hashlib.sha256(canonical.encode("utf8")).hexdigest(),
        "required_events":list(record["events"]),
        "physics_evidence":record["source"],
        "scene":scene,
        "selected_by":"ISOMORFISMO_GRAFO_TIPADO_EXATO",
        "title_used_for_dispatch":False,
        "external_visual_reference_downloaded":False,
        "industrial_identity_verified":False,
        "media_license_verified":False,
        "visual_approval":False,
        "publish":False,
    }

def load_request(path):
    p=Path(path)
    if p.suffix!=".json" or not p.is_file() or p.stat().st_size>25_000:
        blocked("ARQUIVO")
    try:
        req=json.loads(p.read_text("utf8"))
    except (UnicodeError,ValueError):
        blocked("JSON")
    _validate_request(req)
    return req

def render_private(request,output,plan=None):
    plan=compile_request(request) if plan is None else compile_request(request)
    scene=plan["scene"]
    output=Path(output)
    if plan["compiled_family"]=="slider_crank_parametrico":
        record=CRANK.renderizar(scene,output,transmissao_animada=True,
                               enquadramento_mobile="hero_lateral_f13")
    else:
        record=GEARS.render(scene,output)
    if record.get("publish") is not False:
        blocked("PUBLICACAO_RENDER")
    return {"family":plan["compiled_family"],"video_sha256":record["sha256"],
            "publish":False,"visual_approval":False}

def main(argv=None):
    parser=argparse.ArgumentParser(description="LAB F15 — decidir pela topologia; render privado opcional")
    parser.add_argument("request",type=Path)
    parser.add_argument("--plan",type=Path,required=True)
    parser.add_argument("--render",type=Path)
    args=parser.parse_args(argv)
    req=load_request(args.request)
    plan=compile_request(req)
    args.plan.parent.mkdir(parents=True,exist_ok=True)
    args.plan.write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding="utf8")
    if args.render:
        render_private(req,args.render,plan)
    print(json.dumps({"status":plan["status"],"family":plan["compiled_family"],
                      "rendered":bool(args.render),"published":False},ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
