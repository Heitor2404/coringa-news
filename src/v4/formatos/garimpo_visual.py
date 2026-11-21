"""Garimpo visual ATLAS — REUSA acervo V4 + verificação visual V4, sem nova API.

NÃO é uma aprovação para publicar: a mídia passa a integrar APENAS o catálogo
temporário da prévia privada. Arquivo real é identificado por SHA-256 dos bytes
baixados; licença/perfil são registrados por item, sem fotos de IA e sem scraping.
Falha de fonte, cota ou ausência de objeto: cenário permanece SEM PROVA.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw

# Por segurança optamos inicialmente por licenças simples. BY-SA só após
# análise específica de obrigações de distribuição da obra derivada.
LICENCAS = {'CC BY 2.0', 'CC BY 3.0', 'CC BY 4.0', 'CC0', 'PUBLIC DOMAIN', 'PUBLIC DOMAIN MARK'}


def _licenca(credito: str) -> str | None:
    texto = str(credito or '').upper().replace('-', ' ')
    for x in ('CC BY 4.0', 'CC BY 3.0', 'CC BY 2.0', 'CC0', 'PUBLIC DOMAIN MARK', 'PUBLIC DOMAIN'):
        if re.search(r'(?<![A-Z])' + re.escape(x) + r'(?![A-Z])', texto):
            return x
    return None


def procurar(brief: dict, usados: set[str], procurar_candidatos=None, escolher=None,
            baixar=None) -> tuple[dict | None, dict]:
    """1 plano de mídia por pergunta visual, nunca foto aleatória por palavra-chave."""
    if procurar_candidatos is None or escolher is None:
        from src.v4 import acervo_v4
        procurar_candidatos = procurar_candidatos or acervo_v4.candidatos
        escolher = escolher or acervo_v4.escolher
    if baixar is None:
        def baixar(url):
            import requests
            r = requests.get(url, headers={'User-Agent': 'CoringaExplica/1.0 (https://github.com/Heitor2404)'}, timeout=90)
            r.raise_for_status()
            if len(r.content) > 20_000_000:
                raise ValueError('mídia >20 MB: ignorar')
            return r.content
    busca = {'consultas_en': brief.get('consultas_en') or [], 'tipo': 'foto'}
    candidatos = procurar_candidatos(busca) or []
    filtrados = [c for c in candidatos
                 if c.get('url') not in usados and _licenca(c.get('credito')) in LICENCAS
                 and min(int(c.get('w') or 0), int(c.get('h') or 0)) >= 700]
    if not filtrados:
        return None, {'id': brief.get('id'), 'estado': 'SEM_MIDIA', 'motivo': 'sem candidatos livres/legíveis em dimensão mínima'}
    escolha, veredito = escolher(filtrados, brief['deve_mostrar'], usados, brief.get('consultas_en'))
    if not escolha or (veredito or {}).get('prova') != 'PROVADO':
        return None, {'id': brief.get('id'), 'estado': 'SEM_MIDIA', 'motivo': (veredito or {}).get('motivo') or 'visão não comprovou'}
    url = escolha['url']
    if url in usados:
        return None, {'id': brief.get('id'), 'estado': 'REPETIDA'}
    try:
        dados = baixar(url)
        with Image.open(io.BytesIO(dados)) as img:
            img.verify()
        with Image.open(io.BytesIO(dados)) as img:
            w, h = img.size
            if min(w, h) < 700 or img.format not in ('JPEG', 'PNG'):
                raise ValueError(f'baixa resolução/arquivo inválido {w}x{h}')
        sha = hashlib.sha256(dados).hexdigest()
        nome = f"scout:{sha[:16]}"
        lic = _licenca(escolha['credito'])
        it = {'id': nome, 'titulo': escolha.get('titulo') or '', 'natureza': 'foto',
              'mostra': brief['deve_mostrar'], 'termos': brief.get('consultas_en') or [],
              'credito': escolha['credito'], 'licenca': lic, 'uso_comercial': 'sim',
              'url': url, 'pagina': escolha.get('pagina') or '',
              'sha256_origem': sha, 'wh': [w, h],
              'prova': {'midia_corresponde': True, 'revisor': 'Gemini visão - seleção privada',
                        'evidencia': (veredito or {}).get('motivo'),
                        'criterio_visual': brief['deve_mostrar'],
                        'local_confere': veredito.get('local_confere'),
                        'objeto_confere': veredito.get('objeto_confere'),
                        'roi': veredito.get('roi')},
              'uso_provisorio_previa': True}
        usados.add(url)
        return (it, dados), {'id': brief.get('id'), 'estado': 'CANDIDATO_VERIFICADO',
                             'asset': nome, 'w': w, 'h': h, 'licenca': lic, 'sha256_origem': sha}
    except Exception as ex:
        return None, {'id': brief.get('id'), 'estado': 'SEM_MIDIA',
                      'motivo': f'falha na origem: {type(ex).__name__}: {str(ex)[:130]}'}


def coletar(briefs: list[dict], destino: Path, procurar_candidatos=None, escolher=None,
            baixar=None) -> dict:
    destino = Path(destino)
    (destino / 'imagens').mkdir(parents=True, exist_ok=True)
    # Somente JPEG de prévia nunca substitui o original: preserve exatamente
    # os bytes verificados pela visão/SHA para o runner seguinte.
    (destino / 'originais').mkdir(parents=True, exist_ok=True)
    usados, itens, rel, thumbs = set(), [], [], []
    for brief in briefs:
        o, status = procurar(brief, usados, procurar_candidatos, escolher, baixar)
        rel.append(status)
        if o is None:
            continue
        it, dados = o
        sha = hashlib.sha256(dados).hexdigest()
        if sha != it['sha256_origem']:
            raise RuntimeError('A mídia mudou após aprovação visual: recusar')
        with Image.open(io.BytesIO(dados)) as src:
            ext = 'png' if src.format == 'PNG' else 'jpg'
        original = destino / 'originais' / f'{sha}.{ext}'
        original.write_bytes(dados)
        it['arquivo_original'] = str(original.relative_to(destino))
        itens.append(it)
        arq = destino / 'imagens' / (it['id'].replace(':', '_') + '.jpg')
        with Image.open(io.BytesIO(dados)) as img:
            rgb = img.convert('RGB')
            rgb.thumbnail((1300, 1300), Image.Resampling.LANCZOS)
            rgb.save(arq, quality=91)
            im = rgb.copy()
        im.thumbnail((400, 360), Image.Resampling.LANCZOS)
        thumbs.append((it['id'], im))
    if thumbs:
        w, h = 430, 455
        contato = Image.new('RGB', (w * min(3, len(thumbs)),
                                   h * ((len(thumbs) + 2) // 3)), '#080F1A')
        d = ImageDraw.Draw(contato)
        for i, (nome, im) in enumerate(thumbs):
            x, y = (i % 3) * w, (i // 3) * h
            contato.paste(im, (x + (w - im.width) // 2, y + 16))
            d.text((x + 15, y + 378), nome[:29], fill='#FFD21F')
        contato.save(destino / 'contato.jpg', quality=85)
    res = {'versao': 1, 'uso': 'PREVIA_PRIVADA_APENAS',
           'itens': itens, 'relatorio': rel}
    (destino / 'catalogo.json').write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
    return res


def main(argv=None) -> int:
    args = argv or sys.argv[1:]
    if len(args) != 2:
        print('Uso: python -m src.v4.formatos.garimpo_visual <briefs.json> <saida>', file=sys.stderr)
        return 2
    briefs = json.loads(Path(args[0]).read_text(encoding='utf-8'))['briefs']
    r = coletar(briefs, Path(args[1]))
    print(json.dumps({'itens': len(r['itens']), 'relatorio': r['relatorio']}, ensure_ascii=False)[:12000])
    return 0 if len(r['itens']) == len(briefs) else 1


if __name__ == '__main__':
    raise SystemExit(main())
