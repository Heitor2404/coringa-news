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


def licenca_confere(declarada: str, meta: dict) -> bool:
    """Confronta descrição local com a classificação do próprio Commons.

    Não substitui a leitura humana dos termos; evita liberar troca grosseira
    entre CC BY, CC BY-SA e domínio público.
    """
    nome = str(meta.get("short_name") or "").casefold()
    url = str(meta.get("url") or "").casefold()
    declarada = declarada.casefold()
    if declarada.startswith("cc by-sa"):
        versao = declarada.rsplit(" ", 1)[-1]
        return (("by-sa/" + versao) in url or ("by-sa " + versao) in nome)
    if declarada.startswith("cc by "):
        versao = declarada.rsplit(" ", 1)[-1]
        return (("/by/" + versao) in url or ("cc by " + versao) in nome) and "by-sa" not in nome + url
    if declarada.startswith("public domain"):
        return any(p in nome for p in ("public domain", "pd-us", "pd "))
    return False


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
    for i, item in enumerate(itens[:6]):
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
            # Guardar bytes EXATOS usados no sha256_thumb (sem recompressão).
            extension = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}.get(orig.format)
            if not extension:
                raise ValueError(f"Formato não suportado: {orig.format}")
            nome_thumb = i["id"] + extension
            (destino / nome_thumb).write_bytes(data)
            assert hashlib.sha256((destino / nome_thumb).read_bytes()).hexdigest() == i["sha256_thumb"]
            i["arquivo_thumb"] = nome_thumb
            metadata = info.get("extmetadata") or {}
            i["licenca_commons"] = {
                "short_name": html.unescape((metadata.get("LicenseShortName") or {}).get("value", "")),
                "url": html.unescape((metadata.get("LicenseUrl") or {}).get("value", "")),
                "restrictions": html.unescape((metadata.get("Restrictions") or {}).get("value", "")),
            }
            i["licenca_conciliada_com_commons"] = licenca_confere(i["licenca"], i["licenca_commons"])
            i["conferencia_licenca_manual_pendente"] = (
                not i["licenca_conciliada_com_commons"]
                or (not i["licenca_commons"]["url"] and not i["licenca"].startswith("Public domain"))
            )
            print(f"OK {i['id']}: {orig.size}, hash do arquivo salvo {i['sha256_thumb'][:12]}",flush=True)
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
        "hashes_conferidos_dos_arquivos_salvos": [i["id"] for i in itens if i["download_ok"] and i.get("arquivo_thumb")],
        "licencas_com_checagem_manual_pendente": [i["id"] for i in itens if i.get("conferencia_licenca_manual_pendente")],
        "licencas_nao_conciliadas": [i["id"] for i in itens if i["download_ok"] and not i.get("licenca_conciliada_com_commons")],
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
