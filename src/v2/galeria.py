"""GALERIA DE VALIDAÇÃO V2: cada composição do catálogo renderizada com o seu exemplo (capturas + prévia animada),
os parâmetros usados, o resultado do fiscal geométrico e os problemas conhecidos; mais as comparações antes/depois.

Uso: python -m src.v2.galeria [--saida saida/galeria_v2] [--so id1,id2] [--sem-previa]
Mídia dos exemplos: '@nome' → MIDIA (fotos do Panamá recuperadas da auditoria, se CORINGA_AUDITORIA apontar para a
pasta do diagnóstico; senão, imagens de teste do repositório). Nada é baixado nem gerado por IA.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import time
from pathlib import Path

from src.v2 import palco

RAIZ = palco.RAIZ
AUD = Path(os.environ.get('CORINGA_AUDITORIA', str(RAIZ / 'saida' / 'auditoria')))
_PANAMA = {'lago_navios': 'a13-g.jpg', 'ancon_1914': 'a16-g.jpg', 'margem_lago': 'a18-g.jpg', 'satelite': 'a2-g.jpg',
           'navio_eclusa': 'a20-g.jpg', 'camara_eclusa': 'a23-g.jpg', 'construcao_1913': 'a31-g.jpg', 'navio_mar': 'a41-g.jpg',
           'agua_clara': 'a8-g.jpg'}
_TESTE = {'fundo_a': 'tests/img/fundo_a.png', 'fundo_b': 'tests/img/fundo_b.jpg', 'fundo_c': 'tests/img/fundo_c.jpg',
          'fundo_d': 'tests/img/fundo_d.jpg', 'pele': 'prototipos/editorial/midia/pele_macro.jpg'}


def midia() -> dict[str, str]:
    m = {k: str(RAIZ / v) for k, v in _TESTE.items()}
    for k, v in _PANAMA.items():
        m[k] = str(AUD / 'img' / v) if (AUD / 'img' / v).exists() else m['fundo_b']
    return m


def _resolver(x, M):
    if isinstance(x, str) and x.startswith('@') and x[1:] in M:
        return M[x[1:]]
    if isinstance(x, list):
        return [_resolver(v, M) for v in x]
    if isinstance(x, dict):
        return {k: _resolver(v, M) for k, v in x.items()}
    return x


def legendas_sinteticas(fala: str, ini: float, fim: float, por_bloco: int = 4) -> list[dict]:
    """Palavras distribuídas por igual no tempo (sem TTS: é só para ver a legenda convivendo com a cena)."""
    ws = [w for w in re.split(r'\s+', fala.strip()) if w]
    if not ws:
        return []
    passo = (fim - ini - 0.3) / len(ws)
    caps = []
    for b in range(0, len(ws), por_bloco):
        bloco = ws[b:b + por_bloco]
        s0 = ini + 0.15 + b * passo
        caps.append({'start': round(s0, 3), 'end': round(s0 + len(bloco) * passo, 3),
                     'words': [{'w': w.strip('*').upper(), 'hl': w.startswith('*'), 's': round(s0 + i * passo, 3)} for i, w in enumerate(bloco)]})
    return caps


def dados_exemplo(meta: dict, M: dict | None = None) -> dict:
    M = M or midia()
    ex = _resolver(json.loads(json.dumps(meta.get('exemplo') or {})), M)
    dur = float(ex.get('dur', 4))
    sc = {'comp': meta['id'], 'start': 0.0, 'end': dur, 'params': ex.get('params', {}), 'fala': ex.get('fala', '')}
    if ex.get('fundo'):
        sc['fundo'] = ex['fundo']
    caps = legendas_sinteticas(ex.get('fala', ''), 0, dur) if ex.get('fala') else []
    return {'duration': dur, 'meta': {'titulo': meta['nome'], 'marca': '@coringa.explica'}, 'scenes': [sc], 'captions': caps}


def catalogo(trabalho: Path) -> list[dict]:
    with palco.abrir(palco.preparar({'duration': 1, 'meta': {}, 'scenes': [], 'captions': []}), trabalho) as pg:
        return pg.evaluate('V2.catalogo()')


def renderizar_comp(meta: dict, saida: Path, trabalho: Path, previa: bool = True, tempos=None) -> dict:
    d = dados_exemplo(meta)
    dur = d['duration']
    tempos = tempos or [round(dur * f, 2) for f in (0.12, 0.5, 0.92)]
    t0 = time.time()
    r = {'id': meta['id'], 'tempos': tempos, 'capturas': [], 'previa': None, 'problemas': [], 'erros': [], 'params': d['scenes'][0]['params']}
    try:
        with palco.abrir(palco.preparar(d), trabalho / meta['id']) as pg:
            for t in tempos:
                arq = saida / 'quadros' / f"{meta['id']}_{t:05.2f}.jpg"
                palco.capturar(pg, t, arq, 88)
                r['capturas'].append(arq.relative_to(saida).as_posix())
            r['problemas'] = palco.medir(pg, dur, 0.25)
            if previa:
                arq = saida / 'previas' / f"{meta['id']}.mp4"
                palco.previa(pg, 0, dur, arq, fps=24)
                r['previa'] = arq.relative_to(saida).as_posix()
            r['erros'] = pg.erros + pg.evaluate('V2.avisos')
            r['alertas'] = pg.evaluate('V2.alertas || []')
    except Exception as e:  # a galeria mostra a falha em vez de esconder
        r['erros'].append(f'{type(e).__name__}: {e}')
    r['segundos'] = round(time.time() - t0, 1)
    return r


def _agrupar(problemas: list[dict]) -> list[str]:
    vistos = {}
    for p in problemas:
        k = (p['tipo'], p['txt'])
        vistos.setdefault(k, []).append(p['t'])
    return [f"{tipo}: {txt} ({min(ts):.1f}–{max(ts):.1f}s)" for (tipo, txt), ts in vistos.items()]


def renderizar_temas(saida: Path, trabalho: Path, previa: bool = True) -> list[dict]:
    from src.v2.temas_exemplo import TEMAS
    M = midia()
    out = []
    for nome, (titulo, d) in TEMAS.items():
        d = _resolver(json.loads(json.dumps(d)), M)
        r = {'id': nome, 'titulo': titulo, 'capturas': [], 'previa': None, 'problemas': [], 'erros': []}
        with palco.abrir(palco.preparar(d), trabalho / ('tema_' + nome)) as pg:
            for sc in d['scenes']:
                t = round(sc['start'] + (sc['end'] - sc['start']) * .75, 2)
                arq = saida / 'temas' / f'{nome}_{t:05.2f}.jpg'
                palco.capturar(pg, t, arq, 86)
                r['capturas'].append(arq.relative_to(saida).as_posix())
            r['problemas'] = palco.medir(pg, d['duration'], .25)
            if previa:
                r['previa'] = palco.previa(pg, 0, d['duration'], saida / 'temas' / f'{nome}.mp4', fps=24).relative_to(saida).as_posix()
            r['erros'] = pg.erros + pg.evaluate('V2.avisos')
        print(f"  tema {nome:12s} problemas={len(r['problemas'])} erros={len(r['erros'])}")
        out.append(r)
    return out


def pagina_html(itens: list[dict], metas: dict, comparacoes: list[dict], saida: Path, resumo: dict, temas: list[dict] | None = None) -> Path:
    def esc(x):
        return html.escape(str(x))
    cards = []
    for r in itens:
        m = metas[r['id']]
        graves = [p for p in r['problemas'] if p.get('grave')]
        leves = [p for p in r['problemas'] if not p.get('grave')]
        estado = 'reprovada' if r['erros'] or graves else ('com avisos' if leves else 'ok')
        cor = {'ok': '#3ddc84', 'com avisos': '#ffd21f', 'reprovada': '#ff4d3d'}[estado]
        imgs = ''.join(f'<img loading="lazy" src="{esc(c)}">' for c in r['capturas'])
        vid = f'<video src="{esc(r["previa"])}" muted loop playsinline controls preload="none" poster="{esc(r["capturas"][1] if len(r["capturas"]) > 1 else "")}"></video>' if r.get('previa') else ''
        lim = ', '.join(f'{k} ≤ {v}' for k, v in (m.get('limites') or {}).items())
        cards.append(f'''<section class="card" id="{esc(r['id'])}">
<header><h2>{esc(m['nome'])}</h2><code>{esc(r['id'])}</code><span class="st" style="background:{cor}">{estado}</span></header>
<p class="obj">{esc(m.get('objetivo', ''))}</p>
<div class="midia">{imgs}{vid}</div>
<dl>
<dt>Tratamento</dt><dd>{esc(m.get('tratamento', ''))} · legenda: {esc(m.get('legenda', ''))} · transição: {esc(m.get('transicao', ''))}</dd>
<dt>Layout</dt><dd>{esc(m.get('layout', ''))}</dd>
<dt>Animação</dt><dd>{esc(m.get('animacao', ''))}</dd>
<dt>Duração</dt><dd>{esc(m.get('duracao', ''))} s (mín, ideal, máx) · limites: {esc(lim)}</dd>
<dt>Área segura</dt><dd>{esc(m.get('area_segura', ''))}</dd>
<dt>Legibilidade</dt><dd>{esc(m.get('legibilidade', ''))}</dd>
<dt>Rejeição</dt><dd>{'<br>'.join(esc(x) for x in m.get('rejeicao', []))}</dd>
<dt>Parâmetros</dt><dd><pre>{esc(json.dumps(r['params'], ensure_ascii=False, indent=1)[:1600])}</pre></dd>
<dt>Fiscal</dt><dd>{'<br>'.join(esc(x) for x in _agrupar(r['problemas'])) or 'sem problemas geométricos'}{('<br><b>Erros:</b> ' + '<br>'.join(esc(e) for e in r['erros'])) if r['erros'] else ''}</dd>
<dt>Problemas conhecidos</dt><dd>{'<br>'.join(esc(x) for x in m.get('problemas_conhecidos', []) + r.get('alertas', [])) or '—'}</dd>
</dl></section>''')
    comps = []
    for c in comparacoes:
        comps.append(f'''<section class="card cmp" id="cmp-{esc(c['id'])}"><header><h2>Antes × depois: {esc(c['titulo'])}</h2></header>
<p class="obj">{esc(c.get('nota', ''))}</p><div class="ad"><figure><img loading="lazy" src="{esc(c['antes'])}"><figcaption>ANTES · motor atual (main)</figcaption></figure>
<figure><img loading="lazy" src="{esc(c['depois'])}"><figcaption>DEPOIS · V2 ({esc(c.get('comp', ''))})</figcaption></figure>
{f'<figure><video src="{esc(c["previa"])}" muted loop playsinline controls preload="none"></video><figcaption>prévia V2</figcaption></figure>' if c.get('previa') else ''}</div></section>''')
    tms = []
    for t in temas or []:
        imgs = ''.join(f'<img loading="lazy" src="{esc(c)}">' for c in t['capturas'])
        vid = f'<video src="{esc(t["previa"])}" muted loop playsinline controls preload="none"></video>' if t.get('previa') else ''
        tms.append(f'<section class="card" id="tema-{esc(t["id"])}"><header><h2>{esc(t["titulo"])}</h2><span class="st" style="background:{"#3ddc84" if not t["erros"] and not any(p.get("grave") for p in t["problemas"]) else "#ff4d3d"}">{len(t["problemas"])} problema(s) geométrico(s)</span></header><p class="obj">Dados aproximados/sintéticos, só para testar a reutilização da biblioteca fora do Panamá.</p><div class="midia">{imgs}{vid}</div></section>')
    idx = ''.join(f'<a href="#{esc(r["id"])}">{esc(r["id"])}</a>' for r in itens)
    css = '''body{margin:0;background:#0b0f17;color:#e9edf3;font:15px/1.5 system-ui,sans-serif}main{max-width:1500px;margin:auto;padding:24px}
h1{font-size:28px;margin:0 0 6px}nav{display:flex;flex-wrap:wrap;gap:6px;margin:14px 0 24px}nav a{color:#ffd21f;font:12px monospace;text-decoration:none;border:1px solid #2a3344;padding:3px 8px;border-radius:4px}
.card{background:#121826;border:1px solid #232c3d;border-radius:10px;padding:18px;margin:0 0 22px}.card header{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.card h2{font-size:20px;margin:0}code{color:#9fb3d1}.st{color:#000;font-weight:700;font-size:12px;padding:2px 8px;border-radius:99px}.obj{color:#c7cfdb;margin:8px 0}
.midia,.ad{display:flex;gap:10px;overflow-x:auto}.midia img,.midia video{height:420px;border-radius:6px;background:#000}.ad figure{margin:0}.ad img,.ad video{height:520px;border-radius:6px}
figcaption{font:12px monospace;color:#9fb3d1;margin-top:4px}dl{display:grid;grid-template-columns:150px 1fr;gap:4px 14px;margin:14px 0 0}dt{color:#9fb3d1}dd{margin:0}pre{margin:0;white-space:pre-wrap;font-size:12px;color:#c7cfdb}
.resumo{display:flex;gap:18px;flex-wrap:wrap;margin:10px 0}.resumo div{background:#121826;border:1px solid #232c3d;border-radius:8px;padding:10px 14px}.resumo b{display:block;font-size:22px;color:#ffd21f}'''
    res = ''.join(f'<div><b>{esc(v)}</b>{esc(k)}</div>' for k, v in resumo.items())
    doc = f'''<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Coringa Explica · Galeria V2</title><style>{css}</style></head>
<body><main><h1>Coringa Explica — Galeria de composições V2</h1><p>Ramo <code>visual-v2</code>. Capturas e prévias renderizadas pelo próprio palco V2 (Playwright, sem IA, sem geração paga). Estado = resultado do fiscal geométrico (choque de textos, fora do quadro, zona da interface, letra pequena); <b>não é aprovação estética</b>.</p>
<div class="resumo">{res}</div><nav>{idx}<a href="#temas">temas</a><a href="#comparacoes">antes × depois</a></nav>{''.join(cards)}<h1 id="temas">Reutilização em outros temas</h1>{''.join(tms)}<h1 id="comparacoes">Comparações com o vídeo do Panamá (execução 43435732255)</h1>{''.join(comps)}</main></body></html>'''
    arq = saida / 'index.html'
    arq.write_text(doc, encoding='utf-8')
    return arq


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--saida', default=str(RAIZ / 'saida' / 'galeria_v2'))
    ap.add_argument('--so', default='')
    ap.add_argument('--sem-previa', action='store_true')
    a = ap.parse_args(argv)
    saida = Path(a.saida).resolve()
    saida.mkdir(parents=True, exist_ok=True)
    trabalho = saida / '_trabalho'
    cat = catalogo(trabalho / '_cat')
    metas = {m['id']: m for m in cat}
    so = [x for x in a.so.split(',') if x]
    itens = []
    for m in cat:
        if so and m['id'] not in so:
            continue
        r = renderizar_comp(m, saida, trabalho, previa=not a.sem_previa)
        print(f"  {m['id']:28s} {r['segundos']:5.1f}s  problemas={len(r['problemas'])} erros={len(r['erros'])}")
        itens.append(r)
    (saida / 'resultado.json').write_text(json.dumps(itens, ensure_ascii=False, indent=1), encoding='utf-8')
    temas = [] if a.so else renderizar_temas(saida, trabalho, previa=not a.sem_previa)
    comparacoes = []
    cmp_arq = saida / 'comparacoes.json'
    if cmp_arq.exists():
        comparacoes = json.loads(cmp_arq.read_text(encoding='utf-8'))
    resumo = {'composições': len(cat), 'renderizadas': len(itens),
              'sem problema grave': sum(1 for r in itens if not r['erros'] and not any(p.get('grave') for p in r['problemas'])),
              'comparações': len(comparacoes)}
    print(pagina_html(itens, metas, comparacoes, saida, resumo, temas))


if __name__ == '__main__':
    main()
