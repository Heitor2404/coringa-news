"""Inspecao multimodal com evidencias de quadros do GIF original.

Reutiliza src.gemini.json_visao. Uma resposta do modelo e apenas analise
provisoria: nao aprova a animacao, nao garante sua fisica nem autoriza postagem.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
from pathlib import Path

from PIL import Image

from src.v4.formatos import referencias_mecanismos as REF

SHA = re.compile(r"^[0-9a-f]{64}$")
STATUS = {"RELEVANTE", "PARCIAL", "IRRELEVANTE", "INCERTO"}


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def quadros_gif(origem: Path, reference_id: str) -> tuple[list[bytes], list[dict], str]:
    """Abre o original de SHA fixado; sem rede e sem confiar em thumbnail."""
    pasta = Path(origem)
    m = json.loads((pasta / "inspecao.json").read_text(encoding="utf8"))
    if m.get("referencia_id") != reference_id:
        raise ValueError("F-REFERENCIA-ID: manifesto pertence a outro candidato")
    data = (pasta / "original.gif").read_bytes()
    sha = m.get("sha256")
    if len(data) > 16_000_000 or not isinstance(sha, str) or not SHA.fullmatch(sha) or _hash(data) != sha:
        raise ValueError("F-REFERENCIA-SHA: GIF alterado ou ausente")
    expected = m.get("amostras")
    if not isinstance(expected, list) or not 3 <= len(expected) <= 8:
        raise ValueError("F-QUADROS-AMOSTRA: faltam indices de 3 a 8 quadros")
    if (any(not isinstance(i,int) or isinstance(i,bool) or i < 0 for i in expected)
            or expected != sorted(set(expected))):
        raise ValueError("F-QUADROS-ORDEM: indices ausentes, repetidos ou desordenados")
    images, inspected = [], []
    with Image.open(io.BytesIO(data)) as gif:
        if gif.format != "GIF" or gif.n_frames < 3 or gif.n_frames > 1200:
            raise ValueError("F-GIF-INVALIDO: somente GIF animado")
        for pos, index in enumerate(expected):
            if index >= gif.n_frames:
                raise ValueError("F-QUADRO-FORA-DO-GIF")
            gif.seek(index)
            frame = gif.convert("RGB")
            if min(frame.size) < 64 or frame.width * frame.height > 12_000_000:
                raise ValueError("F-QUADRO-ILEGIVEL: resolucao insuficiente")
            frame.thumbnail((512, 512), Image.Resampling.LANCZOS)
            buff = io.BytesIO()
            frame.save(buff, format="JPEG", quality=89)
            payload = buff.getvalue()
            images.append(payload)
            inspected.append({"ordinal": pos, "indice": index, "sha256": _hash(payload)})
    return images, inspected, sha



def quadros_video(origem: Path, reference_id: str) -> tuple[list[bytes], list[dict], str]:
    """Usa extrair_quadros EXISTENTE; confirma SHA do video e de cada frame.

    Sem video local disponivel, NAO finge que os 5 jpgs sao prova de origem.
    """
    folder = Path(origem)
    meta = json.loads((folder / "frames_meta.json").read_text(encoding="utf8"))
    if meta.get("referencia_id") != reference_id:
        raise ValueError("F-REFERENCIA-ID: manifesto de outro video")
    sha = meta.get("arquivo_sha256")
    location = meta.get("arquivo_origem")
    if not isinstance(sha,str) or not SHA.fullmatch(sha) or not isinstance(location,str):
        raise ValueError("F-REFERENCIA-SHA: falta origem do video")
    video = Path(location)
    if not video.is_file() or video.suffix.lower() not in (".mp4",".webm",".mov"):
        raise ValueError("F-REFERENCIA-VIDEO-INACESSIVEL")
    hasher = hashlib.sha256()
    with video.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024),b""):
            hasher.update(chunk)
    if hasher.hexdigest()!=sha:
        raise ValueError("F-REFERENCIA-SHA: video original alterado")
    items = meta.get("quadros") or []
    if not isinstance(items,list) or not 3<=len(items)<=8:
        raise ValueError("F-QUADROS-AMOSTRA")
    images, sampled = [], []
    previous = -1.0
    for ordinal,frame in enumerate(items):
        if not isinstance(frame,dict):
            raise ValueError("F-QUADROS-META")
        filename = frame.get("arquivo")
        second = frame.get("segundo")
        declared = frame.get("sha256")
        if (not isinstance(filename,str)
                or not re.fullmatch(r"ref_[0-9]{2}\.jpg",filename)
                or not isinstance(second,(float,int)) or isinstance(second,bool)
                or not previous < second
                or not isinstance(declared,str) or not SHA.fullmatch(declared)):
            raise ValueError("F-QUADROS-META")
        previous = float(second)
        p = folder / filename
        if not p.is_file() or p.stat().st_size>5_000_000:
            raise ValueError("F-QUADROS-AUSENTES")
        data = p.read_bytes()
        if _hash(data)!=declared:
            raise ValueError("F-QUADROS-SHA: jpg diferente do extraido")
        try:
            with Image.open(io.BytesIO(data)) as im:
                if im.format!="JPEG" or min(im.size)<64:
                    raise ValueError("F-QUADROS-ILEGIVEIS")
                im.verify()
        except OSError as e:
            raise ValueError("F-QUADROS-CORROMPIDOS") from e
        images.append(data)
        sampled.append({"ordinal":ordinal, "indice":second, "sha256":declared})
    return images,sampled,sha

def prompt(brief: dict, n: int) -> str:
    pedido = json.dumps({
        "pergunta": brief.get("pergunta"),
        "acoes_necessarias": brief.get("acoes_necessarias"),
        "fases_necessarias": brief.get("fases_necessarias")
    }, ensure_ascii=False)
    return (
        f"Analise os {n} QUADROS REAIS da mesma animacao na ordem 0 a {n-1}. "
        "Nao confunda titulo, texto ou conhecimento previo com acontecimentos "
        "que os quadros realmente mostram. Uma rotacao do modelo de um coracao "
        "NAO prova fluxo sanguineo e pistao de Minecraft NAO e motor a combustao. "
        "Cite somente movimentos com estado ANTES e DEPOIS visivel, nunca "
        "preencha a lista de acoes solicitadas por obediencia. "
        f"Pergunta e objetivo: {pedido}. "
        "Responda JSON: categoria RELEVANTE, PARCIAL, IRRELEVANTE ou INCERTO; "
        "atores_visiveis lista de nomes concretos; fases_visiveis lista de "
        "fases que realmente aparecem; eventos lista de objetos com: acao "
        "(identificador EXATO de acoes_necessarias), antes (ordinal 0..n-1), "
        "depois (ordinal > antes), alvo (objeto observado), evidencia (o que "
        "visivelmente mudou entre esses dois quadros), visivel (booleano); "
        "problemas lista de strings e justificativa string. "
        "Se nao for possivel verificar o movimento nos quadros, eventos=[] "
        "e categoria INCERTO."
    )


def inspecionar(brief: dict, candidato: dict, pasta: Path, chamar_visao=None) -> dict:
    REF.validar_brief(brief)
    rid = candidato.get("id")
    report = {"brief_id": brief["id"], "referencia_id": rid, "publicar": False,
              "estado": "BLOQUEADO", "revisao_humana": "PENDENTE",
              "bloqueios": [], "observacao": None}
    try:
        if candidato.get("midia") == "animacao_gif":
            images, frames, sha = quadros_gif(pasta, rid)
        elif candidato.get("midia") == "video":
            images, frames, sha = quadros_video(pasta, rid)
        else:
            raise ValueError("F-REFERENCIA-MIDIA: nao suporta modelo 3D sem animacao")
        report["origem_sha256"] = sha
        report["quadros"] = frames
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        report["bloqueios"] = ["F-SEM-EVIDENCIA-ORIGINAL: " + str(exc)[:160]]
        return report
    if chamar_visao is None:
        if not (os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY_2")):
            report["bloqueios"] = ["F-VISAO-INDISPONIVEL"]
            return report
        from src.gemini import json_visao
        chamar_visao = lambda text, imgs: json_visao(text, imgs, leve=False)
    try:
        answer = chamar_visao(prompt(brief, len(images)), images)
    except Exception as exc:
        report["bloqueios"] = ["F-VISAO-FALHOU: " + type(exc).__name__ + " " + str(exc)[:160]]
        return report
    if not isinstance(answer, dict) or answer.get("categoria") not in STATUS:
        report["bloqueios"] = ["F-VISAO-FORMATO"]
        return report
    category = answer["categoria"]
    report["categoria"] = category
    problems = answer.get("problemas")
    report["problemas"] = [str(x)[:180] for x in problems[:6] if isinstance(x,str)] if isinstance(problems,list) else []
    report["justificativa"] = str(answer.get("justificativa") or "")[:400]
    if category in ("IRRELEVANTE", "INCERTO"):
        report["bloqueios"] = ["F-REFERENCIA-IRRELEVANTE-OU-INCERTA"]
        return report
    actors = REF._words(answer.get("atores_visiveis"))
    phases = REF._words(answer.get("fases_visiveis"))
    events = answer.get("eventos")
    if not actors or not phases or not isinstance(events, list):
        report["bloqueios"] = ["F-SEM-ATORES-FASES-EVENTOS"]
        return report

    needed = REF._words(brief.get("acoes_necessarias"))
    proofs = []
    previous_action = -1
    for item in events[:15]:
        if not isinstance(item,dict) or item.get("visivel") is not True:
            continue
        action, before, after = item.get("acao"), item.get("antes"), item.get("depois")
        ev, target = item.get("evidencia"), item.get("alvo")
        if action not in needed or needed.index(action) <= previous_action:
            continue
        if (not isinstance(before,int) or isinstance(before,bool)
                or not isinstance(after,int) or isinstance(after,bool)
                or not 0 <= before < after < len(frames)
                or not isinstance(target,str) or len(target.strip()) < 3
                or not isinstance(ev,str) or len(ev.strip()) < 24):
            continue
        proofs.append({
            "acao": action, "antes": before, "depois": after,
            "alvo": target[:90], "evidencia": ev.strip()[:350],
            "hash_antes": frames[before]["sha256"],
            "hash_depois": frames[after]["sha256"],
        })
        previous_action = needed.index(action)
    if not proofs:
        report["bloqueios"] = ["F-SEM-MOVIMENTO-VISIVEL"]
        return report
    complete = [e["acao"] for e in proofs] == needed and category == "RELEVANTE"
    report["estado"] = ("EVENTOS_VISUAIS_PROVISORIOS" if complete else "OBSERVACAO_PARCIAL")
    report["observacao"] = {
        "referencia_id": rid, "metodo": "inspecao_ia_quadros",
        "estado": report["estado"], "categoria": category, "origem_sha256": sha,
        "quadros": [f["indice"] for f in frames],
        "quadros_sha256": [f["sha256"] for f in frames],
        "atores_visiveis": actors, "fases_visiveis": phases,
        "acoes_visiveis": [e["acao"] for e in proofs], "evidencias": proofs,
        "revisao_humana": "PENDENTE",
    }
    if not complete:
        report["bloqueios"] = ["F-ETAPAS-NAO-COMPROVADAS"]
    return report


def executar(brief: dict, descoberta: dict, pasta: Path, destino: Path,
             chamar_visao=None) -> dict:
    folder = Path(pasta)
    source_meta = folder / ("inspecao.json" if (folder/"inspecao.json").is_file()
                            else "frames_meta.json")
    meta = json.loads(source_meta.read_text(encoding="utf8"))
    reference_id = meta.get("referencia_id")
    candidate = next((x for x in descoberta.get("candidatos") or []
                      if x.get("id") == reference_id), None)
    if candidate is None:
        raise ValueError("F-REFERENCIA-NAO-ENCONTRADA-NO-CATALOGO")
    report = inspecionar(brief, candidate, pasta, chamar_visao)
    obs = report.get("observacao")
    plan = REF.planejar(brief, descoberta, [obs] if obs else [])
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "inspecao_semantica.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf8")
    (destino / "planejamento_inspecionado.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf8")
    return {"inspecao": report, "planejamento": plan}


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("brief_json")
    p.add_argument("catalogo_json")
    p.add_argument("quadros_dir")
    p.add_argument("saida_dir")
    p.add_argument("--usar-gemini", action="store_true")
    a = p.parse_args(argv)
    brief = json.loads(Path(a.brief_json).read_text(encoding="utf8"))
    catalog = json.loads(Path(a.catalogo_json).read_text(encoding="utf8"))
    # O usuario/diretor deve pedir explicitamente a chamada multimodal.
    fake_off = lambda *_: (_ for _ in ()).throw(RuntimeError("visao desligada"))
    r = executar(brief, catalog, Path(a.quadros_dir), Path(a.saida_dir),
                 chamar_visao=None if a.usar_gemini else fake_off)
    print(json.dumps({
        "estado": r["inspecao"]["estado"],
        "bloqueios": r["inspecao"]["bloqueios"],
        "plano": r["planejamento"]["estado"]
    }, ensure_ascii=False))
    return 0 if (r["planejamento"]["renderer"]
                 and r["inspecao"]["estado"] == "EVENTOS_VISUAIS_PROVISORIOS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
