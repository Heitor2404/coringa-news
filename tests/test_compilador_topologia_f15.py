"""F15 — provas de seleção por grafo, sem título, sem render por família inventada."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.v4.formatos import compilador_topologia_f15 as ROUTER
from src.v4.formatos import compositor_cinematico_parametrico_2d as CRANK
from src.v4.formatos import compositor_engrenagens_f14 as GEAR

DIR=Path(__file__).resolve().parents[1]/"src/v4/formatos/pedidos_topologia_f15"


def requests():
    return [ROUTER.load_request(DIR/"pedido_estrutura_biela_f15.json"),
            ROUTER.load_request(DIR/"pedido_estrutura_engrenagens_f15.json")]


@pytest.mark.parametrize("index,family",[
    (0,"slider_crank_parametrico"),
    (1,"external_spur_gear_reduction"),
])
def test_identifica_pela_estrutura_nao_pela_palavra_no_titulo(index,family):
    request=requests()[index]
    plan=ROUTER.compile_request(request)
    assert plan["compiled_family"]==family
    assert plan["selected_by"]=="ISOMORFISMO_GRAFO_TIPADO_EXATO"
    assert plan["title_used_for_dispatch"] is False
    assert plan["publish"] is False
    assert plan["visual_approval"] is False
    assert plan["external_visual_reference_downloaded"] is False
    assert plan["media_license_verified"] is False
    # De propósito, dar título enganoso para provar que ele NÃO roteia.
    changed=copy.deepcopy(request)
    changed["title"]="REDUTOR" if index==0 else "PISTAO"
    compiled=ROUTER.compile_request(changed)
    assert compiled["compiled_family"]==family
    assert compiled["scene"]["title"]==changed["title"]


@pytest.mark.parametrize("index",[0,1])
def test_ids_sao_arbitrarios_e_ordem_dos_nos_arestas_irrelevante(index):
    req=requests()[index]
    expected=ROUTER.compile_request(req)
    renamed=copy.deepcopy(req)
    ids={n["id"]:"actor_"+str(i) for i,n in enumerate(renamed["graph"]["nodes"])}
    for n in renamed["graph"]["nodes"]:
        n["id"]=ids[n["id"]]
    for e in renamed["graph"]["edges"]:
        e["from"]=ids[e["from"]]
        e["to"]=ids[e["to"]]
    renamed["graph"]["nodes"].reverse()
    renamed["graph"]["edges"].reverse()
    p=ROUTER.compile_request(renamed)
    assert p["compiled_family"]==expected["compiled_family"]
    assert p["scene"]==expected["scene"]
    assert p["graph_sha256"]!=expected["graph_sha256"]


def test_dois_nucleos_fisicos_efetivamente_montados_de_parametros_novos():
    a,b=requests()
    pa,pb=ROUTER.compile_request(a),ROUTER.compile_request(b)
    assert pa["scene"]["crank"]["radius"]==50
    assert pa["scene"]["crank"]["rod"]==175
    assert pa["scene"]["id"]=="biela_estrutura_f15"
    assert pa["scene"]["visual_parts"] is None
    assert pb["scene"]["gears"]=={
        "z1":20,"z2":40,"module":5.8,"input_x":155,"center_y":510}
    assert pb["scene"]["driver_revolutions"]==2
    assert pb["scene"]["id"]=="engrenagens_estrutura_f15"
    assert abs(GEAR.validate(pb["scene"]).ratio-2)<1e-10
    aa=CRANK.frame_svg(pa["scene"],2.3,transmissao_animada=True,
                       enquadramento_mobile="hero_lateral_f13")
    bb=GEAR.frame(pb["scene"],2.3)
    assert 'id="role-piston"' in aa
    assert 'id="role-drive_belt"' in aa
    assert 'id="role-input_gear"' in bb
    assert 'id="role-output_gear"' in bb
    assert 'id="machine-stage"' in aa and 'id="machine-stage"' in bb


@pytest.mark.parametrize("change,reason",[
    ("unknown_kind","NO_DUPLICADO_OU_DESCONHECIDO"),
    ("new_component","TOPOLOGIA_NAO_SUPORTADA"),
    ("inverted_edge","TOPOLOGIA_NAO_SUPORTADA"),
    ("extra_edge","TOPOLOGIA_NAO_SUPORTADA"),
    ("missing_edge","TOPOLOGIA_NAO_SUPORTADA"),
    ("repeated_edge","ARESTA_DUPLICADA"),
    ("different_event","EVENTOS_NAO_IMPLEMENTADOS"),
    ("wrong_source","FONTE_NAO_VERIFICADA_OU_DIREITOS"),
    ("visual_license_lying","FONTE_NAO_VERIFICADA_OU_DIREITOS"),
    ("extra_physics","PARAMETROS_NAO_DISPONIVEIS"),
    ("publish_true","CONTRATO"),
    ("visual_approved","CONTRATO"),
    ("renderer_injected","CONTRATO"),
])
def test_bloqueio_em_estrutura_evidencia_ou_status(change,reason):
    req=requests()[0]
    if change=="unknown_kind":
        req["graph"]["nodes"][0]["kind"]="motor_3d_generico"
    elif change=="new_component":
        req["graph"]["nodes"].append({"id":"outro","kind":"rod"})
    elif change=="inverted_edge":
        edge=req["graph"]["edges"][0]
        edge["from"],edge["to"]=edge["to"],edge["from"]
    elif change=="extra_edge":
        req["graph"]["edges"].append({"from":"eixo_motriz","to":"camisa","joint":"drives"})
    elif change=="missing_edge":
        req["graph"]["edges"].pop()
    elif change=="repeated_edge":
        req["graph"]["edges"].append(copy.deepcopy(req["graph"]["edges"][0]))
    elif change=="different_event":
        req["required_events"].append("explosao_em_motor_otto")
    elif change=="wrong_source":
        req["evidence"]["locator"]="https://random.example.com/fisica"
    elif change=="visual_license_lying":
        req["evidence"]["source_is_image_license"]=True
    elif change=="extra_physics":
        req["parameters"]["dynamic_3d_reconstruction"]=True
    elif change=="publish_true":
        req["publish"]=True
    elif change=="visual_approved":
        req["visual_approval"]=True
    elif change=="renderer_injected":
        req["renderer"]="legacy_model_discarded"
    with pytest.raises(ValueError,match="F15-BLOQUEADO-"+reason):
        ROUTER.compile_request(req)


def test_rejeita_parametros_fisicos_impossiveis_sem_ativar_render():
    for req in requests():
        if len(req["graph"]["nodes"])==6:
            req["parameters"]["crank_radius_px"]=500
            with pytest.raises((ValueError,TypeError)):
                ROUTER.compile_request(req)
        else:
            req["parameters"]["z_input"]=200
            with pytest.raises((ValueError,TypeError)):
                ROUTER.compile_request(req)


def test_titulo_que_nao_cabe_na_area_editorial_bloqueia_render_sem_trocar_familia():
    req=requests()[0]
    req["title"]="REDUTOR DE ENGRENAGENS"
    assert ROUTER.identify(req)[0]=="slider_crank_parametrico"
    with pytest.raises(ValueError,match="F13-HOOK-LINHAS_NAO_CABEM"):
        ROUTER.compile_request(req)


def test_efeito_de_titulo_so_editorial_nao_muda_resultado_do_router():
    req=requests()[1]
    base=ROUTER.identify(req)
    req["title"]="E SE AS BARATAS SUMISSEM"
    assert ROUTER.identify(req)[0]==base[0]
    assert base[2]==ROUTER.identify(req)[2]


def test_plano_nao_da_acesso_ao_renderer_sem_confirmar_request(monkeypatch,tmp_path):
    req_a,req_b=requests()
    called=[]
    def render_crank(scene,path,**kwargs):
        called.append(("crank",scene["id"],kwargs))
        return {"publish":False,"sha256":"a"*64}
    def render_gears(scene,path):
        called.append(("gear",scene["id"],{}))
        return {"publish":False,"sha256":"b"*64}
    monkeypatch.setattr(CRANK,"renderizar",render_crank)
    monkeypatch.setattr(GEAR,"render",render_gears)
    assert ROUTER.render_private(req_a,tmp_path/"a.mp4")["video_sha256"]=="a"*64
    assert ROUTER.render_private(req_b,tmp_path/"b.mp4")["video_sha256"]=="b"*64
    assert called==[
       ("crank","biela_estrutura_f15",{
         "transmissao_animada":True,
         "enquadramento_mobile":"hero_lateral_f13"}),
       ("gear","engrenagens_estrutura_f15",{}),
    ]
    forged=ROUTER.compile_request(req_a)
    forged["compiled_family"]="external_spur_gear_reduction"
    ROUTER.render_private(req_a,tmp_path/"c.mp4",plan=forged)
    assert called[-1][0]=="crank"


def test_requisicao_validada_gera_plano_privado_salvo_no_disco(tmp_path):
    origin=requests()[1]
    request=tmp_path/"pedido.json"
    request.write_text(json.dumps(origin,ensure_ascii=False),"utf8")
    target=tmp_path/"plans"/"compilado.json"
    assert ROUTER.main([str(request),"--plan",str(target)])==0
    plan=json.loads(target.read_text("utf8"))
    assert plan["compiled_family"]=="external_spur_gear_reduction"
    assert plan["publish"] is False and plan["visual_approval"] is False
    assert plan["selected_by"]=="ISOMORFISMO_GRAFO_TIPADO_EXATO"
    assert not list(tmp_path.glob("*.mp4"))


def test_nao_altera_catalogo_produtivo_ou_fabrica_reconhecimento_3d():
    from src.v4.formatos import catalogo_mecanismos as PROD
    assert "slider_crank_parametrico" not in PROD.CAPACIDADES
    assert "external_spur_gear_reduction" not in PROD.CAPACIDADES
    assert set(ROUTER.REGISTRY)=={
        "slider_crank_parametrico","external_spur_gear_reduction"}
    assert all(not r["source"]["source_is_image_license"] for r in ROUTER.REGISTRY.values())
