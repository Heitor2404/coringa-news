"""VALIDAÇÃO SOBRE QUADROS RENDERIZADOS + STYLEFRAMES (formatos ATLAS/DOSSIÊ), sem IA e sem rede.

Para um plano JÁ preflightado: escolhe os quadros (um por composição, no instante em que tudo do beat já entrou),
renderiza Formato + Camada (marca/legenda) com a medição da própria página e confere, no quadro real:
  - camada × camada (exceto marcação sobre o seu alvo), camada × território do beat (roi), camada/rótulo × marca e legenda;
  - camada que transborda a própria caixa (> 24 px); texto cortado (reticências/overflow);
  - corpo de texto mínimo (informação ≥ texto_min_px; crédito/atribuição ≥ texto_meta_min_px) e o equivalente num
    celular de 400 px de largura; cena vazia (sem camada, rótulo nem território).
Gera styleframes (1080×1920 com legenda), versão de celular (405×720), folhas de contato e relatorio.json/.md.
Teste técnico verde NÃO é aprovação estética: a folha vai para o olho humano.
Amostragem ampliada (gancho, transições, a cada 2,5 s) + máscaras de plataforma + alinhamento de cartões + faixa da legenda +
atribuição obrigatória presente.
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
from src.v4.formatos import layout, plano as P  # noqa: E402

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
            t = round(min(fim - .3, inicio(b) + max(.9, (fim - inicio(b)) * .7)), 2)
            if not any(a <= t <= z for a, z in furos):     # sob o clipe o vídeo mostra o clipe, não o palco
                ts.append(t)
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


def amostrar(pl: dict, passo: float = 2.5) -> list[dict]:
    """amostragem AMPLIADA (não só 1 quadro por composição): gancho (0,5/1,5/2,5 s), cada transição de beat (+0,35 s),
    o quadro "cheio" de cada beat e um a cada `passo` s dentro dos beats; sob clipes o vídeo mostra o clipe (pula)."""
    furos = [(c['t0'], c['t1']) for c in pl.get('clipes') or []]
    dur = pl['duracao']
    cand = {}
    for t in (.5, 1.5, 2.5):
        cand[t] = 'gancho'
    bs = pl['beats']
    for i, b in enumerate(bs):
        a = inicio(b)
        z = inicio(bs[i + 1]) if i + 1 < len(bs) else dur
        cand.setdefault(round(a + .35, 2), 'transicao')
        x = a + passo
        while x < z - .4:
            cand.setdefault(round(x, 2), 'interno')
            x += passo
    for t in escolher(pl, 10 ** 6):
        cand[t] = 'cheio'
    out = []
    for t in sorted(cand):
        if t >= dur - .05 or any(a - .05 <= t <= z + .05 for a, z in furos):
            continue
        if out and t - out[-1]['t'] < .4:          # quadros quase iguais: fica o de maior prioridade
            pri = {'cheio': 3, 'gancho': 2, 'transicao': 1, 'interno': 0}
            if pri[cand[t]] > pri[out[-1]['tipo']]:
                out[-1] = {'t': t, 'tipo': cand[t]}
            continue
        out.append({'t': t, 'tipo': cand[t]})
    return out


def checar_plataformas(m: dict, pl: dict, t: float, perfis: list[str] | None = None) -> list[dict]:
    """informação essencial (camadas, rótulos, créditos, legenda, marca, cartões) contra as MÁSCARAS de interface simulada
    de cada plataforma ativa (plataformas.json); recorte do feed do Reels = aviso, EXCETO a marca (erro bloqueador)"""
    prob = []
    # partes de pino: recuo de 6 px (anel/sombra), a mesma tolerância do posicionamento no plano
    elems = [(f"camada {c['id']}", ({'x': x['x'] + 6, 'y': x['y'] + 6, 'w': x['w'] - 12, 'h': x['h'] - 12} if c.get('partes') else x))
             for c in m['camadas'] for x in (c.get('partes') or [c['caixa']])] + [(f"rótulo {r['txt']!r}", r['caixa']) for r in m['rotulos']]
    elems += [(f"{x['tipo']}", x['caixa']) for x in m.get('metas') or []]
    cm = m.get('camada') or {}
    for k in ('legenda', 'marca'):
        if cm.get(k):
            elems.append((k, cm[k]))
    for nome in perfis or layout.CFG['ativos']:
        for mk in layout.mascaras(nome):
            x, y, w, h = mk['caixa']
            z = {'x': x, 'y': y, 'w': w, 'h': h}
            for rotulo, bx in elems:
                if _cruza(bx, z, 2):
                    if pl.get('formato') == 'atlas' and rotulo == 'atribuicao' and mk['tipo'] == 'base':
                        prob.append({'t': t, 'regra': 'A-CREDITO-RODAPE', 'aviso': True,
                                     'texto': f'crédito no rodapé pode ser coberto pela interface de {nome}'})
                        continue
                    if mk.get('aviso'):
                        if rotulo == 'marca':
                            # Identidade do canal precisa aparecer no feed; 40/40 cortes não são um aviso aceitável.
                            prob.append({'t': t, 'regra': 'R-MARCA-RECORTE-FEED',
                                         'texto': f'marca cortada no feed do {nome}; corrigir posicao antes do render'})
                        elif rotulo == 'legenda' or rotulo.startswith('camada'):
                            prob.append({'t': t, 'regra': 'A-RECORTE-FEED', 'texto': f'{rotulo} cortado no feed do {nome} (aviso)', 'aviso': True})
                        continue
                    prob.append({'t': t, 'regra': 'R-PLATAFORMA', 'texto': f"{rotulo} sob a interface do {nome} ({mk['tipo']})"})
    return prob


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
            pa, pb = cam[a].get('partes'), cam[b].get('partes')
            if pa or pb:       # pino: confere PARTE × caixa (a caixa-união inclui espaço vazio entre foto, rótulo e ponto)
                if any(_cruza(x, y) for x in (pa or [cam[a]['caixa']]) for y in (pb or [cam[b]['caixa']])):
                    add('R-COLISAO', f'{a} × {b}: partes se sobrepõem')
            elif _cruza(cam[a]['caixa'], cam[b]['caixa']):
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
        if x['tipo'] == 'atribuicao':   # checar moldura E texto efetivamente desenhado, incluindo quebra de linha
            zc = P.zonas(pl['formato']).get('creditos')
            if zc and (x['caixa']['y'] + x['caixa']['h'] > zc[1] + zc[3] + 2 or x['caixa']['y'] < zc[1] - 2):
                add('R-CREDITOS-TRANSBORDA', f"créditos cartográficos saem da faixa própria ({x['caixa']['h']:.0f} px de altura)")
            texto = x.get('texto_caixa')
            if zc and texto and (texto['y'] < zc[1] - 2 or texto['y'] + texto['h'] > zc[1] + zc[3] + 2):
                add('R-CREDITOS-TEXTO-TRANSBORDA', 'texto real dos créditos ultrapassa a faixa e pode sobrepor a legenda')
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
    # cartões: sistema único — centro no centro do slot (±3 px) e sem inclinação
    for c in m.get('cartoes') or []:
        dx, dy = c['centro'][0] - c['alvo'][0], c['centro'][1] - c['alvo'][1]
        if abs(dx) > 3 or abs(dy) > 3:
            add('R-CARTAO-DESALINHADO', f"{c['camada']}: centro a ({dx:+.0f}, {dy:+.0f}) px do centro do slot")
        if abs(c.get('rot') or 0) > .3:
            add('R-CARTAO-INCLINADO', f"{c['camada']}: inclinado {c['rot']:.1f}°")
    # legenda: na faixa PRÓPRIA (nunca sobre créditos, cartões, pinos ou rótulos)
    cm = m.get('camada') or {}
    lg = cm.get('legenda')
    if lg and pl['formato'] == 'atlas':
        zx, zy, zw, zh = P.zonas('atlas')['legenda']
        if lg['y'] < zy - 2 or lg['y'] + lg['h'] > zy + zh + 2 or lg['x'] < zx - 2 or lg['x'] + lg['w'] > zx + zw + 2:
            add('R-LEGENDA-FORA', f"legenda sai da faixa própria ({lg['x']:.0f},{lg['y']:.0f},{lg['w']:.0f}×{lg['h']:.0f})")
        for x in m.get('metas') or []:
            if _cruza(lg, x.get('texto_caixa') or x['caixa'], 1):
                add('R-LEGENDA-CREDITO', f"legenda sobre texto real de {x['tipo']}")
        for c in m['camadas']:
            if _cruza(lg, c['caixa'], 2):
                add('R-LEGENDA-COLISAO', f"legenda sobre {c['id']}")
        for r in m['rotulos']:
            if _cruza(lg, r['caixa'], 2):
                add('R-LEGENDA-COLISAO', f"legenda sobre o rótulo {r['txt']!r}")
    # atribuição obrigatória presente sempre que o mapa aparece
    cr = pl.get('creditos') or P._creditos(pl)
    if m.get('roi') and cr and pl['formato'] == 'atlas':
        ats = [x for x in m.get('metas') or [] if x['tipo'] == 'atribuicao']
        txt = ' '.join(x.get('txt') or '' for x in ats)
        if not txt:
            add('R-ATRIBUICAO-AUSENTE', 'mapa visível sem créditos cartográficos')
        else:   # cada dataset de licença (CC BY, ODbL) VISÍVEL neste quadro tem o seu texto exigido na faixa
            vis = {d for x in ats for d in x.get('datasets') or []}
            for d in cr.get('obrigatorias') or []:
                exig = (cr.get('datasets') or {}).get(d) or ''
                if d in vis and exig and exig[:28].lower() not in txt.lower():
                    add('R-ATRIBUICAO-AUSENTE', f'{d} visível sem a atribuição exigida ({exig[:28]!r}…)')
    return prob


def main(S: Path, out: Path, tempos: str = 'auto', n: int = 6):
    out.mkdir(parents=True, exist_ok=True)
    pl = json.loads((S / 'plano_resolvido.json').read_text())
    meta = json.loads((S / 'narracao.json').read_text())
    imgs = json.loads((S / 'ativos.json').read_text())
    can = P.canal(pl.get('canal', 'coringa'))
    geo = json.loads((RAIZ / pl['geo']).read_text()) if pl.get('geo') else None
    pf = out / 'props_formato.json'
    pf.write_text(json.dumps(P.props(pl, P.tokens_canal(can), geo, imgs), ensure_ascii=False))
    pc = out / 'props_camada.json'
    cam = P.props_camada(pl, meta)
    pc.write_text(json.dumps(cam, ensure_ascii=False))
    if tempos == 'auto':
        amos = amostrar(pl)
        ts = [a['t'] for a in amos]
        tipo = {a['t']: a['tipo'] for a in amos}
        folha_ts = set(escolher(pl, n))
    else:
        ts = [float(x) for x in tempos.split(',')]
        tipo, folha_ts = {t: 'pedido' for t in ts}, set(ts)
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
        problemas += checar(m, pl, t) + checar_plataformas(m, pl, t)
        f = Image.open(out / f'f_{q}.png').convert('RGBA')
        f.alpha_composite(Image.open(out / f'c_{q}.png').convert('RGBA'))
        sf = out / f'styleframe_{t:05.2f}.png'
        f.convert('RGB').save(sf)
        f.convert('RGB').resize((405, 720), Image.LANCZOS).save(out / f'celular_{t:05.2f}.png')
        menor = min((x['px'] for x in m['textos'] if not x['meta']), default=None)
        beat = next((b for b in reversed(pl['beats']) if inicio(b) <= t + 1e-6), None)
        quadros.append({'t': t, 'quadro': q, 'beat': beat and beat['id'], 'composicao': beat and beat.get('composicao'),
                        'camadas': [c['id'] for c in m['camadas']], 'menor_texto_px': menor,
                        'menor_texto_celular_px': menor and round(menor * 400 / 1080, 1), 'roi': m.get('roi'), 'arquivo': sf.name,
                        'amostra': tipo.get(t), 'folha': t in folha_ts})
        if t in folha_ts:
            mascaras_plataformas(out, f, t)
    fq = [q for q in quadros if q['folha']] or quadros
    folha(out, fq, 'styleframes.jpg', 'styleframe', (540, 960))
    folha(out, fq, 'celular.jpg', 'celular', (405, 720))
    folha(out, quadros, 'amostragem.jpg', 'celular', (270, 480))
    for nome in layout.CFG['ativos']:
        folha(out, fq, f'plataforma_{nome}.jpg', f'ui_{nome}', (405, 720))
    erros = [p for p in problemas if not p.get('aviso')]
    rel = {'plano': pl.get('video_id'), 'formato': pl['formato'], 'quadros': quadros, 'problemas': problemas, 'ok': not erros,
           'avisos': [p for p in problemas if p.get('aviso')],
           'amostragem': {k: sum(1 for q in quadros if q['amostra'] == k) for k in ('gancho', 'transicao', 'interno', 'cheio', 'pedido')},
           'nota': 'validação técnica sobre quadros renderizados; NÃO é aprovação estética (só o Heitor aprova)'}
    (out / 'relatorio.json').write_text(json.dumps(rel, ensure_ascii=False, indent=1))
    linhas = [f"# Quadros renderizados — {pl.get('video_id')} ({pl['formato']})", '', '| t (s) | beat | composição | camadas | menor texto (1080 → celular 400) |', '|---|---|---|---|---|']
    linhas += [f"| {q['t']:.2f} | {q['beat']} | {q['composicao']} | {', '.join(q['camadas'])} | {q['menor_texto_px']} → {q['menor_texto_celular_px']} px |" for q in quadros]
    linhas += ['', f"Problemas: {len(problemas)}"] + [f"- {p['t']:.2f}s {p['regra']}: {p['texto']}" for p in problemas]
    (out / 'relatorio.md').write_text('\n'.join(linhas) + '\n')
    print(json.dumps({'quadros': len(quadros), 'problemas': len(erros), 'avisos': len(problemas) - len(erros)}, ensure_ascii=False))
    for p in problemas:
        print(' ', p['t'], p['regra'], p['texto'])
    return rel


def mascaras_plataformas(out: Path, f: Image.Image, t: float):
    """interface SIMULADA por plataforma sobre o styleframe (topo, base, coluna de ícones; recorte do feed tracejado)"""
    for nome in layout.CFG['ativos']:
        im = f.convert('RGBA').copy()
        ov = Image.new('RGBA', im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        for mk in layout.mascaras(nome):
            x, y, w, h = mk['caixa']
            if mk.get('aviso'):
                d.rectangle([x, y, x + w, y + h], outline=(255, 80, 80, 230), width=4)
            else:
                d.rectangle([x, y, x + w, y + h], fill=(255, 40, 120, 92), outline=(255, 40, 120, 220), width=3)
        im.alpha_composite(ov)
        ImageDraw.Draw(im).text((24, 24), nome.upper(), fill=(255, 255, 255, 255))
        im.convert('RGB').resize((405, 720), Image.LANCZOS).save(out / f'ui_{nome}_{t:05.2f}.png')


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
