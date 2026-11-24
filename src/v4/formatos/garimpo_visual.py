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



# E206 — aquisição documental antes de solicitar representação sintética.
def candidatos_documentais(consultas, video, buscar=None, diagnostico=None):
    """Reusa pesquisa Commons de midia, mas preserva página e original da API.
    Metadados não demonstram ação e não homologam direitos.
    """
    from src import midia
    from urllib.parse import urlsplit
    buscar = buscar or midia._commons
    out, vistos, falhas = [], set(), []
    for q in consultas[:2]:
        try:
            pages = buscar(q, video=video)
        except Exception as exc:
            falhas.append({'consulta': q, 'erro': str(exc)[:180]})
            if getattr(getattr(exc, 'response', None), 'status_code', None) in (403, 429):
                break
            continue
        if diagnostico is not None:
            diagnostico.append({'consulta': q, 'tipo': 'video' if video else 'foto', 'retornados_api': len(pages),
                                'recusados': {}})
        for p in pages:
            inf = (p.get('videoinfo' if video else 'imageinfo') or [{}])[0]
            meta = inf.get('extmetadata') or {}
            lic = midia._txt(meta, 'LicenseShortName').upper()
            autor = midia._txt(meta, 'Artist')
            url, pagina = inf.get('url') or '', inf.get('descriptionurl') or ''
            u, pg = urlsplit(url), urlsplit(pagina)
            mime = inf.get('mime') or ''
            razoes = []
            if lic not in LICENCAS or not autor:
                razoes.append('licenca_ou_autor')
            if (u.scheme != 'https' or u.netloc != 'upload.wikimedia.org'
                    or not u.path.startswith('/wikipedia/commons/') or u.query or u.fragment
                    or pg.scheme != 'https' or pg.netloc != 'commons.wikimedia.org'
                    or not pg.path.startswith('/wiki/File:')):
                razoes.append('origem')
            if url in vistos or not midia._relevante(p.get('title', ''), q):
                razoes.append('repetida_ou_relevancia_textual')
            if min(inf.get('width') or 0, inf.get('height') or 0) < 700:
                razoes.append('resolucao')
            if not 0 < (inf.get('size') or 0) <= 25_000_000:
                razoes.append('tamanho')
            if mime not in (('video/webm', 'video/ogg', 'video/mp4', 'application/ogg') if video else ('image/jpeg', 'image/png')):
                razoes.append('mime')
            if razoes:
                if diagnostico is not None:
                    d = diagnostico[-1]['recusados']
                    for motivo in razoes:
                        d[motivo] = d.get(motivo, 0)+1
                continue
            vistos.add(url)
            out.append({'url': url, 'pagina': pagina, 'titulo': p.get('title'),
                        'autor': autor, 'licenca': lic, 'credito': autor + ' · ' + lic,
                        'bytes_declarados': inf['size'], 'mime': mime,
                        'tipo': 'video' if video else 'foto', 'consulta': q,
                        'estado': 'CANDIDATO_SEM_INSPECAO', 'publicar': False})
    return out, falhas


def _original_documental(candidato, destino, reader=None):
    """Preserva bytes, gera amostras de vídeo com tempos originais.
    Ainda não autoriza uso, nem insere automaticamente no acervo comprovado.
    """
    from src.v4.formatos import prospeccao_video_acao as V
    if reader is None:
        def reader(url):
            import requests
            with requests.get(url, timeout=(12, 45), stream=True, allow_redirects=False,
                              headers={'User-Agent': 'CoringaExplica/QA-Privada/1.0 (GitHub Heitor2404)'}) as r:
                if r.status_code != 200:
                    raise ValueError('HTTP ' + str(r.status_code))
                data = bytearray()
                for chunk in r.iter_content(256 * 1024):
                    data.extend(chunk)
                    if len(data) > 25_000_000:
                        raise ValueError('E206-LIMITE')
                return bytes(data)
    data = reader(candidato['url'])
    if (not isinstance(data, bytes) or not 0 < len(data) <= 25_000_000
            or (candidato.get('bytes_declarados') is not None and len(data) != candidato['bytes_declarados'])):
        raise ValueError('E206-BYTES')
    sha = hashlib.sha256(data).hexdigest()
    ext = {'video/webm': '.webm', 'video/ogg': '.ogv', 'application/ogg': '.ogv',
           'video/mp4': '.mp4', 'image/jpeg': '.jpg', 'image/png': '.png'}[candidato['mime']]
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    arq = destino / (sha + ext)
    if candidato['tipo'] == 'foto':
        with Image.open(io.BytesIO(data)) as im:
            im.verify()
        with Image.open(io.BytesIO(data)) as im:
            if im.format not in ('JPEG', 'PNG') or min(im.size) < 700:
                raise ValueError('E206-FOTO')
            meta = {'largura': im.width, 'altura': im.height}
            im = im.convert('RGB')
            im.thumbnail((900, 900))
            im.save(destino / (sha + '-contato.jpg'), quality=90)
        arq.write_bytes(data)
    else:
        arq.write_bytes(data)
        try:
            meta = V.ffprobe(arq)
            if min(meta['largura'], meta['altura']) < 700:
                raise ValueError('E206-VIDEO')
            dur = meta['duracao_s']
            janela = min(8., dur - .1)
            meta.update(V.contato(arq, {'janela_candidata': {'inicio_s': (dur-janela)/2,
                        'duracao_s': janela}}, destino / (sha + '-contato.jpg'), meta))
        except Exception:
            arq.unlink(missing_ok=True)
            raise
    return {**candidato, **meta, 'arquivo': arq.name, 'sha256_origem': sha,
            'contato': sha + '-contato.jpg', 'estado': 'BYTES_ADQUIRIDOS_REVISAO_PENDENTE',
            'identidade_e_acao_confirmadas': False, 'direitos_revisados': False,
            'publicar': False}



def candidato_institucional(fonte):
    """Adapter for specific FWS media pages with individually declared PD status.
    This accepts a research receipt, not a model-generated license or a final approval.
    """
    from urllib.parse import urlsplit
    u = urlsplit(str(fonte.get('url') or ''))
    p = urlsplit(str(fonte.get('pagina') or ''))
    if (u.scheme != 'https' or u.netloc != 'www.fws.gov'
            or not u.path.startswith('/sites/default/files/images/')
            or not u.path.lower().endswith(('.jpg','.jpeg','.png')) or u.query or u.fragment
            or p.scheme != 'https' or p.netloc != 'www.fws.gov'
            or not p.path.startswith('/media/') or p.query or p.fragment
            or fonte.get('licenca') != 'PUBLIC DOMAIN'
            or not all(isinstance(fonte.get(k), str) and fonte[k].strip()
                       for k in ('autor','titulo','mostra','evidencia_licenca'))):
        raise ValueError('E208-FONTE-INSTITUCIONAL')
    return {'url': fonte['url'], 'pagina': fonte['pagina'], 'titulo': fonte['titulo'],
            'autor': fonte['autor'], 'licenca': fonte['licenca'],
            'credito': fonte['autor']+' · U.S. Fish & Wildlife Service · Public Domain',
            'evidencia_licenca': fonte['evidencia_licenca'], 'mostra': fonte['mostra'],
            'bytes_declarados': None, 'mime': 'image/png' if u.path.lower().endswith('.png') else 'image/jpeg',
            'tipo': 'foto', 'provedor': 'FWS', 'estado': 'CANDIDATO_SEM_INSPECAO', 'publicar': False}


def pesquisar_triagem(triagem, destino, buscar=None, reader=None, fontes_institucionais=None):
    """Pesquisa necessidades documentais; mantém mapa e lacuna em filas próprias.
    Procura vídeo e foto, sem conversão automática para desenho.
    """
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    resultados, adquiridos, usados = [], [], set()
    for n in triagem:
        if n['modalidade_proposta'] != 'registro_real':
            resultados.append({'id': n['id'], 'estado': n['estado']})
            continue
        q = n['pesquisa'].get('consultas_en') or n['pesquisa']['consultas']
        linha = {'id': n['id'], 'candidatos': [], 'falhas': [], 'adquiridos': [], 'diagnostico_busca': []}
        for video in (True, False):
            cs, falhas = candidatos_documentais(q, video, buscar, linha['diagnostico_busca'])
            linha['candidatos'] += cs
            linha['falhas'] += falhas
            for c in [x for x in cs if x['url'] not in usados][:2]:
                try:
                    a = _original_documental(c, destino / 'originais', reader)
                    adquiridos.append(a)
                    usados.add(c['url'])
                    linha['adquiridos'].append(a['sha256_origem'])
                    break
                except Exception as exc:
                    linha['falhas'].append({'url': c['url'], 'erro': str(exc)[:180]})
                    if 'HTTP 429' in str(exc) or 'HTTP 403' in str(exc):
                        break
        # Fonte institucional explícita, pesquisada/registrada fora do modelo.
        # Nunca aceitar links arbitrários sugeridos pela IA.
        if not linha['adquiridos']:
            for fonte in (fontes_institucionais or {}).get(n['id'], [])[:3]:
                try:
                    c = candidato_institucional(fonte)
                    linha['candidatos'].append(c)
                    if c['url'] in usados:
                        continue
                    a = _original_documental(c, destino / 'originais', reader)
                    adquiridos.append(a)
                    usados.add(c['url'])
                    linha['adquiridos'].append(a['sha256_origem'])
                except Exception as exc:
                    linha['falhas'].append({'provedor':'institucional', 'erro':str(exc)[:180]})
        linha['estado'] = ('REVISAO_MIDIA_PENDENTE' if linha['adquiridos'] else 'PESQUISA_SEM_BYTES')
        resultados.append(linha)
    r = {'publicar': False, 'aprovacao_humana': 'PENDENTE',
         'resultados': resultados, 'adquiridos': adquiridos}
    (destino / 'manifesto.json').write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding='utf8')
    return r


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
