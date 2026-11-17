"""Produção por FORMATO (ATLAS / DOSSIÊ): narração → mídia comprovada → PREFLIGHT → render → portões no MP4.

Etapas separadas (cada uma é um comando; o Actions roda em sequência e PARA no primeiro preflight vermelho):
  narrar   — reutiliza a narração cifrada ou gera a do texto do plano (1 chamada de TTS, cota grátis; nada de repetir)
  ativos   — baixa só itens da biblioteca comprovada (procedência + licença + prova)
  preflight— sem IA e sem rede: plano válido, 100% das mídias/geometria/narração/clipes presentes, geometria do clipe V2
  render   — Remotion `Formato` (palco + primitivas) + clipes aprovados (palco V2) + camada global (marca/legendas) + som
"""
from __future__ import annotations

import base64
import json
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
    if n.get('cifrada'):
        from src.v3 import material
        pac = json.loads(material.decifrar(material._segredo(), (RAIZ / n['cifrada']).read_bytes()))
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
def assets_do_plano(plano: dict) -> list[str]:
    return sorted({(L.get('p') or {}).get('asset') for b in plano['beats'] for L in b['camadas'] if (L.get('p') or {}).get('asset')})


def ativos(plano: dict, saida: Path) -> dict:
    """baixa SÓ itens da biblioteca comprovada; devolve {asset: {src, w, h, credito, licenca}}"""
    from src.v4 import acervo_v4, viabilidade
    por = {it['id']: it for it in viabilidade.carregar()['itens']}
    PUBLICO.mkdir(parents=True, exist_ok=True)
    out = {}
    for k, a in enumerate(assets_do_plano(plano)):
        it = por[a]
        x = acervo_v4.baixar({'url': it['url'], 'titulo': it['titulo'], 'credito': it['credito']}, saida / 'ativos', f'f{k}')
        dest = PUBLICO / f'f{k}.jpg'
        shutil.copy(x['arq'], dest)
        out[a] = {'src': f'_formato/f{k}.jpg', 'w': x.get('w'), 'h': x.get('h'), 'credito': it['credito'], 'licenca': it['licenca']}
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
        f = RAIZ / 'motor4' / 'remotion' / 'public' / imgs.get(a, {}).get('src', '_nada')
        add(f'arquivo de mídia {a[:50]}', f.exists() and (imgs.get(a) or {}).get('w'), str(f.name))
        lic = (it or {}).get('licenca', '#')
        cred = ' '.join(m for b in pl['beats'] for L in b['camadas'] if (L.get('p') or {}).get('asset') == a for m in (L['p'].get('meta') or []))
        add(f'crédito visível {a[:50]}', any(x.lower() in cred.lower() for x in (lic, 'domínio público', 'cc by')), cred[:90])
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
    au = medir_audio(mp4)
    res = {'video_id': pl['video_id'], 'formato': pl['formato'], 'mp4': str(mp4), 'duracao': pl['duracao'], 'info': info, 'som': reg_som,
           'audio': au, 'janelas': janelas, 'nao_publicado': True,
           'portoes': {'preto_ou_congelado': [j for j in janelas if j['problemas']],
                       'audio_ok': au.get('lufs') is not None and abs(au['lufs'] + 14) <= 1.0 and (au.get('pico') or 0) <= -1.0}}
    res['estado'] = 'AGUARDANDO_APROVACAO_HUMANA' if not res['portoes']['preto_ou_congelado'] and res['portoes']['audio_ok'] else 'BLOQUEADO'
    _gravar(saida / 'resultado.json', res)
    return res


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
    env = previa_telegram.enviar(Path(r['mp4']), est, titulo, '\n'.join(linhas))
    _gravar(saida / 'telegram.json', {'enviado': True, **env})
    return env
