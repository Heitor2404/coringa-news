"""Solver hidráulico parametrizado de DOIS reservatórios abertos.

Um mesmo kernel recebe larguras internas (áreas relativas com mesma
profundidade), alturas iniciais e instantes de abrir/transferir. A água
é incompressível, as áreas constantes e o volume TOTAL se conserva.
Exibição de tempo DIDÁTICO, não cinemática experimental calibrada.
"""
from __future__ import annotations
import math
from dataclasses import dataclass


def _n(x,lo=None,hi=None):
    if type(x) not in (float,int) or not math.isfinite(x):
        raise ValueError("F-SOLVER-NUMERO")
    if lo is not None and x<lo or hi is not None and x>hi:
        raise ValueError("F-SOLVER-LIMITE")
    return float(x)


def _smooth(u):
    p=max(0.,min(1.,u))
    return p*p*(3.-2.*p)


@dataclass(frozen=True)
class Estado:
    tempo_s: float
    nivel_esquerdo_y: float
    nivel_direito_y: float
    nivel_final_y: float
    valvula_aberta: float
    fluxo: float
    diferenca_pressao_relativa: float
    volume_total: float


def simular(t:float, *, duracao:float,
            area_esquerda:float, area_direita:float,
            fundo_y:float,topo_y:float,
            esquerda_y:float,direita_y:float,
            abertura_de:float,abertura_ate:float,
            vazao_de:float,vazao_ate:float)->Estado:
    t=_n(t,0,duracao)
    duracao=_n(duracao,1,30)
    a=_n(area_esquerda,30,400)
    b=_n(area_direita,30,400)
    base=_n(fundo_y,450,900)
    top=_n(topo_y,200,700)
    yl=_n(esquerda_y,top+18,base-24)
    yr=_n(direita_y,top+18,base-24)
    start=_n(abertura_de,0,duracao)
    opened=_n(abertura_ate,start+.01,duracao)
    flow_start=_n(vazao_de,opened,duracao)
    flow_end=_n(vazao_ate,flow_start+.01,duracao)
    if not top<yl<yr<base:
        raise ValueError("F-SOLVER-NIVEIS")
    open_frac=_smooth((t-start)/(opened-start))
    phase=max(0.,min(1.,(t-flow_start)/(flow_end-flow_start)))
    # Aproximação quasi-estática de escoamento pela diferença de pressão:
    # ∆h(t)=∆h0 (1-τ)^2 (decaimento sem inércia); NÃO é duração física.
    remaining=(1.-phase)**2
    target=(a*yl+b*yr)/(a+b)
    delta=(yl-yr)*remaining
    left=target+b/(a+b)*delta
    right=target-a/(a+b)*delta
    flow=max(0.,1.-phase) if flow_start<=t<flow_end else 0.
    if open_frac<.999:
        # Níveis ainda parados até a válvula realmente terminar de abrir.
        if t<flow_start:
            left,right=yl,yr
            flow=0.
    volume=a*(base-left)+b*(base-right)
    reference=a*(base-yl)+b*(base-yr)
    if abs(volume-reference)>1e-6:
        raise ValueError("F-SOLVER-NAO-CONSERVA-AGUA")
    return Estado(
        tempo_s=t,nivel_esquerdo_y=left,nivel_direito_y=right,
        nivel_final_y=target,valvula_aberta=open_frac,
        fluxo=flow*open_frac,
        diferenca_pressao_relativa=remaining,volume_total=volume)
