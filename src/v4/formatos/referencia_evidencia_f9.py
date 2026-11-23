"""F9 — referência visual externa para inspeção do compressor COMPLETO.

Integra scouting Commons já existente: não refaz busca nem importa mídia na
biblioteca produtiva. Download EXCLUSIVAMENTE para artefato privado, com
hash exato, licença/autor documentados, escopo de ator visível e corte da
máquina REAL renderizado pelo código existente. Zero inferência de CAD/rig.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

import cairosvg
import requests
from PIL import Image, ImageDraw, ImageFont

from src.v4.formatos import render_compressor_conjunto_2d as COMP

MANIFEST = Path(__file__).with_name("referencias_visuais_f9") / "compressor_elliott_2018.json"
HEX = re.compile(r"^[0-9a-f]{64}$")
BBOX = re.compile(r"^[a-z][a-z0-9_]+$")
ROOT_URL = "https://upload.wikimedia.org/wikipedia/commons/"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
CONTACT_SIZE = (1530, 1050)
MAX_BYTES = 1_500_000


def fail(code: str):
    raise ValueError("F9-REFERENCIA-" + code)


def carregar(path=MANIFEST):
    try:
        content = json.loads(Path(path).read_text(encoding="utf8"))
    except (OSError, UnicodeError, ValueError):
        fail("MANIFESTO")
    validar(content)
    return content


def validar(ref: dict) -> dict:
    if (not isinstance(ref, dict) or ref.get("schema") != "coringa-reference-evidence-f9-v1"
            or ref.get("status") != "CANDIDATO_CURADORIA_AINDA_NAO_APROVADA"
            or ref.get("intended_use") != "COMPARACAO_VISUAL_PRIVADA_NAO_ASSET_DE_RENDER"
            or ref.get("reference_type") not in ("ilustracao_tecnica_estatica_nao_fotografia", "foto_estatica")
            or not isinstance(ref.get("source"), dict)
            or not isinstance(ref.get("file"), dict)
            or not isinstance(ref.get("claims"), dict)
            or not isinstance(ref.get("rights_and_gates"), dict)):
        fail("CONTRATO")
    src, file, claims, rights = (
        ref["source"], ref["file"], ref["claims"], ref["rights_and_gates"]
    )
    url = src.get("file_url")
    page = src.get("page")
    p = urlsplit(str(url or ""))
    pagep = urlsplit(str(page or ""))
    if (p.scheme != "https" or p.netloc != "upload.wikimedia.org"
            or p.query or p.fragment or p.username or p.password
            or not p.path.startswith("/wikipedia/commons/")
            or not re.fullmatch(r"/wikipedia/commons/[0-9a-f]/[0-9a-f]{2}/[A-Za-z0-9_%-]+\.jpg",p.path)
            or pagep.scheme != "https" or pagep.netloc != "commons.wikimedia.org"
            or not pagep.path.startswith("/wiki/File:")
            or pagep.query or pagep.fragment
            or src.get("license") != "CC BY-SA 4.0"
            or src.get("license_url") != LICENSE_URL
            or len(str(src.get("author") or "")) < 6
            or len(str(src.get("attribution") or "")) < 50
            or src.get("author") not in src["attribution"]
            or src.get("license") not in src["attribution"]
            or src.get("changes_notice") is None
            or src.get("external_media_authorization") !=
               "LICENCA_DECLARADA_NA_PAGINA_REQUER_CREDITO_E_SHAREALIKE_SE_APLICAVEL"):
        fail("PROVENIENCIA")
    if file.get("format") != "JPEG" or file.get("max_bytes") != MAX_BYTES:
        fail("FORMATO")
    w, h = file.get("width"), file.get("height")
    if type(w) is not int or type(h) is not int or not 640 <= w <= 6000 or not 400 <= h <= 4000:
        fail("DIMENSOES")
    sha = file.get("expected_sha256")
    if sha is not None and (not isinstance(sha, str) or not HEX.fullmatch(sha)):
        fail("SHA")
    if (claims.get("type") != "external_appearance_only"
            or claims.get("independent_recognition") != "NAO_EXECUTADO"
            or claims.get("industrial_identity_certified") is not False):
        fail("SEM-RECONHECIMENTO")
    visible, hidden = claims.get("visible_parts"), claims.get("hidden_parts")
    if (not isinstance(visible, list) or not visible
            or not isinstance(hidden, list) or not hidden
            or len(hidden) != len(set(hidden))):
        fail("ATORES")
    seen = set()
    for item in visible:
        if not isinstance(item, dict):
            fail("BBOX")
        role, coords = item.get("role"), item.get("bbox")
        if (not isinstance(role, str) or not BBOX.fullmatch(role)
                or role in seen or role in hidden
                or item.get("basis") != "BBOX_MANUAL_IMAGEM_ORIGINAL"
                or not isinstance(coords, list) or len(coords) != 4):
            fail("BBOX")
        seen.add(role)
        if any(type(n) not in (int, float) or not math.isfinite(n) for n in coords):
            fail("BBOX")
        x, y, ww, hh = coords
        if not (0 <= x < 1 and 0 <= y < 1 and 0.001 < ww <= 1 and 0.001 < hh <= 1
                and x + ww <= 1.001 and y + hh <= 1.001):
            fail("BBOX")
    if (not set(hidden).isdisjoint(seen) or
            any(not isinstance(r, str) or not BBOX.fullmatch(r) for r in hidden)):
        fail("ATORES-OCULTOS")
    if (set(rights) != {
            "source_license_reproduced_as_declared",
            "commercial_use_review_pending",
            "derivative_obligations_review_pending",
            "publication_allowed",
            "reference_only",
            "automatic_geometry_extraction",
            "visual_approval"}
            or rights["source_license_reproduced_as_declared"] is not True
            or rights["commercial_use_review_pending"] is not True
            or rights["derivative_obligations_review_pending"] is not True
            or rights["publication_allowed"] is not False
            or rights["reference_only"] is not True
            or rights["automatic_geometry_extraction"] is not False
            or rights["visual_approval"] is not False):
        fail("PUBLICACAO")
    return {
        "manifest_status":ref["status"],"sha_pinned":bool(sha),
        "visible_parts":len(visible),"hidden_parts":len(hidden),
        "automatic_recognition":False,"published":False,
    }


def conferir_bytes(ref: dict, data: bytes, *, exigir_pin=False) -> dict:
    validar(ref)
    if not isinstance(data, bytes) or not 10_000 < len(data) <= MAX_BYTES:
        fail("ARQUIVO")
    if data[:3] != b"\xff\xd8\xff":
        fail("JPEG")
    try:
        with Image.open(io.BytesIO(data)) as im:
            if im.format != "JPEG" or im.size != (
                ref["file"]["width"],ref["file"]["height"]):
                fail("TIPO-OU-TAMANHO")
            im.verify()
    except (OSError, Image.DecompressionBombError, SyntaxError):
        fail("JPEG-CORROMPIDO")
    digest = hashlib.sha256(data).hexdigest()
    expected = ref["file"]["expected_sha256"]
    if exigir_pin and not expected:
        fail("SHA-NAO-FIXADO")
    if expected and expected != digest:
        fail("SHA-DIVERGENTE")
    return {
        "original_sha256":digest,
        "sha_pinned_and_verified":bool(expected),
        "file_bytes":len(data),
        "dimensions":[ref["file"]["width"],ref["file"]["height"]],
        "license_declared":ref["source"]["license"],
        "publication_allowed":False,
        "use":"COMPARACAO_PRIVADA",
    }


def adquirir(ref: dict, *, get=None, exigir_pin=False) -> bytes:
    """Baixa 1 JPG de host fixo; bloqueia redirecionamentos e URL dinâmica."""
    validar(ref)
    get = get or requests.get
    url = ref["source"]["file_url"]
    try:
        response = get(url, timeout=24, allow_redirects=False, headers={
            "User-Agent":"CoringaExplicaReferenceAuditor/1.0 (github.com/Heitor2404/coringa-news)",
        })
        response.raise_for_status()
        if response.status_code != 200 or response.is_redirect:
            fail("HTTP-REDIRECT")
        if "image/jpeg" not in response.headers.get("Content-Type","").lower():
            fail("CONTENT-TYPE")
        body = response.content
    except requests.RequestException as exc:
        raise ValueError("F9-REFERENCIA-HTTP-"+type(exc).__name__) from exc
    conferir_bytes(ref,body,exigir_pin=exigir_pin)
    return body


def _fonte(size=17):
    for name in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                 "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"):
        try:
            return ImageFont.truetype(name,size)
        except OSError:
            pass
    return ImageFont.load_default()


def _foto(data: bytes):
    with Image.open(io.BytesIO(data)) as im:
        return im.convert("RGB").copy()


def _composicao(ref: dict, original: Image.Image, mechanism: Image.Image,
                timestamp: str):
    canvas = Image.new("RGB", CONTACT_SIZE, "#eaf3f7")
    d = ImageDraw.Draw(canvas)
    dark="#18394c"; muted="#456577"
    d.rectangle((0,0,1530,89),fill="#112e42")
    d.text((26,18),"AUDITORIA F9 — REFERENCIA EXTERNA x MOTOR 2D",
           font=_fonte(23),fill="white")
    d.text((26,57),"Comparacao visual, nao reconstrucao automatica nem video publicado",
           font=_fonte(15),fill="#d4e7ee")
    x0, y0 = 24, 140
    src = original.copy()
    src.thumbnail((905,670))
    canvas.paste(src, (x0+(910-src.width)//2,y0+(680-src.height)//2))
    d.rectangle((24,138,934,821),outline="#9fbbc9",width=2)
    d.text((29,100),"REFERENCIA EXTERNA — imagem ORIGINAL em escala reduzida",
           fill=dark,font=_fonte(17))
    d.text((954,100),"MOTOR CORINGA — SVG gerado pelo renderizador atual",
           fill=dark,font=_fonte(16))
    dst=mechanism.copy()
    dst.thumbnail((540,960))
    canvas.paste(dst,(957,89+(960-dst.height)//2))
    # Regras de proveniencia e alertas. Area lateral inferior sob a foto.
    d.text((28,840),"Autor: "+ref["source"]["author"]+
           "  |  Licenca: "+ref["source"]["license"],font=_fonte(16),fill=dark)
    d.text((28,868),"Origem: Wikimedia Commons  |  anotacoes de pecas = candidatas manuais",
           font=_fonte(14),fill=muted)
    d.text((28,898),"NAO E FOTO INDUSTRIAL, NEM MODELO 3D; BELT/PISTAO INTERNOS NAO VISIVEIS",
           font=_fonte(14),fill="#8c4431")
    d.text((28,926),"A carenagem cobre a correia; nao usá-la como prova do trajeto.",
           font=_fonte(14),fill=dark)
    d.text((28,962),"CC BY-SA 4.0 — redimensionado na prancha. Publicacao: BLOQUEADA.",
           font=_fonte(14),fill=dark)
    d.text((28,995),"SHA verificado: "+timestamp[:36],
           font=_fonte(13),fill=muted)
    return canvas


def gerar(ref: dict, body: bytes, out: Path, *, animar=False) -> dict:
    check=conferir_bytes(ref,body)
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    original=_foto(body)
    manifest=json.loads(COMP.MANIFESTO_PADRAO.read_text(encoding="utf8"))
    COMP.validar_plano(manifest)
    def frame(progress):
        svg=COMP.frame_svg(progress,manifest,camera_causal=False,realce_causal=False)
        with Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode("utf8")))) as im:
            return im.convert("RGB").copy()
    sheet=_composicao(ref,original,frame(0.52),check["original_sha256"])
    sheet_path=out/"CONTATO_REFERENCIA_VS_COMPRESSOR_REAL_F9.jpg"
    sheet.save(sheet_path,quality=92)
    sample = Image.new("RGB",(1000,714),"white")
    resized=original.copy();resized.thumbnail((1000,714))
    sample.paste(resized,((1000-resized.width)//2,(714-resized.height)//2))
    dd=ImageDraw.Draw(sample)
    for part in ref["claims"]["visible_parts"]:
        x,y,w,h=part["bbox"]
        dd.rectangle((x*1000,y*714,(x+w)*1000,(y+h)*714),outline="#e86528",width=3)
    sample.save(out/"BBOX_CANDIDATAS_MANUAIS_NAO_VLM.jpg",quality=88)
    report={
        "schema":"coringa-reference-evidence-f9-result-v1",
        "source_page":ref["source"]["page"],
        "source_url":ref["source"]["file_url"],
        "credit":ref["source"]["attribution"],
        "license":ref["source"]["license"],
        "license_url":ref["source"]["license_url"],
        "changes_notice":ref["source"]["changes_notice"],
        "source_license_evidence":"commons_page_reviewed_not_license_of_new_3d_model",
        "reference_type":ref["reference_type"],
        "scope":"whole_assembly_external_appearance_only",
        "physics_simulated_from_external_image":False,
        "frames_inferred_from_image":False,
        "visual_parts_published":False,
        "identity_homologated":False,
        "publication_allowed":False,
        "visible_manual_roles":[x["role"] for x in ref["claims"]["visible_parts"]],
        "hidden_unverified_roles":ref["claims"]["hidden_parts"],
        **check,
    }
    if animar:
        if not check["sha_pinned_and_verified"]:
            fail("SHA-NAO-FIXADO")
        path=out/"AUDITORIA_F9_COMPRESSOR_VS_REFERENCIA_PRIVADA.mp4"
        cmd=["ffmpeg","-hide_banner","-loglevel","error","-y",
             "-f","rawvideo","-pix_fmt","rgb24","-video_size","1530x1050",
             "-r","16","-i","-","-c:v","libx264","-preset","veryfast",
             "-crf","24","-pix_fmt","yuv420p","-movflags","+faststart",str(path)]
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
        try:
            for i in range(128): # 8s x 16fps, somente QA comparativo
                board=_composicao(ref,original,frame(i/128),check["original_sha256"])
                if proc.stdin is None: fail("ENCODER")
                proc.stdin.write(board.tobytes())
        finally:
            if proc.stdin: proc.stdin.close()
        if proc.wait()!=0 or not path.is_file() or path.stat().st_size<40000:
            fail("ENCODER")
        report["private_comparison_mp4_sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
        report["private_comparison_duration_s"]=8
        report["private_comparison_fps"]=16
    report["evidence_files"]=["CONTATO_REFERENCIA_VS_COMPRESSOR_REAL_F9.jpg",
                              "BBOX_CANDIDATAS_MANUAIS_NAO_VLM.jpg"]
    (out/"RELATORIO_REFERENCIA_F9.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
    return report


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--manifesto",type=Path,default=MANIFEST)
    p.add_argument("--saida",type=Path,required=True)
    p.add_argument("--animar",action="store_true")
    args=p.parse_args(argv)
    ref=carregar(args.manifesto)
    data=adquirir(ref,exigir_pin=args.animar)
    report=gerar(ref,data,args.saida,animar=args.animar)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if not ref["file"]["expected_sha256"]:
        print("F9_SHA_CANDIDATO_PARA_FIXAR="+report["original_sha256"])
        print("F9_SEM_PIN=apenas referencia comparativa, sem MP4 e sem habilitar pipeline")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
