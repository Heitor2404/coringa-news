"""Legendas × ÁUDIO REAL (sem IA): confere as marcas de tempo das palavras contra a voz gravada (voz.wav).

- atraso global: correlação entre "há palavra" (marcas) e "há fala" (energia do áudio, janelas de 10 ms), ±0,5 s;
- palavra no lugar: a fala precisa começar perto do início marcado (−80 ms … +200 ms);
- fala sem legenda: trecho de voz > 0,6 s sem palavra marcada (legenda atrasada/faltando);
- trocas bruscas: grupo de legenda (mesmo agrupamento da Camada: ≤ 4 palavras, páginas de 0,9 s) visível < 0,3 s.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np

PASSO = .01


def energia(wav: Path) -> np.ndarray:
    p = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(wav), '-ac', '1', '-ar', '16000', '-f', 's16le', '-'], capture_output=True, check=True)
    x = np.frombuffer(p.stdout, np.int16).astype(np.float32) / 32768
    n = int(16000 * PASSO)
    x = x[: len(x) // n * n].reshape(-1, n)
    return np.sqrt((x ** 2).mean(axis=1))


def mascara_fala(e: np.ndarray) -> np.ndarray:
    """fala = energia acima de ~0,6 % do pico (voz de TTS tem silêncio quase digital entre frases), buracos < 60 ms fechados"""
    # o ruído de fundo (p15) só eleva o limiar até 8 % do pico: narração densa (pouca pausa) não vira "silêncio" inteiro
    lim = max(e.max() * .006, min(np.percentile(e, 15) * 4, e.max() * .08))
    f = e > lim
    i = 0
    while i < len(f):
        if not f[i]:
            j = i
            while j < len(f) and not f[j]:
                j += 1
            if j - i < 6 and i > 0 and j < len(f):
                f[i:j] = True
            i = j
        i += 1
    return f


def pausas(f: np.ndarray, minimo: float = .15) -> list[tuple[float, float]]:
    out, i = [], 0
    while i < len(f):
        if not f[i]:
            j = i
            while j < len(f) and not f[j]:
                j += 1
            if (j - i) * PASSO >= minimo and i > 0 and j < len(f):
                out.append((i * PASSO, j * PASSO))
            i = j
        i += 1
    return out


def realinhar(palavras: list[dict], wav: Path) -> list[dict]:
    """corrige as marcas de tempo pela VOZ: cada pausa real (≥ 150 ms) vira âncora — a fronteira de palavra mais próxima
    passa a cair nela (fim da palavra anterior = início da pausa; início da seguinte = fim da pausa) — e o resto é
    reescalonado linearmente entre âncoras. Sem IA. Corrige o Whisper, que começa a palavra seguinte DENTRO da pausa."""
    f = mascara_fala(energia(wav))
    ps = pausas(f)
    if not palavras or not ps:
        return palavras
    palavras = [{**w, 'e': min(w['e'], palavras[i + 1]['s']) if i + 1 < len(palavras) else w['e']} for i, w in enumerate(palavras)]
    pts = [(0.0, 0.0)]
    j_ant = 0
    for a, b in ps:
        cand = [(abs(palavras[j]['s'] - (a + b) / 2), j) for j in range(max(1, j_ant + 1), len(palavras))
                if abs(palavras[j]['s'] - (a + b) / 2) <= .8 + (b - a) / 2]
        if not cand:
            continue
        _, j = min(cand)
        if palavras[j]['s'] <= pts[-1][0] + .05:
            continue
        pts.append((palavras[j]['s'] - 1e-3, a))
        pts.append((palavras[j]['s'], b))
        j_ant = j
    fim_m = max(w['e'] for w in palavras)
    pts.append((fim_m, max(fim_m, pts[-1][1] + (fim_m - pts[-1][0]))))
    xs = np.array([p[0] for p in pts]); ys = np.array([p[1] for p in pts])
    ordem = np.argsort(xs, kind='stable'); xs, ys = xs[ordem], np.maximum.accumulate(ys[ordem])
    mapa = lambda t: float(np.interp(t, xs, ys))
    out = []
    for w in palavras:
        s_, e_ = mapa(w['s']), mapa(w['e'])
        for a, b in ps:                  # nenhuma palavra atravessa uma pausa real: termina nela / começa depois dela
            if s_ < a + .02 < e_:
                e_ = a
            elif a <= s_ < b:
                s_ = b
        out.append({**w, 's': round(s_, 3), 'e': round(max(e_, s_ + .05), 3)})
    return out


def caixa_frase(palavras: list[dict], nomes: set[str], siglas: set[str], pausa_frase: float = .35) -> list[dict]:
    """palavras do TTS (MAIÚSCULAS, sem pontuação) → caixa de FRASE: maiúscula no início de frase (pausa real ≥ 0,35 s) e
    em nomes próprios/siglas que aparecem assim no próprio plano (fatos, rótulos, pinos, título)"""
    import unicodedata
    n = lambda w: unicodedata.normalize('NFKD', w).encode('ascii', 'ignore').decode().upper()
    proprios = {}
    for x in sorted(nomes, key=lambda w: sum(ord(ch) > 127 for ch in w)):   # a grafia COM acento vence (Panamá > Panama)
        proprios[n(x)] = x
    sig = {n(x): x for x in siglas}
    out = []
    for i, w in enumerate(palavras):
        k = n(w['w'])
        if k in sig:
            txt = sig[k]
        elif k in proprios:
            txt = proprios[k]
        else:
            txt = w['w'].lower()
            if i == 0 or w['s'] - palavras[i - 1]['e'] >= pausa_frase:
                txt = txt[:1].upper() + txt[1:]
        out.append({**w, 'w': txt})
    return out


def nomes_do_plano(pl: dict) -> tuple[set[str], set[str]]:
    """nomes próprios = palavras Capitalizadas no MEIO de frase nos textos do plano (fatos, título, rótulos do mapa, pinos),
    menos as que também aparecem em minúscula (ambíguas: 'canal'); siglas = MAIÚSCULAS de 2–5 letras dos FATOS e do
    título (rótulos de pílula são caixa-alta de desenho, não contam)"""
    import re
    fatos = [pl.get('titulo') or ''] + [f.get('texto', '') for f in (pl.get('narracao') or {}).get('fatos', []) if isinstance(f, dict)]
    mapa = [r.get('nome', '') for r in pl.get('rotulos') or []] + [d.get('nome_pt') or d.get('nome', '') for d in pl.get('destaques') or []]
    for b in pl.get('beats') or []:
        for L in b.get('camadas') or []:
            q = L.get('p') or {}
            if L.get('componente') == 'atlas.geoPin':
                mapa.append(str(q.get('rotulo') or ''))
    textos = fatos + mapa
    nomes, minus, siglas = set(), set(), set()
    for t in mapa:                       # rótulo de mapa/pino: nome próprio quando tem 2+ palavras capitalizadas ou é 1 palavra
        ws = re.findall(r"[\wÀ-ÿ]+", t)
        caps = [w for w in ws if w[:1].isupper() and w[1:].islower()]
        if len(caps) >= 2 or len(ws) == 1:
            nomes |= set(caps)
    for t in textos:
        for frase in re.split(r'[.!?;:]\s+', t):
            ws = re.findall(r"[\wÀ-ÿ]+", frase)
            for i, w in enumerate(ws):
                if w[:1].isupper() and w[1:].islower() and i > 0:
                    nomes.add(w)
                elif w.islower():
                    minus.add(w)
    for t in fatos:
        siglas |= {m for m in re.findall(r"\b([A-Z]{2,5})\b", t)}
    return {n for n in nomes if n.lower() not in minus}, siglas


def grupos(palavras: list[dict], maximo: int = 4, pausa: float = .25, dur_max: float = 1.6, dur_min: float = .35) -> list[dict]:
    """agrupamento da legenda (MESMA regra da Camada.tsx): quebra na pausa real, em 4 palavras ou 1,6 s; grupo curto
    demais (< 0,35 s, troca brusca) é fundido com o vizinho que ainda tem espaço"""
    gs, cur = [], []
    for w in palavras:
        if cur and (w['s'] - cur[-1]['e'] >= pausa or len(cur) >= maximo or w['e'] - cur[0]['s'] > dur_max):
            gs.append(cur); cur = []
        cur.append(w)
    if cur:
        gs.append(cur)
    mudou = True
    while mudou:
        mudou = False
        for i, g in enumerate(gs):
            if g[-1]['e'] - g[0]['s'] >= dur_min or len(gs) == 1:
                continue
            viz = [k for k in (i - 1, i + 1) if 0 <= k < len(gs) and len(gs[k]) + len(g) <= maximo + 1]
            if viz:
                k = min(viz, key=lambda k: abs((gs[k][0]['s'] if k > i else gs[k][-1]['e']) - (g[0]['s'] if k > i else g[-1]['e'])))
                gs[min(i, k)] = gs[min(i, k)] + gs[max(i, k)] if k > i else gs[k] + g
                del gs[max(i, k)]
                mudou = True
                break
    out = [{'ini': g[0]['s'] - .06, 'fim': g[-1]['e'] + .12, 'txt': ' '.join(x['w'] for x in g), 'n': len(g), 'i0': palavras.index(g[0])} for g in gs]
    for a_, b_ in zip(out, out[1:]):
        a_['fim'] = min(a_['fim'], b_['ini'])
    return out


def conferir(narracao: Path, wav: Path, maximo: int = 4) -> dict:
    meta = json.loads(Path(narracao).read_text())
    pal = meta['palavras']
    fala = mascara_fala(energia(wav))
    marc = np.zeros_like(fala)
    for w in pal:
        marc[int(w['s'] / PASSO): int(w['e'] / PASSO) + 1] = True
    n = min(len(fala), len(marc))
    f, m = fala[:n].astype(float) - fala[:n].mean(), marc[:n].astype(float) - marc[:n].mean()
    lags = range(-50, 51)
    corr = [float((f[max(0, L):n + min(0, L)] * m[max(0, -L):n - max(0, L)]).sum()) for L in lags]
    atraso = (list(lags)[int(np.argmax(corr))]) * PASSO          # > 0: a voz vem DEPOIS das marcas
    fora = []
    for w in pal:
        a, b = int((w['s'] - .08) / PASSO), int((w['s'] + .2) / PASSO)
        if b > a and not fala[max(0, a):b].any():
            fora.append({'w': w['w'], 's': round(w['s'], 2)})
    sem_leg, i = [], 0
    while i < n:
        if fala[i] and not marc[max(0, i - 15): i + 15].any():
            j = i
            while j < n and fala[j] and not marc[max(0, j - 15): j + 15].any():
                j += 1
            if (j - i) * PASSO > .6:
                sem_leg.append([round(i * PASSO, 2), round(j * PASSO, 2)])
            i = j
        i += 1
    gs = grupos(pal, maximo)
    flashes = [g for g in gs if g['fim'] - g['ini'] < .3]
    ok = abs(atraso) <= .1 and len(fora) <= max(1, .03 * len(pal)) and not sem_leg and not flashes
    return {'ok': ok, 'atraso_s': round(atraso, 2), 'palavras': len(pal), 'palavras_sem_fala': fora[:12], 'n_palavras_sem_fala': len(fora),
            'fala_sem_legenda': sem_leg, 'grupos': len(gs), 'trocas_bruscas': [{'txt': g['txt'], 'dur': round(g['fim'] - g['ini'], 2)} for g in flashes]}


if __name__ == '__main__':
    import sys
    print(json.dumps(conferir(Path(sys.argv[1]), Path(sys.argv[2])), ensure_ascii=False, indent=1))
