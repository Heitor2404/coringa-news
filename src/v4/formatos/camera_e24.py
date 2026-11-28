"""E24: enquadramento por geometria em movimento, não só origem da junta.

Limites conservadores por caixas locais transformadas em TODOS os quadros
renderizados. Amostras materiais de vértices reais medem rotação/translação.
Não são prova de visibilidade/oclusão por pixels nem de homologação editorial.
"""
from itertools import product
import numpy as np


def indices_amostra(n, limite):
    if n <= 0:
        raise ValueError("E24-SEM_AMOSTRAS")
    return np.unique(np.linspace(0, n-1, min(n, limite), dtype=int))


def evidencia(mont, qs):
    if not len(qs) or not mont.visuais:
        raise ValueError("E24-SEM_GEOMETRIA_OU_POSES")
    dados = []
    for v in mont.visuais:
        p = np.asarray(v.vertices, float)
        if p.ndim != 2 or p.shape[1] != 3 or not len(p) or not np.isfinite(p).all():
            raise ValueError("E24-MALHA")
        lo, hi = p.min(0), p.max(0)
        box = np.array(list(product(*zip(lo,hi))))
        real = p[indices_amostra(len(p), 96)]
        dados.append((v.corpo, v.local, box, real))
    # Todas as poses: inclusive uma ação rápida entre amostras de câmera.
    caixas = {}
    traj = {}
    amostra = set(indices_amostra(len(qs), 24).tolist())
    referencia = {}
    moveis = set()
    for i,q in enumerate(qs):
        X = mont.poses(q)
        por_corpo = {}
        for k,(b,L,box,real) in enumerate(dados):
            T = X[b] @ L
            R,t = T[:3,:3],T[:3,3]
            caixas.setdefault(b,[]).append(box @ R.T + t)
            p = real @ R.T + t
            if i==0:
                referencia[k]=p
            if np.linalg.norm(p-referencia[k],axis=1).max()>1e-7:
                moveis.add(b)
            if i in amostra:
                por_corpo.setdefault(b,[]).append(p)
        for b,p in por_corpo.items():
            traj.setdefault(b,[]).append(np.vstack(p))
    bounds={b:np.vstack(p) for b,p in caixas.items()}
    tracks={b:np.stack(traj[b]) for b in moveis}
    return bounds, tracks


def pontos_foco(bounds, tracks):
    todos=np.vstack(list(bounds.values()))
    if not tracks:
        return todos,"tudo"
    mov=np.vstack([bounds[b] for b in tracks])
    largura=np.ptp(mov,axis=0).max()
    if largura >= .4*np.ptp(todos,axis=0).max():
        return todos,"tudo"
    c=(mov.max(0)+mov.min(0))/2
    contexto=todos[np.all(np.abs(todos-c)<=largura*.65,axis=1)]
    return np.vstack((mov,contexto)),"pecas_moveis"


def movimento_projetado(cam, tracks, altura):
    """RMS em pixels dos pontos materiais, incluindo rotação em eixo fixo."""
    scores=[]
    for pts in tracks.values():
        u,v,z,_=cam.projetar(pts.reshape(-1,3))
        if (z<=0).any() or not np.isfinite(u).all() or not np.isfinite(v).all():
            return 0.
        uv=np.stack([u,v],axis=-1).reshape(pts.shape[0],pts.shape[1],2)
        delta=uv-uv[0]
        scores.append(float(np.sqrt(np.mean(np.sum(delta**2,axis=-1))))/altura)
    return float(np.mean(scores)) if scores else 0.


def cabe(cam, pontos, regiao, W,H):
    u,v,z,_=cam.projetar(pontos)
    x0,y0,x1,y1=regiao
    return (np.isfinite(u).all() and np.isfinite(v).all() and (z>0).all()
            and u.min()>=x0*W and u.max()<=x1*W
            and v.min()>=y0*H and v.max()<=y1*H)
