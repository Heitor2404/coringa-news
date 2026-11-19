"""Prepara três pilotos documentais narrados usando o MESMO compositor e fontes do Commons.

Sem tema fixo nas regras. Os três planos são storyboard curado, não saem de IA;
essa rodada mede regressão multiassunto do pipeline com filmagens/fotos reais.
Mídias de origem conservadas com SHA-256. NUNCA publica, aprova ou troca eventos
implicitamente. Edge TTS é apenas VOZ DE TESTE, não substitui Charon de produção.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote, urlsplit

import requests
from PIL import Image

IDENTIFICADOR = re.compile(r"^[a-z0-9_]{3,40}$")
LICENCAS = {"CC BY 4.0", "CC BY 2.0", "CC0", "Public domain", "NASA PD"}
HEADERS = {"User-Agent":"CoringaExplica/4.0 (curadoria de material com crédito verificável)"}


def url_commons(nome: str) -> str:
    """URL canônica Wikimedia por MD5, não busca por semelhança de título."""
    n=nome.replace(" ","_")
    if "/" in n or "\\" in n or not n.lower().endswith((".jpg",".jpeg",".png",".webp")):
        raise ValueError("nome de arquivo inválido")
    h=hashlib.md5(n.encode("utf8")).hexdigest()
    return f"https://upload.wikimedia.org/wikipedia/commons/{h[0]}/{h[:2]}/{quote(n)}"


def _baixar(c: dict, destino: Path) -> dict:
    if c.get("local_video"):
        origem=Path(c["local_video"])
        if not str(origem).startswith("tests/midia/") or not origem.is_file():
            raise RuntimeError(f"{c['id']}: fixture de vídeo ausente")
        data=origem.read_bytes()
        formato="video"
    else:
        url=url_commons(c["commons"])
        data=None
        erros=[]
        for tent in range(3):
            try:
                r=requests.get(url,headers=HEADERS,timeout=110)
                r.raise_for_status()
                data=r.content
                break
            except requests.RequestException as e:
                erros.append(type(e).__name__+":"+str(e)[:100])
        if data is None:
            raise RuntimeError(f"{c['id']}: download original falhou em {url}: {erros}")
        origem=destino/(c["id"]+"."+c["commons"].rsplit(".",1)[1].lower())
        origem.parent.mkdir(parents=True,exist_ok=True)
        origem.write_bytes(data)
        formato="photo"
        with Image.open(origem) as im:
            im.verify()
        with Image.open(origem) as im:
            if min(im.size)<600:
                raise RuntimeError(f"{c['id']}: imagem original inadequada {im.size}")
    if len(data)<25_000 or len(data)>26_000_000:
        raise RuntimeError(f"{c['id']}: arquivo fora do limite de segurança {len(data)} bytes")
    if c["licenca"] not in LICENCAS or not c.get("autor"):
        raise RuntimeError(f"{c['id']}: licença/autor ausentes")
    if urlsplit(c["fonte"]).netloc!="commons.wikimedia.org":
        raise RuntimeError("somente páginas curadas do Commons")
    return {
        "id":c["id"],"local_source":str(origem),"media_type":"video" if formato=="video" else "photo",
        "expected_sha256":hashlib.sha256(data).hexdigest(),
        "license":c["licenca"],"credit":c["autor"],"page":c["fonte"],
        "source_bytes":len(data),"source_media":formato,
        "source_original":url_commons(c["commons"]) if formato=="photo" else c["fonte"]
    }


def compilar_um(ep: dict, midias: list[dict], dur: float) -> dict:
    if not IDENTIFICADOR.fullmatch(ep["id"]) or len(ep["cenas"])!=len(midias):
        raise ValueError("id ou quantidade de cenas inválida")
    shots=[]; media={}
    for i,(c,m) in enumerate(zip(ep["cenas"],midias)):
        if c["id"]!=m["id"]:
            raise ValueError("mídia do episódio fora de ordem")
        key=f"orig_{i+1:02d}"
        tipo="video" if m["media_type"]=="video" else "photo"
        media[key]={k:m[k] for k in ("local_source","media_type","expected_sha256","license","credit","page")}
        inicio=round(i*dur,3)
        end=round((i+1)*dur,3)
        # Registros literais têm referente exato; imagens representativas
        # nunca podem receber local falso.
        lit=bool(c.get("original"))
        x={
            "id":f"{ep['id']}_{i+1:02d}","type":tipo,
            "start":inicio,"end":end,"asset":key,
            "source_in_seconds":0,
            "evidence":"literal" if lit else "representative",
            "lead":f"{i+1:02d} · {ep['dominio'].upper()}",
            "subject":c["prova"][:140],
            "headline":c["titulo"],"highlight":c.get("destaque"),
            "focus":[.5,.5],
            "cues":[{"at":.45,"label":c["titulo"][:44]}],
        }
        if lit:
            x["literal_identity"]=c["prova"]
        shots.append(x)
    return {
        "formato":"filme_editorial","tipo":"PROVA_VISUAL_PRIVADA",
        "titulo":ep["titulo"],"duracao":round(len(shots)*dur,3),
        "media":media,"shots":shots,
        "auditoria_privada":{
            "dominio":ep["dominio"],"roteiro_por_cena":[c["voz"] for c in ep["cenas"]],
            "fontes":[c["fonte"] for c in ep["cenas"]],
            "rotulos_verdadeiros":[c["prova"] for c in ep["cenas"]],
            "narracao_teste":"Edge pt-BR AntonioNeural, proibido publicar",
        },
    }


def preparar(manifesto: dict, root: Path, saida: Path) -> dict:
    from src.v4.formatos.filme_editorial import avaliar
    if manifesto.get("schema")!=1 or len(manifesto.get("episodios") or [])!=3:
        raise ValueError("exigir três temas declarados")
    eps=manifesto["episodios"]
    dominios={x["dominio"] for x in eps}
    if len(dominios)!=3:
        raise ValueError("assuntos repetidos não demonstram generalização")
    saida.mkdir(parents=True,exist_ok=True)
    resumo={}
    for ep in eps:
        d=saida/ep["id"];d.mkdir(parents=True,exist_ok=True)
        stage=Path("tests/midia/qa_multitema")/ep["id"]
        stage.mkdir(parents=True,exist_ok=True)
        with ThreadPoolExecutor(max_workers=4) as pool:
            midias=list(pool.map(lambda c: _baixar(c,stage),ep["cenas"]))
        plan=compilar_um(ep,midias,float(manifesto["duracao_cena"]))
        q=avaliar(plan)
        (d/"preflight.json").write_text(json.dumps(q,indent=2,ensure_ascii=False),encoding="utf-8")
        (d/"fontes.json").write_text(json.dumps(midias,indent=2,ensure_ascii=False),encoding="utf-8")
        (d/"plano.json").write_text(json.dumps(plan,indent=2,ensure_ascii=False),encoding="utf-8")
        if not q["pronto"]:
            raise RuntimeError(f"preflight {ep['id']} BLOQUEADO: {q['bloqueios'][:5]}")
        resumo[ep["id"]]={"roteiro":str(d/"plano.json"),"dominio":ep["dominio"],
                          "cenas":len(ep["cenas"]),"duracao":plan["duracao"],
                          "material_real":len(midias),"fontes_hash_verificadas":True}
    (saida/"preparacao.json").write_text(json.dumps(resumo,indent=2,ensure_ascii=False),encoding="utf-8")
    return resumo


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("manifesto",type=Path)
    ap.add_argument("saida",type=Path)
    o=ap.parse_args(argv)
    m=json.loads(o.manifesto.read_text(encoding="utf-8"))
    print(json.dumps(preparar(m,Path.cwd(),o.saida),ensure_ascii=False))


if __name__=="__main__":
    main()
