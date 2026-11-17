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
import re
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
CFG = json.loads((Path(__file__).with_name('formatos.json')).read_text(encoding='utf-8'))
SLOTS = CFG['slots']
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
    if isinstance(p.get('duracao'), str):
        p['duracao'] = a(p['duracao'])
    return p


def camadas(plano: dict) -> list[dict]:
    out = []
    for b in plano['beats']:
        for L in b['camadas']:
            out.append({**L, 'beat': b['id'], 'caixa': caixa(L)})
    return out


def caixa(L: dict) -> dict:
    if isinstance(L.get('caixa'), dict):
        return L['caixa']
    if L.get('caixa'):
        x, y, w, h = L['caixa']
    else:
        x, y, w, h = SLOTS[L['slot']]
    return {'x': x, 'y': y, 'w': w, 'h': h}


def _cruza(a: dict, b: dict) -> bool:
    return a['x'] < b['x'] + b['w'] and b['x'] < a['x'] + a['w'] and a['y'] < b['y'] + b['h'] and b['y'] < a['y'] + a['h']


def _largura(txt: str, px: float, peso: float = .72) -> float:
    return len(str(txt)) * px * peso


def fonte_nivel(w: float) -> int:
    """mesma regra do componente Hierarchy (Primitivas.tsx)"""
    return 22 if w > 150 else (18 if w > 110 else 16)


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
        if p.get('estilo') == 'pilula':
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
    for L in Ls:
        onde = f"{L['beat']}/{L['id']}"
        if L['componente'] not in F['componentes']:
            v('erro', 'F-COMPONENTE', onde, f"{L['componente']} não é do formato {plano['formato']}")
        if not L.get('caixa') and L.get('slot') not in SLOTS:
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
    # zonas fixas da identidade (marca no topo, faixa de legenda): nenhuma caixa entra nelas (colisão de 17/11)
    for L in Ls:
        for nome, (x, y, w, h) in CFG.get('zonas_identidade', {}).items():
            if _cruza(L['caixa'], {'x': x, 'y': y, 'w': w, 'h': h}):
                v('erro', 'F-ZONA-IDENTIDADE', f"{L['beat']}/{L['id']}", f'caixa cruza a zona da {nome}')
    # colisão: caixas de camadas simultâneas
    for i, a in enumerate(Ls):
        for b in Ls[i + 1:]:
            junto = a['t0'] < b['t1'] + SAI and b['t0'] < a['t1'] + SAI
            ok = (a['componente'] == 'dossie.evidenceHighlight' and (a.get('p') or {}).get('alvo') == b['id']) or \
                 (b['componente'] == 'dossie.evidenceHighlight' and (b.get('p') or {}).get('alvo') == a['id'])
            if junto and not ok and _cruza(a['caixa'], b['caixa']):
                v('erro', 'F-COLISAO', f"{a['id']}×{b['id']}", f"{a['slot'] or 'caixa'} e {b['slot'] or 'caixa'} ao mesmo tempo ({max(a['t0'], b['t0']):.1f}s)")
            if junto and (a.get('p') or {}).get('asset') and (a.get('p') or {}).get('asset') == (b.get('p') or {}).get('asset'):
                v('erro', 'F-MIDIA-DUPLICADA', f"{a['id']}×{b['id']}", 'a mesma mídia duas vezes no mesmo plano (ERR-055)')
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
        if L['componente'] == 'dossie.evidenceHighlight' and q.get('parte') and q.get('alvo') in por:
            alvo = por[q['alvo']]
            im = imagens.get((alvo.get('p') or {}).get('asset'))
            if im:
                L['caixa'] = {k: round(v, 1) for k, v in geom_documento(alvo, im)[q['parte']].items()}


def props(plano: dict, tokens: dict, geo: dict | None, imagens: dict) -> dict:
    furos = [{'t0': c['t0'], 't1': c['t1']} for c in plano.get('clipes') or []]
    Ls = camadas(plano)
    _mirar(Ls, imagens)
    return {'duracao': plano['duracao'], 'formato': plano['formato'], 'tokens': tokens, 'geo': geo, 'palco': plano['palco'],
            'destaques': plano.get('destaques') or [], 'rotas': plano.get('rotas') or [], 'rotulos': plano.get('rotulos') or [],
            'camadas': [{'id': L['id'], 'componente': L['componente'], 't0': L['t0'], 't1': L['t1'], 'caixa': L['caixa'], 'p': L.get('p') or {}}
                        for L in Ls], 'imagens': imagens, 'furos': furos}
