"""Três domínios, arquivos de vídeo de origem real e regra honesta de substituição.

Amostra MP4s e cria evidência para revisão humana; NÃO infere fato histórico,
adequação da ação narrada, identidade ou licença a partir de mudança de pixels.
Falta de prova visual SEMPRE permanece pendente.
"""
from __future__ import annotations

import hashlib
import io
import json
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops, ImageStat

DOMINIOS = ("engenharia", "ciencia", "historia")


def decidir_uso(*, acontecimento: str, evento_da_midia: str, uso: str,
                cena_especifica: bool, rotulo: str = "",
                origem_verificada: bool, licenca_verificada: bool,
                representacao: dict | None = None) -> dict:
    """Nunca permitir que material de OUTRO evento prove a cena narrada.

    Um b-roll de outro conflito só pode ilustrar uma frase genérica, e
    sempre com legenda revelando seu evento verdadeiro. Registro fiel
    depende ainda de checagem visual independente.
    """
    if not origem_verificada or not licenca_verificada:
        return {"permitido":False,"codigo":"M-SEM-PROVENIENCIA","categoria":"BLOQUEADO"}
    if uso not in ("registro", "contexto", "ilustracao"):
        return {"permitido":False,"codigo":"M-USO-DESCONHECIDO","categoria":"BLOQUEADO"}
    mesmo = bool(acontecimento and evento_da_midia and
                 acontecimento.strip().casefold() == evento_da_midia.strip().casefold())
    if uso == "registro":
        return ({"permitido":True,"codigo":"M-IDENTIDADE-DECLARADA-INSPECAO-PENDENTE",
                 "categoria":"REGISTRO_CANDIDATO","prova_do_fato":False}
                if mesmo else
                {"permitido":False,"codigo":"M-OUTRO-EVENTO-NAO-E-PROVA",
                 "categoria":"BLOQUEADO","prova_do_fato":False})
    # Ilustração de um PROCESSO tecnicamente equivalente não é substituição
    # do registro de um evento. NIST pode mostrar deposição real para explicar
    # deposição em wafers; e-beam não pode virar EUV, nem conflito A conflito B.
    # A fala não deve alegar que vemos a entidade/lugar/evento específico.
    if uso in ("ilustracao", "demonstracao") and isinstance(representacao, dict) and not mesmo:
        rep = representacao
        processo = str(rep.get("processo_narrado") or "").strip().casefold()
        registrado = str(rep.get("processo_midia") or "").strip().casefold()
        origem_credito = str(rep.get("origem_no_credito") or "").strip().casefold()
        if (rep.get("fala_atribui_registro") is True or
                rep.get("tipo") != "processo_equivalente"):
            return {"permitido":False,"codigo":"M-REGISTRO-NAO-REPRESENTAVEL",
                    "categoria":"BLOQUEADO","prova_do_fato":False}
        if not (processo and registrado and len(processo)>=8 and
                processo == registrado and
                rep.get("compatibilidade_tecnica_verificada") is True and
                isinstance(rep.get("evidencia_inspecao"), str) and
                len(rep["evidencia_inspecao"].strip()) >= 12):
            return {"permitido":False,"codigo":"M-PROCESSO-NAO-EQUIVALENTE",
                    "categoria":"BLOQUEADO","prova_do_fato":False}
        if not origem_credito or evento_da_midia.strip().casefold() not in origem_credito:
            return {"permitido":False,"codigo":"M-ORIGEM-NAO-IDENTIFICADA",
                    "categoria":"BLOQUEADO","prova_do_fato":False}
        return {"permitido":True,"codigo":"M-PROCESSO-EQUIVALENTE-COM-ORIGEM",
                "categoria":"ILUSTRACAO_TECNICA","prova_do_fato":False,
                "aprovacao_humana":"PENDENTE"}

    # Quando a fala narra o evento específico, inserir imagens de outro
    # desastre/guerra mesmo com etiqueta troca visualmente a identidade.
    if not mesmo and cena_especifica:
        return {"permitido":False,"codigo":"M-SUBSTITUICAO-ENGANOSA",
                "categoria":"BLOQUEADO","prova_do_fato":False}
    if not mesmo:
        # Exigir identificação clara do evento de origem, não só "arquivo".
        if not evento_da_midia or evento_da_midia.casefold() not in rotulo.casefold():
            return {"permitido":False,"codigo":"M-ORIGEM-NAO-IDENTIFICADA",
                    "categoria":"BLOQUEADO","prova_do_fato":False}
    if not rotulo.strip():
        return {"permitido":False,"codigo":"M-SEM-ROTULO-CONTEXTO",
                "categoria":"BLOQUEADO","prova_do_fato":False}
    return {"permitido":True,"codigo":"M-CONTEXTO-ROTULADO-REVISAO-PENDENTE",
            "categoria":"CONTEXTO_OU_ILUSTRACAO","prova_do_fato":False}


def _probe(arquivo: Path) -> dict:
    p=subprocess.run(["ffprobe","-v","error","-show_entries",
          "stream=codec_type,width,height:format=duration,size","-of","json",
          str(arquivo)],capture_output=True,text=True,check=True,timeout=35)
    d=json.loads(p.stdout)
    v=next((s for s in d["streams"] if s.get("codec_type")=="video"),None)
    if not v:
        raise ValueError(f"sem faixa de vídeo: {arquivo}")
    return {"largura":int(v["width"]),"altura":int(v["height"]),
            "duracao":float(d["format"]["duration"]),"bytes":arquivo.stat().st_size}


def _frame(arquivo: Path, at: float) -> Image.Image:
    png=subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-ss",
      f"{at:.3f}","-i",str(arquivo),"-frames:v","1","-vf",
      "scale=300:-2","-f","image2pipe","-vcodec","png","pipe:1"],
      check=True,capture_output=True,timeout=50).stdout
    return Image.open(io.BytesIO(png)).convert("RGB")


def auditar_fontes(manifesto: dict, raiz: Path, saida: Path) -> dict:
    """Audita vídeos existentes — nunca cria vídeo nem aprova edição."""
    saida=Path(saida);saida.mkdir(parents=True,exist_ok=True)
    arquivos=manifesto.get("itens") or []
    if len(arquivos)!=3 or {x["dominio"] for x in arquivos}!=set(DOMINIOS):
        raise ValueError("exigir engenharia, ciência e história reais e distintos")
    grid=Image.new("RGB",(5*270,3*(170+38)),(10,18,28))
    draw=ImageDraw.Draw(grid)
    resultados=[]
    for i,fonte in enumerate(arquivos):
        p=(Path(raiz)/fonte["arquivo"]).resolve()
        if not p.is_file() or p.stat().st_size<100000:
            raise ValueError(f"arquivo ausente ou vazio: {fonte['id']}")
        info=_probe(p)
        if info["duracao"]<4:
            raise ValueError(f"mídia curta/inválida: {fonte['id']}")
        checksums={"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
                   "sha1":hashlib.sha1(p.read_bytes()).hexdigest()}
        if fonte.get("sha1_esperado") and checksums["sha1"]!=fonte["sha1_esperado"]:
            raise ValueError("SHA-1 do arquivo histórico difere da declaração de origem")
        # Arquivo por frame, sem IA e sem alegar que 5 quadros mostram a ação.
        instantes=[info["duracao"]*f for f in (.04,.19,.40,.65,.87)]
        quadros=[_frame(p,t) for t in instantes]
        mudancas=[]
        for a,b in zip(quadros,quadros[1:]):
            a1=a.resize((240,135)).convert("L")
            b1=b.resize((240,135)).convert("L")
            mudancas.append(round(ImageStat.Stat(ImageChops.difference(a1,b1)).mean[0],2))
        for j,(im,t) in enumerate(zip(quadros,instantes)):
            im.thumbnail((262,154))
            cx=j*270;cy=i*(170+38)
            grid.paste(im,(cx+(270-im.width)//2,cy+39+(154-im.height)//2))
            draw.text((cx+6,cy+7),f"{fonte['dominio']} {t:.1f}s",fill="#FFFFFF")
        # "Movimentou" é apenas métrica técnica, NUNCA "demonstrou acontecimento".
        uso=decidir_uso(acontecimento=fonte["acontecimento"],
                       evento_da_midia=fonte["evento_da_midia"],uso=fonte["uso"],
                       cena_especifica=fonte["cena_especifica"],
                       rotulo=fonte["rotulo"],origem_verificada=bool(fonte.get("pagina")),
                       licenca_verificada=bool(fonte.get("licenca")))
        resultados.append({
            "id":fonte["id"],"dominio":fonte["dominio"],"titulo":fonte["titulo"],
            "pagina":fonte["pagina"],"licenca_declarada":fonte["licenca"],
            "arquivo":str(fonte["arquivo"]),"sha256_real":checksums["sha256"],
            "largura":info["largura"],"altura":info["altura"],
            "duracao":round(info["duracao"],3),"variacao_pixels":mudancas,
            "risco_ampliacao_no_celular":min(info["altura"],info["largura"])<540,
            "licenca_ainda_exige_conferencia_de_origem":True,
            "checagem_de_uso":uso,
            "acao_que_a_fala_promete":"NAO_INSPECIONADA",
            "adequacao_editorial":"AGUARDANDO_REVISAO_HUMANA",
        })
    grid.save(saida/"contato_3_dominios.jpg",quality=90)
    rel={"modo":"AMOSTRA_REAL_DE_FONTES_SEM_EDICAO",
         "arquivos_inspecionados":len(resultados),"assuntos":resultados,
         "criterio_visual_comum":"contrato_visual_comum.julgar_inspecao",
         "falsos_positivos_semanticos":"NAO_MENSURADOS_SEM_VEREDITOS_HUMANOS",
         "midia_representativa":"NAO_CONFUNDIR_COM_REGISTRO_DO_EVENTO",
         "aprovacao_humana":"PENDENTE","publicado":False}
    (saida/"qa_fontes_reais.json").write_text(
        json.dumps(rel,ensure_ascii=False,indent=2),encoding="utf-8")
    return rel


def main(argv=None) -> int:
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("manifesto",type=Path)
    ap.add_argument("saida",type=Path)
    ap.add_argument("--root",type=Path,default=Path("."))
    o=ap.parse_args(argv)
    r=auditar_fontes(json.loads(o.manifesto.read_text(encoding="utf-8")),o.root,o.saida)
    print(json.dumps({"arquivos":r["arquivos_inspecionados"],
       "dominios":[x["dominio"] for x in r["assuntos"]],
       "publicado":r["publicado"],
       "pendencia":r["aprovacao_humana"]},ensure_ascii=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
