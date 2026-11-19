"""Narração de teste para três storyboards, sem gastar Gemini ou Claude.

Edge TTS, mesma interface para todos os temas, sem áudio de terceiros.
Se indisponível, ERRO explícito, sem fallback escondido para voz de produção.
Cada frase é sincronizada ao começo da cena; registra aceleração e duração.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
from pathlib import Path

VOZ="pt-BR-AntonioNeural"
RATE="+10%"


def sonda(arq: Path) -> float:
    p=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                      "-of","default=nw=1:nk=1",str(arq)],
                     capture_output=True,text=True,check=True,timeout=20)
    return float(p.stdout.strip())


async def _falar(texto: str, mp3: Path):
    import edge_tts
    erros=[]
    for tentativa in range(2):
        try:
            await edge_tts.Communicate(texto,VOZ,rate=RATE).save(str(mp3))
            if mp3.stat().st_size<2500:
                raise RuntimeError("retorno de voz vazio")
            return
        except Exception as ex:
            erros.append(f"{type(ex).__name__}: {str(ex)[:180]}")
            if tentativa==0:
                await asyncio.sleep(3)
    raise RuntimeError(f"Edge TTS indisponível: {'; '.join(erros)}")


def falar_cenas(plano: dict,saida: Path) -> dict:
    textos=(plano.get("auditoria_privada") or {}).get("roteiro_por_cena") or []
    cenas=plano.get("shots") or []
    if len(textos)!=len(cenas) or not textos:
        raise ValueError("ausência de texto narrado para cada cena")
    saida.mkdir(parents=True,exist_ok=True)
    clipPaths=[]
    velocidades=[]
    resumo=[]
    for i,(c,texto) in enumerate(zip(cenas,textos)):
        if not texto or len(texto)>220:
            raise ValueError(f"{c['id']}: frase de voz inválida")
        alvo=round(float(c["end"])-float(c["start"]),3)
        raw=saida/f"fala_{i+1:02d}.mp3"
        asyncio.run(_falar(texto,raw))
        dur=sonda(raw)
        # Ajuste máximo controlado para não mascarar roteiro que não cabe.
        velocidade=max(1.0,dur/max(.4,alvo-.1))
        if velocidade>1.60:
            raise RuntimeError(f"fala {i+1} longa demais {dur:.2f}s / {alvo:.2f}s; reescrever")
        out=saida/f"fala_{i+1:02d}.wav"
        subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(raw),
            "-af",f"atempo={velocidade:.5f},aresample=48000,aformat=channel_layouts=mono,apad,atrim=0:{alvo:.3f}",
            "-ar","48000","-ac","1","-c:a","pcm_s16le",str(out)],check=True,timeout=35)
        clipPaths.append(out)
        velocidades.append(velocidade)
        resumo.append({"cena":c["id"],"texto":texto,"voz_bruta_s":round(dur,3),
                       "alvo_s":alvo,"tempo_aplicado":round(velocidade,3)})
    args=["ffmpeg","-hide_banner","-loglevel","error","-y"]
    for f in clipPaths:
        args+=["-i",str(f)]
    filt="".join(f"[{i}:a]asetpts=PTS-STARTPTS[a{i}];" for i in range(len(clipPaths)))
    filt+="".join(f"[a{i}]" for i in range(len(clipPaths)))
    filt+=f"concat=n={len(clipPaths)}:v=0:a=1[out]"
    target=saida/"narracao.wav"
    subprocess.run(args+["-filter_complex",filt,"-map","[out]","-ar","48000",
                         "-ac","1","-c:a","pcm_s16le",str(target)],
                   check=True,timeout=40)
    d=sonda(target)
    if abs(d-plano["duracao"])>.16:
        raise RuntimeError(f"narração não sincronizada: {d} x {plano['duracao']}")
    r={"motor":"edge-tts","voz":VOZ,"rate":RATE,"cenas":resumo,
       "duracao":round(d,3),"voz_de_producao":False,
       "aprovacao_de_audio":"PENDENTE"}
    (saida/"narracao_qa.json").write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding="utf-8")
    return r


def unir(video: Path, voz: Path, saida: Path) -> Path:
    saida.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
        "-i",str(video),"-i",str(voz),
        "-map","0:v:0","-map","1:a:0",
        "-c:v","copy","-c:a","aac","-b:a","160k","-ar","48000","-ac","1",
        "-af","loudnorm=I=-14:TP=-1:LRA=9",
        "-shortest","-movflags","+faststart",str(saida)],check=True,timeout=80)
    return saida


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("plano",type=Path)
    ap.add_argument("video_visual",type=Path)
    ap.add_argument("saida",type=Path)
    a=ap.parse_args()
    plano=json.loads(a.plano.read_text(encoding="utf8"))
    resumo=falar_cenas(plano,a.saida)
    unir(a.video_visual,a.saida/"narracao.wav",a.saida/"episodio_narrado.mp4")
    print(json.dumps({"status":"NARRADO_PRIVADO","cenas":len(resumo["cenas"]),
                      "duracao":resumo["duracao"],
                      "arquivo":str(a.saida/"episodio_narrado.mp4")},ensure_ascii=False))


if __name__=="__main__":
    main()
