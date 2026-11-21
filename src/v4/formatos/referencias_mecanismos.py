"""Prototipo de pesquisa de referencias de mecanismo 2D/3D.

Integra a busca de videos existente (acervo V4) e busca metadados de modelos
Sketchfab. Nao baixa/copia automaticamente conteudo de terceiro, nao deduz
movimento a partir de titulos e nao publica. O que esta sem evidencia e bloqueado.
Esta etapa NAO e um renderer; planeja reaproveitamento antes de renderizar.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

import requests

from src.v4.formatos import catalogo_mecanismos as CAT

UA = {"User-Agent": "CoringaExplicaReferenceScout/1.0 (github.com/Heitor2404/coringa-news)"}
REF_ID = re.compile(r"^[a-zA-Z0-9_.:-]{2,100}$")
MODES = {"video", "modelo_3d"}
METHODS = {"inspecao_humana_quadros", "inspecao_ia_quadros"}
MAX_ITEMS = 6
_GENERIC_SEARCH = {"animation", "animated", "3d", "2d", "mechanism",
                   "cutaway", "educational", "how", "works", "operation",
                   "four", "stroke", "engine", "blood", "flow", "model",
                   "working", "diagram", "science"}


def termos_essenciais(consultas: list[str]) -> list[str]:
    """Termos curtos de objeto: candidatos por metadata; nao prova visual."""
    out = []
    for c in consultas:
        words = re.findall(r"[a-zA-Z]{4,}", c.lower())
        selected = [w for w in words if w not in _GENERIC_SEARCH]
        if not selected:
            selected = words
        for word in selected[:2]:
            if word not in out:
                out.append(word)
    return out[:3]


def buscar_commons_animacoes(consultas: list[str], get=None) -> tuple[list[dict],list[str]]:
    """Pesquisa Wikimedia por imagens animadas e video, sem restringir a HD.

    O acervo de footage historico V4 rejeita tecnicos pequenos por tamanho.
    Aqui somente entram como REFERENCIA de estudo, nunca como prova publicavel.
    """
    import html
    get = get or requests.get
    found, errors = [], []
    for term in termos_essenciais(consultas)[:2]:
        try:
            r = get("https://commons.wikimedia.org/w/api.php",
                    params={"action": "query", "generator": "search",
                            "gsrsearch": term, "gsrnamespace": 6,
                            "gsrlimit": 25, "prop": "imageinfo",
                            "iiprop": "url|mime|extmetadata|size",
                            "format": "json", "formatversion": 2},
                    headers=UA, timeout=18)
            r.raise_for_status()
            pages = (r.json().get("query") or {}).get("pages") or []
            for page in pages:
                if not isinstance(page, dict):
                    continue
                inf = (page.get("imageinfo") or [{}])[0]
                mime = str(inf.get("mime") or "")
                if mime not in ("image/gif", "video/webm", "video/ogg",
                                "video/mp4", "application/ogg"):
                    continue
                url = inf.get("url")
                if not _https(url, {"upload.wikimedia.org"}):
                    continue
                title = str(page.get("title") or "")[:180]
                if not title:
                    continue
                page_url = inf.get("descriptionurl")
                if not _https(page_url, {"commons.wikimedia.org"}):
                    # A pagina de descricao e a origem editorial da imagem.
                    from urllib.parse import quote
                    page_url = "https://commons.wikimedia.org/wiki/" + quote(
                        title.replace(" ", "_"), safe=":_")
                md = inf.get("extmetadata") or {}
                license_name = html.unescape(str((md.get("LicenseShortName") or {}).get("value") or ""))[:100]
                creator = re.sub("<[^>]+>", " ", str((md.get("Artist") or {}).get("value") or ""))
                found.append({
                    "id": "commons-" + hashlib.sha256(url.encode()).hexdigest()[:16],
                    "midia": "animacao_gif" if mime=="image/gif" else "video",
                    "provedor": "Wikimedia Commons",
                    "titulo": title, "pagina": page_url, "origem_media": url,
                    "consulta": term, "licenca_declarada": license_name,
                    "credito_declarado": html.unescape(creator).strip()[:250],
                    "licenca_verificada": False,
                    "movimento_observado": False,
                    "status": "CANDIDATO_SEM_INSPECAO",
                })
        except Exception as exc:
            errors.append("commons:"+type(exc).__name__+":"+str(exc)[:120])
    return found[:MAX_ITEMS], errors


def _https(url: object, domains: set[str] | None = None) -> bool:
    if not isinstance(url, str):
        return False
    p = urlsplit(url)
    return p.scheme == "https" and bool(p.hostname) and (
        domains is None or p.hostname.lower() in domains
    )


def _words(values: object, *, limit: int = 12) -> list[str]:
    if not isinstance(values, list):
        return []
    result = []
    for value in values[:limit]:
        if isinstance(value, str) and value.strip() and len(value) <= 100:
            result.append(value.strip())
    return result


def validar_brief(brief: dict) -> None:
    if not isinstance(brief, dict):
        raise ValueError("brief nao e objeto")
    if not REF_ID.fullmatch(str(brief.get("id") or "")):
        raise ValueError("id de brief invalido")
    if len(str(brief.get("pergunta") or "").strip()) < 15:
        raise ValueError("falta pergunta explicativa")
    consultas = _words(brief.get("consultas_en"), limit=4)
    if not consultas or any(len(x) < 5 for x in consultas):
        raise ValueError("consultas_en precisa de termos especificos")
    if len(consultas) != len(set(consultas)):
        raise ValueError("consultas duplicadas")


def buscar_modelos_3d(consultas: list[str], get=None) -> tuple[list[dict], list[str]]:
    """Sketchfab Data API: pesquisa so metadados publicos, sem baixar modelos.

    O endpoint de download de modelos exige OAuth quando aplicavel. Resultado
    de busca nunca prova que o modelo e animavel, tem rig ou esta licenciado.
    """
    get = get or requests.get
    encontrados, erros = [], []
    for termo in termos_essenciais(consultas)[:2]:
        try:
            resp = get("https://api.sketchfab.com/v3/search",
                       params={"type": "models", "q": termo,
                               "downloadable": "true", "count": 6},
                       headers=UA, timeout=18)
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, dict):
                raise ValueError("JSON inesperado")
            for item in (data.get("results") or [])[:6]:
                if not isinstance(item, dict):
                    continue
                uid = str(item.get("uid") or "")
                if not re.fullmatch(r"[A-Za-z0-9]{10,64}", uid):
                    continue
                page = item.get("viewerUrl")
                if not _https(page, {"sketchfab.com", "www.sketchfab.com"}):
                    page = "https://sketchfab.com/models/" + uid
                license_value = item.get("license")
                if isinstance(license_value, dict):
                    license_value = license_value.get("slug") or license_value.get("label")
                encontrados.append({
                    "id": "sf-" + uid,
                    "midia": "modelo_3d",
                    "provedor": "Sketchfab",
                    "titulo": str(item.get("name") or "")[:180],
                    "pagina": page,
                    "consulta": termo,
                    "licenca_declarada": str(license_value or "")[:80],
                    "modelo_editavel": "NAO_VERIFICADO",
                    "download_autorizado": "NAO_VERIFICADO",
                    "movimento_observado": False,
                    "status": "CANDIDATO_SEM_INSPECAO",
                })
        except Exception as exc:
            erros.append("sketchfab:" + type(exc).__name__ + ":" + str(exc)[:150])
    return encontrados[:MAX_ITEMS], erros


def buscar_videos(consultas: list[str], buscar=None) -> tuple[list[dict], list[str]]:
    """Reutiliza o garimpo V4, preservando incerteza sobre o conteudo do clip."""
    if buscar is None:
        from src.v4.acervo_v4 import candidatos
        buscar = candidatos
    try:
        results = buscar({"tipo": "video", "consultas_en": consultas[:4]}) or []
    except Exception as exc:
        return [], ["acervo_v4:" + type(exc).__name__ + ":" + str(exc)[:150]]
    candidates = []
    for row in results[:40]:
        if not isinstance(row, dict):
            continue
        original = row.get("video") or {}
        url = original.get("url") if isinstance(original, dict) else None
        page = row.get("pagina") or row.get("page") or row.get("url")
        if not _https(url) or not _https(page):
            continue
        uid = hashlib.sha256((page + "|" + url).encode("utf-8")).hexdigest()[:16]
        candidates.append({
            "id": "v4-" + uid,
            "midia": "video",
            "provedor": "Acervo V4 (Commons/Archive/Pixabay conforme origem)",
            "titulo": str(row.get("titulo") or "")[:180],
            "pagina": page,
            "origem_media": url,
            "consulta": consultas[0],
            "credito_declarado": str(row.get("credito") or "")[:350],
            "licenca_verificada": False,
            "movimento_observado": False,
            "status": "CANDIDATO_SEM_INSPECAO",
        })
    return candidates[:MAX_ITEMS], []


def descobrir(brief: dict, buscar=None, get=None) -> dict:
    """Descoberta real de referencias, sem inferir processos pelo titulo."""
    validar_brief(brief)
    queries = _words(brief["consultas_en"], limit=4)
    v, ve = buscar_videos(queries, buscar=buscar)
    # Stubs offline podem isolar o provedor existente para testes.
    commons, ce = (buscar_commons_animacoes(queries)
                   if buscar is None else ([], []))
    m, me = buscar_modelos_3d(queries, get=get)
    unique: dict[str, dict] = {}
    for item in v + commons + m:
        unique.setdefault(item["id"], item)
    return {
        "versao": 1, "brief_id": brief["id"],
        "estado": "CANDIDATOS_NAO_INSPECIONADOS" if unique else "SEM_REFERENCIAS",
        "candidatos": list(unique.values()),
        "erros": ve + ce + me,
        "publicar": False,
        "observacao_visual": "NAO_EXECUTADA",
        "renderer_aprovado": None,
    }


def extrair_quadros(caminho: Path, saida: Path, run=None) -> dict:
    """Extrai frames de um arquivo LOCAL; nao afirma o que aparece nos frames."""
    run = run or subprocess.run
    caminho = Path(caminho)
    if not caminho.is_file() or caminho.suffix.lower() not in (".mp4", ".webm", ".mov"):
        raise ValueError("F-VIDEO-INEXISTENTE: exige video local valido")
    if caminho.stat().st_size > 250_000_000:
        raise ValueError("F-VIDEO-GRANDE: limite 250 MB")
    meta = run(["ffprobe", "-v", "error", "-show_entries",
                "format=duration:stream=codec_type,width,height",
                "-of", "json", str(caminho)], capture_output=True, text=True,
               timeout=40, check=True)
    info = json.loads(meta.stdout)
    video = next((s for s in info.get("streams") or []
                  if s.get("codec_type") == "video"), None)
    dur = float((info.get("format") or {}).get("duration") or 0)
    if not video or not 0.5 < dur <= 1800:
        raise ValueError("F-VIDEO-METADADOS: video invalido")
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    pontos = [round(dur * p, 3) for p in (.07, .28, .52, .76, .94)]
    arquivos = []
    for i, sec in enumerate(pontos):
        fn = saida / ("ref_%02d.jpg" % i)
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
             "-ss", str(sec), "-i", str(caminho),
             "-vf", "scale=480:-2", "-frames:v", "1", str(fn)],
            capture_output=True, timeout=40, check=True)
        if not fn.is_file() or fn.stat().st_size == 0:
            raise ValueError("F-FRAME-VAZIO")
        arquivos.append({"segundo": sec, "arquivo": fn.name})
    manifesto = {
        "arquivo_sha256": hashlib.sha256(caminho.read_bytes()).hexdigest(),
        "duracao_s": round(dur, 3),
        "w": video.get("width"), "h": video.get("height"),
        "quadros": arquivos,
        "veredito": "NAO_ANALISADO_SEMANTICAMENTE",
    }
    (saida / "frames_meta.json").write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifesto


def planejar(brief: dict, descoberta: dict, observacoes: list[dict]) -> dict:
    """So seleciona renderer por evidencias de video, nao por titulo/tema.

    Observacoes de visao IA permitem pre-plano, NAO aprovacao fisica/estetica.
    Acoes precisam estar na ordem de catalogo_mecanismos existente.
    """
    validar_brief(brief)
    candidates = {x["id"]: x for x in descoberta.get("candidatos") or []
                  if isinstance(x, dict) and "id" in x}
    rel = {"brief_id": brief["id"], "publicar": False,
           "renderer": None, "plano": None,
           "estado": "REFERENCIA_SEM_INSPECAO", "bloqueios": []}
    if not candidates:
        rel["estado"] = "SEM_REFERENCIAS"
        rel["bloqueios"] = ["F-REFERENCIA-NAO-ENCONTRADA"]
        return rel
    validos = []
    for x in observacoes or []:
        if not isinstance(x, dict) or x.get("referencia_id") not in candidates:
            continue
        if x.get("metodo") not in METHODS:
            continue
        quadros = x.get("quadros") or []
        if (not isinstance(quadros, list) or len(quadros) < 2
                or any(not isinstance(q, (int,float)) or q < 0 for q in quadros)):
            continue
        ações = _words(x.get("acoes_visiveis"))
        fases = _words(x.get("fases_visiveis"))
        atores = _words(x.get("atores_visiveis"))
        if not ações or not fases or not atores:
            continue
        validos.append((x, ações, fases, atores))
    if not validos:
        rel["bloqueios"] = ["F-REFERENCIA-NAO-INSPECIONADA"]
        return rel

    needed = _words(brief.get("acoes_necessarias"))
    phases = _words(brief.get("fases_necessarias"))
    if not needed or not phases:
        rel["bloqueios"] = ["F-ACOES-E-FASES-AUSENTES"]
        return rel
    for obs, actions, seen_phases, actors in validos:
        if actions != needed or not set(phases).issubset(seen_phases):
            continue
        scene = {
            "type": "mechanism", "mechanism": "auto",
            "processo_visual": {
                "acoes_necessarias": needed, "fases_necessarias": phases,
            },
            "cues": [{"action": a} for a in actions],
        }
        renderer, errors = CAT.decidir(scene)
        if not errors and renderer:
            ref = candidates[obs["referencia_id"]]
            rel.update({
                "estado": "RENDERER_EXISTENTE_PLANO_PRELIMINAR",
                "renderer": renderer,
                "plano": {
                    "referencia_id": obs["referencia_id"],
                    "fonte": ref.get("pagina"),
                    "acoes": actions, "fases": phases,
                    "atores_visiveis": actors,
                    "metodo_observacao": obs["metodo"],
                    "revisao_humana": "PENDENTE",
                    "revisao_fisica": "PENDENTE",
                    "render_testado": False,
                },
            })
            return rel
    rel["estado"] = "CAPACIDADE_OU_EVIDENCIA_INSUFICIENTE"
    rel["bloqueios"] = ["F-CAPACIDADE-NAO-COBRE-ETAPAS-OBSERVADAS"]
    rel["alternativa"] = (
        "Avaliar montagem com video real apos inspeçao visual, checagem de "
        "fonte/uso e hash; ou adicionar um operador reutilizavel ao catalogo."
    )
    return rel


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("brief_json")
    parser.add_argument("saida")
    parser.add_argument("--sem-rede", action="store_true")
    args = parser.parse_args(argv)
    brief = json.loads(Path(args.brief_json).read_text(encoding="utf-8"))
    destino = Path(args.saida)
    destino.mkdir(parents=True, exist_ok=True)
    if args.sem_rede:
        resultado = {"versao": 1, "brief_id": brief.get("id"),
                     "estado": "BUSCA_NAO_EXECUTADA_OFFLINE",
                     "candidatos": [], "erros": [], "publicar": False,
                     "observacao_visual": "NAO_EXECUTADA", "renderer_aprovado": None}
    else:
        resultado = descobrir(brief)
    (destino / "referencias.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    plano = planejar(brief, resultado, [])
    (destino / "planejamento.json").write_text(
        json.dumps(plano, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"brief_id": brief["id"],
                      "candidatos": len(resultado["candidatos"]),
                      "estado": plano["estado"], "erros": resultado["erros"]},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
