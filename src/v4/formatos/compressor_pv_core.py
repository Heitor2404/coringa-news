"""Ciclo de compressor alternativo monoestagio, valvulas por PRESSAO.

Uma volta de virabrequim = reexpansao do volume residual, sucção,
compressão e descarga. Fonte conceitual: EFRC Recip training tutorial
e Reddy Compressors 'how it works'. Não é CFD nem simulador termodinâmico
para projeto: é um ciclo politrópico didático normalizado (Pv^n constante).
NÃO utiliza a animação do motor Otto como prova de compressor.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import math
from src.v4.formatos import cinematica_biela_manivela as CM

PROCESSO = "compressor_alternativo"
REFERENCIAS = (
    "https://www.recip.org/tutorial-reciprocating-compressors/",
    "https://reddycompressors.com/compressors/reciprocating/how-it-works/",
)


@dataclass(frozen=True)
class CompressorSpec:
    raio: float = 67.0
    biela: float = 231.0
    eixo_y: float = 768.0
    eixo_x: float = 268.0
    folga_relativa: float = 0.06
    pressao_saida_relativa: float = 5.0
    expoente_politropico: float = 1.25

    def validar(self):
        if not (24 < self.raio < 100 and
                2.0 * self.raio < self.biela < 350 and
                0.01 < self.folga_relativa < 0.2 and
                1.5 < self.pressao_saida_relativa < 9 and
                1.0 <= self.expoente_politropico <= 1.6):
            raise ValueError("F-COMPRESSOR-PARAMETROS-FORA-DE-FAIXA")


@dataclass(frozen=True)
class CompressorState:
    progresso: float
    angulo: float
    pistao_y: float
    crank_x: float
    crank_y: float
    volume_relativo: float
    fracao_curso: float
    pressao_relativa: float
    estado: str
    admissao_aberta: bool
    descarga_aberta: bool
    sentido_pistao: str
    energia: str

    def json(self):
        return asdict(self)


ESTADOS = (
    "REEXPANSAO_RESIDUAL",
    "ADMISSAO_AR",
    "COMPRESSAO_AR",
    "DESCARGA_PRESSURIZADA",
)


def estado(progress: float, spec: CompressorSpec = CompressorSpec()) -> CompressorState:
    spec.validar()
    if not (math.isfinite(progress) and 0.0 <= progress <= 1.0):
        raise ValueError("F-COMPRESSOR-PROGRESSO")
    theta = 2 * math.pi * progress
    r, L = spec.raio, spec.biela
    rig = CM.calcular(theta,r,L,spec.eixo_x,spec.eixo_y)
    dx = rig.crank_x - rig.piston_x
    crank_y = rig.crank_y
    piston_y = rig.piston_y
    y_tdc = spec.eixo_y - r - L
    pos = max(0., min(1., (piston_y - y_tdc) / (2*r)))
    V = spec.folga_relativa + pos
    Vs = spec.folga_relativa + 1
    P2 = spec.pressao_saida_relativa
    exponent = spec.expoente_politropico
    if progress <= .5:
        # Retorno inicial do volume residual pressurizado. Só entra ar quando
        # a pressão interna cair até a da admissão.
        pres = max(1.0, P2*(spec.folga_relativa/V)**exponent)
        mode = ("REEXPANSAO_RESIDUAL" if pres > 1.001
                else "ADMISSAO_AR")
        direction = "DESCENDO"
        source = "EIXO_IMPELE_PISTAO"
    else:
        # Na subida, entrada fechada; pressão cresce até vencer a pressão
        # da linha de descarga. Nunca abertura da válvula por tempo hardcoded.
        pres = min(P2,(Vs/V)**exponent)
        mode = ("COMPRESSAO_AR" if pres < P2-0.001
                else "DESCARGA_PRESSURIZADA")
        direction = "SUBINDO"
        source = "EIXO_COMPRIME_GAS"
    return CompressorState(
        progresso=progress, angulo=theta,
        pistao_y=piston_y,
        crank_x=spec.eixo_x+dx, crank_y=crank_y,
        volume_relativo=V, fracao_curso=pos,
        pressao_relativa=pres,
        estado=mode, admissao_aberta=mode=="ADMISSAO_AR",
        descarga_aberta=mode=="DESCARGA_PRESSURIZADA",
        sentido_pistao=direction, energia=source,
    )


def limites_fases(spec: CompressorSpec = CompressorSpec()) -> dict:
    # Busca numérica genérica, sem instantes por assunto.
    sample = [estado(k/2000, spec) for k in range(2001)]
    ranges = {}
    for state in sample:
        if state.estado not in ranges:
            ranges[state.estado] = [state.progresso, state.progresso]
        else:
            ranges[state.estado][1] = state.progresso
    if set(ranges) != set(ESTADOS):
        raise ValueError("F-CICLO-SEM-FASE")
    return {name:{"de":round(bounds[0],4),"ate":round(bounds[1],4)}
            for name,bounds in ranges.items()}
