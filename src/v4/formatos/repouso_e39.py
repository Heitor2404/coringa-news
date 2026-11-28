"""Observable dwell of a measured coordinate, not proof of mechanical locking.

Intervals are between actual rendered samples. Long near-static intervals are
identified with both a per-step and total excursion bound. No causal claim.
"""
import math
import numpy as np


def extrair(serie, fps, unidade, min_s=.25):
    q=np.asarray(serie,dtype=float)
    if (q.ndim!=1 or len(q)<2 or not np.isfinite(q).all()
            or not math.isfinite(fps) or fps<=0 or unidade not in ("rad","mm")
            or not math.isfinite(min_s) or min_s<=0):
        raise ValueError("E39-SERIE")
    # Conservative relative excursion, not manufacturing tolerance.
    span=float(np.ptp(q))
    tol=max(1e-9 if unidade=="rad" else 1e-6,span*1e-5)
    minimo=max(1,math.ceil(min_s*fps))
    flat=[]
    i=0
    while i<len(q)-1:
        if abs(q[i+1]-q[i])>tol:
            i+=1
            continue
        j=i+1
        lo,hi=min(q[i],q[j]),max(q[i],q[j])
        while j+1<len(q):
            v=q[j+1]
            nl,nh=min(lo,v),max(hi,v)
            if nh-nl>tol:
                break
            lo,hi=nl,nh
            j+=1
        if j-i>=minimo:
            flat.append((i,j))
        i=j
    limits=sorted({0,len(q)-1,*[k for pair in flat for k in pair]})
    phases=[]
    for a,b in zip(limits,limits[1:]):
        dwell=any(a>=x and b<=y for x,y in flat)
        phases.append(dict(tipo="repouso_amostrado" if dwell else "variacao_observada",
            frame_inicio=a,frame_fim=b,tempo_inicio_s=a/fps,tempo_fim_s=b/fps,
            delta=float(q[b]-q[a]),excursao=float(np.ptp(q[a:b+1]))))
    return dict(schema="coringa.repouso.amostrado.v1",unidade=unidade,
        fps=float(fps),quadros=len(q),limiar_excursao=tol,min_duracao_s=min_s,
        fracao_intervalos_repouso=sum(b-a for a,b in flat)/(len(q)-1),
        fases=phases,interpretacao_causal="NAO_INFERIDA",publish=False)
