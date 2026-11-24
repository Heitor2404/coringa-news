"""Extract observable changes of a measured quantity from rendered poses.

Events refer to an exact rendered frame, never to an invented narration or
causal mechanism. A measurement going up does not by itself prove force,
pressure, load, contact, opening of a valve, etc.
"""
import math
import numpy as np


def extrair(serie_m, fps, tipo, rotulo, indices=None):
    s=np.asarray(serie_m,dtype=float)
    if s.ndim!=1 or len(s)<2 or not np.isfinite(s).all():
        raise ValueError("E27-SERIE")
    if not isinstance(fps,(int,float)) or not math.isfinite(fps) or fps<=0:
        raise ValueError("E27-FPS")
    if not isinstance(tipo,str) or not tipo or not isinstance(rotulo,str) or not rotulo.strip():
        raise ValueError("E27-MEDIDA")
    if indices is None:
        indices=list(range(len(s)))
    ix=np.asarray(indices)
    if (ix.ndim!=1 or len(ix)<2 or ix.dtype.kind not in "iu"
            or ix[0]<0 or ix[-1]>=len(s) or (np.diff(ix)<=0).any()):
        raise ValueError("E27-INDICES")
    y=s[ix]*1000
    amplitude=float(np.ptp(y))
    # Hysteresis is a declared presentation sampling threshold, NOT a
    # manufacturing tolerance. No tiny noise promoted to physical event.
    eps=max(1e-5,amplitude*.02)
    limites=[0]
    d=0
    extremo=0
    for i in range(1,len(y)):
        if d==0:
            diff=y[i]-y[0]
            if abs(diff)>=eps:
                d=1 if diff>0 else -1
                extremo=i
        elif d*(y[i]-y[extremo])>0:
            extremo=i
        elif d*(y[extremo]-y[i])>=eps:
            if extremo>limites[-1]:
                limites.append(extremo)
            d=-d
            extremo=i
    if limites[-1]!=len(y)-1:
        limites.append(len(y)-1)
    fases=[]
    for a,b in zip(limites,limites[1:]):
        delta=float(y[b]-y[a])
        classe="aumenta" if delta>=eps else "diminui" if delta<=-eps else "variacao_pequena"
        fases.append(dict(tipo=classe,frame_inicio=int(a),frame_fim=int(b),
                          tempo_inicio_s=a/fps,tempo_fim_s=b/fps,
                          pose_inicio=int(ix[a]),pose_fim=int(ix[b]),
                          inicio_mm=float(y[a]),fim_mm=float(y[b]),
                          delta_mm=delta))
    pontos=[dict(tipo="minimo_amostrado",frame=int(np.argmin(y))),
            dict(tipo="maximo_amostrado",frame=int(np.argmax(y)))]
    for p in pontos:
        p.update(tempo_s=p["frame"]/fps,valor_mm=float(y[p["frame"]]),
                 pose=int(ix[p["frame"]]))
    return dict(schema="coringa.eventos.trajetoria.v1",medida=dict(tipo=tipo,rotulo=rotulo,
                     unidade="mm"),fps=float(fps),quadros=len(y),duracao_s=len(y)/fps,
                indices_pose=ix.tolist(),limiar_visual_mm=eps,curso_amostrado_mm=amplitude,
                fases=fases,extremos=pontos,interpretacao_causal="NAO_INFERIDA",
                publish=False,visual_approved=False)
