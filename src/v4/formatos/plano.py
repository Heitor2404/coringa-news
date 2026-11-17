"""PLANO DE FORMATO: beats → camadas em slots fixos sobre um palco persistente (ATLAS / DOSSIÊ).

Tudo determinístico e sem IA:
- `resolver_tempos`: tempos podem ser números (s) ou âncoras na fala ("@1880", "@comporta+0.3") resolvidas pelas
  palavras sincronizadas da narração — a revelação acompanha a palavra que a pede.
- `validar`: componente/slot/palco permitidos pelo formato; COLISÃO = caixas de camadas simultâneas que se cruzam
  (posições são fixas, então a geometria é verificável antes do render); texto que não cabe no slot; PROGRESSÃO
  informativa (nenhum intervalo > 4 s sem nova informação, sem contar legenda/marca); mesma mídia duas vezes ao mesmo
  tempo (ERR-055); mídia usada demais; número de componentes distintos (excesso de modalidades).
- `props`: entrega à composição Remotion `Formato`.
"""
from __future__ import annotations

import copy
import json
import math
import re
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
CFG = json.loads((Path(__file__).with_name('formatos.json')).read_text(encoding='utf-8'))
SLOTS = CFG['slots']
COMP = {k: v for k, v in CFG.get('composicoes', {}).items() if not k.startswith('_')}
RASTER_DIR = RAIZ / 'motor4' / 'formatos' / 'dados' / 'raster'
REGRAS = CFG['regras']
SAI = 0.3


def canal(nome: str = 'coringa') -> dict:
    return json.loads((Path(__file__).parent / 'canais' / f'{nome}.json').read_text(encoding='utf-8'))


def _norm(t: str) -> str:
    return ''.join(ch for ch in unicodedata.normalize('NFD', str(t).lower()) if unicodedata.category(ch) != 'Mn')


def ancora(valor, palavras: list[dict], depois: float = 0.0) -> float:
    """'@palavra' / '@palavra+0.4' / '@2:palavra' (2ª ocorrência) → início da palavra na narração"""
    if isinstance(valor, (int, float)):
        return float(valor)
    m = re.fullmatch(r'@(?:(\d+):)?([^+\-]+)([+\-]\d+(?:\.\d+)?)?', str(valor).strip())
    if not m:
        raise ValueError(f'tempo inválido {valor!r}')
    n, alvo, desl = int(m.group(1) or 1), _norm(m.group(2)), float(m.group(3) or 0)
    if alvo == 'fim':                                   # fim da fala (+ respiro): fecho de camadas e duração
        if not palavras:
            raise ValueError('âncora @fim sem narração')
        return round(palavras[-1]['e'] + .6 + desl, 3)
    achados = [w['s'] for w in palavras if _norm(w['w']).strip('.,!?:;') == alvo]
    if len(achados) < n:
        raise ValueError(f'âncora {valor!r}: palavra não está na narração')
    return round(achados[n - 1] + desl, 3)


def resolver_tempos(plano: dict, palavras: list[dict]) -> dict:
    p = copy.deepcopy(plano)
    a = lambda v: ancora(v, palavras)
    for k in p.get('palco') or []:
        k['t'] = a(k['t'])
    for lst in ('destaques', 'rotulos'):
        for x in p.get(lst) or []:
            x['t0'] = a(x['t0'])
            if x.get('t1') is not None:
                x['t1'] = a(x['t1'])
    for r in p.get('rotas') or []:
        r['t0'], r['t1'] = a(r['t0']), a(r['t1'])
        if r.get('some') is not None:
            r['some'] = a(r['some'])
    for c in p.get('clipes') or []:
        c['t0'], c['t1'] = a(c['t0']), a(c['t1'])
        c['params']['tempos'] = [round(a(x) - c['t0'], 2) for x in c['params'].get('tempos') or []]
    for b in p['beats']:
        if b.get('t') is not None:
            b['t'] = a(b['t'])
        for L in b['camadas']:
            L['t0'], L['t1'] = a(L['t0']), a(L['t1'])
            q = L.get('p') or {}
            for lista in ('marcos', 'nos', 'niveis', 'linhas', 'itens'):
                for x in q.get(lista) or []:
                    if isinstance(x, dict) and x.get('t') is not None:
                        x['t'] = a(x['t'])
            for at in q.get('ativo') or []:
                at['t0'] = a(at['t0'])
                if at.get('t1') is not None:
                    at['t1'] = a(at['t1'])
            if q.get('zoom'):
                q['zoom']['t0'] = a(q['zoom']['t0'])
            if q.get('legenda_t') is not None:
                q['legenda_t'] = a(q['legenda_t'])
            for k in ('t_marca', 't_total', 't_carimbo', 't_abre'):
                if q.get(k) is not None:
                    q[k] = a(q[k])
            if isinstance(q.get('carimbo'), dict) and q['carimbo'].get('t') is not None:
                q['carimbo']['t'] = a(q['carimbo']['t'])
            for lista in ('campos', 'marcas', 'etiquetas', 'ativos'):
                for x in q.get(lista) or []:
                    if isinstance(x, dict) and x.get('t') is not None:
                        x['t'] = a(x['t'])
    if isinstance(p.get('duracao'), str):
        p['duracao'] = a(p['duracao'])
    if p.get('camera') == 'roi':
        p['palco'] = palco_dos_beats(p)
    return p


# ---------------------------------------------------------------- câmera geográfica (mesma matemática do Palco.tsx)
def merc(lon: float, lat: float) -> tuple[float, float]:
    """Web Mercator normalizado 0–1 (MapLibre: mundo = 512·2^zoom px)"""
    s_ = math.sin(math.radians(max(-85.0, min(85.0, lat))))
    return (lon + 180) / 360, .5 - math.log((1 + s_) / (1 - s_)) / (4 * math.pi)


def camera_roi(roi, quadro, zmax: float | None = None, folga: float = .86) -> dict:
    """enquadra o território (roi = oeste, sul, leste, norte) DENTRO do quadro livre da composição"""
    o, s_, l, n = roi
    (x0, y0), (x1, y1) = merc(o, n), merc(l, s_)
    qx, qy, qw, qh = quadro
    z = math.log2(min(qw * folga / ((x1 - x0) * 512), qh * folga / ((y1 - y0) * 512)))
    if zmax is not None:
        z = min(z, zmax)
    fx, fy = (x0 + x1) / 2, (y0 + y1) / 2
    lon = fx * 360 - 180
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * fy))))
    return {'foco': [round(lon, 6), round(lat, 6)], 'ancora': [qx + qw / 2, qy + qh / 2], 'zoom': round(z, 3)}


def _ease(t: float) -> float:
    return 4 * t * t * t if t < .5 else 1 - (-2 * t + 2) ** 3 / 2


def _cam(c: dict) -> dict:
    if 'foco' in c:
        return c
    return {'foco': c['centro'], 'ancora': [540, 960], 'zoom': c['zoom']}


def camera_em(palco: list[dict], t: float) -> dict | None:
    """câmera no instante t: transição com pan ponderado pela escala (zoom-in pana cedo) + deriva lenta no beat"""
    ks = [k for k in palco if k.get('camera')]
    if not ks:
        return None
    a = ks[0]
    for k in ks:
        if t >= k['t']:
            a = k
    i = ks.index(a)
    ca, d = _cam(a['camera']), a.get('dur_camera', 1.2)
    if i > 0 and d > 0 and t < a['t'] + d:
        cb = _cam(ks[i - 1]['camera'])
        e = _ease(max(0., min(1., (t - a['t']) / d)))
        z = cb['zoom'] + (ca['zoom'] - cb['zoom']) * e
        u = e if abs(ca['zoom'] - cb['zoom']) < 1e-3 else (2 ** -cb['zoom'] - 2 ** -z) / (2 ** -cb['zoom'] - 2 ** -ca['zoom'])
        (bx, by), (ax, ay) = merc(*cb['foco']), merc(*ca['foco'])
        fx, fy = bx + (ax - bx) * u, by + (ay - by) * u
        anc = [cb['ancora'][0] + (ca['ancora'][0] - cb['ancora'][0]) * e, cb['ancora'][1] + (ca['ancora'][1] - cb['ancora'][1]) * e]
        return {'fx': fx, 'fy': fy, 'ancora': anc, 'zoom': z}
    fx, fy = merc(*ca['foco'])
    z = ca['zoom'] + a.get('deriva', 0) * max(0., t - a['t'] - max(0, d))
    return {'fx': fx, 'fy': fy, 'ancora': ca['ancora'], 'zoom': z}


def roi_tela(cam: dict, roi) -> dict:
    o, s_, l, n = roi
    ws = 512 * 2 ** cam['zoom']
    (x0, y0), (x1, y1) = merc(o, n), merc(l, s_)
    px = lambda x: cam['ancora'][0] + (x - cam['fx']) * ws
    py = lambda y: cam['ancora'][1] + (y - cam['fy']) * ws
    return {'x': px(x0), 'y': py(y0), 'w': px(x1) - px(x0), 'h': py(y1) - py(y0)}


def _creditos(plano: dict) -> dict | None:
    """créditos cartográficos (manifesto) e a faixa onde aparecem — separados das fontes factuais do roteiro"""
    if plano.get('formato') != 'atlas':
        return None
    from src.v4.formatos import atlas_ref
    z = zonas('atlas').get('creditos', [72, 1174, 936, 46])
    return {'datasets': {k: v['atribuicao_exigida'] for k, v in atlas_ref.datasets().items() if v.get('atribuicao_exigida')}, 'caixa': z}


def raster_info(nome: str) -> dict:
    m = json.loads((RASTER_DIR / f'{nome}.json').read_text(encoding='utf-8'))
    (o, n), (l, s_) = m['cantos'][0], m['cantos'][2]
    ppg = m.get('px_por_grau_fonte') or m['px'][0] / (l - o)   # resolução REAL da fonte (não a superamostrada)
    m['nitido_ate'] = round(math.log2(ppg * 360 / 512) + 1.0, 2)   # até 2× de ampliação ainda lê como relevo/imagem
    m['bbox'] = [o, s_, l, n]
    return m


def palco_dos_beats(p: dict) -> list[dict]:
    """cada beat → uma chave de palco: tipo da composição, câmera que enquadra o roi no quadro, véu da composição.
    Movimento medido na referência (atlas_ref.DERIVA): 'aproxima' (≈ +2,4 %/s enquanto camadas se revelam), 'fixo'
    (o dado muda, a câmera para) e 'recua' (fecho: começa mais perto e TERMINA no enquadramento do roi)."""
    from src.v4.formatos import atlas_ref
    beats = [b for b in p['beats'] if COMP.get(b.get('composicao') or '')]
    ini = [b.get('t', min((L['t0'] for L in b['camadas']), default=0.0)) for b in beats]
    out, ultima = [], None
    for i, b in enumerate(beats):
        c = COMP[b['composicao']]
        t = ini[i]
        fim = ini[i + 1] if i + 1 < len(beats) else p.get('duracao', t + 5)
        k = {'t': t, 'tipo': c['palco'], 'composicao': b['composicao'], 'veu': c.get('veu', 'nenhum')}
        if c['palco'] == 'mapa':
            k['dur_camera'] = b.get('transicao', 1.6)
            mov = b.get('movimento') or c.get('movimento') or 'fixo'
            k['movimento'] = mov
            k['deriva'] = b['deriva'] if b.get('deriva') is not None else atlas_ref.deriva(mov)
            if b.get('roi'):
                k['camera'] = camera_roi(b['roi'], c.get('quadro') or [0, 0, 1080, 1920], b.get('zoom_max'))
                if mov == 'recua':           # termina no enquadramento: começa |deriva|·duração mais perto
                    k['camera'] = {**k['camera'], 'zoom': round(k['camera']['zoom'] - k['deriva'] * max(0, fim - t - k['dur_camera']), 3)}
                if c.get('quadro'):
                    k['roi'] = b['roi']
            elif ultima:
                k['camera'] = ultima
            ultima = k.get('camera', ultima)
        out.append(k)
    if out:
        out[0]['t'] = 0.0
    return out


# ---------------------------------------------------------------- pinos geográficos (atlas.geoPin)
def zonas(formato: str) -> dict:
    z = {k: v for k, v in CFG.get('zonas_identidade', {}).items()}
    z.update({k: v for k, v in (CFG.get('zonas_por_formato', {}).get(formato) or {}).items() if not k.startswith('_')})
    return z


def projetar(cam: dict, lon: float, lat: float) -> tuple[float, float]:
    ws = 512 * 2 ** cam['zoom']
    x, y = merc(lon, lat)
    return cam['ancora'][0] + (x - cam['fx']) * ws, cam['ancora'][1] + (y - cam['fy']) * ws


def caixa_pino(q: dict, ax: float, ay: float) -> dict:
    """caixa ocupada por um pino ancorado em (ax, ay) — MESMA geometria de Primitivas.GeoPin"""
    if q.get('tipo') == 'foto':
        r = q.get('raio', 112)
        dx, dy = q.get('desloc', [0, -190])
        cx, cy = ax + dx, ay + dy
        lw = max(2 * r, _largura(q.get('rotulo', ''), 30, .66) + 40)
        return {'x': cx - lw / 2, 'y': cy - r - 6, 'w': lw, 'h': 2 * r + 12 + 60 + (26 if q.get('meta') else 0)}
    lw = _largura(q.get('rotulo', ''), 30, .66) + 44
    lado = q.get('lado', 'direita')
    return {'x': ax + 26 if lado == 'direita' else ax - 26 - lw, 'y': ay - 28, 'w': lw, 'h': 56}


def pinos_em(plano: dict, Ls: list[dict], t: float) -> dict[str, dict]:
    cam = camera_em(plano.get('palco') or [], t)
    out = {}
    if not cam:
        return out
    for L in Ls:
        if L['componente'] == 'atlas.geoPin' and L['t0'] <= t <= L['t1'] + SAI:
            q = L.get('p') or {}
            ax, ay = projetar(cam, *q['lonlat'])
            out[L['id']] = {**caixa_pino(q, ax, ay), 'ancora': (ax, ay)}
    return out


def camadas(plano: dict) -> list[dict]:
    out = []
    for b in plano['beats']:
        for L in b['camadas']:
            if L.get('componente') == 'atlas.geoPin':     # ancorado no território: caixa calculada pela câmera (pinos_em)
                out.append({**L, 'beat': b['id'], 'composicao': b.get('composicao'), 'caixa': {'x': -9e3, 'y': -9e3, 'w': 0, 'h': 0}, 'dinamica': True})
                continue
            out.append({**L, 'beat': b['id'], 'composicao': b.get('composicao'), 'caixa': caixa(L, b.get('composicao'))})
    return out


def caixa(L: dict, comp: str | None = None) -> dict:
    if isinstance(L.get('caixa'), dict):
        return L['caixa']
    if L.get('caixa'):
        x, y, w, h = L['caixa']
    elif comp and L.get('slot') in (COMP.get(comp) or {}).get('slots', {}):
        x, y, w, h = COMP[comp]['slots'][L['slot']]
    else:
        x, y, w, h = SLOTS[L['slot']]
    return {'x': x, 'y': y, 'w': w, 'h': h}


def _cruza(a: dict, b: dict) -> bool:
    return a['x'] < b['x'] + b['w'] and b['x'] < a['x'] + a['w'] and a['y'] < b['y'] + b['h'] and b['y'] < a['y'] + a['h']


def _largura(txt: str, px: float, peso: float = .72) -> float:
    return len(str(txt)) * px * peso


def fonte_nivel(w: float) -> int:
    """mesma regra do componente Hierarchy (Primitivas.tsx)"""
    return 26 if w > 150 else (22 if w > 110 else 20)


def _cabe(L: dict) -> list[str]:
    """estimativa conservadora de largura (Montserrat 900 em caixa alta ≈ 0,72 em; JetBrains Mono ≈ 0,6 em)"""
    p, b, c, out = L.get('p') or {}, caixa(L), L['componente'], []
    if c == 'editorial.titleOrPayoff':
        if len(p.get('linhas') or []) > REGRAS['titulo_max_linhas']:
            out.append(f"título com {len(p['linhas'])} linhas (máx. {REGRAS['titulo_max_linhas']}): vira slide")
        for l in p.get('linhas') or []:
            if _largura(l['texto'], l.get('tamanho', 104)) > b['w']:
                out.append(f"título {l['texto']!r} não cabe em {b['w']} px a {l.get('tamanho', 104)} px")
    elif c == 'editorial.statCard':
        txt = f"{p.get('prefixo', '')}{p.get('valor')}"
        if p.get('estilo') == 'dial':        # número à direita do meio-círculo (Primitivas.Dial)
            R = min(b['h'] - 120, b['w'] * .48)
            livre = b['w'] - (40 + 2 * R + 30) - 34
            if _largura(txt, 92, .7) > livre or _largura(p.get('unidade', ''), 34, .7) > livre:
                out.append(f'número {txt!r} {p.get("unidade", "")!r} não cabe ao lado do mostrador ({livre:.0f} px)')
            for x in p.get('partes') or []:
                if _largura(x['rotulo'], 26, .62) + 28 > livre:
                    out.append(f"legenda {x['rotulo']!r} não cabe ao lado do mostrador")
        elif p.get('estilo') in ('calendario', 'ficha'):
            pass
        elif p.get('estilo') == 'pilula':
            tot = _largura(txt, 40, .62) + _largura(f" {p.get('unidade', '')}", 40) + _largura(f" · {p.get('rotulo', '')}" if p.get('rotulo') else '', 40, .66) + 60
            if tot > b['w']:
                out.append(f'pílula {txt} {p.get("rotulo", "")!r} não cabe ({tot:.0f} > {b["w"]} px)')
        else:
            px = 150 if p.get('grande') else 112
            if _largura(txt, px, .7) + _largura(p.get('unidade', ''), px * .45) + 90 > b['w']:
                out.append(f'número {txt!r} não cabe no cartão')
            if p.get('rotulo') and _largura(p['rotulo'], 34) > 2 * (b['w'] - 90):
                out.append(f"rótulo {p['rotulo']!r} longo demais (> 2 linhas)")
    elif c == 'editorial.hierarchy':
        n = len(p.get('niveis') or [])
        w = (b['w'] - 10 * (n - 1)) / max(1, n)
        if p.get('rotulos_abaixo') is not False and n > 5:     # nomes embaixo em 2 fileiras, corpo 26 (Primitivas.Hierarchy)
            for nv in p.get('niveis') or []:
                if _largura(nv['rotulo'], 26, .62) > 220:
                    out.append(f"nível {nv['rotulo']!r} não cabe em 220 px a 26 px")
            return out
        for nv in p.get('niveis') or []:
            if max((_largura(x, fonte_nivel(w), .62) for x in str(nv['rotulo']).split()), default=0) > w - 8:
                out.append(f"nível {nv['rotulo']!r} não cabe em {w:.0f} px")
    elif c == 'editorial.timeline':
        for m in p.get('marcos') or []:
            if _largura(m['texto'], 28) > 2 * 300:
                out.append(f"marco {m['texto']!r} longo demais")
    elif c == 'editorial.flowConnections':
        for no in p.get('nos') or []:
            if _largura(no['rotulo'], 38) > (p.get('largura') or 640) - 30:
                out.append(f"nó {no['rotulo']!r} não cabe")
    return out


def _passos(a: float, b: float, d: float):
    x = a
    while x < b:
        yield round(x, 3)
        x += d


def eventos(plano: dict) -> list[float]:
    """instantes em que surge informação NOVA no conteúdo (nunca legenda/marca)"""
    ev = [k['t'] for k in plano.get('palco') or []]
    ev += [x['t0'] for x in plano.get('destaques') or []] + [x['t0'] for x in plano.get('rotulos') or []]
    for r in plano.get('rotas') or []:
        ev += [r['t0'], (r['t0'] + r['t1']) / 2, r['t1']]
    for c in plano.get('clipes') or []:
        # clipe aprovado com animação contínua (o portão CONGELADO confere no render): progride o tempo todo
        ev += [c['t0'] + x for x in c['params'].get('tempos') or []] + [c['t0']] + list(_passos(c['t0'], c['t1'], 1.0))
    for L in camadas(plano):
        ev.append(L['t0'])
        q = L.get('p') or {}
        for lista in ('marcos', 'nos', 'niveis', 'linhas', 'itens'):
            ev += [x['t'] for x in q.get(lista) or [] if isinstance(x, dict) and x.get('t') is not None]
        ev += [a['t0'] for a in q.get('ativo') or []]
        if q.get('zoom'):
            ev.append(q['zoom']['t0'])
        if q.get('legenda_base') and q.get('legenda_t') is not None:
            ev.append(q['legenda_t'])
        if q.get('contagem'):
            ev.append(L['t0'] + (q.get('dur_contagem') or 1.2))
        ev += [q[k] for k in ('t_marca', 't_total', 't_carimbo', 't_abre') if isinstance(q.get(k), (int, float))]
        if isinstance(q.get('carimbo'), dict) and isinstance(q['carimbo'].get('t'), (int, float)):
            ev.append(q['carimbo']['t'])
        for lista in ('campos', 'ativos'):
            ev += [x['t'] for x in q.get(lista) or [] if isinstance(x, dict) and isinstance(x.get('t'), (int, float))]
    return sorted(ev)


def validar(plano: dict, imagens: dict | None = None) -> list[dict]:
    """plano com tempos JÁ resolvidos → [{gravidade, regra, onde, texto}]"""
    out = []
    v = lambda g, r, o, t: out.append({'gravidade': g, 'regra': r, 'onde': o, 'texto': t})
    F = CFG['formatos'].get(plano.get('formato'))
    if not F:
        return [{'gravidade': 'erro', 'regra': 'F-FORMATO', 'onde': '-', 'texto': f"formato desconhecido {plano.get('formato')!r}"}]
    dur = float(plano['duracao'])
    for k in plano.get('palco') or []:
        if k['tipo'] not in F['palcos']:
            v('erro', 'F-PALCO', f"t={k['t']}", f"palco {k['tipo']} fora do formato {plano['formato']}")
    if not plano.get('palco') or plano['palco'][0]['t'] > 0:
        v('erro', 'F-PALCO', 't=0', 'o palco precisa existir desde o primeiro quadro')
    Ls = camadas(plano)
    if imagens:
        _mirar(Ls, imagens)
    for L in Ls:
        onde = f"{L['beat']}/{L['id']}"
        if L['componente'] not in F['componentes']:
            v('erro', 'F-COMPONENTE', onde, f"{L['componente']} não é do formato {plano['formato']}")
        comp = COMP.get(L.get('composicao') or '')
        if L.get('composicao') and not comp:
            v('erro', 'F-COMPOSICAO', onde, f"composição {L['composicao']!r} desconhecida")
        elif L.get('dinamica'):
            if comp and not comp.get('pinos'):
                v('erro', 'F-COMPOSICAO', onde, f"{L['composicao']} não aceita pinos geográficos")
            if not (L.get('p') or {}).get('lonlat'):
                v('erro', 'F-PINO', onde, 'pino sem coordenada (lonlat)')
        elif comp and not (L.get('slot') in comp['slots'] or L.get('caixa_livre')):
            v('erro', 'F-SLOT', onde, f"slot {L.get('slot')!r} não existe na composição {L['composicao']} ({', '.join(comp['slots'])})")
        elif not comp and L.get('slot') not in SLOTS and not isinstance(L.get('caixa'), (list, dict)):
            v('erro', 'F-SLOT', onde, f"slot {L.get('slot')!r} desconhecido")
        if not (0 <= L['t0'] < L['t1'] <= dur + .01):
            v('erro', 'F-TEMPO', onde, f"tempo {L['t0']}–{L['t1']} fora de 0–{dur}")
        for f in _cabe(L):
            v('erro', 'F-TEXTO-NAO-CABE', onde, f)
        a = (L.get('p') or {}).get('asset')
        if a and imagens is not None and a not in imagens:
            v('erro', 'F-ASSET', onde, f'mídia {a!r} indisponível')
    for c in plano.get('clipes') or []:
        if c['componente'] not in F['clipes']:
            v('erro', 'F-CLIPE', f"{c['t0']}", f"clipe {c['componente']} não aprovado no formato")
    # composições: formato, palco, máximo de camadas simultâneas, reconstrução identificada
    for b in plano['beats']:
        comp = COMP.get(b.get('composicao') or '')
        if not comp:
            if plano.get('camera') == 'roi':
                v('erro', 'F-COMPOSICAO', b['id'], 'beat sem composição num plano de câmera automática')
            continue
        if comp['formato'] != plano['formato']:
            v('erro', 'F-COMPOSICAO', b['id'], f"{b['composicao']} é do formato {comp['formato']}")
        if comp['palco'] == 'mapa' and comp.get('quadro') and not b.get('roi'):
            v('erro', 'F-COMPOSICAO', b['id'], f"{b['composicao']} enquadra um território: falta roi (oeste, sul, leste, norte)")
        Lb = [L for L in Ls if L['beat'] == b['id'] and L['componente'] not in ('dossie.evidenceHighlight', 'atlas.geoPin')]
        for L in Lb:
            junto = sum(1 for M in Lb if M['t0'] < L['t1'] and L['t0'] < M['t1'])
            if junto > comp.get('max_camadas', 9):
                v('erro', 'F-COMPOSICAO', f"{b['id']}/{L['id']}", f"{junto} camadas ao mesmo tempo (máx. {comp['max_camadas']} em {b['composicao']}): vira slide")
                break
    for L in Ls:
        q = L.get('p') or {}
        if q.get('estilo') in ('calendario', 'ficha', 'regua') and not str(q.get('reconstrucao') or '').strip():
            v('erro', 'F-RECONSTRUCAO', f"{L['beat']}/{L['id']}", f"{q['estilo']} é reconstrução editorial: precisa do rótulo 'reconstrucao' visível (nunca passa por arquivo histórico)")
    # território: a câmera enquadra o roi no quadro e NENHUMA camada do beat o cobre (início e fim do beat, com a deriva)
    if plano.get('camera') == 'roi':
        ks = plano.get('palco') or []
        tempos_b = {}
        for k, b in zip([k for k in ks], [b for b in plano['beats'] if COMP.get(b.get('composicao') or '')]):
            tempos_b[b['id']] = k['t']
        fins = {}
        ids = list(tempos_b)
        for i, bid in enumerate(ids):
            fins[bid] = tempos_b[ids[i + 1]] if i + 1 < len(ids) else dur
        rasters = [raster_info(r['nome']) for r in plano.get('rasters') or []]
        for b in plano['beats']:
            comp = COMP.get(b.get('composicao') or '')
            if not comp or comp['palco'] != 'mapa' or not b.get('roi') or not comp.get('quadro'):
                continue
            t0 = tempos_b[b['id']] + next((k.get('dur_camera', 0) for k in ks if k['t'] == tempos_b[b['id']]), 0)
            qx, qy, qw, qh = comp['quadro']
            recua = next((k.get('movimento') for k in ks if k['t'] == tempos_b[b['id']]), None) == 'recua'
            # recuo: começa por dentro do território e TERMINA nele inteiro — confere o fim
            for t in ((fins[b['id']] - .05,) if recua else (min(t0, fins[b['id']]), fins[b['id']] - .05)):
                cam = camera_em(ks, t)
                r = roi_tela(cam, b['roi'])
                if r['x'] < qx - 8 or r['y'] < qy - 8 or r['x'] + r['w'] > qx + qw + 8 or r['y'] + r['h'] > qy + qh + 8:
                    v('erro', 'F-COBRE-TERRITORIO', b['id'], f"território sai do quadro livre em {t:.1f}s ({r['x']:.0f},{r['y']:.0f},{r['w']:.0f}×{r['h']:.0f})")
                for L in Ls:
                    if L['beat'] == b['id'] and not L.get('dinamica') and L['t0'] <= t <= L['t1'] + SAI and _cruza(L['caixa'], r):
                        v('erro', 'F-COBRE-TERRITORIO', f"{b['id']}/{L['id']}", f"camada cobre o território explicado em {t:.1f}s")
                if rasters:
                    ok = [ri for ri in rasters if ri['bbox'][0] <= b['roi'][0] and ri['bbox'][1] <= b['roi'][1] and ri['bbox'][2] >= b['roi'][2]
                          and ri['bbox'][3] >= b['roi'][3] and ri['nitido_ate'] >= cam['zoom']]
                    if not ok:
                        v('erro', 'F-MAPA-BAIXA-RESOLUCAO', b['id'], f"zoom {cam['zoom']:.2f} sem raster nítido que cubra o território (mapa de baixa qualidade)")
    # zonas fixas da identidade (marca no topo, faixa de legenda): nenhuma caixa entra nelas (colisão de 17/11)
    ZN = zonas(plano['formato'])
    for L in Ls:
        for nome, (x, y, w, h) in ZN.items():
            if _cruza(L['caixa'], {'x': x, 'y': y, 'w': w, 'h': h}):
                v('erro', 'F-ZONA-IDENTIDADE', f"{L['beat']}/{L['id']}", f'caixa cruza a zona da {nome}')
    # colisão: caixas de camadas simultâneas
    for i, a in enumerate(Ls):
        for b in Ls[i + 1:]:
            # mesma cena: conta a saída (0,3 s); troca de beat: a saída de um sob a entrada do outro é o dissolve da transição
            folga = SAI if a['beat'] == b['beat'] else -.02
            junto = a['t0'] < b['t1'] + folga and b['t0'] < a['t1'] + folga
            ev_a, ev_b = a['componente'] == 'dossie.evidenceHighlight', b['componente'] == 'dossie.evidenceHighlight'
            alvo_a, alvo_b = (a.get('p') or {}).get('alvo'), (b.get('p') or {}).get('alvo')
            ok = (ev_a and alvo_a == b['id']) or (ev_b and alvo_b == a['id']) or (ev_a and ev_b and alvo_a == alvo_b)
            if junto and not ok and not (a.get('dinamica') or b.get('dinamica')) and _cruza(a['caixa'], b['caixa']):
                v('erro', 'F-COLISAO', f"{a['id']}×{b['id']}", f"{a['slot'] or 'caixa'} e {b['slot'] or 'caixa'} ao mesmo tempo ({max(a['t0'], b['t0']):.1f}s)")
            if junto and (a.get('p') or {}).get('asset') and (a.get('p') or {}).get('asset') == (b.get('p') or {}).get('asset'):
                v('erro', 'F-MIDIA-DUPLICADA', f"{a['id']}×{b['id']}", 'a mesma mídia duas vezes no mesmo plano (ERR-055)')
    # pinos geográficos: seguem a câmera; a cada 0,25 s conferem âncora no quadro, colisão e zonas
    if any(L.get('dinamica') for L in Ls) and plano.get('palco'):
        vistos = set()
        ks = plano['palco']
        for i in range(int(dur / .25) + 1):
            t = i * .25
            pins = pinos_em(plano, Ls, t)
            if not pins:
                continue
            k = ks[0]
            for kk in ks:
                if t >= kk['t']:
                    k = kk
            qd = (COMP.get(k.get('composicao') or '') or {}).get('quadro')
            ativos = [L for L in Ls if not L.get('dinamica') and L['t0'] <= t <= L['t1'] + SAI]
            for pid, bx in pins.items():
                ax, ay = bx['ancora']
                if qd and not (qd[0] - 40 <= ax <= qd[0] + qd[2] + 40 and qd[1] - 40 <= ay <= qd[1] + qd[3] + 40) and (pid, 'fora') not in vistos:
                    vistos.add((pid, 'fora'))
                    v('erro', 'F-PINO-FORA', pid, f'âncora fora do território enquadrado em {t:.2f}s ({ax:.0f},{ay:.0f})')
                if (bx['x'] < 20 or bx['x'] + bx['w'] > 1060 or bx['y'] < 336) and (pid, 'tela') not in vistos:
                    vistos.add((pid, 'tela'))
                    v('erro', 'F-PINO-FORA', pid, f'pino sai da área útil em {t:.2f}s')
                for L in ativos:
                    if _cruza(bx, L['caixa']) and (pid, L['id']) not in vistos:
                        vistos.add((pid, L['id']))
                        v('erro', 'F-COLISAO', f"{pid}×{L['id']}", f'pino sob/sobre camada em {t:.2f}s')
                for nome, (x, y, w, h) in ZN.items():
                    if _cruza(bx, {'x': x, 'y': y, 'w': w, 'h': h}) and (pid, nome) not in vistos:
                        vistos.add((pid, nome))
                        v('erro', 'F-ZONA-IDENTIDADE', pid, f'pino invade a {nome} em {t:.2f}s')
                for qid, by in pins.items():
                    if qid > pid and _cruza(bx, by) and (pid, qid) not in vistos:
                        vistos.add((pid, qid))
                        v('erro', 'F-COLISAO', f'{pid}×{qid}', f'pinos sobrepostos em {t:.2f}s')
    usos = {}
    for L in Ls:
        a = (L.get('p') or {}).get('asset')
        if a:
            usos[a] = usos.get(a, 0) + 1
    for a, n in usos.items():
        if n > REGRAS['asset_max_usos']:
            v('erro', 'F-MIDIA-REPETIDA', a, f'mídia usada {n}× (máx. {REGRAS["asset_max_usos"]})')
    distintos = {L['componente'] for L in Ls} | {c['componente'] for c in plano.get('clipes') or []}
    if len(distintos) > F['max_componentes_distintos']:
        v('erro', 'F-EXCESSO-MODALIDADES', '-', f"{len(distintos)} componentes distintos (máx. {F['max_componentes_distintos']}): vitrine de ferramentas")
    # progressão informativa: furos (clipes) contam com os próprios eventos
    ev = [e for e in eventos(plano) if 0 <= e <= dur] + [dur]
    ev = sorted(set([0.0] + ev))
    for x, y in zip(ev, ev[1:]):
        if y - x > REGRAS['progressao_max_s']:
            v('erro', 'F-SEM-PROGRESSAO', f'{x:.1f}–{y:.1f}s', f'{y - x:.1f} s sem informação nova no conteúdo')
    # rota prometida exige geometria
    if plano.get('rotas') and not plano.get('geo'):
        v('erro', 'F-ROTA-SEM-GEOMETRIA', '-', 'rota sem arquivo de geometria')
    return out


def geom_documento(L: dict, im: dict) -> dict:
    """mesmas contas do DocumentCard (Primitivas.tsx): retângulos do cartão, da foto e do texto à direita do cabeçalho"""
    b, p = caixa(L), L.get('p') or {}
    cab, rod = (52 if p.get('cabecalho') else 0), 22 + len(p.get('meta') or []) * 36
    esc = min((b['w'] - 36) / im['w'], (b['h'] - cab - rod - 36) / im['h'])
    fw, fh = im['w'] * esc, im['h'] * esc
    x0, y0 = b['x'] + (b['w'] - fw - 36) / 2, b['y'] + (b['h'] - fh - cab - rod - 36) / 2
    dw = len(str(p.get('cabecalho_dir') or '')) * 22 * .62 + 8
    return {'cartao': {'x': x0, 'y': y0, 'w': fw + 36, 'h': fh + cab + rod + 36},
            'foto': {'x': x0 + 18, 'y': y0 + 18 + cab + (12 if cab else 0), 'w': fw, 'h': fh},
            'cabecalho_dir': {'x': x0 + 18 + fw - dw, 'y': y0 + 18 + 6, 'w': dw, 'h': cab - 12}}


def _mirar(Ls: list[dict], imagens: dict) -> None:
    por = {L['id']: L for L in Ls}
    for L in Ls:
        q = L.get('p') or {}
        if L['componente'] == 'dossie.evidenceHighlight' and (q.get('parte') or q.get('regiao')) and q.get('alvo') in por:
            alvo = por[q['alvo']]
            im = imagens.get((alvo.get('p') or {}).get('asset'))
            if im:
                g = geom_documento(alvo, im)
                if q.get('regiao'):              # região da PRÓPRIA imagem (frações 0–1): marca exatamente o trecho citado
                    f, (a0, b0, a1, b1) = g['foto'], q['regiao']
                    L['caixa'] = {'x': round(f['x'] + a0 * f['w'], 1), 'y': round(f['y'] + b0 * f['h'], 1),
                                  'w': round((a1 - a0) * f['w'], 1), 'h': round((b1 - b0) * f['h'], 1)}
                else:
                    L['caixa'] = {k: round(v, 1) for k, v in g[q['parte']].items()}


def props(plano: dict, tokens: dict, geo: dict | None, imagens: dict) -> dict:
    furos = [{'t0': c['t0'], 't1': c['t1']} for c in plano.get('clipes') or []]
    Ls = camadas(plano)
    _mirar(Ls, imagens)
    rasters = []
    for r in plano.get('rasters') or []:
        m = raster_info(r['nome'])
        rasters.append({'dataset': m.get('dataset'), 'nome': r['nome'], 'src': f"_formato/raster/{m.get('arquivo') or r['nome'] + '.jpg'}", 'cantos': m['cantos'], 'de': r.get('de'), 'ate': r.get('ate'),
                        'atribuicao': m['atribuicao'], 'tipo': m.get('tipo', 'fisico'), 'ajuste': r.get('ajuste') or {}})
    return {'duracao': plano['duracao'], 'formato': plano['formato'], 'tokens': tokens, 'geo': geo, 'palco': plano['palco'], 'rasters': rasters,
            'composicoes': {k: {'quadro': v.get('quadro'), 'veu': v.get('veu')} for k, v in COMP.items()},
            'creditos': _creditos(plano), 'tecnico': plano.get('tecnico') or {},
            'destaques': plano.get('destaques') or [], 'rotas': plano.get('rotas') or [], 'rotulos': plano.get('rotulos') or [],
            'camadas': [{'id': L['id'], 'componente': L['componente'], 't0': L['t0'], 't1': L['t1'], 'caixa': L['caixa'], 'p': L.get('p') or {}}
                        for L in Ls], 'imagens': imagens, 'furos': furos}
