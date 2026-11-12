"""VERIFICADOR DE EVENTOS do NTC (Fase 4, CP2 — 12/11/2026). Só avalia: não muda o vídeo.

Responde, ANTES de renderizar: o motor consegue MOSTRAR o que a narração conta?
- Cada acontecimento vira (verbo, alvo) e recebe um nível pelo catálogo canais/ntc/vetor/capacidades.json:
  A direto · B substituto declarado · C simbólico (painel) · D impossível hoje.
- E um status de EXECUÇÃO: "mostrado" (possível e o roteiro pediu), "possível, não pedido", "impossível".
- Não dá para burlar trocando o papel da cena: os acontecimentos são tirados TAMBÉM da própria narração (todas as cenas,
  qualquer papel) e a importância é calculada pelo código (só pode subir em relação ao que o roteiro declarou).
- Evento CENTRAL impossível ou nunca mostrado gera alerta próprio.
Nada aqui conhece tema, bicho ou personagem: tudo vem do catálogo (dado) e de regras gerais.
"""
import json
import re
import unicodedata
from pathlib import Path

CATALOGO = Path(__file__).resolve().parents[1] / 'canais' / 'ntc' / 'vetor' / 'capacidades.json'
ORDEM_IMP = {'detalhe': 0, 'apoio': 1, 'central': 2}
PAPEIS = ('acao', 'reacao', 'consequencia', 'contexto', 'indicio')
PAPEIS_QUE_MOSTRAM = ('acao', 'consequencia', 'indicio')


def norm(s: str) -> str:
    s = unicodedata.normalize('NFD', str(s or '').lower())
    return ''.join(ch for ch in s if not unicodedata.combining(ch))


def catalogo() -> dict:
    return json.loads(CATALOGO.read_text(encoding='utf-8'))


# ───────────────────────── identificar o alvo ─────────────────────────
def _indice(cat: dict) -> dict:
    """palavra → (tipo, chave, nivel_base, motivo). tipo: 'objeto' (A), 'substituto' (B), 'classe' (sem objeto)."""
    ix = {}
    for nome, o in cat['objetos'].items():
        for w in o.get('palavras', []):
            ix[w] = ('objeto', nome, 'A', '')
        for w in o.get('substitui', []):
            ix.setdefault(w, ('substituto', nome, 'B', o.get('motivo_substituto', '')))
    for nome, c in cat['classes_sem_objeto'].items():
        if nome.startswith('_'):
            continue
        for w in c.get('palavras', []):
            ix.setdefault(w, ('classe', nome, 'D', c.get('motivo', '')))
    return ix


def resolver_alvo(texto: str, cat: dict | None = None) -> dict | None:
    """'a porta do armário' → {'tipo','chave','nivel','motivo','palavra'} usando a 1ª palavra conhecida."""
    cat = cat or catalogo()
    ix = _indice(cat)
    for w in re.findall(r'[a-z]+', norm(texto)):
        if w in ix:
            t, k, n, m = ix[w]
            return {'tipo': t, 'chave': k, 'nivel': n, 'motivo': m, 'palavra': w}
    return None


# ───────────────────────── nível A–D de (verbo, alvo) ─────────────────────────
def nivel(verbo: str, alvo: dict | None, cat: dict | None = None) -> tuple[str, str]:
    cat = cat or catalogo()
    vb = cat['verbos'].get(verbo) or {}
    if alvo is None:
        sub = vb.get('substituto')
        if sub:
            return sub['nivel'], f"{sub['objeto']}: {sub['motivo']}"
        return 'D', 'não identifiquei o que sofre a ação'
    if alvo['tipo'] in ('objeto', 'substituto'):
        classe = cat['objetos'][alvo['chave']]['classe']
        if vb.get('requer') == 'estado':
            return 'D', f"'{verbo}' precisa de troca de estado (inteiro → danificado → destruído), que ainda não existe"
        if vb.get('classes') and classe not in vb['classes']:
            return 'D', f"'{verbo}' não se aplica à classe {classe}"
        return (alvo['nivel'], alvo['motivo'] or f"{alvo['chave']} com animação '{vb.get('anim', verbo)}'")
    # classe sem objeto na biblioteca
    classe = alvo['chave']
    info = cat['classes_sem_objeto'].get(classe, {})
    if classe == 'quantidade' and vb.get('painel') or (classe == 'quantidade' and verbo in ('aparece', 'some')):
        return 'C', 'número no painel/contador (simbólico)'
    if verbo == 'indicio' and vb.get('substituto'):
        sub = vb['substituto']
        return sub['nivel'], f"{sub['objeto']}: {sub['motivo']}"
    if info.get('cenario_fixo') and verbo == 'aparece':
        return 'B', 'existe desenhado no cenário, sem animação própria'
    return 'D', info.get('motivo') or 'não há peça para isso'


# ───────────────────────── acontecimentos contados na narração ─────────────────────────
def eventos_narrados(narracao: str, cat: dict | None = None) -> list[dict]:
    """Acha verbos de mudança (catálogo) e o alvo mais próximo na mesma frase. Heurística, sem IA: o que ela não pega,
    o roteiro novo declara em 'evento'."""
    cat = cat or catalogo()
    ix = _indice(cat)
    out = []
    frases = [' '.join(re.findall(r'[a-z]+', f)) for f in re.split(r'[.!?…]+', norm(narracao))]
    frases = [f for f in frases if f]
    ignorar = [norm(x) for x in (cat.get('expressoes_ignoradas') or {}).get('lista', [])]
    for fi, txt in enumerate(frases):
        for exp in ignorar:                                   # "caiu na real" não é queda de nada
            txt = re.sub(r'\b' + re.escape(exp) + r'\b', ' ', txt)
        toks = txt.split()
        if not toks:
            continue
        txt = ' '.join(toks)
        vistos = set()
        for verbo, vb in cat['verbos'].items():
            if verbo.startswith('_'):
                continue
            for p in sorted(vb.get('palavras', []), key=lambda x: -len(x)):
                m = re.search(r'\b' + re.escape(p) + r'\b', txt)
                if not m or (verbo, m.start()) in vistos:
                    continue
                vistos.add((verbo, m.start()))
                pos = len(txt[:m.start()].split())
                # alvo = palavra conhecida mais perto do verbo; "sem X" é ausência, não alvo
                proibidos = {norm(x) for x in vb.get('nao_alvo', [])}   # o agente ("fogo queimou") não é o alvo
                cands = [(abs(i - pos) + (0 if i < pos else 0.5), w) for i, w in enumerate(toks)
                         if w in ix and w not in proibidos and not (i > 0 and toks[i - 1] == 'sem')]
                if not cands and fi + 1 < len(frases):          # "Quem apareceu? Os cupins": o alvo vem na frase seguinte
                    cands = [(10 + i, w) for i, w in enumerate(frases[fi + 1].split()) if w in ix]
                antes = ' ' + ' '.join(toks[max(0, pos - 3):pos]) + ' '      # sujeito logo antes do verbo
                if not cands and any(f' {norm(x)} ' in antes for x in (cat.get('sujeitos_personagem') or {}).get('lista', [])):
                    break                                       # "a personagem saiu correndo": é ela, não um acontecimento
                alvo = None
                if cands:
                    w = min(cands)[1]
                    t, k, n, mo = ix[w]
                    alvo = {'tipo': t, 'chave': k, 'nivel': n, 'motivo': mo, 'palavra': w}
                out.append({'verbo': verbo, 'alvo': alvo, 'trecho': p, 'origem': 'narracao'})
                break
    return out


def _chave_alvo(a: dict | None) -> str:
    return f"{a['tipo']}:{a['chave']}" if a else '?'


def _pedido_no_roteiro(cena: dict, verbo: str, alvo: dict | None, nivel_: str, cat: dict) -> bool:
    """O roteiro pediu alguma representação dessa coisa nesta cena?"""
    if nivel_ == 'C':
        return bool((cena.get('painel') or {}).get('rotulo'))
    if not alvo:
        return False
    objs = [o.get('tipo') for o in cena.get('objetos') or []]
    if alvo['tipo'] in ('objeto', 'substituto'):
        return alvo['chave'] in objs
    if verbo == 'indicio':
        return 'folhas' in objs
    return False


# ───────────────────────── avaliação do roteiro inteiro ─────────────────────────
def avaliar(r: dict, cat: dict | None = None) -> dict:
    cat = cat or catalogo()
    titulo = norm(f"{r.get('tema', '')} {r.get('titulo_tela', '')}")
    declarados = {str(a.get('id')): a for a in (r.get('acontecimentos') or []) if isinstance(a, dict)}
    linhas = []
    for k, c in enumerate(r.get('cenas') or [], 1):
        evs = []
        ev = c.get('evento') if isinstance(c.get('evento'), dict) else None
        if ev and ev.get('verbo') in cat['verbos']:
            alvo_txt = ev.get('alvo', {}).get('nome') if isinstance(ev.get('alvo'), dict) else ev.get('alvo')
            alvo = resolver_alvo(f"{alvo_txt or ''} {(ev.get('alvo') or {}).get('classe', '') if isinstance(ev.get('alvo'), dict) else ''}", cat)
            imp = (declarados.get(str(c.get('mostra'))) or {}).get('importancia') or ev.get('importancia')
            evs.append({'verbo': ev['verbo'], 'alvo': alvo, 'trecho': f"{ev['verbo']} {alvo_txt}", 'origem': 'declarado',
                        'importancia_declarada': imp})
        for e in eventos_narrados(c.get('narracao', ''), cat):
            if not any(x['verbo'] == e['verbo'] and _chave_alvo(x['alvo']) == _chave_alvo(e['alvo']) for x in evs):
                evs.append(e)
        papel = c.get('papel') if c.get('papel') in PAPEIS else None
        for e in evs:
            n, motivo = nivel(e['verbo'], e['alvo'], cat)
            if e['origem'] == 'narracao' and e['alvo'] is None and n == 'D':
                n, motivo = '?', 'revisar: não identifiquei o que sofre a ação (não conta como impossível)'
            pedido = _pedido_no_roteiro(c, e['verbo'], e['alvo'], n, cat) if n not in ('D', '?') else False
            linhas.append({'cena': k, 'papel': papel or '(sem papel)', 'verbo': e['verbo'],
                           'alvo': e['alvo']['palavra'] if e['alvo'] else '?', 'chave': _chave_alvo(e['alvo']),
                           'nivel': n, 'motivo': motivo, 'origem': e['origem'], 'trecho': e['trecho'],
                           'status': 'impossível' if n == 'D' else 'revisar' if n == '?' else ('mostrado' if pedido else 'possível, não pedido'),
                           'importancia_declarada': e.get('importancia_declarada')})
    # importância: o código calcula; a declarada só pode SUBIR (trocar papel/importância não esconde nada)
    cenas_por_alvo: dict = {}
    for l in linhas:
        cenas_por_alvo.setdefault(l['chave'], set()).add(l['cena'])
    for l in linhas:
        inferida = 'central' if (l['alvo'] != '?' and (l['alvo'] in titulo or len(cenas_por_alvo[l['chave']]) >= 3)) else \
                   ('apoio' if len(cenas_por_alvo[l['chave']]) >= 2 else 'detalhe')
        dec = l['importancia_declarada'] if l['importancia_declarada'] in ORDEM_IMP else 'detalhe'
        l['importancia'] = max((inferida, dec), key=lambda x: ORDEM_IMP[x])
    # alertas
    alertas = []
    centrais: dict = {}
    for l in linhas:
        if l['importancia'] == 'central':
            centrais.setdefault((l['verbo'], l['chave'], l['alvo']), []).append(l)
    for (verbo, chave, alvo), ls in centrais.items():
        cenas = sorted({x['cena'] for x in ls})
        if all(x['nivel'] == 'D' for x in ls):
            alertas.append(f"⛔ evento CENTRAL impossível de mostrar: {verbo} {alvo} (cenas {', '.join(map(str, cenas))}) — {ls[0]['motivo']}")
        elif not any(x['status'] == 'mostrado' for x in ls):
            so_reacao = [x['cena'] for x in ls if x['papel'] in ('reacao', 'contexto')]
            extra = f"; marcado como reação/contexto na(s) cena(s) {', '.join(map(str, so_reacao))}" if so_reacao else ''
            alertas.append(f"⚠️ evento CENTRAL possível mas nunca mostrado: {verbo} {alvo} (cenas {', '.join(map(str, cenas))}){extra}")
    cont = {n: sum(1 for l in linhas if l['nivel'] == n) for n in 'ABCD?'}
    total = len(linhas) - cont['?']                      # "revisar" não entra na conta de impossíveis
    pct_d = round(100 * cont['D'] / total) if total else 0
    # papel não esconde nada: evento central entra na conta mesmo marcado como reação/contexto
    acao = [l for l in linhas if l['nivel'] != '?' and (l['papel'] in PAPEIS_QUE_MOSTRAM or l['papel'] == '(sem papel)'
                                                         or l['importancia'] == 'central')]
    pct_d_acao = round(100 * sum(1 for l in acao if l['nivel'] == 'D') / len(acao)) if acao else 0
    if pct_d_acao > 30:
        alertas.insert(0, f'NÃO RECOMENDO: {pct_d_acao}% dos acontecimentos não têm como ser mostrados')
    cenas_sem_nada = [k for k, c in enumerate(r.get('cenas') or [], 1)
                      if not (c.get('objetos') or []) and not any(l['cena'] == k and l['status'] == 'mostrado' for l in linhas)]
    return {'eventos': linhas, 'contagem': cont, 'total': total, 'pct_D': pct_d, 'pct_D_acao': pct_d_acao,
            'alertas': alertas, 'cenas_sem_acontecimento_na_tela': cenas_sem_nada,
            'mostrados': sum(1 for l in linhas if l['status'] == 'mostrado'), 'catalogo_versao': cat.get('versao')}


def texto(rel: dict, titulo: str = '') -> str:
    L = [f"Eventos {titulo}".strip() + f": {rel['total']} acontecimento(s) · A {rel['contagem']['A']} · B {rel['contagem']['B']} · "
         f"C {rel['contagem']['C']} · D {rel['contagem']['D']} ({rel['pct_D']}% impossível) · mostrados {rel['mostrados']}"
         + (f" · revisar {rel['contagem']['?']}" if rel['contagem'].get('?') else '')]
    L += [f'  {a}' for a in rel['alertas']]
    if rel['cenas_sem_acontecimento_na_tela']:
        L.append('  cenas sem nenhum acontecimento na tela: ' + ', '.join(map(str, rel['cenas_sem_acontecimento_na_tela'])))
    for l in rel['eventos']:
        L.append(f"  cena {l['cena']:>2} · {l['nivel']} · {l['status']:<20} · {l['importancia']:<7} · {l['papel']:<12} · "
                 f"{l['verbo']} {l['alvo']} ({l['origem']}: \"{l['trecho']}\") — {l['motivo']}")
    return '\n'.join(L)


def resumo_telegram(rel: dict) -> str:
    c = rel['contagem']
    s = f"🎯 Eventos: A {c['A']} · B {c['B']} · C {c['C']} · D {c['D']} ({rel['pct_D']}% impossível) · mostrados {rel['mostrados']}/{rel['total']}"
    return '\n'.join([s] + [f'   {a}' for a in rel['alertas'][:4]])
