"""E45: revelação editorial por malha oclusora medida. Não é corte sólido.
O solver, os contatos, os vértices e a trajetória não são modificados.
Cada vista protege o alvo e os parceiros de contato declarados.
"""
from __future__ import annotations

import copy
import hashlib
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from . import raster_e18 as R

W, H = 180, 320
MAX_OCULTOS = 3
GANHO_MIN = .15
PIOR_MIN = .35


def preparar(mont, qs, indices):
    cenas = []
    for i in indices:
        X = mont.poses(qs[i])
        cenas.append([(k, v.vertices @ (X[v.corpo] @ v.local)[:3,:3].T
                        + (X[v.corpo] @ v.local)[:3,3], v.faces)
                       for k, v in enumerate(mont.visuais)])
    return cenas


def mapa(cam, cena):
    depth = np.full((H,W), np.inf)
    ids = np.full((H,W), -1, np.int32)
    normals = np.zeros((H,W,3))
    for k, v, f in cena:
        u, y, z, _ = cam.projetar(v)
        if not np.isfinite(np.column_stack((u,y,z))).all() or np.any(z <= 1e-6):
            raise ValueError("E45-PROJECAO")
        zeros = np.zeros(len(f))
        R._rasterizar(u*W/cam.W,y*H/cam.H,z,np.asarray(f,np.int64),
                      np.full(len(f),k,np.int32),W,H,depth,ids,normals,
                      zeros,zeros,zeros)
    return ids


def planejar(cam, cenas, protegidos):
    if not cenas or not protegidos:
        raise ValueError("E45-EVIDENCIA")
    universo = {k for k,_,_ in cenas[0]}
    if any(len(c)!=len(universo) or {k for k,_,_ in c}!=universo for c in cenas):
        raise ValueError("E45-IDENTIDADE")
    if any(a not in universo or not set(p)<=universo for a,p in protegidos.items()):
        raise ValueError("E45-PROTEGIDOS")
    base = [mapa(cam,c) for c in cenas]
    planos = []
    for alvo, parceiros in sorted(protegidos.items()):
        guarda = set(parceiros)|{alvo}
        solos = [mapa(cam,[m for m in c if m[0]==alvo])==alvo for c in cenas]
        denominadores = [int(s.sum()) for s in solos]
        def medidas(maps):
            return [float(np.count_nonzero((m==alvo)&s)/max(n,8))
                    for m,s,n in zip(maps,solos,denominadores)]
        antes = medidas(base)
        atual = antes
        mapas = base
        ocultos = set()
        for _ in range(MAX_OCULTOS):
            bloqueios = {}
            for m,s in zip(mapas,solos):
                for k,n in zip(*np.unique(m[s],return_counts=True)):
                    if int(k) in universo-guarda-ocultos:
                        bloqueios[int(k)] = bloqueios.get(int(k),0)+int(n)
            melhor = None
            for k in sorted(bloqueios):
                teste = [mapa(cam,[m for m in c if m[0] not in ocultos|{k}]) for c in cenas]
                vals = medidas(teste)
                ganho = float(np.mean(vals)-np.mean(atual))
                if ganho < .02 or min(vals) < min(atual)-1e-12:
                    continue
                nota = (min(vals),float(np.mean(vals)),-k)
                if melhor is None or nota > melhor[0]:
                    melhor = (nota,k,teste,vals)
            if melhor is None:
                break
            _,k,mapas,atual = melhor
            ocultos.add(k)
            if min(atual)>=.70:
                break
        ganho = float(np.mean(atual)-np.mean(antes))
        aceita = bool(ocultos and ganho>=GANHO_MIN and min(atual)>=PIOR_MIN
                      and min(denominadores)>=8)
        planos.append(dict(alvo=alvo,protegidos=sorted(guarda),
            ocultos=sorted(ocultos) if aceita else [],aceita=aceita,
            antes=antes,depois=atual if aceita else antes,
            ganho=ganho if aceita else 0.,motivo=None if aceita else "GANHO_OU_VISIBILIDADE_INSUFICIENTE"))
    return dict(schema="coringa.revelacao.e45.v1",vistas=planos,
                natureza="ocultacao_seletiva_nao_e_corte_solido",
                resolucao=[W,H],poses=len(cenas),publish=False,visual_approved=False)


def previa(mont, qs, cam, protegidos, destino, ffmpeg, font, aviso):
    amostra = np.linspace(0,len(qs)-1,min(5,len(qs)),dtype=int).tolist()
    rel = planejar(cam,preparar(mont,qs,amostra),protegidos)
    rel["indices_auditados"] = amostra
    rel["hash_poses"] = hashlib.sha256(np.asarray(qs,dtype="<f8").tobytes()).hexdigest()
    vistas = [v for v in rel["vistas"] if v["aceita"]]
    if not vistas:
        rel["resultado"] = "SEM_REVELACAO_FUNDAMENTADA"
        return rel
    # Comparação por repetição explícita da mesma trajetória; o original não muda.
    cam = copy.copy(cam)
    cam.W,cam.H = 540,960
    cam.f *= .5
    cam.cx *= .5
    cam.cy *= .5
    fundo = R.fundo_gradiente(cam.W,cam.H)
    indices = np.linspace(0,len(qs)-1,min(48,len(qs)),dtype=int).tolist()
    fps = 24
    destino = Path(destino)
    sequencias = [(None,set())]+[(v["alvo"],set(v["ocultos"])) for v in vistas]
    rel["segmentos"] = []
    cmd = [ffmpeg,"-v","error","-y","-f","rawvideo","-pix_fmt","rgb24",
           "-s","540x960","-r",str(fps),"-i","-","-c:v","libx264","-crf","20",
           "-pix_fmt","yuv420p",str(destino)]
    with subprocess.Popen(cmd,stdin=subprocess.PIPE) as enc:
        for j,(alvo,ocultos) in enumerate(sequencias):
            rel["segmentos"].append(dict(frame_inicio=j*len(indices),indices_pose=indices,
                                       alvo=alvo,ocultos=sorted(ocultos)))
            for i in indices:
                X = mont.poses(qs[i])
                malhas = []
                for k,v in enumerate(mont.visuais):
                    if k in ocultos:
                        continue
                    T = X[v.corpo]@v.local
                    cor = np.array([.92,.58,.17] if k==alvo else [.48,.57,.66])
                    malhas.append((v.vertices@T[:3,:3].T+T[:3,3],v.faces,cor,0.))
                rgb,_ = R.renderizar(cam,malhas,fundo,ss=1,estilo="e33")
                im = Image.fromarray(rgb)
                d = ImageDraw.Draw(im)
                d.text((25,24),"PRÉVIA TÉCNICA PRIVADA",font=font(18,True),fill="#E0E8EF")
                d.text((25,52),"NÚCLEO EXIBIDO" if alvo is None else "VISTA COM PEÇAS OCULTAS",
                       font=font(21,True),fill="#FFD21F")
                d.text((25,650),"Trajetória original" if alvo is None else
                       f"Repetição · {len(ocultos)} peça(s) ocultada(s)",font=font(19),fill="white")
                d.text((25,680),aviso,font=font(16,True),fill="#FFB1A0")
                enc.stdin.write(np.asarray(im).tobytes())
        enc.stdin.close()
        if enc.wait():
            raise RuntimeError("E45-ENCODIFICACAO")
    rel.update(resultado="PREVIA_GERADA",arquivo=destino.name,fps=fps,
               quadros=len(sequencias)*len(indices),
               sha256=hashlib.sha256(destino.read_bytes()).hexdigest())
    return rel


def verificar_previa(path, rel, ffmpeg):
    """Não confunde mudança de vista com movimento dentro de cada segmento."""
    import re
    info = subprocess.run([ffmpeg,"-hide_banner","-i",str(path)],
                          capture_output=True,text=True).stderr
    streams = re.findall(r"Stream #\d+:\d+.*?: (Video|Audio|Data|Subtitle): (.*)",info)
    if (len(streams)!=1 or streams[0][0]!="Video" or
        not streams[0][1].startswith("h264") or
        not re.search(r"\b540x960\b",streams[0][1])):
        raise ValueError("E45-FORMATO")
    raw = subprocess.check_output([ffmpeg,"-v","error","-i",str(path),
        "-vf","scale=270:480","-f","rawvideo","-pix_fmt","rgb24","-"])
    frames = np.frombuffer(raw,np.uint8).reshape(-1,480,270,3)
    if len(frames)!=rel["quadros"]:
        raise ValueError("E45-QUADROS")
    picos=[]
    for s in rel["segmentos"]:
        ini=s["frame_inicio"]
        parte=frames[ini:ini+len(s["indices_pose"]),72:308].astype(np.int16)
        picos.append(int((np.abs(parte-parte[0]).max(-1)>18).sum((1,2)).max()))
    return dict(quadros=len(frames),picos_movimento_por_segmento=picos,
                movimento_em_todos_segmentos=all(p>=300 for p in picos))
