"""VALIDAÇÃO SOBRE QUADROS RENDERIZADOS + STYLEFRAMES (formatos ATLAS/DOSSIÊ), sem IA e sem rede.

Para um plano JÁ preflightado: escolhe os quadros (um por composição, no instante em que tudo do beat já entrou),
renderiza Formato + Camada (marca/legenda) com a medição da própria página e confere, no quadro real:
  - camada × camada (exceto marcação sobre o seu alvo), camada × território do beat (roi), camada/rótulo × marca e legenda;
  - camada que transborda a própria caixa (> 24 px); texto cortado (reticências/overflow);
  - corpo de texto mínimo (informação ≥ texto_min_px; crédito/atribuição ≥ texto_meta_min_px) e o equivalente num
    celular de 400 px de largura; cena vazia (sem camada, rótulo nem território).
Gera styleframes (1080×1920 com legenda), versão de celular (405×720), folhas de contato e relatorio.json/.md.
Teste técnico verde NÃO é aprovação estética: a folha vai para o olho humano.
uso: python scripts/formatos_validar.py <saida_preflight> <dir_saida> [auto|t1,t2,...] [n=6]
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src.v4.formatos import plano as P  # noqa: E402

FPS = 30
TOL = 6


def _cruza(a, b, tol=TOL):
    return a['x'] + tol < b['x'] + b['w'] and b['x'] + tol < a['x'] + a['w'] and a['y'] + tol < b['y'] + b['h'] and b['y'] + tol < a['y'] + a['h']


def inicio(b: dict) -> float:
    return b['t'] if b.get('t') is not None else min((L['t0'] for L in b['camadas']), default=0.0)


def escolher(pl: dict, n: int) -> list[float]:
    """um quadro por beat (o mais "cheio": logo antes de sair, com tudo revelado), depois espalha até n"""
    furos = [(c['t0'], c['t1']) for c in pl.get('clipes') or []]
    ts = []
    bs = pl['beats']
    for i, b in enumerate(bs):
        Ls = [L for L in b['camadas'] if L['componente'] != 'dossie.evidenceHighlight'] or b['camadas']
        if not Ls:              # beat só de mapa (o território é a informação): meio do beat, câmera assentada
            fim = inicio(bs[i + 1]) if i + 1 < len(bs) else pl['duracao']
            ts.append(round(min(fim - .3, inicio(b) + max(.9, (fim - inicio(b)) * .7)), 2))
            continue
        fim = min(L['t1'] for L in Ls)
        ini = max(L['t0'] for L in b['camadas'])
        t = max(ini + .7, fim - .35) if fim - ini > .9 else (ini + fim) / 2
        t = min(t, fim - .2)
        if not any(a <= t <= z for a, z in furos):
            ts.append(round(t, 2))
    if len(ts) > n:   # primeiro uma por COMPOSIÇÃO (cobre o repertório), depois espalha no tempo
        comp = {}
        for t in ts:
            bb = next((b for b in reversed(bs) if inicio(b) <= t + 1e-6), None)
            comp[t] = bb and bb.get('composicao')
        vistas, esc = set(), []
        for t in ts:
            if comp[t] not in vistas:
                vistas.add(comp[t]); esc.append(t)
        for t in ts:
            if len(esc) >= n:
                break
            if t not in esc:
                esc.append(t)
        ts = sorted(esc[:n])
    return ts


def checar(m: dict, pl: dict, t: float) -> list[dict]:
    R = P.REGRAS
    prob = []
    add = lambda regra, txt: prob.append({'t': t, 'regra': regra, 'texto': txt})
    cam = {c['id']: c for c in m['camadas']}
    decl = {L['id']: L for L in P.camadas(pl)}
    alvo = {L['id']: (L.get('p') or {}).get('alvo') for L in decl.values() if L['componente'] == 'dossie.evidenceHighlight'}
    ids = list(cam)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            if alvo.get(a) == b or alvo.get(b) == a or (a in alvo and b in alvo and alvo[a] == alvo[b]):
                continue
            if _cruza(cam[a]['caixa'], cam[b]['caixa']):
                add('R-COLISAO', f'{a} × {b} se sobrepõem no quadro renderizado')
    pinos = {L['id'] for L in decl.values() if L['componente'] == 'atlas.geoPin'}
    if m.get('roi'):
        for c in m['camadas']:
            if c['id'] in pinos:
                continue          # o pino É do território (ancorado nele); confere-se que não descola (R-PINO-DESCOLADO)
            if _cruza(c['caixa'], m['roi'], 10):
                add('R-COBRE-TERRITORIO', f"{c['id']} cobre o território do beat")
    for p_ in m.get('pinos') or []:
        if p_['desvio'] > 3:
            add('R-PINO-DESCOLADO', f"pino {p_['lonlat']} a {p_['desvio']:.1f} px do ponto do mapa (segue a câmera errada)")
        if not (0 <= p_['centro'][0] <= 1080 and 0 <= p_['centro'][1] <= 1920):
            add('R-PINO-FORA', f"pino {p_['lonlat']} fora da tela")
    for nome, (x, y, w, h) in P.zonas(pl['formato']).items():
        z = {'x': x, 'y': y, 'w': w, 'h': h}
        for c in m['camadas']:
            if _cruza(c['caixa'], z, 2):
                add('R-ZONA-IDENTIDADE', f"{c['id']} invade a {nome}")
        for r in m['rotulos']:
            if _cruza(r['caixa'], z, 2):
                add('R-ZONA-IDENTIDADE', f"rótulo {r['txt']!r} invade a {nome}")
    for x in m.get('metas') or []:      # escala gráfica e atribuição: nunca sob cartões nem na faixa da legenda/marca
        for c in m['camadas']:
            if _cruza(x['caixa'], c['caixa'], 2):
                add('R-COLISAO', f"{x['tipo']} sob {c['id']}")
        if x['tipo'] == 'atribuicao':   # a faixa de créditos É a zona 'creditos': tem de caber INTEIRA nela
            zc = P.zonas(pl['formato']).get('creditos')
            if zc and (x['caixa']['y'] + x['caixa']['h'] > zc[1] + zc[3] + 2 or x['caixa']['y'] < zc[1] - 2):
                add('R-CREDITOS-TRANSBORDA', f"créditos cartográficos saem da faixa própria ({x['caixa']['h']:.0f} px de altura)")
            continue
        for nome, (zx, zy, zw, zh) in P.zonas(pl['formato']).items():
            if _cruza(x['caixa'], {'x': zx, 'y': zy, 'w': zw, 'h': zh}, 2):
                add('R-ZONA-IDENTIDADE', f"{x['tipo']} invade a {nome}")
    for r in m['rotulos']:
        for c in m['camadas']:
            if _cruza(r['caixa'], c['caixa'], 4):
                add('R-ROTULO-COBERTO', f"rótulo do mapa {r['txt']!r} sob {c['id']}")
    for c in m['camadas']:
        d = decl.get(c['id'])
        if not d or d['componente'] in ('dossie.evidenceHighlight', 'atlas.geoPin'):
            continue
        k, b = d['caixa'], c['caixa']
        exc = max(k['x'] - b['x'], k['y'] - b['y'], (b['x'] + b['w']) - (k['x'] + k['w']), (b['y'] + b['h']) - (k['y'] + k['h']))
        if exc > 24:
            add('R-TRANSBORDA', f"{c['id']} sai {exc:.0f} px da própria caixa")
    for x in m['textos']:
        lim = R['texto_meta_min_px'] if x['meta'] else R['texto_min_px']
        if x['px'] + .01 < lim:
            add('R-TEXTO-PEQUENO', f"{x['txt']!r} a {x['px']} px (mín. {lim}; ≈ {x['px'] * 400 / 1080:.1f} px num celular)")
    for x in m['cortados']:
        add('R-TEXTO-CORTADO', f"{x['camada']}: {x['txt']!r}")
    if not m['camadas'] and not m['rotulos'] and not m.get('roi'):
        add('R-CENA-VAZIA', 'quadro sem camada, rótulo ou território')
    return prob


def main(S: Path, out: Path, tempos: str = 'auto', n: int = 6):
    out.mkdir(parents=True, exist_ok=True)
    pl = json.loads((S / 'plano_resolvido.json').read_text())
    meta = json.loads((S / 'narracao.json').read_text())
    imgs = json.loads((S / 'ativos.json').read_text())
    can = P.canal(pl.get('canal', 'coringa'))
    geo = json.loads((RAIZ / pl['geo']).read_text()) if pl.get('geo') else None
    pf = out / 'props_formato.json'
    pf.write_text(json.dumps(P.props(pl, {k: can[k] for k in ('cores', 'fontes', 'tempo', 'palco')}, geo, imgs), ensure_ascii=False))
    cenas = [{'ini': 0.0, 'fim': pl['duracao'], 'selo': None, 'credito': None, 'legenda': True}]
    pc = out / 'props_camada.json'
    cam = {'duracao': pl['duracao'], 'palavras': meta['palavras'], 'cenas': cenas}
    lz = P.zonas(pl['formato']).get('legenda')
    if lz and pl['formato'] == 'atlas':
        cam['legenda_topo'] = lz[1]
    pc.write_text(json.dumps(cam, ensure_ascii=False))
    ts = escolher(pl, n) if tempos == 'auto' else [float(x) for x in tempos.split(',')]
    qs = [int(round(t * FPS)) for t in ts]
    chrome = os.environ.get('CORINGA_CHROME') or os.environ.get('REMOTION_CHROME') or '/usr/bin/google-chrome'
    r = subprocess.run(['node', 'medir.mjs', str(pf.resolve()), str(pc.resolve()), ','.join(map(str, qs)), str(out.resolve()), chrome], cwd=RAIZ / 'motor4' / 'remotion',
                       capture_output=True, text=True, timeout=3600)
    (out / 'medir.log').write_text(r.stdout + r.stderr)
    if r.returncode:
        raise SystemExit(f'medição falhou: {r.stderr[-800:]}')
    med = json.loads((out / 'medidas.json').read_text())
    problemas, quadros = [], []
    for t, q in zip(ts, qs):
        m = med.get(str(q))
        if not m:
            problemas.append({'t': t, 'regra': 'R-SEM-MEDIDA', 'texto': 'a página não registrou a geometria'})
            continue
        problemas += checar(m, pl, t)
        f = Image.open(out / f'f_{q}.png').convert('RGBA')
        f.alpha_composite(Image.open(out / f'c_{q}.png').convert('RGBA'))
        sf = out / f'styleframe_{t:05.2f}.png'
        f.convert('RGB').save(sf)
        f.convert('RGB').resize((405, 720), Image.LANCZOS).save(out / f'celular_{t:05.2f}.png')
        menor = min((x['px'] for x in m['textos'] if not x['meta']), default=None)
        beat = next((b for b in reversed(pl['beats']) if inicio(b) <= t + 1e-6), None)
        quadros.append({'t': t, 'quadro': q, 'beat': beat and beat['id'], 'composicao': beat and beat.get('composicao'),
                        'camadas': [c['id'] for c in m['camadas']], 'menor_texto_px': menor,
                        'menor_texto_celular_px': menor and round(menor * 400 / 1080, 1), 'roi': m.get('roi'), 'arquivo': sf.name})
    folha(out, quadros, 'styleframes.jpg', 'styleframe', (540, 960))
    folha(out, quadros, 'celular.jpg', 'celular', (405, 720))
    rel = {'plano': pl.get('video_id'), 'formato': pl['formato'], 'quadros': quadros, 'problemas': problemas, 'ok': not problemas,
           'nota': 'validação técnica sobre quadros renderizados; NÃO é aprovação estética (só o Heitor aprova)'}
    (out / 'relatorio.json').write_text(json.dumps(rel, ensure_ascii=False, indent=1))
    linhas = [f"# Quadros renderizados — {pl.get('video_id')} ({pl['formato']})", '', '| t (s) | beat | composição | camadas | menor texto (1080 → celular 400) |', '|---|---|---|---|---|']
    linhas += [f"| {q['t']:.2f} | {q['beat']} | {q['composicao']} | {', '.join(q['camadas'])} | {q['menor_texto_px']} → {q['menor_texto_celular_px']} px |" for q in quadros]
    linhas += ['', f"Problemas: {len(problemas)}"] + [f"- {p['t']:.2f}s {p['regra']}: {p['texto']}" for p in problemas]
    (out / 'relatorio.md').write_text('\n'.join(linhas) + '\n')
    print(json.dumps({'quadros': len(quadros), 'problemas': len(problemas)}, ensure_ascii=False))
    for p in problemas:
        print(' ', p['t'], p['regra'], p['texto'])
    return rel


def folha(out: Path, quadros: list[dict], nome: str, pref: str, tam: tuple[int, int]):
    if not quadros:
        return
    w, h = tam
    cols = min(3, len(quadros))
    rows = (len(quadros) + cols - 1) // cols
    o = Image.new('RGB', (w * cols, (h + 34) * rows), '#111')
    d = ImageDraw.Draw(o)
    try:
        fnt = ImageFont.truetype(str(RAIZ / 'motor4' / 'identidade' / 'ttf' / 'jetbrains-mono-latin-700-normal.ttf'), 22)
    except Exception:
        fnt = None
    for i, q in enumerate(quadros):
        im = Image.open(out / f"{pref}_{q['t']:05.2f}.png").convert('RGB').resize((w, h), Image.LANCZOS)
        x, y = (i % cols) * w, (i // cols) * (h + 34)
        o.paste(im, (x, y + 34))
        d.text((x + 8, y + 6), f"{q['t']:.1f}s · {q['composicao'] or ''}", fill='#FFD21F', font=fnt)
    o.save(out / nome, quality=86)


if __name__ == '__main__':
    a = sys.argv
    main(Path(a[1]), Path(a[2]), a[3] if len(a) > 3 else 'auto', int(a[4]) if len(a) > 4 else 6)
