"""Ritmo por mudanças de estado FÍSICO, sem reescrever a física.

Concede um piso de duração às fases curtas de um processo e distribui o
tempo restante proporcionalmente ao intervalo físico. É retiming didático:
preserva a sequência, os estados e toda equação P–V original. Usar apenas
em vídeo de explicação privada com indicação de velocidade não uniforme.
"""
from __future__ import annotations
import math


def distribuir(limites: dict, duracao_s: float, minimo_s: float = 1.15):
    if (not isinstance(limites,dict) or not limites or
        type(duracao_s) not in (int,float) or not math.isfinite(duracao_s)
        or type(minimo_s) not in (int,float) or not math.isfinite(minimo_s)
        or minimo_s<=0 or duracao_s<len(limites)*minimo_s):
        raise ValueError("F-RITMO-FASES-NAO-CABEM")
    starts=[(name,limits["de"]) for name,limits in limites.items()]
    if (not all(isinstance(name,str) and type(begin) in (int,float)
                and math.isfinite(begin) and 0<=begin<1
                for name,begin in starts)
            or not starts or starts[0][1] != 0
            or [x[1] for x in starts] != sorted(set(x[1] for x in starts))):
        raise ValueError("F-RITMO-FASE-INVALIDA")
    ends=[x[1] for x in starts[1:]]+[1.]
    durations=[end-start for (_,start),end in zip(starts,ends)]
    if min(durations)<=0:
        raise ValueError("F-RITMO-FASE-INVALIDA")
    extra=duracao_s-len(starts)*minimo_s
    # Distribui proporcionalmente o tempo ALEM do piso, mantendo soma exata.
    result=[]
    elapsed=0.
    for i,((name,beg),end,span) in enumerate(zip(starts,ends,durations)):
        segundos=minimo_s+extra*span
        result.append({"fase":name,"fisico_de":beg,"fisico_ate":end,
            "video_de":elapsed,"video_ate":elapsed+segundos})
        elapsed+=segundos
    result[-1]["video_ate"]=float(duracao_s)
    return result


def mapear(tempo_s: float, trilha: list[dict]):
    if (not trilha or type(tempo_s) not in (int,float) or
        not math.isfinite(tempo_s) or tempo_s<0 or
        tempo_s>trilha[-1]["video_ate"]+1e-8):
        raise ValueError("F-RITMO-TEMPO-INVALIDO")
    fase=next((s for s in trilha if tempo_s<s["video_ate"]),trilha[-1])
    f=(tempo_s-fase["video_de"])/(fase["video_ate"]-fase["video_de"])
    t=fase["fisico_de"]+max(0.,min(1.,f))*(fase["fisico_ate"]-fase["fisico_de"])
    return t,fase["fase"],fase["video_de"]
