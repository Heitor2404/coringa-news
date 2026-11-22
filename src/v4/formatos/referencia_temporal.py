"""Amostragem TEMPORAL de referência real (GIF ou vídeo local).

Objetivo: observar mudança mecânica ao longo do tempo. Cinco imagens genéricas
não bastam para afirmar etapas de motor/compressor. Nada é publicado/copiadado
para um vídeo de produção. Fonte local obrigatória, com SHA e frames JPEG.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import subprocess
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

MAX_BYTES = 30_000_000
FILE_RE = re.compile(r"^quadro_[0-9]{2}\.jpg$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hash_file(path: Path) -> str:
    hash_obj = hashlib.sha256()
    with path.open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            hash_obj.update(part)
    return hash_obj.hexdigest()


def _indices(n: int, count: int) -> list[int]:
    return sorted(set(round((n - 1) * x / (count - 1))
                      for x in range(count)))


def _validar_frame(data: bytes) -> None:
    if not data or len(data) > 5_000_000:
        raise ValueError("F-QUADRO-TAMANHO")
    try:
        with Image.open(io.BytesIO(data)) as im:
            if im.format != "JPEG" or min(im.size) < 80:
                raise ValueError("F-QUADRO-ILEGIVEL")
            im.verify()
    except OSError as exc:
        raise ValueError("F-QUADRO-INVALIDO") from exc


def _distancia(x: bytes, y: bytes) -> float:
    with Image.open(io.BytesIO(x)) as a, Image.open(io.BytesIO(y)) as b:
        aa = a.convert("RGB").resize((96, 96))
        bb = b.convert("RGB").resize((96, 96))
        return sum(ImageStat.Stat(ImageChops.difference(aa, bb)).mean) / 3


def amostrar(arquivo: Path, destino: Path, referencia_id: str, *,
            pagina: str | None = None, licenca_declarada: str | None = None,
            count: int = 12, run=None) -> dict:
    """Gera 12+ quadros e um manifest de integridade; NUNCA sem arquivo real."""
    arquivo, destino = Path(arquivo), Path(destino)
    if (not isinstance(referencia_id, str)
            or not re.fullmatch(r"[a-zA-Z0-9_.:-]{3,90}", referencia_id)):
        raise ValueError("F-REFERENCIA-ID")
    if count < 10 or count > 20:
        raise ValueError("F-FRAMES-TEMPORAIS: usar 10..20 quadros")
    if not arquivo.is_file() or arquivo.stat().st_size > MAX_BYTES:
        raise ValueError("F-REFERENCIA-ARQUIVO-INVALIDO")
    ext = arquivo.suffix.lower()
    if ext not in (".gif", ".mp4", ".webm", ".mov"):
        raise ValueError("F-REFERENCIA-EXTENSAO")
    if destino.resolve() == arquivo.parent.resolve():
        raise ValueError("F-REFERENCIA-DESTINO: nunca sobrescrever origem")
    destino.mkdir(parents=True, exist_ok=True)
    imgs: list[tuple[int, float, bytes]] = []

    if ext == ".gif":
        with Image.open(arquivo) as gif:
            if gif.format != "GIF" or gif.n_frames < count or gif.n_frames > 2500:
                raise ValueError("F-REFERENCIA-CICLO-CURTO: GIF tem poucos frames")
            indices = _indices(gif.n_frames, count)
            durations: list[float] = []
            for pos in range(gif.n_frames):
                gif.seek(pos)
                durations.append(max(.02, float(gif.info.get("duration", 100)) / 1000))
            starts = [0.]
            for duration in durations[:-1]:
                starts.append(starts[-1] + duration)
            for index in indices:
                gif.seek(index)
                im = gif.convert("RGB")
                if min(im.size) < 80 or im.width * im.height > 8_000_000:
                    raise ValueError("F-REFERENCIA-RESOLUCAO")
                im.thumbnail((720, 720), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                im.save(buf, "JPEG", quality=91)
                imgs.append((index, round(starts[index], 3), buf.getvalue()))
    else:
        run = run or subprocess.run
        output = run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration:stream=codec_type,width,height",
             "-of", "json", str(arquivo)],
            capture_output=True, text=True, timeout=40, check=True)
        md = json.loads(output.stdout)
        duration = float(md.get("format", {}).get("duration", 0))
        stream = next((s for s in md.get("streams", [])
                       if s.get("codec_type") == "video"), None)
        if not stream or not .65 <= duration <= 1200:
            raise ValueError("F-REFERENCIA-VIDEO-METADADOS")
        for index in range(count):
            t = duration * (.03 + .93 * index / (count - 1))
            out = destino / f"quadro_{index:02d}.jpg"
            run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                 "-ss", f"{t:.4f}", "-i", str(arquivo), "-vf",
                 "scale=640:-2", "-frames:v", "1", str(out)],
                capture_output=True, timeout=50, check=True)
            data = out.read_bytes()
            imgs.append((index, round(t, 3), data))

    for _, _, data in imgs:
        _validar_frame(data)
    moving = sum(_distancia(imgs[i][2], imgs[i + 1][2]) >= 2.4
                 for i in range(len(imgs) - 1))
    if moving < 3:
        raise ValueError("F-SEM-MOVIMENTO-SUFICIENTE: quadros quase estaticos")
    frames = []
    for ordinal, (index, second, data) in enumerate(imgs):
        filename = f"quadro_{ordinal:02d}.jpg"
        (destino / filename).write_bytes(data)
        frames.append({"ordinal": ordinal, "indice_origem": index,
                       "segundo": second, "arquivo": filename, "sha256": _sha(data)})
    manifest = {
        "schema": "reference-first-temporal-v1",
        "referencia_id": referencia_id,
        "arquivo_origem": str(arquivo.resolve()),
        "arquivo_sha256": _hash_file(arquivo),
        "pagina_declarada": pagina, "licenca_declarada": licenca_declarada,
        "licenca_verificada_para_publicacao": False,
        "midia": ext[1:],
        "amostras": frames, "intervalos_em_movimento": moving,
        "estado": "FRAMES_REAIS_SEM_VALIDACAO_SEMANTICA",
        "publicar": False,
    }
    (destino / "manifesto_temporal.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf8")
    return manifest


def carregar(destino: Path) -> tuple[dict, list[bytes]]:
    """Fail closed ante origem ou quadros adulterados; recusa path traversal."""
    destino = Path(destino)
    m = json.loads((destino / "manifesto_temporal.json").read_text(encoding="utf8"))
    if m.get("schema") != "reference-first-temporal-v1":
        raise ValueError("F-REFERENCIA-MANIFESTO-VERSAO")
    original_path = Path(m.get("arquivo_origem") or "")
    sha = m.get("arquivo_sha256")
    if (not original_path.is_file() or not isinstance(sha, str)
            or not SHA_RE.fullmatch(sha) or _hash_file(original_path) != sha):
        raise ValueError("F-REFERENCIA-SHA-ORIGINAL")
    frames = m.get("amostras")
    if not isinstance(frames, list) or not 10 <= len(frames) <= 20:
        raise ValueError("F-REFERENCIA-QUADROS")
    images, last_t, names = [], -1., set()
    for i, it in enumerate(frames):
        name = it.get("arquivo") if isinstance(it, dict) else None
        if (not isinstance(name, str) or not FILE_RE.fullmatch(name)
                or name in names or it.get("ordinal") != i
                or not isinstance(it.get("segundo"), (float, int))
                or isinstance(it.get("segundo"), bool)
                or it["segundo"] <= last_t):
            raise ValueError("F-REFERENCIA-QUADROS-META")
        names.add(name)
        last_t = it["segundo"]
        src = destino / name
        if not src.is_file():
            raise ValueError("F-REFERENCIA-QUADRO-AUSENTE")
        data = src.read_bytes()
        if (_sha(data) != it.get("sha256") or
                not SHA_RE.fullmatch(str(it.get("sha256", "")))):
            raise ValueError("F-REFERENCIA-QUADRO-MODIFICADO")
        _validar_frame(data)
        images.append(data)
    return m, images
