"""Private CAD illustration style. Original implementation; no external assets.

Appearance only: immutable solver poses and triangles. A focus schedule is
editorial attention, NOT simulated force or a new physical event.
"""
import numpy as np

PALETA={
    "entrada":np.array([.98,.66,.23]),
    "laco":np.array([.31,.79,.72]),
    "acoplado":np.array([.43,.67,.94]),
    "movel":np.array([.73,.78,.83]),
    "estrutura":np.array([.39,.46,.53]),
}


def focos(mont,grafo,indices):
    if grafo.get("schema")!="coringa.cinematica.observada.v1":
        raise ValueError("E33-GRAFO")
    # Include only bodies with an observed, moving joint; no inference by name.
    corpos=list(mont.corpos)
    mov={m["junta"]:m for m in grafo["movimentos"]}
    nomes=[]
    for r in grafo["relacoes"]:
        for key in ("entrada","movimento"):
            m=mov[r[key]]
            if m["corpo"] not in nomes:
                nomes.append(m["corpo"])
    if not nomes:
        nomes=[m["corpo"] for m in mov.values() if m["papel"]=="entrada_prescrita"]
        nomes=list(dict.fromkeys(nomes))
    if not nomes or any(n not in corpos for n in nomes):
        raise ValueError("E33-SEM_FOCO")
    # At most three groups. Equal spans are an editorial decision, not
    # causal timing. All bodies remain visible.
    grupos=[[corpos.index(n)] for n in nomes[:2]]
    if len(nomes)>2:
        grupos.append([corpos.index(n) for n in nomes[2:]])
    n=len(indices)
    if n<len(grupos):
        raise ValueError("E33-QUADROS")
    tr=[]
    for j,g in enumerate(grupos):
        a=j*n//len(grupos);b=(j+1)*n//len(grupos)
        tr.append(dict(frame_inicio=a,frame_fim_exclusivo=b,
                       corpos=g,nomes=[corpos[k] for k in g],
                       natureza="atencao_editorial_nao_causal"))
    return tr


def intensidade(frame,corpo,trilha):
    # Continuous easing at focus changes, with no change in geometry.
    val=0.
    for f in trilha:
        if corpo not in f["corpos"]:
            continue
        a,b=f["frame_inicio"],f["frame_fim_exclusivo"]
        r=max(1.,min(8.,(b-a)/3))
        u=min(1.,max(0.,(frame-a+1)/r),max(0.,(b-frame)/r))
        val=max(val,u*u*(3-2*u))
    return val


def material(papel,focus):
    base=PALETA[papel]
    t=float(focus)
    if not 0<=t<=1:
        raise ValueError("E33-FOCO")
    return base*(.90+.10*t)+(.10*t)*(1-base),0.


def sombrear(base,lam,fill,rim):
    # Soft matte bands, not metallic specular glare.
    bands=np.interp(lam,[0,.22,.32,.55,.65,1],[.46,.46,.68,.68,.88,.98])
    return np.clip(base*(bands[:,None]+.11*fill[:,None])+
                   (.075*rim)[:,None],0,1)


def bordas_locais(ids,depth,normals):
    """Only darken foreground, on the near side of an occlusion.
    Same-depth seams and sharp creases remain legible. No background halo.
    """
    h,w=ids.shape
    out=np.zeros((h,w),bool)
    for dy,dx in ((0,1),(1,0)):
        aa=(slice(0,h-dy),slice(0,w-dx))
        bb=(slice(dy,h),slice(dx,w))
        ia,ib=ids[aa],ids[bb]
        za,zb=depth[aa],depth[bb]
        na,nb=normals[aa],normals[bb]
        va,vb=ia>=0,ib>=0
        both=va&vb
        # Avoid inf-inf and use scale-independent depth threshold.
        delta=np.zeros_like(za)
        np.subtract(za,zb,out=delta,where=both)
        near=np.minimum(za,zb)
        gap=both&(np.abs(delta)>.008*near)
        crease=both&(~gap)&(np.einsum("ijk,ijk->ij",na,nb)<.72)
        seam=both&(~gap)&(ia!=ib)
        out[aa]|=va&((~vb)|(gap&(delta<0))|crease|seam)
        out[bb]|=vb&((~va)|(gap&(delta>0))|crease|seam)
    return out
