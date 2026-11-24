"""Occlusion-aware camera ranking, using the real triangles and depth buffer.

A low resolution sample is evidence of visibility in the sampled poses,
not proof of visibility in every frame. Never hide or remove CAD bodies.
"""
import numpy as np
from . import raster_e18 as R


def preparar(mont, qs, indices):
    result=[]
    for i in indices:
        X=mont.poses(qs[i])
        scene=[]
        for v in mont.visuais:
            T=X[v.corpo]@v.local
            scene.append((v.corpo,v.vertices@T[:3,:3].T+T[:3,3],
                          np.asarray(v.faces,np.int64)))
        result.append(scene)
    return result


def pixels(cam, scene, width=180, height=320):
    """Body ID z-buffer at scaled resolution, no shading."""
    depth=np.full((height,width),np.inf)
    ids=np.full((height,width),-1,np.int32)
    normals=np.zeros((height,width,3))
    for b,V,F in scene:
        u,v,z,_=cam.projetar(V)
        if not (np.isfinite(u).all() and np.isfinite(v).all() and np.isfinite(z).all()):
            raise ValueError("E26-PROJECAO_INVALIDA")
        zeros=np.zeros(len(F))
        R._rasterizar(u*(width/cam.W),v*(height/cam.H),z,F,
                      np.full(len(F),b,np.int32),width,height,depth,ids,normals,
                      zeros,zeros,zeros)
    valid=ids>=0
    return {int(b):int(n) for b,n in zip(*np.unique(ids[valid],return_counts=True))}


def avaliar(cam, scenes, moveis):
    """Compare all bodies to each moving body alone, preserving self-occlusion."""
    moveis=sorted(set(moveis))
    if not moveis:
        return dict(media=1.,pior_corpo=1.,pior_pose=1.,corpos={},
                    poses=len(scenes),resolucao=[180,320])
    ratios={b:[] for b in moveis}
    for scene in scenes:
        total=pixels(cam,scene)
        for b in moveis:
            solo=pixels(cam,[x for x in scene if x[0]==b]).get(b,0)
            # Tiny or off-frame parts should not earn a perfect score.
            ratios[b].append(min(1.,total.get(b,0)/max(solo,8)))
    medias={str(b):float(np.mean(xs)) for b,xs in ratios.items()}
    return dict(media=float(np.mean(list(medias.values()))),
                pior_corpo=min(medias.values()),
                pior_pose=min(min(xs) for xs in ratios.values()),
                corpos=medias,poses=len(scenes),resolucao=[180,320])


def nota(geometrica, oc):
    # A view with much of a moving body hidden loses even if projected motion
    # is large. Keep a small floor to allow the best available opaque view.
    return geometrica*(.02+.98*oc["media"])*(.02+.98*oc["pior_corpo"])


def candidatos_por_setor(candidatos):
    """Top geometry candidate in each 30° sector + top 4 overall."""
    ordered=sorted(candidatos,key=lambda x:-x[0])
    setores={}
    for item in ordered:
        setores.setdefault(item[2]["guinada_graus"]//30,item)
    out=[]
    for item in ordered[:4]+list(setores.values()):
        if not any(item is old for old in out):
            out.append(item)
    return out
