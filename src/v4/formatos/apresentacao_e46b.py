"""E46B: opt-in studio material. No geometry or pose changes.
Colors denote known roles; no assertion of real material or load.
"""
import numpy as np

PALETA={
    "entrada":([.99,.53,.13],.35),
    "laco":([.18,.79,.67],.22),
    "acoplado":([.22,.62,.96],.28),
    "movel":([.63,.75,.82],.40),
    "estrutura":([.25,.34,.44],.25),
    "saida":([.20,.70,.98],.30),
    "contato":([.50,.60,.67],.38),
    "perfil":([.16,.80,.67],.28),
}

def material(papel,foco):
    if papel not in PALETA or not np.isfinite(foco) or not 0<=foco<=1:
        raise ValueError("E46B-MATERIAL")
    c,b=PALETA[papel]
    c=np.asarray(c,float)
    return c*(.87+.13*foco)+.09*foco*(1-c),b

def sombrear(base,lam,fill,rim,spec,brilho):
    key=.22+.75*lam**.72
    cool=np.array([.54,.73,1.0])
    warm=np.array([1.0,.93,.82])
    out=base*(key[:,None]*warm + .28*fill[:,None]*cool)
    out+= (.15*rim[:,None])*cool
    out+= (.22*spec**.32*(.35+.65*brilho))[:,None]
    return np.clip(out,0,1)

def bordas(ids,depth,n):
    h,w=ids.shape
    out=np.zeros((h,w),bool)
    for dy,dx in ((0,1),(1,0)):
        a=(slice(0,h-dy),slice(0,w-dx)); b=(slice(dy,h),slice(dx,w))
        ia,ib=ids[a],ids[b]; za,zb=depth[a],depth[b]
        va,vb=ia>=0,ib>=0; both=va&vb
        delta=np.zeros_like(za)
        np.subtract(za,zb,out=delta,where=both)
        gap=both&(np.abs(delta)>.008*np.minimum(za,zb))
        seam=both&(~gap)&(ia!=ib)
        crease=both&(~gap)&(np.einsum("ijk,ijk->ij",n[a],n[b])<.40)
        out[a]|=va&((~vb)|(gap&(delta<0))|seam|crease)
        out[b]|=vb&((~va)|(gap&(delta>0))|seam|crease)
    return out
