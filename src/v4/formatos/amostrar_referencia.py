"""Baixa e AMOSTRA GIFs de referencias, sem inferir o processo do titulo.

Somente referencia visual privada. Os originais ficam no artifact e nunca no
repositório nem no video final. A conclusao sobre as fases depende de visao.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

import requests
from PIL import Image, ImageDraw

from src.v4.formatos.referencias_mecanismos import UA

MAX_BYTES = 16_000_000


def amostrar_gif(candidato: dict, saida: Path, get=None) -> dict:
    if candidato.get("midia") != "animacao_gif":
        raise ValueError("F-REFERENCIA-TIPO: so GIF aqui")
    url = candidato.get("origem_media")
    parts = urlsplit(str(url or ""))
    if (parts.scheme != "https" or parts.hostname != "upload.wikimedia.org"
            or not parts.path.lower().endswith(".gif")):
        raise ValueError("F-REFERENCIA-ORIGEM: somente GIF Commons")
    get = get or requests.get
    r = get(url, headers=UA, stream=True, timeout=32)
    r.raise_for_status()
    raw = bytearray()
    for chunk in r.iter_content(chunk_size=65536):
        raw.extend(chunk)
        if len(raw) > MAX_BYTES:
            raise ValueError("F-REFERENCIA-TAMANHO: GIF acima do limite")
    if not raw.startswith((b"GIF87a", b"GIF89a")):
        raise ValueError("F-REFERENCIA-CONTEUDO: resposta nao e GIF")
    try:
        with Image.open(io.BytesIO(raw)) as im:
            n = im.n_frames
            if n < 2 or n > 1200:
                raise ValueError("F-REFERENCIA-QUADROS: nao animado/limite")
            # Index da primeira e quatro amostras, sem dizer que toda fase
            # foi representada. Temporalidade do GIF nao equivale a 30fps.
            indices = sorted(set(round((n-1)*j/4) for j in range(5)))
            images = []
            for i in indices:
                im.seek(i)
                frame = im.convert("RGB")
                frame.thumbnail((320,420), Image.Resampling.LANCZOS)
                images.append((i,frame.copy()))
    except (OSError, SyntaxError) as e:
        raise ValueError("F-REFERENCIA-GIF-INVALIDO") from e
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGB", (340*len(images), 475), "#13243A")
    draw = ImageDraw.Draw(sheet)
    for j,(i,im) in enumerate(images):
        x = 340*j+(340-im.width)//2
        y = 35+(420-im.height)//2
        sheet.paste(im,(x,y))
        draw.text((340*j+15,12),f"Frame {i}/{n-1}",fill="#FFD21F")
    sheet.save(saida/"contato_referencia.jpg",quality=88)
    (saida/"original.gif").write_bytes(raw)
    ret = {
        "referencia_id": candidato.get("id"),
        "pagina": candidato.get("pagina"),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "numero_quadros": n, "amostras": indices,
        "estado": "QUADROS_EXTRAIDOS_SEM_ANALISE_SEMANTICA",
        "publicar": False,
        "veredito_visual": "PENDENTE",
    }
    (saida/"inspecao.json").write_text(json.dumps(ret,ensure_ascii=False,indent=2),
                                       encoding="utf-8")
    return ret
