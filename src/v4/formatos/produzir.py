"""Produção por FORMATO (ATLAS / DOSSIÊ): narração → mídia comprovada → PREFLIGHT → render → portões no MP4.

Etapas separadas (cada uma é um comando; o Actions roda em sequência e PARA no primeiro preflight vermelho):
  narrar   — reutiliza a narração cifrada ou gera a do texto do plano (1 chamada de TTS, cota grátis; nada de repetir)
  ativos   — baixa só itens da biblioteca comprovada (procedência + licença + prova)
  preflight— sem IA e sem rede: plano válido, 100% das mídias/geometria/narração/clipes presentes, geometria do clipe V2
  render   — Remotion `Formato` (palco + primitivas) + clipes aprovados (palco V2) + camada global (marca/legendas) + som
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

from src.v4.formatos import plano as P
from src.v4.util import rodar

RAIZ = P.RAIZ
PUBLICO = RAIZ / 'motor4' / 'remotion' / 'public' / '_formato'


def _ler(arq: Path):
    return json.loads(Path(arq).read_text(encoding='utf-8'))


def _gravar(arq: Path, obj):
    Path(arq).parent.mkdir(parents=True, exist_ok=True)
    Path(arq).write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=str), encoding='utf-8')


# ---------------------------------------------------------------- narração
def narrar(plano: dict, saida: Path) -> dict:
    """→ saida/narracao.json {palavras, duracao, origem} + saida/voz.wav"""
    saida.mkdir(parents=True, exist_ok=True)
    n = plano['narracao']
    pac = None
    if n.get('cifrada'):
        from src.v3 import material
        pac = json.loads(material.decifrar(material._segredo(), (RAIZ / n['cifrada']).read_bytes()))
        if n.get('texto') and pac.get('texto') and pac['texto'] != n['texto']:
            pac = None                                   # texto do plano mudou: a gravação antiga não serve
    if pac:
        flac = saida / 'voz.flac'
        flac.write_bytes(base64.b64decode(pac['flac_b64']))
        rodar(['ffmpeg', '-v', 'error', '-y', '-i', flac, '-ar', '48000', saida / 'voz.wav'])
        meta = {'palavras': pac['palavras'], 'duracao': pac['duracao'], 'origem': pac.get('origem')}
    else:
        from src import voz
        wav, _tempos, caps, dur = voz.narrar([{'fala': n['texto']}], saida / 'tts')
        shutil.copy(wav, saida / 'voz.wav')
        pal = []
        for bl in caps:
            ws = bl['words']
            for k, w in enumerate(ws):
                fim = ws[k + 1]['s'] if k + 1 < len(ws) else bl['end']
                pal.append({'w': w['w'], 's': w['s'], 'e': round(fim, 3), 'hl': bool(w.get('hl'))})
        meta = {'palavras': pal, 'duracao': round(dur, 3), 'origem': 'TTS desta execução (uma chamada)'}
    _gravar(saida / 'narracao.json', meta)
    return meta


# ---------------------------------------------------------------- mídia
def nome_publico(asset: str) -> str:
    import hashlib
    return 'm_' + hashlib.sha1(asset.encode()).hexdigest()[:16]


def _sha(arq: Path) -> str:
    import hashlib
    return hashlib.sha256(Path(arq).read_bytes()).hexdigest()


def assets_do_plano(plano: dict) -> list[str]:
    """mídias citadas: p.asset e as presas em marcos da régua (p.marcos[].asset)"""
    out = set()
    for b in plano['beats']:
        for L in b['camadas']:
            q = L.get('p') or {}
            if q.get('asset'):
                out.add(q['asset'])
            out |= {m['asset'] for m in q.get('marcos') or [] if isinstance(m, dict) and m.get('asset')}
    return sorted(out)


def _origem(it: dict, cache: Path | None) -> tuple[bytes, str]:
    """bytes DA ORIGEM da mídia (URL da biblioteca) — ou do cache local indexado por sha256 — e de onde vieram"""
    sha = it.get('sha256_origem')
    if cache and sha:
        for f in cache.glob(f'{sha}.*'):
            return f.read_bytes(), f'cache:{f.name}'
    if cache and not sha and (cache / f"{nome_publico(it['id'])}.jpg").exists():     # só desenvolvimento local (sem rede)
        return (cache / f"{nome_publico(it['id'])}.jpg").read_bytes(), 'cache-local-sem-origem'
    import time

    import requests
    # UA no formato da política de robôs da Wikimedia (nome/versão + URL de contato): o UA sem URL do acervo_v4 recebe
    # 429 "daab851" em upload.wikimedia.org (44110855696, 44112788790); este é o mesmo que baixou tudo na coleta 44097219552
    UA = {'User-Agent': 'CoringaExplica/formatos-coleta (pesquisa editorial; https://github.com/Heitor2404)'}
    for k in range(6):          # Wikimedia devolve 429 a downloads seguidos (44110855696): respeita Retry-After e espaça
        r = requests.get(it['url'], headers=UA, timeout=120)
        if r.status_code != 429:
            break
        time.sleep(min(60, int(r.headers.get('Retry-After') or 0) or 5 * (k + 1)))
    r.raise_for_status()
    time.sleep(1.5)
    return r.content, it['url']


def ativos(plano: dict, saida: Path, cache: Path | None = None) -> dict:
    """baixa SÓ itens da biblioteca comprovada, confere a impressão digital DA ORIGEM (sha256_origem) e grava com nome
    próprio por mídia; copia os rasters do palco com o sha256 do .json de procedência. → {asset: {src, w, h, ...}}"""
    import io

    from PIL import Image

    from src.v4 import viabilidade
    from src.v4.formatos import plano as P
    por = {it['id']: it for it in viabilidade.carregar()['itens']}
    PUBLICO.mkdir(parents=True, exist_ok=True)
    (saida / 'ativos').mkdir(parents=True, exist_ok=True)
    cache = cache or (Path(os.environ['CORINGA_MIDIA_LOCAL']) if os.environ.get('CORINGA_MIDIA_LOCAL') else None)
    out = {}
    for a in assets_do_plano(plano):
        it = por[a]
        bruto, veio = _origem(it, cache)
        sha_o = hashlib.sha256(bruto).hexdigest()
        if it.get('sha256_origem') and sha_o != it['sha256_origem']:
            raise RuntimeError(f'{a}: o arquivo da origem mudou (sha256 {sha_o[:12]} ≠ {it["sha256_origem"][:12]}) — não entra no vídeo')
        im = Image.open(io.BytesIO(bruto)).convert('RGB')
        if max(im.size) > 2000:
            im.thumbnail((2000, 2000))
        nome = nome_publico(a)              # nome PRÓPRIO por mídia: dois episódios na mesma pasta não se sobrescrevem (44084129999)
        dest = PUBLICO / f'{nome}.jpg'
        im.save(dest, 'JPEG', quality=92)
        shutil.copy(dest, saida / 'ativos' / dest.name)
        out[a] = {'src': f'_formato/{nome}.jpg', 'w': im.size[0], 'h': im.size[1], 'credito': it['credito'], 'licenca': it['licenca'],
                  'url': it['url'], 'sha256': _sha(dest), 'sha256_origem': sha_o, 'origem_conferida': bool(it.get('sha256_origem')), 'veio_de': veio}
    rast = PUBLICO / 'raster'
    rast.mkdir(parents=True, exist_ok=True)
    for r in plano.get('rasters') or []:
        m = P.raster_info(r['nome'])
        src = P.RASTER_DIR / (m.get('arquivo') or f"{r['nome']}.jpg")
        shutil.copy(src, rast / src.name)
        out[f"raster:{r['nome']}"] = {'src': f'_formato/raster/{src.name}', 'sha256': _sha(rast / src.name), 'sha256_json': m['sha256'],
                                      'atribuicao': m['atribuicao'], 'licenca': (m.get('fonte') or {}).get('licenca')}
    _gravar(saida / 'ativos.json', out)
    return out


# ---------------------------------------------------------------- preflight
def preflight(plano_bruto: dict, saida: Path, palco_real: bool = True) -> dict:
    """100% dos recursos antes do render, sem IA e sem rede. → {pronto, itens:[{item, ok, detalhe}]}"""
    from src.v4 import prerender, viabilidade
    itens = []
    add = lambda item, ok, det='': itens.append({'item': item, 'ok': bool(ok), 'detalhe': det})
    narr = saida / 'narracao.json'
    if not narr.exists() or not (saida / 'voz.wav').exists():
        add('narração', False, 'narração ausente (rode `narrar`): sem ela não há tempos nem som')
        return {'pronto': False, 'itens': itens}
    meta = _ler(narr)
    try:
        pl = P.resolver_tempos(plano_bruto, meta['palavras'])
        add('âncoras na fala', True, f"{len(meta['palavras'])} palavras")
    except ValueError as e:
        add('âncoras na fala', False, str(e))
        return {'pronto': False, 'itens': itens}
    if isinstance(plano_bruto.get('duracao'), str) or not plano_bruto.get('duracao'):
        pl['duracao'] = round(meta['duracao'], 3)
    add('duração da narração cobre o plano', meta['duracao'] >= pl['duracao'] - P.REGRAS['fim_tolerancia_s'], f"voz {meta['duracao']:.2f} s × plano {pl['duracao']:.2f} s")
    imgs = _ler(saida / 'ativos.json') if (saida / 'ativos.json').exists() else {}
    for v in P.validar(pl, imgs):
        add(f"plano: {v['regra']} {v['onde']}", v['gravidade'] != 'erro', v['texto'])
    if not any(not i['ok'] and i['item'].startswith('plano:') for i in itens):
        add('plano (slots, colisões, texto, progressão, repetição, modalidades)', True, f'{len(P.camadas(pl))} camadas')
    bib = {it['id']: it for it in viabilidade.carregar()['itens']}
    for a in assets_do_plano(pl):
        it = bib.get(a)
        ok = bool(it and it.get('licenca') and it.get('credito') and (it.get('prova') or {}).get('midia_corresponde') is True)
        add(f'mídia comprovada {a[:60]}', ok, (it or {}).get('licenca', 'fora da biblioteca'))
        f = PUBLICO.parent / imgs.get(a, {}).get('src', '_nada')
        reg = imgs.get(a) or {}
        add(f'arquivo de mídia {a[:50]}', f.exists() and reg.get('w'), str(f.name))
        # o arquivo que vai ao render É o baixado da origem DESTA mídia (impressão digital), não outro com o mesmo nome
        add(f'arquivo é a mídia certa {a[:44]}', f.exists() and reg.get('sha256') == _sha(f) and reg.get('url') == (it or {}).get('url')
            and f.name == nome_publico(a) + '.jpg', reg.get('sha256', 'sem impressão digital')[:16])
        add(f'origem conferida (sha256 da URL) {a[:40]}', reg.get('origem_conferida') is True or not (it or {}).get('sha256_origem'),
            f"{reg.get('sha256_origem', '?')[:16]} via {str(reg.get('veio_de', '?'))[:40]}" + ('' if (it or {}).get('sha256_origem') else ' (1º registro)'))
        lic = (it or {}).get('licenca', '#')
        cred = ' '.join(m for b in pl['beats'] for L in b['camadas'] if (L.get('p') or {}).get('asset') == a for m in (L['p'].get('meta') or []))
        add(f'crédito visível {a[:50]}', any(x.lower() in cred.lower() for x in (lic, 'domínio público', 'cc by')), cred[:90])
    for r in pl.get('rasters') or []:
        reg = imgs.get(f"raster:{r['nome']}") or {}
        f = PUBLICO.parent / reg.get('src', '_nada')
        js = P.RASTER_DIR / f"{r['nome']}.json"
        add(f"raster {r['nome']} com procedência e licença", js.exists() and bool(reg.get('licenca')) and bool(reg.get('atribuicao')), reg.get('licenca') or 'sem .json')
        add(f"raster {r['nome']} é o arquivo registrado", f.exists() and reg.get('sha256') == _sha(f) == reg.get('sha256_json'), (reg.get('sha256') or '')[:16])
    if pl.get('geo'):
        g = RAIZ / pl['geo']
        ok = g.exists()
        topo = _ler(g) if ok else {}
        add('geometria do mapa', ok, pl['geo'])
        atr = ' '.join((topo.get('meta') or {}).get('atribuicao') or [])
        add('atribuição dos dados no vídeo (Natural Earth; OSM/ODbL se houver rota)', 'Natural Earth' in atr and (not pl.get('rotas') or 'OpenStreetMap' in atr), atr)
        if pl.get('rotas'):
            add('rota com geometria real', ok and 'rota' in topo.get('topo', {}).get('objects', {}) and (topo.get('meta') or {}).get('rota_km'),
                f"{(topo.get('meta') or {}).get('rota_km')} km · {(topo.get('meta') or {}).get('rota_fonte')}")
    for c in pl.get('clipes') or []:
        geo = prerender.geometria_palco(c['componente'], {**c['params'], 'v4': True}, round(c['t1'] - c['t0'], 2), False, saida / 'pre_clipe') if palco_real else []
        add(f"clipe {c['componente']} {c['t0']:.1f}–{c['t1']:.1f}s sem colisão com a identidade", not geo, '; '.join(geo)[:200])
    root = (RAIZ / 'motor4' / 'remotion' / 'src' / 'Root.tsx').read_text()
    add('composição Remotion Formato registrada', 'id="Formato"' in root)
    fontes = RAIZ / 'motor4' / 'remotion' / 'public' / 'fontes'
    add('fontes da identidade', all((fontes / f).exists() for f in ('montserrat-latin-900-normal.woff2', 'jetbrains-mono-latin-700-normal.woff2')))
    out = {'pronto': all(i['ok'] for i in itens), 'itens': itens, 'duracao': pl['duracao']}
    _gravar(saida / 'preflight.json', out)
    _gravar(saida / 'plano_resolvido.json', pl)
    return out


# ---------------------------------------------------------------- render
def _trecho(src: Path, a: float, b: float, dest: Path):
    rodar(['ffmpeg', '-v', 'error', '-y', '-ss', f'{a:.3f}', '-i', src, '-t', f'{b - a:.3f}', '-an', '-c:v', 'libx264', '-preset', 'veryfast',
           '-crf', '16', '-pix_fmt', 'yuv420p', '-r', '30', dest])


def render(saida: Path) -> dict:
    from src.v4 import compositor, portoes, som
    from src.v4.backends import js, legado
    pf = _ler(saida / 'preflight.json')
    if not pf['pronto']:
        raise SystemExit('preflight vermelho: não renderizo (nada de diagnóstico virando episódio)')
    pl, meta, imgs = _ler(saida / 'plano_resolvido.json'), _ler(saida / 'narracao.json'), _ler(saida / 'ativos.json')
    trab = (saida / '_trabalho').resolve()
    trab.mkdir(parents=True, exist_ok=True)
    can = P.canal(pl.get('canal', 'coringa'))
    tokens = {k: can[k] for k in ('cores', 'fontes', 'tempo', 'palco')}
    geo = _ler(RAIZ / pl['geo']) if pl.get('geo') else None
    base = trab / 'formato.mp4'
    js.remotion('Formato', P.props(pl, tokens, geo, imgs), base, trab / 'formato')
    # clipes aprovados (palco V2) encaixados nos furos — corte limpo
    partes, t = [], 0.0
    for k, c in enumerate(sorted(pl.get('clipes') or [], key=lambda c: c['t0'])):
        if c['t0'] > t:
            partes.append(trab / f'p{len(partes)}.mp4'); _trecho(base, t, c['t0'], partes[-1])
        clip = trab / f'clipe{k}.mp4'
        q = {**c['params'], 'v4': True}
        legado.render_v2(c['componente'], q, round(c['t1'] - c['t0'], 3), trab / f'clipe{k}', clip)
        partes.append(clip)
        t = c['t1']
    if t < pl['duracao']:
        partes.append(trab / f'p{len(partes)}.mp4'); _trecho(base, t, pl['duracao'], partes[-1])
    video = compositor.concatenar([{'arq': p} for p in partes], trab, trab / 'video.mp4') if len(partes) > 1 else base
    # camada global: marca + legendas por palavra (selo só no clipe de esquema, que não tem rótulo próprio no modo V4)
    cenas = []
    marcas = sorted({0.0, pl['duracao']} | {x for c in pl.get('clipes') or [] for x in (c['t0'], c['t1'])})
    for a, b in zip(marcas, marcas[1:]):
        dentro = any(abs(c['t0'] - a) < .01 for c in pl.get('clipes') or [])
        cenas.append({'ini': a, 'fim': b, 'selo': 'ESQUEMA' if dentro else None, 'credito': None, 'legenda': True})
    camada = trab / 'camada.webm'
    js.remotion('Camada', {'duracao': pl['duracao'], 'palavras': meta['palavras'], 'cenas': cenas}, camada, trab / 'camada', alfa=True)
    musicas = sorted((RAIZ / 'assets' / 'musica' / 'explica').glob('*.mp3'))
    musica = musicas[sum(map(ord, pl['video_id'])) % len(musicas)] if musicas else None
    master = trab / 'master.wav'
    reg_som = som.mixar(saida / 'voz.wav', pl['duracao'], [], musica, trab / 'som', master)
    mp4 = saida / f"{pl['video_id']}.mp4"
    info = compositor.final(video, camada, master, mp4, trab)
    # portões no MP4 FINAL: nada preto, nada congelado por janela de 4 s (zona de conteúdo, sem a faixa de legenda)
    janelas = []
    a = 0.0
    while a < pl['duracao'] - .5:
        b = min(pl['duracao'], a + 4.0)
        seg = trab / f'jan_{int(a)}.mp4'
        _trecho(mp4, a, b, seg)
        q = portoes.avaliar_quadros(portoes.amostras(seg, n=5), exige_movimento=True)
        janelas.append({'de': round(a, 1), 'ate': round(b, 1), 'problemas': q})
        a = b
    from src.fiscal import medir_audio
    from src.v4.formatos import ritmo
    au = medir_audio(mp4)
    rit = ritmo.medir(mp4)          # COMPROVA a correção do congelamento (ERR-067) com a métrica das referências
    res = {'video_id': pl['video_id'], 'formato': pl['formato'], 'mp4': str(mp4), 'duracao': pl['duracao'], 'info': info, 'som': reg_som,
           'audio': au, 'janelas': janelas, 'nao_publicado': True, 'ritmo': {k: v for k, v in rit.items()},
           'portoes': {'preto_ou_congelado': [j for j in janelas if j['problemas']],
                       'audio_ok': au.get('lufs') is not None and abs(au['lufs'] + 14) <= 1.0 and (au.get('pico') or 0) <= -1.0}}
    res['portoes']['ritmo_ok'] = rit['maior_trecho_parado_s'] <= 3
    res['estado'] = 'AGUARDANDO_APROVACAO_HUMANA' if not res['portoes']['preto_ou_congelado'] and res['portoes']['audio_ok'] and res['portoes']['ritmo_ok'] else 'BLOQUEADO'
    _gravar(saida / 'resultado.json', res)
    return res


# ---------------------------------------------------------------- folhas e comparação (prévia privada)
def _quadro(mp4: Path, t: float, w: int = 540) -> 'Image.Image':
    import io

    from PIL import Image
    r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.2f}', '-i', str(mp4), '-frames:v', '1', '-vf', f'scale={w}:{w * 16 // 9}', '-f', 'image2', '-c:v', 'mjpeg', '-q:v', '3', '-'],
                       capture_output=True, check=True)
    return Image.open(io.BytesIO(r.stdout)).convert('RGB')


def folhas(saida: Path, antes: str | None = None) -> dict:
    """folha de contato do MP4 final (12 quadros) e, se houver o pacote cifrado do 'antes', a comparação lado a lado
    nos MESMOS instantes dos styleframes (antes = execução 44084129999, depois = este MP4)"""
    import base64
    import io

    from PIL import Image, ImageDraw, ImageFont
    r = _ler(saida / 'resultado.json')
    mp4, dur = Path(r['mp4']), r['duracao']
    fnt = ImageFont.truetype(str(RAIZ / 'motor4' / 'identidade' / 'ttf' / 'jetbrains-mono-latin-700-normal.ttf'), 24)
    ts = [round(dur * (i + .5) / 12, 2) for i in range(12)]
    o = Image.new('RGB', (270 * 6, (480 + 30) * 2), '#111')
    d = ImageDraw.Draw(o)
    for i, t in enumerate(ts):
        x, y = (i % 6) * 270, (i // 6) * 510
        o.paste(_quadro(mp4, t, 270), (x, y + 30))
        d.text((x + 6, y + 2), f'{t:.1f}s', fill='#FFD21F', font=fnt)
    out = {'folha': str(saida / 'folha_final.jpg')}
    o.save(out['folha'], quality=85)
    if antes and (RAIZ / antes).exists():
        from src.v3 import material
        pac = json.loads(material.decifrar(material._segredo(), (RAIZ / antes).read_bytes()))['formatos'].get(r['formato'], {})
        if pac:
            ks = sorted(pac, key=float)
            W, Hh = 360, 640
            o = Image.new('RGB', ((W * 2 + 24) * min(3, len(ks)), (Hh + 44) * ((len(ks) + 2) // 3)), '#0B0B0B')
            d = ImageDraw.Draw(o)
            for i, k in enumerate(ks):
                x, y = (i % 3) * (W * 2 + 24), (i // 3) * (Hh + 44)
                o.paste(Image.open(io.BytesIO(base64.b64decode(pac[k]))).convert('RGB').resize((W, Hh)), (x, y + 40))
                o.paste(_quadro(mp4, float(k), W).resize((W, Hh)), (x + W, y + 40))
                d.text((x + 6, y + 8), f'{float(k):.1f}s  ANTES', fill='#9AA4B2', font=fnt)
                d.text((x + W + 6, y + 8), 'DEPOIS', fill='#FFD21F', font=fnt)
            out['comparativo'] = str(saida / 'comparativo_antes_depois.jpg')
            o.save(out['comparativo'], quality=84)
    _gravar(saida / 'folhas.json', out)
    return out


def evolucao(saida: Path, pl: dict) -> Path:
    """relatório curto de evolução: o que mudou (doc fixo do formato) + números medidos agora × antes × referências"""
    r = _ler(saida / 'resultado.json')
    q = _ler(saida / 'quadros' / 'relatorio.json') if (saida / 'quadros' / 'relatorio.json').exists() else {}
    ims = _ler(saida / 'ativos.json')
    base = (RAIZ / 'docs' / 'v4' / 'formatos' / f"EVOLUCAO_{pl['formato'].upper()}.md")
    a = pl.get('antes_ritmo') or {}
    rit = r.get('ritmo') or {}
    linhas = [base.read_text(encoding='utf-8').strip() if base.exists() else '', '',
              'MEDIDO NESTA PRÉVIA:',
              f"- maior trecho parado: {rit.get('maior_trecho_parado_s')} s (antes {a.get('maior_trecho_parado_s', '?')} s; ref. A 2 s, ref. B 1 s)",
              f"- segundos parados: {rit.get('segundos_parados')}/{rit.get('segundos')} (antes {a.get('segundos_parados', '?')}/{a.get('segundos', '?')})",
              f"- quadros renderizados conferidos: {len(q.get('quadros', []))}, problemas: {len(q.get('problemas', []))}",
              f"- mídias: {sum(1 for k in ims if not k.startswith('raster:'))} com sha256 da origem "
              f"({sum(1 for k, v in ims.items() if not k.startswith('raster:') and v.get('origem_conferida'))} conferidas contra a biblioteca); "
              f"rasters: {sum(1 for k in ims if k.startswith('raster:'))} com .json de procedência",
              'Teste técnico verde não é aprovação: a avaliação estética é do Heitor.']
    out = saida / 'evolucao.md'
    out.write_text('\n'.join(linhas) + '\n', encoding='utf-8')
    return out


# ---------------------------------------------------------------- prévia privada
def telegram(saida: Path, titulo: str) -> dict:
    """MP4 + estado + preflight + portões + áudio, só ao chat privado autorizado. NÃO é publicação."""
    from src.v3 import estado_final, previa_telegram
    r = _ler(saida / 'resultado.json') if (saida / 'resultado.json').exists() else None
    pf = _ler(saida / 'preflight.json') if (saida / 'preflight.json').exists() else {'pronto': False, 'itens': []}
    linhas = [f'FORMATO — PRÉVIA PRIVADA, NÃO PUBLICADO · {titulo}']
    if not r:
        linhas += ['STATUS: BLOQUEADO (não renderizado)', 'preflight:'] + [f"- NÃO {i['item']}: {i['detalhe']}" for i in pf['itens'] if not i['ok']][:15]
        chat, _ = previa_telegram.chat_autorizado()
        previa_telegram._api('sendMessage', {'chat_id': chat, 'text': '\n'.join(linhas)[:3900]})
        return {'enviado': True, 'sem_mp4': True}
    au = r.get('audio') or {}
    linhas += [f"STATUS: {r['estado']} (aprovação estética só do Heitor)", f"duração {r['duracao']:.1f} s · formato {r['formato']}",
               f"preflight: {sum(i['ok'] for i in pf['itens'])}/{len(pf['itens'])} itens OK",
               f"áudio no MP4: {au.get('lufs')} LUFS · pico {au.get('pico')} dBTP",
               f"janelas de 4 s pretas/congeladas: {len(r['portoes']['preto_ou_congelado'])}"]
    linhas += [f"- {j['de']}–{j['ate']}s: {'; '.join(j['problemas'])}" for j in r['portoes']['preto_ou_congelado']][:8]
    est = {'estado': estado_final.AGUARDANDO if r['estado'] == estado_final.AGUARDANDO else estado_final.BLOQUEADO,
           'motivos': [] if r['estado'] == estado_final.AGUARDANDO else ['portões do MP4 final']}
    rit = r.get('ritmo') or {}
    linhas += [f"ritmo medido (zona de conteúdo, 4 q/s): maior trecho parado {rit.get('maior_trecho_parado_s')} s · "
               f"{rit.get('segundos_parados')}/{rit.get('segundos')} s parados (ref. A: 2 s; ref. B: 1 s)"]
    ev = saida / 'evolucao.md'
    if ev.exists():
        linhas += ['', ev.read_text(encoding='utf-8')]
    env = previa_telegram.enviar(Path(r['mp4']), est, titulo, '\n'.join(linhas))
    chat, _ = previa_telegram.chat_autorizado()
    fol = _ler(saida / 'folhas.json') if (saida / 'folhas.json').exists() else {}
    extras = [(saida / 'quadros' / 'styleframes.jpg', 'styleframes (quadros renderizados, com legenda)'),
              (saida / 'quadros' / 'celular.jpg', 'leitura em tela de celular (405×720)'),
              (Path(fol['folha']) if fol.get('folha') else None, 'folha de contato do MP4 final'),
              (Path(fol['comparativo']) if fol.get('comparativo') else None, 'ANTES (44084129999) × DEPOIS, mesmos instantes')]
    enviados = 0
    for arq, leg in extras:
        if arq and arq.exists():
            previa_telegram._api('sendDocument', {'chat_id': chat, 'caption': f'{titulo} — {leg} (prévia privada, não publicado)'[:1000]}, ('document', arq))
            enviados += 1
    env['anexos'] = enviados
    _gravar(saida / 'telegram.json', {'enviado': True, **env})
    return env
