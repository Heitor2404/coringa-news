"""Camera semântica 2D de mecanismos: grafo causal → bbox real → SVG.

O algoritmo é o MESMO para qualquer família, mas as bboxes são metadados
revisados do próprio renderizador. Nunca infere peça a partir de um título.
Mantém a máquina CRÍTICA inteira no viewport; recusa falta de ator, clipping,
zoom inseguro e atributos/caixas inválidos. Opt-in só em prova privada.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from src.v4.formatos import grafo_causal

CAMERAS = json.loads(Path(__file__).with_name("camera_causal_geometrias.json").read_text("utf8"))


@dataclass(frozen=True)
class Caixa:
    x1: float
    y1: float
    x2: float
    y2: float

    @classmethod
    def parse(cls, values):
        if (not isinstance(values, list) or len(values) != 4 or
                any(type(x) not in (int, float) or not math.isfinite(x) for x in values)):
            raise ValueError("F-CAMERA-CAIXA-INVALIDA")
        box = cls(*values)
        if box.x1 >= box.x2 or box.y1 >= box.y2:
            raise ValueError("F-CAMERA-CAIXA-INVALIDA")
        return box

    def shift(self, dy: float) -> "Caixa":
        return Caixa(self.x1,self.y1+dy,self.x2,self.y2+dy)

    @property
    def center(self):
        return ((self.x1+self.x2)/2, (self.y1+self.y2)/2)


@dataclass(frozen=True)
class Pose:
    scale: float
    tx: float
    ty: float
    active: str
    focus_roles: tuple[str,...]

    def transform_svg(self, shift: float) -> str:
        # SVG aplica o translate mais à direita antes do scale.
        return (f"translate({self.tx:.4f} {self.ty:.4f}) "
                f"scale({self.scale:.5f}) translate(0 {-shift:.1f})")


def _ease(t):
    x = max(0.0,min(1.0,t))
    return x*x*(3-2*x)


def _clamp(v,lo,hi):
    return max(lo,min(v,hi))


@lru_cache(maxsize=8)
def _plano(familia: str):
    ficha=grafo_causal.GRAFOS.get(familia)
    if ficha is None:
        raise ValueError("F-CAMERA-SEM-GRAFO")
    return grafo_causal.montar(familia,tuple(e["acao"] for e in ficha["eventos"]))


def _validar(familia: str):
    if CAMERAS.get("schema") != "coringa-camera-causal-svg-v1" or (
            CAMERAS.get("publicar") is not False):
        raise ValueError("F-CAMERA-PRIVACIDADE")
    # Primeiro exigir um processo físico cadastrado; depois geometria.
    # Não apresentar um tema desconhecido como se só faltassem coordenadas.
    scene=_plano(familia)
    cfg=CAMERAS["familias"].get(familia)
    if not isinstance(cfg,dict):
        raise ValueError("F-CAMERA-SEM-GEOMETRIA")
    box=Caixa.parse(cfg["bounds"])
    viewport=Caixa.parse(cfg["viewport"])
    shift=cfg["subida_base_px"]
    zoom=cfg["zoom_max"]
    if (type(shift) not in (int,float) or not math.isfinite(shift)
        or shift < 0 or type(zoom) not in (int,float) or
        not 1<=zoom<=1.30 or
        box.x1 < 0 or box.y1 < 0 or box.x2 > cfg["width"] or
        box.y2 > cfg["height"] or
        viewport.x1 < 0 or viewport.y1 < 0 or
        viewport.x2 > cfg["width"] or viewport.y2 > cfg["height"]):
        raise ValueError("F-CAMERA-PALCO-INVALIDO")
    actor_ids={a["id"] for a in scene["atores"]}
    role_cfg=cfg["roles"]
    if not isinstance(role_cfg,dict) or actor_ids!=set(role_cfg):
        raise ValueError("F-CAMERA-ATOR-SEM-BBOX")
    for name,v in role_cfg.items():
        b=Caixa.parse(v)
        # Curadoria declarada e auditável: nada pode ultrapassar o ator integral.
        if (b.x1 < box.x1-4 or b.x2 > box.x2+4 or
                b.y1 < box.y1-5 or b.y2 > box.y2+5):
            raise ValueError("F-CAMERA-ATOR-FORA-MAQUINA:"+name)
    moved=box.shift(-shift)
    if (moved.x1 < viewport.x1 or moved.x2 > viewport.x2 or
            moved.y1 < viewport.y1 or moved.y2 > viewport.y2):
        raise ValueError("F-CAMERA-BASE-NAO-CABE")
    return cfg,scene,box,viewport


def calcular(familia: str, action: str, tempo_s: float,
             inicio_fase_s: float, duracao_s: float) -> Pose:
    cfg,scene,box,viewport=_validar(familia)
    if (not all(type(x) in (int,float) and math.isfinite(x)
            for x in (tempo_s,inicio_fase_s,duracao_s))
        or duracao_s<=0 or tempo_s<0 or tempo_s>duracao_s
        or inicio_fase_s<0 or inicio_fase_s>tempo_s+.001):
        raise ValueError("F-CAMERA-TEMPO")
    ids=[e["acao"] for e in scene["eventos"]]
    if action not in ids:
        raise ValueError("F-CAMERA-ACAO-SEM-GRAFO")
    i=ids.index(action)
    current=scene["eventos"][i]["camera"]["alvos"]
    previous=scene["eventos"][max(0,i-1)]["camera"]["alvos"]
    roles=cfg["roles"]; shift=cfg["subida_base_px"]
    def centroid(ids):
        # Focos de relações: não escolher só uma ponta do mecanismo.
        bb=[Caixa.parse(roles[name]) for name in ids]
        return ((min(b.x1 for b in bb)+max(b.x2 for b in bb))/2,
                (min(b.y1 for b in bb)+max(b.y2 for b in bb))/2-shift)
    bx,by=box.shift(-shift).center
    px,py=centroid(previous)
    cx,cy=centroid(current)
    mix=_ease((tempo_s-inicio_fase_s)/.5)
    fx=px+(cx-px)*mix
    fy=py+(cy-py)*mix
    zoom_in=_ease((tempo_s-.20)/.75)
    max_fit=min((viewport.x2-viewport.x1)/(box.x2-box.x1),
                (viewport.y2-viewport.y1)/(box.y2-box.y1))
    scale=min(1+(cfg["zoom_max"]-1)*zoom_in,max_fit)
    if scale < 1-1e-8:
        raise ValueError("F-CAMERA-CORTE-INEVITAVEL")
    vx,vy=viewport.center
    idealx=vx-scale*bx + (bx-fx)*.35*zoom_in
    idealy=vy-scale*by + (by-fy)*.11*zoom_in
    stage=box.shift(-shift)
    lowx=viewport.x1-scale*stage.x1
    highx=viewport.x2-scale*stage.x2
    lowy=viewport.y1-scale*stage.y1
    highy=viewport.y2-scale*stage.y2
    if lowx>highx+1e-7 or lowy>highy+1e-7:
        raise ValueError("F-CAMERA-CORTE-INEVITAVEL")
    return Pose(scale,_clamp(idealx,lowx,highx),_clamp(idealy,lowy,highy),
                action,tuple(current))


def verificar_pose(familia: str, pose: Pose) -> bool:
    cfg,scene,box,viewport=_validar(familia)
    b=box.shift(-cfg["subida_base_px"])
    p=lambda x,y:(pose.scale*x+pose.tx,pose.scale*y+pose.ty)
    lo=p(b.x1,b.y1);hi=p(b.x2,b.y2)
    return (lo[0]>=viewport.x1-1e-5 and lo[1]>=viewport.y1-1e-5 and
            hi[0]<=viewport.x2+1e-5 and hi[1]<=viewport.y2+1e-5)
