"""Private editorial replay of evidence-backed CAD views.
No new trajectory, no interpolation, no geometry modification. The three
(or fewer) views replay identical frame indices at the original cadence.
"""
from __future__ import annotations
import copy
import hashlib
import json
import subprocess
import re
from pathlib import Path
import shutil
import numpy as np
from . import raster_e18 as R
from . import apresentacao_e46b as P
from . import ponte_cad_editorial_e28 as B
from . import reflow_cad_e31 as M
from . import hero_cad_e46d as H


def hash_poses(qs):
    return hashlib.sha256(np.asarray(qs,dtype="<f8").tobytes()).hexdigest()


def planos(rel, n_mesh):
    if rel.get("schema")!="coringa.revelacao.e45.v1" or rel.get("publish") is not False:
        raise ValueError("E46F-EVIDENCIA")
    out=[dict(alvo=None,ocultos=[],protegidos=[])]
    for v in rel["vistas"]:
        if v.get("aceita") is not True:
            continue
        a=v["alvo"]; o=v["ocultos"]; g=v["protegidos"]
        if (any(type(k) is not int or not 0<=k<n_mesh for k in [a,*o,*g])
            or a not in g or not 1<=len(o)<=3 or len(set(o))!=len(o)
            or set(o)&set(g) or not v["depois"] or min(v["depois"])<.35
            or v["ganho"]<.15):
            raise ValueError("E46F-VISTA")
        out.append(dict(alvo=a,ocultos=list(o),protegidos=list(g)))
    if len(out)==1:
        raise ValueError("E46F-SEM_REVELACAO")
    return out[:3]


def renderizar(mont,qs,cam,rel,papeis,roles,destino,ffmpeg,fps):
    n=len(qs)
    if fps!=30 or n<2 or rel.get("hash_poses")!=hash_poses(qs):
        raise ValueError("E46F-POSES")
    if any(type(k) is not int or not 0<=k<len(mont.visuais) or v not in P.PALETA
           for k,v in roles.items()):
        raise ValueError("E46F-PAPEIS")
    views=planos(rel,len(mont.visuais))
    cam=copy.copy(cam)
    factor=720/cam.W
    cam.W,cam.H=720,1280
    cam.f*=factor; cam.cx*=factor; cam.cy*=factor
    fundo=R.fundo_gradiente(cam.W,cam.H)
    destino=Path(destino)
    result=[]
    for j,vista in enumerate(views):
        path=destino/f"e46f_vista_{j}_palco.mp4"
        cmd=[ffmpeg,"-v","error","-y","-f","rawvideo","-pix_fmt","rgb24",
            "-s","720x1280","-r",str(fps),"-i","-","-vf","scale=1080:1920:flags=lanczos",
            "-c:v","libx264","-crf","19","-pix_fmt","yuv420p",str(path)]
        with subprocess.Popen(cmd,stdin=subprocess.PIPE) as enc:
            for q in qs:
                X=mont.poses(q)
                meshes=[]
                for k,v in enumerate(mont.visuais):
                    if k in vista["ocultos"]:
                        continue
                    T=X[v.corpo]@v.local
                    papel=roles.get(k,papeis[v.corpo])
                    cor,br=P.material(papel,1. if k==vista["alvo"] else 0.)
                    if vista["alvo"] is not None and k!=vista["alvo"]:
                        cor=cor*.58+np.array([.10,.13,.16])
                    meshes.append((v.vertices@T[:3,:3].T+T[:3,3],v.faces,cor,br))
                rgb,_=R.renderizar(cam,meshes,fundo,ss=1,estilo="e46b")
                enc.stdin.write(rgb.tobytes())
            enc.stdin.close()
            if enc.wait():
                raise RuntimeError("E46F-ENCODER")
        check=B.verificar_video(path,n)
        result.append(dict(**vista,arquivo=path.name,sha256=B.sha(path),quadros=n,
            fps=fps,hash_poses=hash_poses(qs),verificacao=check))
    return dict(schema="coringa.direcao.cad.private.v1",vistas=result,
        hash_poses=hash_poses(qs),quadros=n,fps=fps,malhas=len(mont.visuais),
        resolucao_nativa=[720,1280],resolucao_codificada=[1080,1920],
        natureza="repeticao_da_mesma_trajetoria_sem_mudar_cad",publish=False,visual_approved=False)


def preparar(qa_path,public_root,out):
    qa_path=Path(qa_path).resolve()
    qa=json.loads(qa_path.read_text())
    rel=qa["direcao_e46f"]
    if (rel.get("schema")!="coringa.direcao.cad.private.v1" or rel.get("publish") is not False
        or rel.get("visual_approved") is not False or qa.get("liberado_para_publicacao") is not False):
        raise ValueError("E46F-PRIVADO")
    n=rel["quadros"]
    if (n!=qa["palco_cad"]["quadros"] or rel["fps"]!=30
        or rel["hash_poses"]!=qa["revelacao_e45"]["hash_poses"]):
        raise ValueError("E46F-RELOGIO")
    expected=planos(qa["revelacao_e45"],rel["malhas"])
    if len(expected)!=len(rel["vistas"]):
        raise ValueError("E46F-QUANTIDADE")
    base=B.props(qa,"cad_e28/"+qa["palco_cad"]["sha256"]+".mp4")
    shots=[]
    fg=np.zeros((M.SH,M.SW),bool); motion=fg.copy()
    for j,(v,exp) in enumerate(zip(rel["vistas"],expected)):
        if (any(v.get(k)!=exp[k] for k in exp) or v["quadros"]!=n or v["fps"]!=30
            or v["hash_poses"]!=rel["hash_poses"] or v["arquivo"]!=f"e46f_vista_{j}_palco.mp4"):
            raise ValueError("E46F-CONTRATO")
        src=qa_path.parent/v["arquivo"]
        if src.is_symlink() or not src.is_file() or B.sha(src)!=v["sha256"]:
            raise ValueError("E46F-HASH")
        B.verificar_video(src,n)
        raw=subprocess.check_output([B.ffmpeg(),"-v","error","-i",str(src),"-vf","scale=270:480",
            "-f","rawvideo","-pix_fmt","rgb24","-"])
        a,b=M.masks(np.frombuffer(raw,np.uint8).reshape(n,M.SH,M.SW,3))
        fg|=a; motion|=b
        asset=f"cad_e28/{v['sha256']}.mp4"
        dst=Path(public_root)/asset
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(src,dst)
        if B.sha(dst)!=v["sha256"]:
            raise ValueError("E46F-COPIA")
        shot=copy.deepcopy(base["shots"][0])
        shot.update(id=f"cad_vista_{j}",start=j*n/30,end=(j+1)*n/30,asset=asset)
        if j:
            shot.pop("cad_transmissao",None)
            shot["headline"]="Componente em destaque"
            k=len(v["ocultos"])
            shot["cues"]=[dict(at=0,label=f"Repetição · {k} peça"+("s ocultas" if k>1 else " oculta"),kind="fact")]
        else:
            shot["cad_compact_panel"]=bool(shot.get("cad_transmissao"))
        shots.append(shot)
    framing=H.planejar(fg,motion,balanced=True)
    for shot in shots:
        shot["cad_reflow"]=framing
    base.update(shots=shots,duracao=len(shots)*n/30)
    base.pop("safe_area_profile",None)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    (out/"props.json").write_text(json.dumps(base,ensure_ascii=False,indent=2))
    report=dict(vistas=rel["vistas"],hash_poses=rel["hash_poses"],enquadramento=framing,
        gate=qa.get("estado"),publish=False,visual_approved=False)
    (out/"PROVENIENCIA.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
    return base


if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    for k in ("qa","public","out"):
        p.add_argument(k)
    a=p.parse_args()
    preparar(a.qa,a.public,a.out)
