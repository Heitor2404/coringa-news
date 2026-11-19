"""Duração do plano derivada de ÁUDIO REAL, nunca áudio acelerado para caber na foto.

Uso transversal: qualquer formato que tenha cenas de começo/fim em segundos.
O pré-flight final continua exigindo progresso editorial e fonte válida.
"""
from __future__ import annotations
import copy
import math


def retemporizar(plano: dict, duracoes: list[float], pausa: float = .24) -> dict:
    shots=plano.get('shots') or []
    if not shots or len(shots)!=len(duracoes):
        raise ValueError('cada cena precisa de duração real da narração')
    if not 0.08<=pausa<=.7:
        raise ValueError('pausa de respiração inválida')
    out=copy.deepcopy(plano)
    cursor=0.
    for s,d in zip(out['shots'],duracoes):
        if (not isinstance(d,(int,float)) or isinstance(d,bool) or
            not math.isfinite(d) or d<=0):
            raise ValueError('duração de áudio inválida')
        if s.get('type')=='mechanism':
            raise ValueError('simulação causal exige marcações de ação próprias; não acelerar ou retimar automaticamente')
        # áudio toca naturalmente em velocidade 1, com pequena folga final.
        target=max(1.4,math.ceil((d+pausa)*30)/30)
        # Nunca esticar uma foto/legenda além do limite que o fiscal detecta.
        # A solução para voz longa é fragmentar a fala e acrescentar mídia útil.
        if target>3.8:
            raise ValueError(f"{s.get('id')}: voz natural de {d:.2f}s exige {target:.2f}s;"
                             " dividir a fala em mais ações/mídias, NÃO aplicar atempo")
        prev=float(s['end'])-float(s['start'])
        if any(not (0<=float(c['at'])<target) for c in s.get('cues') or []):
            raise ValueError(f"{s.get('id')}: cue fora da duração natural; reescrever storyboard")
        s['start']=round(cursor,3)
        cursor=round(cursor+target,3)
        s['end']=cursor
        s['voice_duration']=round(d,3)
        s['voice_tempo']=1.
        s['retime_from']=round(prev,3)
    out['duracao']=cursor
    out['sincronia_voz']={'metodo':'DURACAO_DE_ARQUIVO_REAL',
                         'tempo_audio':1.0,
                         'pausa_s':pausa,
                         'estetica_aprovada':False}
    return out
