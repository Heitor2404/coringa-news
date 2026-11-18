"""Prévia auditável de fotos livres para o pacote ATLAS de semicondutores.

Apenas lê CANDIDATOS, obtém miniaturas do Wikimedia Commons e cria
um contato com atribuições + JSON SHA256. NÃO promove mídia à produção.
Uso: python scripts/atlas_acervo_chips_preview.py <diretorio_saida>
Requer Pillow; nenhuma IA, nenhum serviço pago, nenhuma edição no pipeline.
"""
from __future__ import annotations

import hashlib
import html
import io
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError

RAIZ = Path(__file__).resolve().parents[1]
BASE = RAIZ / "src/v4/formatos/biblioteca_atlas/midias_candidatas_chips.json"
UA = "CoringaAtlasLibrary/0.1 (noncommercial metadata validation preview; https://github.com/Heitor2404/coringa-news)"
MAX_BYTES = 12 * 1024 * 1024
CARD_W, CARD_H = 510, 340
W, H = 1120, 1600


def _request_bytes(url: str, limit: int = MAX_BYTES) -> bytes:
    p = urlsplit(url)
    assert p.scheme == "https" and p.hostname in (
        "commons.wikimedia.org", "upload.wikimedia.org", "thumb.wikimedia.org"
    ), f"Origem fora da allowlist: {p.hostname}"
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/json, image/jpeg, image/png, image/webp",
    })
    with urllib.request.urlopen(req, timeout=30) as res:
        body = res.read(limit + 1)
    if len(body) > limit:
        raise ValueError("Download excedeu limite de 12 MiB")
    return body


def consultar_arquivo(nome: str) -> dict:
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query",
        "format": "json",
        "prop": "imageinfo",
        "iiprop": "url|size|sha1|extmetadata",
        "iiurlwidth": "960",
        "titles": "File:" + nome,
    })
    j = json.loads(_request_bytes(url, 2_000_000).decode("utf-8"))
    paginas = j.get("query", {}).get("pages", {})
    for page in paginas.values():
        infos = page.get("imageinfo") or []
        if infos:
            return infos[0]
    raise RuntimeError(f"Commons não devolveu imageinfo para {nome!r}")


def escolher_font():
    for p in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ):
        if Path(p).exists():
            return ImageFont.truetype(p, 19)
    return ImageFont.load_default()


def criar_galeria(itens: list[dict], saida: Path):
    im = Image.new("RGB", (W, H), "#05080F")
    d = ImageDraw.Draw(im)
    font = escolher_font()
    d.text((54, 34), "ATLAS  /  ACERVO DE SEMICONDUTORES", font=font, fill="#FFD21F")
    d.text((54, 74), "PREVIA DE CURADORIA — NAO APROVADA PARA VIDEO", font=font, fill="#F2EDE3")
    for i, item in enumerate(itens[:5]):
        cx = 48 + (i % 2) * 532
        cy = 130 + (i // 2) * 472
        d.rounded_rectangle((cx, cy, cx + CARD_W, cy + 450), radius=12, fill="#101A2A")
        if item.get("_im"):
            foto = item["_im"]
            foto = ImageOps.contain(foto, (CARD_W - 18, CARD_H - 12), Image.Resampling.LANCZOS)
            im.paste(foto, (cx + (CARD_W - foto.width)//2, cy + (CARD_H - foto.height)//2))
        else:
            d.text((cx + 26, cy + 100), "FOTO INDISPONIVEL", fill="#E5483A", font=font)
        nome = item["titulo"]
        if len(nome) > 36:
            nome = nome[:33] + "..."
        d.text((cx + 12, cy + 344), nome, fill="#FFFFFF", font=font)
        credito = item["autor"] + " / " + item["licenca"]
        if len(credito) > 49:
            credito = credito[:46] + "..."
        d.text((cx + 12, cy + 381), credito, fill="#C1CDD9", font=font)
        status = "ARQUIVO CONFERIDO" if item.get("download_ok") else "INCOMPLETO"
        d.text((cx + 12, cy + 412), status, fill="#FFD21F" if item.get("download_ok") else "#E5483A", font=font)
    d.text((54, H - 34), "Fonte: Wikimedia Commons | sem TTS, IA ou alteracao do motor", fill="#C1CDD9", font=font)
    im.save(saida / "galeria_chips.jpg", quality=88, optimize=True)


def main(destino: Path) -> dict:
    destino.mkdir(parents=True, exist_ok=True)
    bib = json.loads(BASE.read_text(encoding="utf-8"))
    itens = []
    for item in bib["itens"]:
        i = dict(item)
        i["download_ok"] = False
        try:
            info = consultar_arquivo(i["arquivo_commons"])
            thumb = info.get("thumburl") or info.get("url")
            if not thumb:
                raise ValueError("Sem URL de imagem resolvida")
            data = _request_bytes(thumb)
            if not data.startswith((b"\xff\xd8\xff", b"\x89PNG")) and data[:4] != b"RIFF":
                raise ValueError("Bytes recebidos não parecem JPEG/PNG/WEBP")
            orig = Image.open(io.BytesIO(data))
            orig.load()
            if orig.width < 300 or orig.height < 250:
                raise ValueError(f"Preview pequeno: {orig.size}")
            if orig.width * orig.height > 16_000_000:
                raise ValueError("Preview excede limite de pixels")
            i["largura_thumb"], i["altura_thumb"] = orig.size
            i["sha256_thumb"] = hashlib.sha256(data).hexdigest()
            i["sha1_origem_commons"] = info.get("sha1")
            i["tamanho_arquivo_origem"] = info.get("size")
            i["thumb_url_resolvida"] = thumb
            i["download_ok"] = True
            i["_im"] = orig.convert("RGB")
            with open(destino / (i["id"] + ".jpg"), "wb") as f:
                i["_im"].save(f, format="JPEG", quality=86)
            print(f"OK {i['id']}: {orig.size}, sha256 thumb {i['sha256_thumb'][:12]}",flush=True)
        except Exception as e:
            i["erro"] = str(e)[:500]
            print(f"FALHA {i['id']}: {i['erro']}",flush=True)
        itens.append(i)
        time.sleep(0.6)
    criar_galeria(itens, destino)
    audit = []
    for i in itens:
        row = {k:v for k,v in i.items() if k != "_im"}
        # Captura é apenas preview; sha256_thumb NÃO É o hash de liberação do original
        row["estado"] = "candidato"
        row["aprovacao_editorial"] = False
        row["sha256"] = None
        audit.append(row)
    output = {
        "objetivo": "inspeção visual e hash de miniatura; não uso produtivo",
        "base": str(BASE.relative_to(RAIZ)),
        "total": len(itens),
        "baixadas": sum(i["download_ok"] for i in itens),
        "reprovadas_ou_indisponiveis": [i["id"] for i in itens if not i["download_ok"]],
        "itens": audit,
    }
    (destino / "auditoria_miniaturas.json").write_text(json.dumps(output,indent=2,ensure_ascii=False),encoding="utf-8")
    (destino / "CREDITOS.txt").write_text(
        "PREVIA DO ACERVO - NÃO LIBERADA PARA PUBLICAÇÃO.\n"
        + "\n".join(f'{i["id"]}: {i["credito"]} — {i["pagina"]}; licença: {i["licenca_url"]}' for i in itens)
        + "\n",encoding="utf-8")
    print(json.dumps({"total":output["total"],"baixadas":output["baixadas"],"falhas":output["reprovadas_ou_indisponiveis"]},ensure_ascii=False),flush=True)
    return output


if __name__ == "__main__":
    r = main(Path(sys.argv[1] if len(sys.argv)>1 else "saida_atlas_chips"))
    # Não marcar sucesso se todas as fontes falharam; o artefato deixa relatório de bloqueio.
    if r["baixadas"] == 0:
        sys.exit(2)
