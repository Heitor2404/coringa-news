"""Ponte ATLAS (Formato/PalcoMapa MapLibre) -> clipe documental reutilizável.

NÃO desenha mapas. Só aceita um plano ATLAS já resolvido e aprovado pelo
fiscal cartográfico nativo, copia exatamente os rasters registrados por SHA,
exporta props para o Remotion Formato ORIGINAL e autentica o MP4 renderizado.
A saída vai ao FilmeEditorial como mídia EXPLICATIVA, nunca filmagem histórica.
O atestado é TÉCNICO; não simula inspeção multimodal nem aprovação humana.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
from pathlib import Path

from src.v4.formatos import plano as ATLAS

ROOT = ATLAS.RAIZ
ALLOWED = {"Domínio público", "CC BY 4.0", "Public domain", "CC0"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024 * 1024),b""):
            h.update(chunk)
    return h.hexdigest()


def jwrite(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")


def _dentro(path: Path, root: Path) -> Path:
    p=Path(path).resolve()
    if not p.is_relative_to(Path(root).resolve()):
        raise ValueError("caminho fora da pasta confiável do projeto")
    return p


def verificar_plano(atlas: dict, start: float, dur: float) -> dict:
    if atlas.get("formato")!="atlas" or atlas.get("canal")!="coringa" or atlas.get("_resolvido") is not True:
        raise ValueError("plano ATLAS resolvido e canal coringa obrigatórios; não sintetizar geografia")
    if not isinstance(start,(int,float)) or not isinstance(dur,(int,float)) or not (
        math.isfinite(start) and math.isfinite(dur) and start>=0 and 1.4<=dur<=8 and start+dur<=atlas["duracao"]+.001):
        raise ValueError("intervalo do clipe inválido")
    # O fixture versionado guarda beats numéricos mas não necessariamente
    # o palco derivado; aplicar o MESMO resolver do ATLAS é obrigatório.
    atlas=ATLAS.resolver_tempos(atlas,[]) if not atlas.get("palco") else atlas
    viol=[v for v in ATLAS.validar(atlas) if v["gravidade"]=="erro"]
    if viol:
        raise ValueError("reprovação no fiscal ATLAS original: "+str([(v["regra"],v["onde"]) for v in viol[:5]]))
    # NÃO exportar transição escura entre palco documental e mapa.
    # No Formato.tsx, op('mapa') entra em 0,5s; se o trecho começa antes,
    # o começo do MP4 exibe a cena anterior/um quadro quase vazio.
    palco=atlas["palco"]
    indices=[i for i,p in enumerate(palco) if float(p["t"])<=start+.001]
    if not indices:
        raise ValueError("início antes do primeiro palco")
    idx=indices[-1]
    key=palco[idx]
    if key["tipo"]!="mapa":
        raise ValueError("trecho selecionado não usa palco cartográfico ATLAS")
    prev=palco[idx-1] if idx else None
    if prev and prev["tipo"]!="mapa" and start<float(key["t"])+.55:
        raise ValueError("F-ATLAS-ENTRADA-ESCURA: iniciar mapa após 0,55 s da troca de palco")
    if idx+1<len(palco) and start+dur>float(palco[idx+1]["t"])+.001:
        raise ValueError("F-ATLAS-ATRAVESSA-BEAT: este clipe deve preservar um único beat cartográfico")
    t=start+min(dur*.55,dur-.1)
    beat=next((b for b in atlas["beats"] if b.get("composicao")==key.get("composicao")
              and abs(float(b.get("t",-999))-float(key["t"]))<.01),None)
    if not beat or not beat.get("roi"):
        raise ValueError("beat sem ROI cartográfico comprovado")
    # Não basta cobrir um ponto; exigir raster nítido e visível no enquadramento.
    from src.v4.formatos import atlas_ref
    ds=atlas_ref.datasets()
    cam=ATLAS.camera_em(atlas["palco"],t)
    if not cam:
        raise ValueError("câmera ATLAS ausente")
    real=[]
    for r in atlas.get("rasters") or []:
        meta=ATLAS.raster_info(r["nome"])
        src=ATLAS.RASTER_DIR/(meta.get("arquivo") or r["nome"]+".jpg")
        if not src.is_file() or sha256(src)!=meta.get("sha256"):
            raise ValueError(f"raster ATLAS adulterado ou ausente: {r['nome']}")
        fonte=ds.get(meta.get("dataset") or "") or {}
        if not fonte.get("uso_comercial") or not meta.get("atribuicao") or not meta.get("sha256"):
            raise ValueError(f"raster sem licença/atribuição comercial aprovada: {r['nome']}")
        if ATLAS.cobre(meta,beat["roi"]) and ATLAS.opacidade_raster(cam["zoom"],r.get("de"),r.get("ate"))>.02 and meta["nitido_ate"]>=cam["zoom"]:
            real.append({"nome":r["nome"],"dataset":meta.get("dataset"),"sha256":meta["sha256"],
                         "arquivo":str(src.relative_to(ROOT)),
                         "atribuicao":meta["atribuicao"]})
    if not real:
        raise ValueError("F-MAPA-SEM-BASE / F-MAPA-BAIXA-RESOLUCAO: sem raster REAL nítido em tela")
    if atlas_ref.proibido(json.dumps(atlas.get("rasters",[]),ensure_ascii=False)):
        raise ValueError("dataset cartográfico proibido")
    return {"palco":"PalcoMapa/MapLibre","beat":beat["id"],"roi":beat["roi"],
            "cam_zoom":cam["zoom"],"rasters_ativos":real,
            "origem_geografica":atlas.get("geo")}


def preparar(atlas: dict, start:float, dur:float, pasta:Path, public:Path) -> dict:
    atlas=ATLAS.resolver_tempos(atlas,[]) if not atlas.get("palco") else atlas
    proof=verificar_plano(atlas,start,dur)
    pasta=Path(pasta);pasta.mkdir(parents=True,exist_ok=True)
    public=Path(public);public.mkdir(parents=True,exist_ok=True)
    # Mesma estrutura e mesmo material do ATLAS produtivo.
    dest_raster=public/"_formato"/"raster"
    dest_raster.mkdir(parents=True,exist_ok=True)
    for r in atlas.get("rasters") or []:
        meta=ATLAS.raster_info(r["nome"])
        src=ATLAS.RASTER_DIR/(meta.get("arquivo") or r["nome"]+".jpg")
        if sha256(src)!=meta["sha256"]:
            raise ValueError("raster mudou durante preparação")
        dest=dest_raster/src.name
        shutil.copyfile(src,dest)
        if sha256(dest)!=meta["sha256"]:
            raise ValueError("cópia de raster divergente")
    geo_path=_dentro(ROOT/atlas["geo"],ROOT)
    geo=json.loads(geo_path.read_text(encoding="utf-8"))
    if "Natural Earth" not in " ".join((geo.get("meta") or {}).get("atribuicao") or []):
        raise ValueError("geometria sem atribuição Natural Earth")
    props=ATLAS.props(atlas,ATLAS.tokens_canal(ATLAS.canal("coringa")),geo,{})
    jwrite(pasta/"props_atlas_formato.json",props)
    k={"schema":1,"renderer":"ATLAS/Formato/PalcoMapa/MapLibre",
       "palco_original":"Formato","atlas_sha256":hashlib.sha256(json.dumps(atlas,sort_keys=True).encode()).hexdigest(),
       "props_sha256":sha256(pasta/"props_atlas_formato.json"),
       "inicio_s":start,"duracao_s":dur,
       "frame_inicio":int(round(start*30)),"frame_fim_inclusivo":int(round((start+dur)*30))-1,
       "quadro_alvo":[1080,1920],"fps":30,
       "mapeamento":proof,"status":"PREPARADO_NAO_RENDERIZADO",
       "aprovacao_humana":"PENDENTE","publicado":False}
    jwrite(pasta/"preparo_atlas.json",k)
    return k


def confirmar(preparo:dict, mp4:Path, pasta:Path) -> dict:
    mp4=Path(mp4)
    if not mp4.is_file():
        raise ValueError("clipe ATLAS ausente: "+str(mp4))
    if mp4.stat().st_size==0:
        raise ValueError("clipe ATLAS vazio: "+str(mp4))
    # Compressed byte size does not establish whether a map is valid.
    # Verify the complete decoded stream below instead of a fixed byte floor.
    if preparo.get("renderer")!="ATLAS/Formato/PalcoMapa/MapLibre":
        raise ValueError("preparo não é do motor cartográfico ATLAS")
    probe=subprocess.run(["ffprobe","-v","error","-show_entries",
       "stream=codec_type,width,height,r_frame_rate,nb_frames:format=duration",
       "-of","json",str(mp4)],capture_output=True,text=True,check=True,timeout=40)
    d=json.loads(probe.stdout)
    video=next((x for x in d.get("streams",[]) if x.get("codec_type")=="video"),{})
    if ((video.get("width"),video.get("height"))!=(1080,1920) or
        any(x.get("codec_type")=="audio" for x in d.get("streams",[])) or
        abs(float(d["format"]["duration"])-preparo["duracao_s"])>.07):
        raise ValueError("MP4 não coincide com intervalo ATLAS, dimensão ou natureza silenciosa")
    from fractions import Fraction
    expected=preparo["frame_fim_inclusivo"]-preparo["frame_inicio"]+1
    if Fraction(video.get("r_frame_rate","0/1"))!=30 or int(video.get("nb_frames") or 0)!=expected:
        raise ValueError("MP4 ATLAS com FPS ou contagem de quadros divergente")
    # Decode the entire video, with errors fatal; metadata alone is insufficient.
    decoded=subprocess.run(["ffmpeg","-v","error","-xerror","-i",str(mp4),
        "-map","0:v:0","-progress","pipe:1","-nostats","-f","null","-"],
        capture_output=True,text=True,check=True,timeout=90)
    counts=[int(line.split("=",1)[1]) for line in decoded.stdout.splitlines()
            if line.startswith("frame=")]
    if not counts or counts[-1]!=expected:
        raise ValueError("MP4 ATLAS com quadros decodificados divergentes")
    from PIL import Image,ImageStat
    from io import BytesIO
    checks=[]
    for frac in (.14,.5,.84):
        t=float(d["format"]["duration"])*frac
        z=subprocess.run(["ffmpeg","-hide_banner","-loglevel","error",
             "-ss",f"{t:.3f}","-i",str(mp4),"-frames:v","1",
             "-vf","scale=270:480","-f","image2pipe","-vcodec","png","pipe:1"],
             capture_output=True,check=True,timeout=50)
        im=Image.open(BytesIO(z.stdout)).convert("RGB")
        gray=ImageStat.Stat(im.convert("L"))
        if gray.mean[0]<7:
            raise ValueError("F-MAPA-QUADRO-ESCURO: raster ausente no vídeo real")
        if gray.stddev[0]<2:
            raise ValueError("F-MAPA-QUADRO-UNIFORME: ausência de informação visual na amostra")
        checks.append({"t":round(t,2),"luminancia":round(gray.mean[0],2),"contraste":round(gray.stddev[0],2)})
    rel={**preparo,"status":"PRONTO_PARA_REVISAO_HUMANA",
         "video_sha256":sha256(mp4),"video_bytes":mp4.stat().st_size,
         "quadros_reais":checks,"quadros_decodificados":counts[-1],"exame_semantico":"PENDENTE",
         "qualidade_estetica":"NAO_INSPECIONADA",
         "aprovacao_humana":"PENDENTE","publicado":False}
    jwrite(Path(pasta)/"comprovante_atlas.json",rel)
    return rel


def inserir_no_filme(plano_filme:dict, shot_id:str, clip:Path, comprovante:Path,
                     intencao:str='localizar') -> dict:
    """Substitui apenas uma cena DECLARADA pelo roteiro. Não escolhe assunto por conta própria.

    Clipes ainda são prévias privadas até revisão humana. Não confundir o mapa
    com registro filmado do evento, nem associar outro país por semelhança.
    """
    import copy
    if intencao not in ('localizar','trajeto'):
        raise ValueError("intenção deve ser localizar ou trajeto")
    clip,comprovante=Path(clip),Path(comprovante)
    rel=json.loads(comprovante.read_text(encoding="utf-8"))
    media={"local_source":str(clip),"atlas_proof":str(comprovante),
           "expected_sha256":rel["video_sha256"],"media_type":"video",
           "page":"https://www.naturalearthdata.com/",
           "license":"CC BY 4.0" if any("Sentinel" in r["atribuicao"]
                      for r in rel["mapeamento"]["rasters_ativos"]) else "Natural Earth PD",
           "credit":" · ".join(dict.fromkeys(r["atribuicao"] for r in rel["mapeamento"]["rasters_ativos"]))}
    problemas=validar_comprovante(media)
    if problemas:
        raise ValueError("clipe atlas-map não validado: "+"; ".join(problemas))
    p=copy.deepcopy(plano_filme)
    if p.get("formato")!="filme_editorial" or p.get("tipo")!="PROVA_VISUAL_PRIVADA":
        raise ValueError("inserção automática só em prova visual privada")
    alvo=[s for s in p.get("shots") or [] if s.get("id")==shot_id]
    if len(alvo)!=1:
        raise ValueError("identificador de cena não é único")
    shot=alvo[0]
    span=float(shot["end"])-float(shot["start"])
    if abs(span-float(rel["duracao_s"]))>.06:
        raise ValueError("duração do mapa não corresponde à cena; retemporizar ANTES de renderizar")
    if not isinstance(shot.get("headline"),str) or not shot["headline"]:
        raise ValueError("roteiro sem informação")
    ident="atlas_map_"+rel["video_sha256"][:14]
    p.setdefault("media",{})[ident]=media
    shot["type"]="atlas_map"
    shot["asset"]=ident
    for campo in ("assetB","mechanism","reference_asset","literal_identity","map"):
        shot.pop(campo,None)
    shot["evidence"]="explainer"
    shot["source_in_seconds"]=0
    shot["atlas_direcao"]={"intencao":intencao,"roi":rel["mapeamento"]["roi"],
                          "palco":"ATLAS/Formato/PalcoMapa"}
    shot["direcao_evento"]={"intencao":intencao,"fato_id":"mapa-"+shot_id,
                           "aprendizado":shot["headline"]}
    shot["subject"]="Cartografia ATLAS real com base raster, câmera e fontes conferidas"
    return p


def validar_comprovante(media:dict) -> list[str]:
    """Validar prova e SHA do clipe, SEM confiar em strings do storyboard."""
    errors=[]
    if not isinstance(media,dict):
        return ["mídia ATLAS ausente"]
    source=media.get("local_source")
    proof=media.get("atlas_proof")
    if not isinstance(source,str) or not isinstance(proof,str):
        return ["caminho/prova ATLAS ausente"]
    src=Path(source);pr=Path(proof)
    for p in (src,pr):
        if p.is_absolute() or ".." in p.parts or not str(p).startswith("stage_atlas/"):
            return ["origem ATLAS fora da pasta de staging autorizada"]
    if not src.is_file() or not pr.is_file():
        return ["clipe ou comprovante ATLAS ausente"]
    try:
        q=json.loads(pr.read_text(encoding="utf-8"))
    except (OSError,ValueError):
        return ["comprovante ATLAS inválido"]
    if q.get("renderer")!="ATLAS/Formato/PalcoMapa/MapLibre" or q.get("status")!="PRONTO_PARA_REVISAO_HUMANA":
        errors.append("não é render ATLAS MapLibre aprovado no preflight técnico")
    if q.get("aprovacao_humana")!="PENDENTE" or q.get("publicado") is not False:
        errors.append("comprovante com estado editorial incoerente")
    if q.get("video_sha256")!=sha256(src) or media.get("expected_sha256")!=q.get("video_sha256"):
        errors.append("MP4 não é o clipe identificado por SHA no comprovante")
    if not q.get("mapeamento",{}).get("rasters_ativos") or not q.get("quadros_reais"):
        errors.append("sem raster real e amostras de quadros auditadas")
    return errors


def main(argv=None):
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("prepare")
    a.add_argument("atlas",type=Path);a.add_argument("saida",type=Path)
    a.add_argument("--start",type=float,required=True);a.add_argument("--duration",type=float,required=True)
    a.add_argument("--public",type=Path,default=ROOT/"motor4/remotion/public")
    b=sub.add_parser("confirm")
    b.add_argument("saida",type=Path);b.add_argument("mp4",type=Path)
    c=sub.add_parser("attach")
    c.add_argument("filme",type=Path)
    c.add_argument("cena")
    c.add_argument("mp4",type=Path)
    c.add_argument("comprovante",type=Path)
    c.add_argument("saida",type=Path)
    c.add_argument("--intent",choices=("localizar","trajeto"),default="localizar")
    args=ap.parse_args(argv)
    if args.cmd=="prepare":
        p=json.loads(args.atlas.read_text(encoding="utf-8"))
        r=preparar(p,args.start,args.duration,args.saida,args.public)
    elif args.cmd=="confirm":
        p=json.loads((args.saida/"preparo_atlas.json").read_text(encoding="utf-8"))
        r=confirmar(p,args.mp4,args.saida)
    else:
        from src.v4.formatos.filme_editorial import avaliar
        p=json.loads(args.filme.read_text(encoding="utf-8"))
        patched=inserir_no_filme(p,args.cena,args.mp4,args.comprovante,args.intent)
        q=avaliar(patched)
        if not q["pronto"]:
            raise ValueError("FilmeEditorial recusou a ponte: "+
                             json.dumps(q["bloqueios"][:7],ensure_ascii=False))
        jwrite(args.saida,patched)
        print(json.dumps({"status":"PONTE_INSERIDA_EM_STORYBOARD_PRIVADO",
                          "cena":args.cena,"arquivo":str(args.saida),
                          "aprovacao_humana":"PENDENTE","publicado":False},ensure_ascii=False))
        return
    print(json.dumps({k:r[k] for k in ("status","renderer","duracao_s","aprovacao_humana")},ensure_ascii=False))


if __name__=="__main__":
    main()
