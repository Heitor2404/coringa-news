"""Auditoria de montagem REAL após três renderizações, separada de julgamento factual.

A mesma planilha de duas amostras por cena vale para indústria, ciência e
história. Detecta material inválido, áudio ausente, tela vazia, conteúdo congelado.
Não trata variação de pixel como significado narrativo. Falha de item crítico
bloqueia entrega automática; estética e fato seguem pendentes de revisão humana.
"""
from __future__ import annotations

import argparse
import io
import json
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageStat, ImageChops

from src.v4.formatos import contrato_visual_comum as comum
from src.v4.formatos.revisao_filme_editorial import janelas

def _probe(path: Path) -> dict:
    p=subprocess.run(["ffprobe","-v","error","-show_entries",
         "stream=codec_type,width,height,sample_rate,channels:format=duration,size",
         "-of","json",str(path)],capture_output=True,text=True,check=True,timeout=40)
    j=json.loads(p.stdout)
    return {
      "duration":float(j["format"]["duration"]),
      "size":int(j["format"]["size"]),
      "audio":next((x for x in j["streams"] if x.get("codec_type")=="audio"),None),
      "video":next((x for x in j["streams"] if x.get("codec_type")=="video"),None),
    }

def _frame(video: Path,t:float)->Image.Image:
    res=subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-ss",str(t),"-i",str(video),
        "-frames:v","1","-vf","scale=270:480",
        "-f","image2pipe","-vcodec","png","pipe:1"],
        capture_output=True,check=True,timeout=45)
    return Image.open(io.BytesIO(res.stdout)).convert("RGB")

def auditar(plano:dict,video:Path,saida:Path)->dict:
    if plano.get("formato")!="filme_editorial":
        raise ValueError("exige o compositor real FilmeEditorial")
    video=Path(video)
    if not video.is_file():
        raise RuntimeError("vídeo não foi gerado")
    saida=Path(saida);saida.mkdir(parents=True,exist_ok=True)
    s=_probe(video)
    problemas=[]
    if abs(s["duration"]-float(plano["duracao"]))>.18:
        problemas.append("QA-DURACAO-DIVERGENTE")
    if not s["audio"] or not s["video"]:
        problemas.append("QA-SEM-TRILHA-AUDIO-OU-VIDEO")
    if s["size"]<90000:
        problemas.append("QA-ARQUIVO-VAZIO")
    jornadas=janelas(plano)
    if len(jornadas)!=len(plano["shots"]):
        problemas.append("QA-QUADROS-SEM-CENA")
    cols=4;rows=len(jornadas)
    sheet=Image.new("RGB",(cols*270,rows*(480+34)),(17,28,36))
    draw=ImageDraw.Draw(sheet)
    items=[]
    for i,w in enumerate(jornadas):
        # Cada cena recebe duas amostras, mais uma próxima ao corte.
        shot=next(x for x in plano["shots"] if x["id"]==w["id"])
        samples=[(float(shot["start"])+.15),
                 w["t0"],w["t1"],float(shot["end"])-.11]
        imagens=[_frame(video,max(0,min(t,s["duration"]-.08))) for t in samples]
        for j,(im,t) in enumerate(zip(imagens,samples)):
            x=j*270;y=i*(480+34)
            sheet.paste(im,(x,y+34))
            draw.text((x+7,y+6),f"{shot['id'][-2:]}: {t:.2f}s",fill=(255,242,210))
        diff=ImageChops.difference(imagens[1].convert("L"),imagens[2].convert("L"))
        variation=round(ImageStat.Stat(diff).mean[0],2)
        # Na área central onde deveriam estar pessoas/objetos.
        center=imagens[2].crop((30,92,240,360)).convert("L")
        stat=ImageStat.Stat(center)
        luminosidade=round(stat.mean[0],2)
        quase_preto=sum(1 for x in center.getdata() if x<13)/len(list(center.getdata()))
        if luminosidade<12 or quase_preto>.92:
            problemas.append(f"QA-CENA-ESCURA:{shot['id']}")
        if variation<.2:
            problemas.append(f"QA-SEM-PROGRESSAO-PIXEL:{shot['id']}")
        items.append({
          "shot":shot["id"],"inicio":shot["start"],"fim":shot["end"],
          "rotulo":shot["headline"],"proveniencia":shot["evidence"],
          "prova_esperada":shot["subject"],
          "media":(plano.get("media",{}).get(shot.get("asset")) or {}).get("page")
                  or "NÃO INFORMADA",
          "assinatura_variacao_pixels":variation,
          "luminancia_central":luminosidade,
          "fracao_quase_preta":round(quase_preto,3),
          "prova_real_foi_vista":"PENDENTE_AVALIACAO_HUMANA",
          "voz_corresponde_a_acao":"PENDENTE_AVALIACAO_HUMANA",
          "enquadramento_seguro":"PENDENTE_AVALIACAO_HUMANA"
        })
    sheet.save(saida/"contato_editorial.jpg",quality=87,optimize=True)
    comp=comum.auditar(plano)
    if not comp["estrutura_declarada_ok"]:
        problemas.append("QA-CONTRATO-ESTRUTURAL-REPROVADO")
    rel={
      "status_tecnico":"BLOQUEADO" if problemas else "PRONTO_PARA_REVISAO",
      "problemas_tecnicos":problemas,
      "arquivo":str(video),"duracao":round(s["duration"],3),
      "bytes":s["size"],
      "tem_audio":bool(s["audio"]),
      "amostras_editoriais":items,
      "contrato_comum":comp,
      "inspecao_semantica":"PENDENTE",
      "nota":"Variação de pixels NÃO mede prova factual nem qualidade de corte",
      "publicavel":False,"aprovacao_humana":"PENDENTE"
    }
    (saida/"qa_montagem.json").write_text(json.dumps(rel,ensure_ascii=False,indent=2),encoding="utf-8")
    return rel

def main():
    p=argparse.ArgumentParser()
    p.add_argument("plano",type=Path);p.add_argument("video",type=Path);p.add_argument("saida",type=Path)
    a=p.parse_args()
    r=auditar(json.loads(a.plano.read_text(encoding="utf-8")),a.video,a.saida)
    print(json.dumps({"status":r["status_tecnico"],
       "cenas":len(r["amostras_editoriais"]),
       "problemas":r["problemas_tecnicos"],
       "aprovacao":r["aprovacao_humana"],
       "arquivo":r["arquivo"]},ensure_ascii=False))
    return 0 if r["status_tecnico"]=="PRONTO_PARA_REVISAO" else 1

if __name__=="__main__":
    raise SystemExit(main())
