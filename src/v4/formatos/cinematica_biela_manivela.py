"""F7: núcleo cinemático compartilhado por compressor, Otto e rigs paramétricos.

Em 2D: cursor se desloca sobre x = eixo_x. Ângulo é definido com o
pino excêntrico acima do eixo em theta=0. A distância biela entre
centro do pistão e pino permanece EXACTAMENTE L; sem aproximação senoidal.

Este módulo não decide válvulas, pressão, combustão nem cronologia didática.
"""
from __future__ import annotations
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Pose:
    angulo_rad:float
    piston_x:float
    piston_y:float
    crank_x:float
    crank_y:float
    raio:float
    biela:float

    @property
    def comprimento_observado(self)->float:
        return math.hypot(self.crank_x-self.piston_x,self.crank_y-self.piston_y)


def calcular(angulo_rad:float, raio:float, comprimento_biela:float,
            eixo_x:float,eixo_y:float)->Pose:
    params=(angulo_rad,raio,comprimento_biela,eixo_x,eixo_y)
    if any(type(x) not in (int,float) or not math.isfinite(x) for x in params):
        raise ValueError("F-CINEMATICA-NUMERO")
    r=float(raio);L=float(comprimento_biela)
    if not 1<r<200 or not r<L<=600 or not 0<=eixo_x<=540 or not 0<=eixo_y<=960:
        raise ValueError("F-CINEMATICA-PARAMETRO")
    dx=r*math.sin(angulo_rad)
    cy=eixo_y-r*math.cos(angulo_rad)
    py=cy-math.sqrt(L*L-dx*dx)
    p=Pose(float(angulo_rad),float(eixo_x),py,eixo_x+dx,cy,r,L)
    if abs(p.comprimento_observado-L)>1e-7:
        raise ValueError("F-CINEMATICA-BIELA-INCONSISTENTE")
    return p


def angulo_motor(angulo_bomba_rad:float,raio_bomba:float,raio_motor:float)->float:
    """Correia aberta ideal, sem escorregamento: ω_motor R_motor = ω_bomba R_bomba."""
    if any(type(x) not in (float,int) or not math.isfinite(x)
           for x in (angulo_bomba_rad,raio_bomba,raio_motor)):
        raise ValueError("F-CINEMATICA-TRANSMISSAO")
    if not 1<raio_motor<=200 or not 1<raio_bomba<=200:
        raise ValueError("F-CINEMATICA-TRANSMISSAO")
    return angulo_bomba_rad*raio_bomba/raio_motor
