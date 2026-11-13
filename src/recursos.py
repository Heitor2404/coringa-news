"""RECURSOS GRÁFICOS COM FUNÇÃO E DADO VERDADEIRO (plano-mestre, etapa F — 12/11/2026).

Cada infográfico responde a uma pergunta (src/render/identidade.FUNCAO) e mostra dado que está nos FATOS:
  - numero / comparacao / escala: os valores precisam aparecer nos fatos (nada de dado inventado);
  - linha_tempo: anos dos fatos, em ordem;
  - mapa: a frase precisa falar de lugar, distância ou trajeto (mapa não é decoração);
  - citacao: o texto precisa estar nos fatos.
`conferir(v, fatos)` devolve os problemas (registro). `rebaixar(v, fatos)` tira da tela SÓ o que mostraria dado
inventado (P0): o gráfico vira cena com imagem e a fala continua a mesma. O resto fica como aviso.
"""
import re
import unicodedata

GRAFICOS = ('numero', 'comparacao', 'escala', 'linha_tempo', 'mapa', 'citacao', 'cards', 'lista')
ESPACO = re.compile(r'\b(km|quil[oô]metro|milha|metro|dist[aâ]ncia|viaj|atravess|cruz|rota|trajet|caminho|fica (em|no|na)|'
                    r'perto|longe|fronteira|norte|sul|leste|oeste|de \w+ (at[eé]|para) |chegou|partiu|fugiu|mudou)', re.I)


def _norm(s) -> str:
    return unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().lower()


def _variantes(x) -> set[str]:
    """1.250.000 · 1250000 · 1,25 · 1.25 · '1,25 milhão'... (só os dígitos importam)."""
    try:
        f = float(str(x).replace('.', '').replace(',', '.')) if re.fullmatch(r'\d{1,3}(\.\d{3})+', str(x)) else float(str(x).replace(',', '.'))
    except (TypeError, ValueError):
        return set()
    out = {re.sub(r'\D', '', f'{f:g}')}
    if f == int(f):
        out.add(str(int(f)))
    for div in (1e3, 1e6, 1e9):                      # "330 milhões" pode estar como 330 nos fatos
        if f >= div and (f / div) == int(f / div):
            out.add(str(int(f / div)))
    return {o for o in out if o}


def _no_texto(valor, fatos: str) -> bool:
    nums = {re.sub(r'\D', '', n) for n in re.findall(r'\d[\d.,]*', fatos)}
    return bool(_variantes(valor) & nums)


def conferir(v: dict, fatos: str) -> list[dict]:
    probs = []
    for k, c in enumerate(v.get('cenas', [])):
        t = c.get('tipo')
        if t not in GRAFICOS:
            continue
        p = lambda m, grave=False: probs.append({'cena': k, 'tipo': t, 'problema': m, 'inventado': grave})
        if t == 'numero' and c.get('valor') is not None and fatos and not _no_texto(c['valor'], fatos):
            p(f"número {c['valor']} não está nos fatos", True)
        if t == 'comparacao':
            fora = [i.get('valor') for i in c.get('itens') or [] if fatos and not _no_texto(i.get('valor'), fatos)]
            if fora:
                p(f"valores fora dos fatos: {fora}", True)
            if len({str(i.get('unidade') or c.get('unidade') or '') for i in c.get('itens') or []}) > 1:
                p('itens com unidades diferentes')
        if t == 'escala' and fatos and c.get('valor') is not None and not _no_texto(c['valor'], fatos):
            p(f"valor {c['valor']} da escala não está nos fatos", True)
        if t == 'linha_tempo':
            anos = [str(i.get('ano')) for i in c.get('itens') or []]
            fora = [a for a in anos if fatos and a not in fatos]
            if fora:
                p(f'anos fora dos fatos: {fora}', True)
            try:
                nums = [int(re.sub(r'\D', '', a)) for a in anos]
                if nums != sorted(nums):
                    p('datas fora de ordem')
            except ValueError:
                pass
        if t == 'mapa':
            fala = f"{c.get('fala', '')} {c.get('rotulo', '')}"
            if not ESPACO.search(_norm(fala)) and len(c.get('pontos') or []) < 2:
                p('mapa sem função: a frase não fala de lugar, distância ou trajeto')
        if t == 'citacao' and fatos and c.get('texto'):
            if _norm(c['texto'])[:40] not in _norm(fatos):
                p('citação que não está nos fatos', True)
        b = c.get('bloco') if isinstance(c.get('bloco'), dict) else {}
        if v.get('plano') and (v['plano'] or {}).get('origem') != 'derivado' and not b.get('funcao'):
            p('recurso sem função declarada no roteiro')
    return probs


def rebaixar(v: dict, fatos: str) -> list[str]:
    """Gráfico que mostraria dado inventado sai da tela (vira cena com imagem; a fala não muda)."""
    feitos = []
    for pb in conferir(v, fatos):
        if not pb['inventado']:
            continue
        c = v['cenas'][pb['cena']]
        c['_rebaixado'] = f"{c['tipo']} → historia: {pb['problema']}"
        c['tipo'] = 'historia'
        feitos.append(c['_rebaixado'])
    for f in feitos:
        print(f'  [recursos] {f}')
    return feitos


def linha_telegram(v: dict, fatos: str) -> str:
    probs = conferir(v, fatos)
    reb = [c['_rebaixado'] for c in v.get('cenas', []) if c.get('_rebaixado')]
    if not probs and not reb:
        return ''
    return ('📊 Recursos gráficos (só registro): ' + '; '.join([f"cena {p['cena'] + 1}: {p['problema']}" for p in probs][:3]
            + [f'rebaixado: {r}' for r in reb][:2]))
