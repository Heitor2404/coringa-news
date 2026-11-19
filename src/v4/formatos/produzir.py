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

from src.v4.formatos import layout, plano as P
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
        meta = {'palavras': pac['palavras'], 'duracao': pac['duracao'], 'origem': pac.get('origem'),
                'narrador': {'modo': 'arquivo_cifrado_preservado', 'origem_declarada': pac.get('origem'),
                             'aprovacao_timbre': 'pendente_humano'}}
    else:
        from src import voz
        if plano.get('formato') == 'atlas':
            preset = P.canal(plano.get('canal', 'coringa')).get('narrador') or {}
            if preset.get('motor') != 'gemini' or not preset.get('voz') or preset.get('fallback') != 'bloquear':
                raise RuntimeError('ATLAS: preset de narrador ausente/inválido; recuso fallback silencioso')
            config_voz = {'voz_motor': 'gemini', 'voz_gemini': preset['voz'],
                          'velocidade_gemini': preset.get('velocidade', 1),
                          'estilo_gemini': preset.get('estilo', voz.ESTILO_PADRAO),
                          '_estilo_separado': True}
            wav, _tempos, caps, dur = voz.narrar([{'fala': n['texto']}], saida / 'tts',
                                                 cfg=config_voz, exigir_gemini=True)
            narrador = {'modo': 'tts_travado', 'motor': 'gemini', 'voz': preset['voz'],
                        'velocidade': config_voz['velocidade_gemini'], 'fallback': 'proibido',
                        'aprovacao_timbre': 'pendente_humano'}
        else:
            wav, _tempos, caps, dur = voz.narrar([{'fala': n['texto']}], saida / 'tts')
            narrador = {'modo': 'tts_legado', 'motor': 'nao_verificado'}
        shutil.copy(wav, saida / 'voz.wav')
        pal = []
        for bl in caps:
            ws = bl['words']
            for k, w in enumerate(ws):
                fim = ws[k + 1]['s'] if k + 1 < len(ws) else bl['end']
                pal.append({'w': w['w'], 's': w['s'], 'e': round(fim, 3), 'hl': bool(w.get('hl'))})
        meta = {'palavras': pal, 'duracao': round(dur, 3), 'origem': 'TTS desta execução', 'narrador': narrador}
    meta['sha256_voz'] = _sha(saida / 'voz.wav')
    # marcas de tempo corrigidas pela VOZ (pausas reais como âncoras; sem IA) — legenda e âncoras do plano no tempo certo
    from src.v4.formatos import legenda_sync
    meta['palavras_originais'] = meta['palavras']
    meta['palavras'] = legenda_sync.realinhar(meta['palavras'], saida / 'voz.wav')
    meta['refino'] = 'legenda_sync.realinhar (pausas do áudio como âncoras)'
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
    out |= {(c.get('params') or {})['asset'] for c in plano.get('clipes') or []
            if c.get('componente') == 'registro.video' and (c.get('params') or {}).get('asset')}
    return sorted(out)


def _origem(it: dict, cache: Path | None) -> tuple[bytes, str]:
    """bytes DA ORIGEM da mídia (URL da biblioteca) — ou do cache local indexado por sha256 — e de onde vieram"""
    sha = it.get('sha256_origem')
    if cache and sha:
        for f in cache.glob(f'{sha}.*'):
            return f.read_bytes(), f'cache:{f.name}'
    if cache and (not sha or os.environ.get('CORINGA_DEV')) and (cache / f"{nome_publico(it['id'])}.jpg").exists():   # só desenvolvimento local (sem rede)
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
        # cópia local de desenvolvimento (CORINGA_DEV, sem rede) não é a origem: não confere, e fica marcada como não conferida
        if it.get('sha256_origem') and sha_o != it['sha256_origem'] and veio != 'cache-local-sem-origem':
            raise RuntimeError(f'{a}: o arquivo da origem mudou (sha256 {sha_o[:12]} ≠ {it["sha256_origem"][:12]}) — não entra no vídeo')
        nome = nome_publico(a)              # nome PRÓPRIO por mídia; não sobrescrever vídeos/fotos diferentes.
        if it.get('natureza') == 'video':
            # A origem é validada via sha256; dados reais são sondados pelo ffprobe do V4 (não por extensão inferida da página).
            if it.get('uso_comercial') != 'sim' or not it.get('sha256_origem'):
                raise RuntimeError(f'{a}: vídeo precisa de licença comercial explícita e SHA256 da origem')
            from urllib.parse import urlsplit
            from src.v4.util import sondar
            ext = Path(urlsplit(it['url']).path).suffix.lower()
            if ext not in ('.mp4', '.webm', '.mov'):
                raise RuntimeError(f'{a}: formato de vídeo não autorizado ({ext or "sem extensão"})')
            dest = PUBLICO / f'{nome}{ext}'
            dest.write_bytes(bruto)
            info = sondar(dest)
            if not info['w'] or not info['h'] or info['duracao'] <= 0:
                dest.unlink(missing_ok=True)
                raise RuntimeError(f'{a}: vídeo original inválido ou sem duração')
            shutil.copy(dest, saida / 'ativos' / dest.name)
            out[a] = {'src': f'_formato/{dest.name}', 'tipo': 'video', 'w': info['w'], 'h': info['h'],
                      'duracao': round(info['duracao'], 3), 'credito': it['credito'], 'licenca': it['licenca'],
                      'url': it['url'], 'sha256': _sha(dest), 'sha256_origem': sha_o,
                      'origem_conferida': sha_o == it['sha256_origem'], 'veio_de': veio}
        else:
            im = Image.open(io.BytesIO(bruto)).convert('RGB')
            if max(im.size) > 2000:
                im.thumbnail((2000, 2000))
            dest = PUBLICO / f'{nome}.jpg'
            im.save(dest, 'JPEG', quality=92)
            shutil.copy(dest, saida / 'ativos' / dest.name)
            out[a] = {'src': f'_formato/{nome}.jpg', 'tipo': 'foto', 'w': im.size[0], 'h': im.size[1],
                      'credito': it['credito'], 'licenca': it['licenca'],
                      'url': it['url'], 'sha256': _sha(dest), 'sha256_origem': sha_o,
                      'origem_conferida': bool(it.get('sha256_origem')) and sha_o == it['sha256_origem'], 'veio_de': veio}
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
        if (it or {}).get('natureza') == 'video':
            ok = bool(ok and it.get('uso_comercial') == 'sim' and it.get('sha256_origem'))
        add(f'mídia comprovada {a[:60]}', ok, (it or {}).get('licenca', 'fora da biblioteca'))
        f = PUBLICO.parent / imgs.get(a, {}).get('src', '_nada')
        reg = imgs.get(a) or {}
        add(f'arquivo de mídia {a[:50]}', f.exists() and reg.get('w'), str(f.name))
        # o arquivo que vai ao render É o baixado da origem DESTA mídia (impressão digital), não outro com o mesmo nome
        ext = Path(reg.get('src') or '').suffix.lower()
        certo = (f.name == nome_publico(a) + ext and
                 (ext in ('.mp4', '.webm', '.mov') if reg.get('tipo') == 'video' else ext == '.jpg'))
        add(f'arquivo é a mídia certa {a[:44]}', f.exists() and reg.get('sha256') == _sha(f) and reg.get('url') == (it or {}).get('url')
            and certo, reg.get('sha256', 'sem impressão digital')[:16])
        add(f'origem conferida (sha256 da URL) {a[:40]}', reg.get('origem_conferida') is True or not (it or {}).get('sha256_origem')
            or (bool(os.environ.get('CORINGA_DEV')) and reg.get('veio_de') == 'cache-local-sem-origem'),
            f"{reg.get('sha256_origem', '?')[:16]} via {str(reg.get('veio_de', '?'))[:40]}" + ('' if (it or {}).get('sha256_origem') else ' (1º registro)'))
        lic = (it or {}).get('licenca', '#')
        if reg.get('tipo') == 'video':
            # Crédito vem da biblioteca comprovada e é inserido na Camada global, em faixa segura.
            cred = reg.get('credito') or ''
            clip_refs = [c for c in pl.get('clipes') or [] if (c.get('params') or {}).get('asset') == a]
            add(f'clipe video registrado {a[:40]}', bool(clip_refs), f'{len(clip_refs)} usos')
            for c in clip_refs:
                inicio = (c.get('params') or {}).get('inicio', 0)
                dur = c['t1'] - c['t0']
                add(f'video duracao/resolucao {a[:35]}', isinstance(inicio, (float, int)) and
                    inicio >= 0 and inicio + dur <= reg.get('duracao', 0) + .01 and
                    reg.get('w', 0) >= 640 and reg.get('h', 0) >= 360,
                    f"fonte {reg.get('w')}x{reg.get('h')} · {reg.get('duracao')}s · {inicio}+{dur:.2f}s")
        else:
            cred = ' '.join(m for b in pl['beats'] for L in b['camadas'] if (L.get('p') or {}).get('asset') == a
                            for m in ([L['p']['meta']] if isinstance(L['p'].get('meta'), str) else (L['p'].get('meta') or [])))
        add(f'crédito visível {a[:50]}', bool(cred) and any(x.lower() in cred.lower() for x in (lic, 'domínio público', 'cc by')), cred[:90])
    if pl.get('formato') == 'atlas':
        # manifesto de atribuição cartográfica: toda camada exibível declarada, com uso comercial; nada de fonte proibida;
        # e atribuição de mapa ≠ fonte factual (não se misturam)
        from src.v4.formatos import atlas_ref
        ds = atlas_ref.datasets()
        txt_plano = json.dumps({k: pl.get(k) for k in ('rasters', 'geo')}, ensure_ascii=False)
        for r in pl.get('rasters') or []:
            mr = P.raster_info(r['nome'])
            d = ds.get(mr.get('dataset') or '')
            add(f"raster {r['nome']} no manifesto com uso comercial", bool(d and d.get('uso_comercial')), f"{mr.get('dataset')} · {(d or {}).get('licenca')}")
            txt_plano += json.dumps(mr, ensure_ascii=False)
        add('nenhuma camada de fonte sem licença comercial (Esri, Google, Mapbox, Sentinel-2 2018+…)', atlas_ref.proibido(txt_plano) is None, atlas_ref.proibido(txt_plano) or 'ok')
        if pl.get('geo'):
            meta_geo = (json.loads((RAIZ / pl['geo']).read_text()).get('meta') or {}).get('atribuicao') or []
            cobre = all(any(k in a for k in ('Natural Earth', 'OpenStreetMap')) for a in meta_geo)
            add('geometria com datasets do manifesto (Natural Earth, OSM)', cobre and 'ne_vetor' in ds and 'osm_rota' in ds, ' · '.join(meta_geo))
        fontes_fatos = {u_ for f_ in (pl.get('narracao') or {}).get('fatos', []) for u_ in (f_.get('fontes') or [])}
        mapa_urls = {d['url_origem'] for d in ds.values()} | {d['termos'] for d in ds.values()}
        cred = ' '.join(d.get('atribuicao_exigida') or '' for d in ds.values())
        add('fonte factual ≠ atribuição cartográfica', not (fontes_fatos & mapa_urls) and not any(u_ in cred for u_ in fontes_fatos), f'{len(fontes_fatos)} fontes factuais separadas')
    if narr.exists() and (saida / 'voz.wav').exists():
        from src.v4.formatos import legenda_sync
        ls = legenda_sync.conferir(narr, saida / 'voz.wav', P.estilo_legenda(plano_bruto).get('max_palavras', 4))
        _gravar(saida / 'legenda_sync.json', ls)
        add('legenda sincronizada com o áudio real', ls['ok'],
            f"atraso {ls['atraso_s']} s · {ls['n_palavras_sem_fala']} palavras fora da fala · {len(ls['fala_sem_legenda'])} falas sem legenda · {len(ls['trocas_bruscas'])} trocas bruscas")
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
        trajeto = [r for r in pl.get('rotas') or [] if not r.get('arco')]     # arco entre dois pontos = desenho do canal, sem dado OSM
        add('atribuição dos dados no vídeo (Natural Earth; OSM/ODbL se houver trajeto medido)', 'Natural Earth' in atr and (not trajeto or 'OpenStreetMap' in atr), atr)
        for r in pl.get('rotas') or []:
            if r.get('arco'):
                a_, b_ = r['arco']
                add(f'conexão {a_}→{b_} com pontas válidas', all(-180 <= p[0] <= 180 and -85 <= p[1] <= 85 for p in (a_, b_)) and a_ != b_)
        if trajeto:
            add('rota com geometria real', ok and 'rota' in topo.get('topo', {}).get('objects', {}) and (topo.get('meta') or {}).get('rota_km'),
                f"{(topo.get('meta') or {}).get('rota_km')} km · {(topo.get('meta') or {}).get('rota_fonte')}")
    for c in pl.get('clipes') or []:
        dur_c = float((c.get('fonte') or {}).get('dur') or round(c['t1'] - c['t0'], 2))
        geo = (prerender.geometria_palco(c['componente'], params_clipe(c, P.canal(pl.get('canal', 'coringa'))), dur_c, False, saida / 'pre_clipe')
               if palco_real and c.get('componente') != 'registro.video' else [])
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


def params_clipe(c: dict, can: dict) -> dict:
    """params do clipe aprovado + TEMPLATE TÉCNICO do canal (palco.tecnico): a mesma linguagem técnica em todo mecanismo"""
    p = can.get('palco') or {}
    # ATLAS tem painel tecnico proprio, sem alterar a mesa/diagramas do DOSSIÊ.
    preset = p.get('tecnico_atlas') if can.get('canal') == 'coringa' else None
    tema = {k: v for k, v in (preset or p.get('tecnico') or {}).items() if not k.startswith('_')}
    return {**c['params'], 'v4': True, **({'tema': tema} if tema else {}),
            'direcao_visual': {k: v for k, v in (can.get('direcao_visual') or {}).items() if not k.startswith('_')}}


def _clipe(c: dict, can: dict, trab: Path, saida_mp4: Path, imgs: dict | None = None) -> None:
    """renderiza o clipe; com c['fonte'] = {dur, ini} renderiza a animação inteira e usa só o trecho [ini, ini + furo]
    (ex.: gancho de 2,4 s mostrando a água subindo e o navio subindo junto, sem acelerar a física)"""
    from src.v4.backends import legado
    furo = round(c['t1'] - c['t0'], 3)
    if c['componente'] == 'registro.video':
        from src.v4.util import FalhaBackend
        from src.v4.backends import legado
        a = (c.get('params') or {}).get('asset')
        reg = (imgs or {}).get(a) or {}
        src = PUBLICO.parent / reg.get('src', '_ausente')
        if not a or reg.get('tipo') != 'video' or not src.is_file():
            raise FalhaBackend('registro.video sem arquivo comprovado: preflight precisa bloquear')
        # Reusa o backend de vídeo REAL do V4 integral: corte estático, 9:16, sem esticar e sem áudio original.
        registro = legado.render_video(src, [reg['w'], reg['h']], None,
                                       float(c.get('params', {}).get('inicio', 0)), furo,
                                       saida_mp4, trab)
        print('ATLAS_VIDEO_REGISTRO ' + json.dumps({'asset': a, **registro}, ensure_ascii=False), flush=True)
        return
    f = c.get('fonte')
    if not f:
        legado.render_v2(c['componente'], params_clipe(c, can), furo, trab, saida_mp4)
        return
    inteiro = trab / 'inteiro.mp4'
    trab.mkdir(parents=True, exist_ok=True)
    legado.render_v2(c['componente'], params_clipe(c, can), float(f['dur']), trab / 'v2', inteiro)
    _trecho(inteiro, float(f['ini']), float(f['ini']) + furo, saida_mp4)


def sfx_do_plano(pl: dict) -> list[dict]:
    """efeitos do PADRÃO SONORO do canal, ancorados nos acontecimentos visuais do plano (o episódio não escolhe efeito):
    troca grande de escala → sopro; cartão de dado entra → tique; rota começa → traço; clipe de mecanismo → água.
    Espaçamento mínimo e ganho baixo: o efeito acompanha a imagem, não compete com a voz."""
    E = (P.canal(pl.get('canal', 'coringa')).get('som') or {}).get('efeitos') or {}
    if not E:
        return []
    ev = []
    ks = [k for k in pl.get('palco') or [] if k.get('camera')]
    for a, b in zip(ks, ks[1:]):
        if abs(P._cam(a['camera'])['zoom'] - P._cam(b['camera'])['zoom']) >= E['troca_de_escala'].get('min_dzoom', 1.0):
            ev.append((b['t'], 'troca_de_escala', 'câmera muda de escala'))
    for L in P.camadas(pl):
        q = L.get('p') or {}
        if L['componente'] == 'editorial.statCard' and q.get('estilo') != 'pilula':
            ev.append((L['t0'], 'cartao', f"cartão {L['id']} entra"))
    for r in pl.get('rotas') or []:
        ev.append((r['t0'], 'rota', 'rota começa a ser desenhada'))
    for c in pl.get('clipes') or []:
        if str(c.get('componente', '')).startswith('mecanismo.'):
            ev.append((c['t0'] + .2, 'mecanismo', f"{c['componente']} em ação"))
    out, ult = [], -9.0
    for t, tipo, just in sorted(ev):
        if t - ult < E.get('espaco_min_s', .9) or tipo not in E:
            continue
        out.append({'id': E[tipo]['sfx'], 't': round(max(0, t - .05), 2), 'ganho_db': E[tipo]['ganho_db'], 'justificativa': just})
        ult = t
    return out


def motivos_bloqueio(portoes: dict, ritmo: dict, legenda_sync: dict | None = None, audio: dict | None = None) -> list[str]:
    """Expõe os portões exatos que impedem a publicação; sem resumo genérico."""
    motivos = []
    for j in portoes.get('preto_ou_congelado') or []:
        motivos.append(f"G-MP4-JANELA {j['de']}–{j['ate']}s: " + '; '.join(j.get('problemas') or []))
    if not portoes.get('audio_ok'):
        a = audio or {}
        motivos.append(f"G-AUDIO: LUFS={a.get('lufs')} pico={a.get('pico')} — fora do preset do canal")
    if not portoes.get('ritmo_ok'):
        sem = (ritmo or {}).get('sem_camera') or {}
        motivos.append(f"G-RITMO: {sem.get('maior_trecho_parado_s')} s sem informação visual, limite 3 s (câmera desconsiderada)")
    if not portoes.get('legenda_ok'):
        l = legenda_sync or {}
        motivos.append(f"G-LEGENDA: atraso={l.get('atraso_s')} s; palavras sem fala={l.get('n_palavras_sem_fala')}; trocas bruscas={l.get('trocas_bruscas')}")
    return motivos


def render(saida: Path) -> dict:
    import time
    from src.v4 import compositor, portoes, som
    from src.v4.backends import js, legado
    pf = _ler(saida / 'preflight.json')
    if not pf['pronto']:
        raise SystemExit('preflight vermelho: não renderizo (nada de diagnóstico virando episódio)')
    rq = saida / 'quadros' / 'relatorio.json'
    if not rq.exists() or not _ler(rq).get('ok'):
        raise SystemExit('quadros renderizados com problema (ou não conferidos): não renderizo o vídeo')
    pl, meta, imgs = _ler(saida / 'plano_resolvido.json'), _ler(saida / 'narracao.json'), _ler(saida / 'ativos.json')
    trab = (saida / '_trabalho').resolve()
    trab.mkdir(parents=True, exist_ok=True)
    can = P.canal(pl.get('canal', 'coringa'))
    tokens = P.tokens_canal(can)
    geo = _ler(RAIZ / pl['geo']) if pl.get('geo') else None
    base = trab / 'formato.mp4'
    t_render = time.monotonic()
    js.remotion('Formato', P.props(pl, tokens, geo, imgs), base, trab / 'formato')
    print(f"ATLAS_PERF formato_base_s={time.monotonic() - t_render:.2f}", flush=True)
    # clipes aprovados (palco V2) encaixados nos furos — corte limpo
    partes, t = [], 0.0
    for k, c in enumerate(sorted(pl.get('clipes') or [], key=lambda c: c['t0'])):
        if c['t0'] > t:
            partes.append(trab / f'p{len(partes)}.mp4'); _trecho(base, t, c['t0'], partes[-1])
        clip = trab / f'clipe{k}.mp4'
        _clipe(c, can, trab / f'clipe{k}', clip, imgs)
        partes.append(clip)
        t = c['t1']
    if t < pl['duracao']:
        partes.append(trab / f'p{len(partes)}.mp4'); _trecho(base, t, pl['duracao'], partes[-1])
    video = compositor.concatenar([{'arq': p} for p in partes], trab, trab / 'video.mp4') if len(partes) > 1 else base
    # camada global: marca + legendas (estilo da legenda = canal por formato; P.props_camada é a fonte única)
    camada = trab / 'camada.webm'
    pcam = P.props_camada(pl, meta, imgs)
    t_camada = time.monotonic()
    js.remotion('Camada', pcam, camada, trab / 'camada', alfa=True)
    print(f"ATLAS_PERF legendas_marca_alpha_s={time.monotonic() - t_camada:.2f}", flush=True)
    musicas = sorted((RAIZ / 'assets' / 'musica' / 'explica').glob('*.mp3'))
    musica = musicas[sum(map(ord, pl['video_id'])) % len(musicas)] if musicas else None
    master = trab / 'master.wav'
    reg_som = som.mixar(saida / 'voz.wav', pl['duracao'], sfx_do_plano(pl), musica, trab / 'som', master, preset=can.get('som'))
    mp4 = saida / f"{pl['video_id']}.mp4"
    t_final = time.monotonic()
    info = compositor.final(video, camada, master, mp4, trab)
    print(f"ATLAS_PERF mix_montagem_final_s={time.monotonic() - t_final:.2f}", flush=True)
    # portões no MP4 FINAL: nada preto, nada congelado por janela de 4 s (zona de conteúdo, sem a faixa de legenda)
    t_portoes = time.monotonic()
    janelas = []
    a = 0.0
    while a < pl['duracao'] - .5:
        b = min(pl['duracao'], a + 4.0)
        seg = trab / f'jan_{int(a)}.mp4'
        _trecho(mp4, a, b, seg)
        q = portoes.avaliar_quadros(portoes.amostras(seg, n=5), exige_movimento=True)
        janelas.append({'de': round(a, 1), 'ate': round(b, 1), 'problemas': q})
        a = b
    print(f"ATLAS_PERF checagem_20_janelas_mp4_s={time.monotonic() - t_portoes:.2f}", flush=True)
    from src.fiscal import medir_audio
    from src.v4.formatos import ritmo
    au = medir_audio(mp4)
    # duas métricas: bruta (comparável às referências) e SEM CÂMERA (zoom/pan não é progresso — decide o portão)
    rit = ritmo.medir_completo(mp4, usar_local=(pl['formato'] == 'atlas'))
    from src.v4.formatos import legenda_sync
    ls = legenda_sync.conferir(saida / 'narracao.json', saida / 'voz.wav', P.estilo_legenda(pl).get('max_palavras', 4))
    res = {'video_id': pl['video_id'], 'formato': pl['formato'], 'mp4': str(mp4), 'duracao': pl['duracao'], 'info': info, 'som': reg_som,
           'audio': au, 'janelas': janelas, 'nao_publicado': True, 'ritmo': {k: v for k, v in rit.items()},
           'portoes': {'preto_ou_congelado': [j for j in janelas if j['problemas']],
                       'audio_ok': au.get('lufs') is not None and abs(au['lufs'] - (can.get('som') or {}).get('lufs', -14)) <= (can.get('som') or {}).get('tolerancia_lufs', .5) and (au.get('pico') or 0) <= (can.get('som') or {}).get('true_peak', -1.0)}}
    res['portoes']['ritmo_ok'] = rit['sem_camera']['maior_trecho_parado_s'] <= 3
    res['portoes']['legenda_ok'] = ls['ok']
    res['legenda_sync'] = {k: ls[k] for k in ('atraso_s', 'n_palavras_sem_fala', 'fala_sem_legenda', 'trocas_bruscas', 'grupos') if k in ls}
    res['motivos_bloqueio'] = motivos_bloqueio(res['portoes'], rit, ls, au)
    res['estado'] = 'BLOQUEADO' if res['motivos_bloqueio'] else 'AGUARDANDO_APROVACAO_HUMANA'
    print('ATLAS_FISCAL ' + json.dumps({'estado': res['estado'], 'motivos_bloqueio': res['motivos_bloqueio']}, ensure_ascii=False), flush=True)
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
              f"- maior trecho parado (pixel bruto): {rit.get('maior_trecho_parado_s')} s (antes {a.get('maior_trecho_parado_s', '?')} s; ref. A 2 s, ref. B 1 s)",
              f"- maior trecho sem informação nova DESCONTANDO a câmera (portão ≤ 3 s): {(rit.get('sem_camera') or {}).get('maior_trecho_parado_s')} s "
              f"({(rit.get('sem_camera') or {}).get('segundos_parados')} s parados; antes {(a.get('sem_camera') or {}).get('maior_trecho_parado_s', '?')} s / {(a.get('sem_camera') or {}).get('segundos_parados', '?')} s)",
              f"- legenda × áudio real: {r.get('legenda_sync')}",
              f"- segundos parados: {rit.get('segundos_parados')}/{rit.get('segundos')} (antes {a.get('segundos_parados', '?')}/{a.get('segundos', '?')})",
              f"- quadros renderizados conferidos: {len(q.get('quadros', []))}, erros bloqueadores: {len(q.get('problemas', [])) - len(q.get('avisos', []))}, avisos: {len(q.get('avisos', []))}",
              f"- mídias: {sum(1 for k in ims if not k.startswith('raster:'))} com sha256 da origem "
              f"({sum(1 for k, v in ims.items() if not k.startswith('raster:') and v.get('origem_conferida'))} conferidas contra a biblioteca); "
              f"rasters: {sum(1 for k in ims if k.startswith('raster:'))} com .json de procedência",
              'Teste técnico verde não é aprovação: a avaliação estética é do Heitor.']
    out = saida / 'evolucao.md'
    out.write_text('\n'.join(linhas) + '\n', encoding='utf-8')
    fiscal_camadas(saida, pl)
    return out


def fiscal_camadas(saida: Path, pl: dict) -> Path:
    """fiscal em QUATRO camadas separadas: integridade técnica (automática, decide), correção factual (automática:
    rastreio fato → fonte), clareza da demonstração (indicadores automáticos, não veredito) e qualidade editorial (HUMANA)."""
    if (saida / 'plano_resolvido.json').exists():
        pl = _ler(saida / 'plano_resolvido.json')            # tempos numéricos (o plano bruto tem âncoras na fala)
    r = _ler(saida / 'resultado.json') if (saida / 'resultado.json').exists() else {}
    pf = _ler(saida / 'preflight.json') if (saida / 'preflight.json').exists() else {'itens': []}
    q = _ler(saida / 'quadros' / 'relatorio.json') if (saida / 'quadros' / 'relatorio.json').exists() else {}
    rit, port = r.get('ritmo') or {}, r.get('portoes') or {}
    ok = lambda b: '— (sem MP4)' if b is None else 'OK' if b else 'FALHA'
    L = [f"# Fiscal em 4 camadas — {pl.get('video_id')}", '',
         '## 1. Integridade técnica (automática — decide BLOQUEADO)',
         f"- preflight: {sum(i['ok'] for i in pf['itens'])}/{len(pf['itens'])} itens",
         f"- quadros renderizados conferidos: {len(q.get('quadros', []))} (amostragem {q.get('amostragem')}) · erros {len(q.get('problemas', [])) - len(q.get('avisos', []))} · avisos {len(q.get('avisos', []))}",
         f"- janelas pretas/congeladas: {len(port.get('preto_ou_congelado') or [])} · áudio {ok(port.get('audio_ok'))} ({(r.get('audio') or {}).get('lufs')} LUFS, {(r.get('audio') or {}).get('pico')} dBTP)",
         f"- ritmo sem câmera {ok(port.get('ritmo_ok'))}: maior trecho {(rit.get('sem_camera') or {}).get('maior_trecho_parado_s')} s · legenda × áudio {ok(port.get('legenda_ok'))}",
         '', '## 2. Correção factual (automática — rastreio, não verificação de verdade)']
    L += [f"- estado: {r.get('estado', 'sem MP4')}"]
    L += [f"- BLOQUEIO: {m}" for m in r.get('motivos_bloqueio') or []]
    fatos = {f['id']: f for f in (pl.get('narracao') or {}).get('fatos', []) if isinstance(f, dict)}
    for L_ in P.camadas(pl):
        p = L_.get('p') or {}
        if L_['componente'] == 'editorial.statCard' and p.get('estilo') != 'pilula':
            f = fatos.get(p.get('fato'))
            L.append(f"- {L_['id']} ({p.get('valor')} {p.get('unidade', '')}): " + (f"fato {f['id']} · {', '.join(f.get('fontes') or [])[:160]}" if f else 'SEM FATO LIGADO'))
    L += ['', '## 3. Clareza da demonstração (indicadores automáticos — o olho humano decide)']
    ev = P.eventos(pl)
    gancho = [c for c in pl.get('clipes') or [] if c.get('papel') == 'gancho']
    L += [f"- gancho: {'clipe ' + gancho[0]['componente'] + ' em 0–' + format(gancho[0]['t1'], '.1f') + ' s' if gancho else 'sem clipe de gancho'}; primeira mudança em {min([e for e in ev if e > .2], default=0):.2f} s",
          f"- eventos de informação: {len(ev)} em {pl['duracao']:.0f} s ({len(ev) / max(1, pl['duracao']):.2f}/s)",
          f"- CTA: {pl.get('cta_decisao', '—')}"]
    for L_ in P.camadas(pl):
        p = L_.get('p') or {}
        if p.get('tipo') == 'foto':
            L.append(f"- foto {L_['id']}: papel {p.get('papel', 'secundario')}, raio {p.get('raio')} px (escala automática {p.get('escala_auto', 1)}), desloc {p.get('desloc')}")
    L += ['', '## 4. Qualidade editorial (HUMANA)', '- pendente: só o Heitor aprova estética e publicação. Teste verde não é aprovação.']
    out = saida / 'fiscal_4camadas.md'
    out.write_text('\n'.join(L) + '\n', encoding='utf-8')
    return out


# ---------------------------------------------------------------- prévia privada
def telegram(saida: Path, titulo: str) -> dict:
    """MP4 + estado + preflight + portões + áudio, só ao chat privado autorizado. NÃO é publicação."""
    from src.v3 import previa_telegram
    from src.v4.formatos import estado as gate
    r = _ler(saida / 'resultado.json') if (saida / 'resultado.json').exists() else None
    pf = _ler(saida / 'preflight.json') if (saida / 'preflight.json').exists() else {'pronto': False, 'itens': []}
    linhas = [f'FORMATO — PRÉVIA PRIVADA, NÃO PUBLICADO · {titulo}']
    if not r:
        linhas += ['STATUS: BLOQUEADO (não renderizado)', 'preflight:'] + [f"- NÃO {i['item']}: {i['detalhe']}" for i in pf['itens'] if not i['ok']][:15]
        chat, _ = previa_telegram.chat_autorizado()
        previa_telegram._api('sendMessage', {'chat_id': chat, 'text': '\n'.join(linhas)[:3900]})
        return {'enviado': True, 'sem_mp4': True}
    au = r.get('audio') or {}
    est = gate.avaliar(r)
    linhas += [f"STATUS EDITORIAL: {est['estado']} (aprovação estética só do responsável humano)", f"duração {r['duracao']:.1f} s · formato {r['formato']}",
               f"preflight: {sum(i['ok'] for i in pf['itens'])}/{len(pf['itens'])} itens OK",
               f"áudio no MP4: {au.get('lufs')} LUFS · pico {au.get('pico')} dBTP",
               f"janelas de 4 s pretas/congeladas: {len(r['portoes']['preto_ou_congelado'])}"]
    linhas += [f"- {j['de']}–{j['ate']}s: {'; '.join(j['problemas'])}" for j in r['portoes']['preto_ou_congelado']][:8]
    linhas += [f"BLOQUEIO: {m}" for m in est.get('motivos') or []][:8]
    rit = r.get('ritmo') or {}
    linhas += [f"ritmo (zona de conteúdo, 4 q/s): bruto {rit.get('maior_trecho_parado_s')} s · sem câmera {(rit.get('sem_camera') or {}).get('maior_trecho_parado_s')} s "
               f"(portão ≤ 3 s; ref. A: 2 s)", f"legenda × áudio real: {'OK' if r['portoes'].get('legenda_ok') else 'FALHA'} {r.get('legenda_sync', {}).get('atraso_s')} s"]
    ev = saida / 'evolucao.md'
    if ev.exists():
        linhas += ['', ev.read_text(encoding='utf-8')]
    env = previa_telegram.enviar(Path(r['mp4']), est, titulo, '\n'.join(linhas))
    chat, _ = previa_telegram.chat_autorizado()
    fol = _ler(saida / 'folhas.json') if (saida / 'folhas.json').exists() else {}
    extras = [(saida / 'quadros' / 'styleframes.jpg', 'styleframes (quadros renderizados, com legenda)'),
              (saida / 'quadros' / 'celular.jpg', 'leitura em tela de celular (405×720)'),
              (Path(fol['folha']) if fol.get('folha') else None, 'folha de contato do MP4 final'),
              (Path(fol['comparativo']) if fol.get('comparativo') else None, 'ANTES × DEPOIS, mesmos instantes'),
              (saida / 'quadros' / 'amostragem.jpg', 'amostragem ampliada (gancho, transições, a cada 2,5 s)'),
              *[(saida / 'quadros' / f'plataforma_{n}.jpg', f'interface simulada {n} (áreas seguras)') for n in layout.CFG['ativos']],
              (saida / 'fiscal_4camadas.md', 'fiscal em 4 camadas')]
    enviados = 0
    for arq, leg in extras:
        if arq and arq.exists():
            previa_telegram._api('sendDocument', {'chat_id': chat, 'caption': f'{titulo} — {leg} (prévia privada, não publicado)'[:1000]}, ('document', arq))
            enviados += 1
    env['anexos'] = enviados
    _gravar(saida / 'telegram.json', {'enviado': True, **env})
    return env
