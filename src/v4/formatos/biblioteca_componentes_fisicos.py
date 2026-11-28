"""F5 — contrato executável entre SceneGraph, SVG real e fontes técnicas.

Unifica atores SEM criar 29 renderers nem tentar inferir geometria de texto.
Cada peça cadastrada tem: tipo físico reutilizável, bbox já existente,
marcador único no SVG da família e referência textual da física.
Referência técnica NÃO é licença de uso da imagem nem prova da identidade
de uma máquina específica. Um componente não encontrado BLOQUEIA o frame.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

from src.v4.formatos import camera_causal_svg, grafo_causal

ARQUIVO=Path(__file__).with_name("biblioteca_componentes_fisicos.json")
CATALOGO=json.loads(ARQUIVO.read_text(encoding="utf8"))
ROLE_ID=re.compile(r'id="role-([a-z_][a-z_0-9]*)"')
ASSET_ID=re.compile(r"^[a-z][a-z0-9_]*$")
TIPOS_PERMITIDOS={
    "rotor","transmission","piston","chamber","filter","valve",
    "conduit","reservoir","fluid_body","igniter","channel",
    "gate","floating_vessel",
}

def _erro(reason: str):
    raise ValueError(reason)

def validar(catalogo:dict|None=None)->dict:
    """Recusa fontes sem escopo, papéis faltantes, geometrias e famílias fictícias."""
    base=CATALOGO if catalogo is None else catalogo
    if (not isinstance(base,dict) or base.get("schema")!="coringa-physical-components-v1"
        or base.get("published") is not False or base.get("visual_approval") is not False):
        _erro("F-BIBLIOTECA-SEM-GATE")
    types=base.get("primitive_types")
    sources=base.get("evidence_sources")
    families=base.get("families")
    if (not isinstance(types,dict) or set(types)!=TIPOS_PERMITIDOS or
        not isinstance(sources,dict) or not isinstance(families,dict) or
        set(families)!={"compressor_oficina_pv","otto_4t_reference","lock_cycle_standalone"}):
        _erro("F-BIBLIOTECA-FAMILIAS-OU-TIPOS")
    if len(sources)!=3:
        _erro("F-BIBLIOTECA-FONTES")
    for key,src in sources.items():
        if not isinstance(src,dict) or not ASSET_ID.fullmatch(key):
            _erro("F-BIBLIOTECA-FONTE-INVALIDA")
        url=urlsplit(str(src.get("url") or ""))
        if (url.scheme!="https" or url.hostname not in
            {"www.atlascopco.com","www.energy.gov","www.swl.usace.army.mil"} or
            src.get("kind")!="explicacao_publica_de_principio_fisico" or
            not isinstance(src.get("supports"),list) or not src["supports"] or
            not isinstance(src.get("does_not_establish"),list) or
            not src["does_not_establish"]):
            _erro("F-BIBLIOTECA-FONTE-SEM-ESCOPO")
    total=0
    uses={}
    for family, entry in families.items():
        if not isinstance(entry,dict):
            _erro("F-BIBLIOTECA-FAMILIA-INVALIDA")
        src=entry.get("technical_source")
        if src not in sources:
            _erro("F-BIBLIOTECA-SEM-FONTE")
        rights=entry.get("rights")
        if not isinstance(rights,dict) or (rights.get("source_pixel_copied") is not False
             or rights.get("source_page_is_media_license") is not False
             or rights.get("republication_approved") is not False):
            _erro("F-BIBLIOTECA-DIREITOS-NAO-APROVADOS")
        if (not str(entry.get("renderer") or "").startswith("render_") or
             not str(entry["renderer"]).endswith("_2d.py") or
             not isinstance(entry.get("identity_reference"),str) or
             not entry["identity_reference"].startswith("docs/v4/formatos/") or
             not (Path(__file__).resolve().parents[3]/entry["identity_reference"]).is_file()):
            _erro("F-BIBLIOTECA-IDENTIDADE-NAO-RASTREAVEL")
        graph=grafo_causal.GRAFOS.get(family)
        camera=camera_causal_svg.CAMERAS.get("familias",{}).get(family)
        if not graph or not camera:
            _erro("F-BIBLIOTECA-SEM-GRAFO-OU-CAMERA")
        expected={x["id"] for x in graph["atores"]}
        actors=entry.get("actor_role_mapping")
        if not isinstance(actors,list) or not actors:
            _erro("F-BIBLIOTECA-SEM-ATORES")
        ids=[x.get("id") for x in actors if isinstance(x,dict)]
        if len(ids)!=len(actors) or len(ids)!=len(set(ids)) or set(ids)!=expected:
            _erro("F-BIBLIOTECA-ATOR-AUSENTE-OUDUPLICADO")
        if set(camera.get("roles",{}))!=expected:
            _erro("F-BIBLIOTECA-GEOMETRIA-INCOMPLETA")
        if entry.get("event_ids")!=[x["acao"] for x in graph["eventos"]]:
            _erro("F-BIBLIOTECA-EVENTO-DIVERGENTE")
        for actor in actors:
            primitive=actor.get("primitive")
            role=actor.get("id")
            if (not ASSET_ID.fullmatch(str(role)) or primitive not in types or
                primitive not in TIPOS_PERMITIDOS or
                actor.get("bbox_source")!="camera_causal_geometrias.json" or
                actor.get("evidence")!="GEOMETRIA_CURADA_NO_RENDERER" or
                actor.get("bitmap_identity_verified") is not False):
                _erro("F-BIBLIOTECA-COMPONENTE-NAO-VALIDADO")
            b=camera_causal_svg.Caixa.parse(camera["roles"][role])
            if (b.x1<0 or b.y1<0 or b.x2>camera["width"] or
                b.y2>camera["height"]):
                _erro("F-BIBLIOTECA-BBOX-FORA-PALCO")
            uses.setdefault(primitive,set()).add(family)
        total+=len(actors)
    if total!=29 or len([t for t,v in uses.items() if len(v)>=2])<5:
        _erro("F-BIBLIOTECA-SEM-REUSO")
    return {
       "gate":"CONTRATO_TECNICO_VALIDO_NAO_IDENTIDADE_VISUAL",
       "familias":len(families),"atores":total,"tipos":len(types),
       "tipos_entre_familias":sorted(t for t,v in uses.items() if len(v)>=2),
       "fonte_tecnica_nao_licenca_visual":True,"publicar":False,
    }

@lru_cache(maxsize=1)
def _certificado():
    return validar()

def etiquetar_svg(family:str,svg:str)->str:
    """Instrumenta ator REAL. Não desenha, não muda câmera, não copia mídia.

    Reprova se um ator essencial do grafo não possui geometria SVG própria.
    Atributos data-* aparecem só no código, sem alterar o aspecto da imagem.
    """
    _certificado()
    entry=CATALOGO["families"].get(family)
    if entry is None:
        _erro("F-BIBLIOTECA-FAMILIA-DESCONHECIDA")
    if not isinstance(svg,str) or "<svg" not in svg or "</svg>" not in svg:
        _erro("F-BIBLIOTECA-SVG-INVALIDO")
    found=ROLE_ID.findall(svg)
    if len(found)!=len(set(found)):
        _erro("F-BIBLIOTECA-ATOR-DUPLICADO-SVG")
    roles={x["id"]:x["primitive"] for x in entry["actor_role_mapping"]}
    missing=set(roles)-set(found)
    if missing:
        _erro("F-BIBLIOTECA-ATOR-SEM-DESENHO:"+",".join(sorted(missing)))
    # Os papéis adicionais como crankcase e manômetro são permitidos, mas
    # NÃO recebem identidade certificada sem cadastro causal.
    src=entry["technical_source"]
    for role,kind in roles.items():
        marker=f'id="role-{role}"'
        annotated=(marker+f' data-primitive="{kind}"'
                   +f' data-source-tech="{src}"'
                   +f' data-visual-identity="PENDENTE"')
        svg=svg.replace(marker,annotated,1)
    return svg

def fichas(family:str)->dict:
    """Primitivas e relações para novos compositores 2D/3D, sem pixels."""
    report=_certificado()
    if family not in CATALOGO["families"]:
        _erro("F-BIBLIOTECA-FAMILIA-DESCONHECIDA")
    entry=CATALOGO["families"][family]
    cfg=camera_causal_svg.CAMERAS["familias"][family]
    return {
        "schema":"physical-component-assembly-v1","family":family,
        "source":entry["technical_source"],
        "identity_state":entry["identity_status"],
        "components":[
            {**actor,"bbox":cfg["roles"][actor["id"]]}
            for actor in entry["actor_role_mapping"]],
        "relations":grafo_causal.GRAFOS[family]["relacoes"],
        "events":entry["event_ids"],"visual_proven":False,"publish":False,
    }
