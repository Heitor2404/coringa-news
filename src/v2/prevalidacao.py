"""PRÉ-VALIDAÇÃO DOS CONTRATOS VISUAIS (V2.4, correção estrutural do piloto da lagartixa).

Problema de fundo das duas execuções (43643345166 e 43646047814): o roteirista declara mecanismos sem os dados que a
composição exige, e isso só aparecia no preparo, depois de ~460 s de pesquisa, acervo e roteiro. Aqui, LOGO DEPOIS do
roteiro (antes do casamento com o acervo, da narração e de qualquer leitura visual):

  1. correções determinísticas, sem IA e sem inventar nada (`contrato.normalizar_dados`): campo sinônimo
     (passos → etapas) e tipo dinâmico (nível/movimento) que só traz uma sequência textual → processo;
  2. validação de cada contrato contra a tabela `contrato.TIPOS` (a MESMA que o motor e o prompt usam);
  3. UMA chamada de conserto, só para os contratos críticos que o preparo bloquearia. O conserto só pode trocar
     `tipo`, `dados` e `observavel`; cada item dos dados novos precisa estar numa linha da pesquisa (rastreio por
     palavras, números pela linha que os contém). Item sem rastreio → o conserto inteiro daquele acontecimento é
     recusado e o bloqueio continua legítimo. Importância e obrigatoriedade NUNCA baixam: o acontecimento crítico
     continua crítico com qualquer tipo novo. `observavel` só pode ficar mais restrito.

Liga só com MOTOR_VISUAL=v2 (ver src/roteiro.py). Tudo fica registrado em `v['_contratos']`.
"""
from __future__ import annotations

import copy
import json
import re

from src.v2 import contrato, preparo

# tipos de "não acontecimento" (a foto do assunto é a representação): um conserto não pode levar um acontecimento
# crítico para eles — seria trocar o fenômeno por uma foto qualquer
PROIBIDOS_NO_REPARO = {'pessoa', 'lugar', 'ambiente', 'documento', 'localizacao', 'territorio', 'citacao', 'evento_historico'}
CHAVES_SEM_TEXTO = {'angulo', 'intensidade', 'sentido', 'lon', 'lat', 't', 'cor', 'unidade', 'moeda', 'ano', 'data', 'id'}
CHAVES_NUMERO = {'valor', 'pct', 'de', 'ate'}


# ───────────────────────── rastreio na pesquisa ─────────────────────────
def _raizes(s) -> set[str]:
    return {w[:5] for w in preparo._palavras(s)}


def rastrear_texto(s: str, linhas: list[dict]) -> dict | None:
    """A linha da pesquisa que contém a maior parte das palavras do item (raiz de 5 letras: "afastam" ≈ "afastadas").
    Exige metade das palavras de conteúdo (pelo menos 1). None = o item não vem da pesquisa."""
    alvo = _raizes(s)
    if not alvo or not linhas:
        return None
    melhor = max(linhas, key=lambda ln: len(alvo & _raizes(ln['texto'])))
    comum = alvo & _raizes(melhor['texto'])
    if len(comum) < max(1, -(-len(alvo) // 2)):
        return None
    return {'fonte': melhor['fonte'], 'trecho': melhor['texto'][:160], 'palavras': sorted(comum)}


def _folhas(x, chave: str = ''):
    if isinstance(x, dict):
        for k, y in x.items():
            yield from _folhas(y, k)
    elif isinstance(x, list):
        for y in x:
            yield from _folhas(y, chave)
    else:
        yield chave, x


def rastreio(dados: dict, linhas: list[dict]) -> dict:
    """Cada item de texto e cada número dos dados → a linha da pesquisa de onde ele vem."""
    itens = []
    dados = dict(dados or {})
    esq = dados.pop('esquema', None)
    if isinstance(esq, dict):                     # V2.4: no esquema só os RÓTULOS são conteúdo; posição/escala é desenho
        dados['_rotulos_esquema'] = [o.get('rotulo') for o in esq.get('objetos') or [] if isinstance(o, dict) and o.get('rotulo')] + \
            [x.get('rotulo') for e in esq.get('estados') or [] if isinstance(e, dict)
             for x in [e] + [r for r in e.get('relacoes') or [] if isinstance(r, dict)] if x.get('rotulo')]
    for chave, x in _folhas(dados):
        if chave in CHAVES_SEM_TEXTO or x is None or isinstance(x, bool):
            continue
        if chave in CHAVES_NUMERO or isinstance(x, (int, float)):
            try:
                r = preparo.rastrear(float(str(x).replace(',', '.')), None, linhas)
            except ValueError:
                r = None
            itens.append({'item': x, 'campo': chave, 'ok': bool(r), **(r or {})})
            continue
        s = str(x).strip()
        if len(s) < 4:
            continue
        r = rastrear_texto(s, linhas)
        itens.append({'item': s, 'campo': chave, 'ok': bool(r), **(r or {})})
    return {'itens': itens, 'todos': bool(itens) and all(i['ok'] for i in itens), 'algum': any(i['ok'] for i in itens)}


# ───────────────────────── acontecimentos do roteiro ─────────────────────────
def grupos(v: dict) -> tuple[dict, list[str]]:
    """O MESMO agrupamento do preparo: id declarado, senão o `evento` da ideia, senão a cena."""
    g, ordem = {}, []
    for k, c in enumerate(v.get('cenas') or []):
        bruto = c.get('acontecimento') if isinstance(c.get('acontecimento'), dict) else None
        if not bruto or not bruto.get('tipo'):
            continue
        chave = bruto.get('id') or c.get('evento') or f'cena{k}'
        if chave not in g:
            g[chave] = []; ordem.append(chave)
        g[chave].append(k)
    return g, ordem


def _aplicar(v: dict, idx: list[int], campos: dict):
    for k in idx:
        ac = dict(v['cenas'][k].get('acontecimento') or {})
        ac.update(copy.deepcopy(campos))
        v['cenas'][k]['acontecimento'] = ac


def prevalidar(v: dict) -> dict:
    """Correções determinísticas + validação de todos os contratos (modifica `v['cenas']`). Sem IA, sem rede."""
    g, ordem = grupos(v)
    rel = {'eventos': [], 'pendentes': [], 'correcoes': []}
    for chave in ordem:
        idx = g[chave]
        bruto = v['cenas'][idx[0]]['acontecimento']
        ac = contrato.normalizar(bruto)
        ac['id'] = chave
        novo, motivos = contrato.normalizar_dados(ac)
        # a MESMA reclassificação que o preparo fará (proporção com etapas → processo…): a pré-validação vê o que ele verá
        c0 = v['cenas'][idx[0]]
        t2, m2 = preparo.reclassificar({**novo, '_quem': bruto.get('quem')}, {'mostrar': c0.get('mostrar'), 'tipo': c0.get('tipo')})
        if t2 != novo.get('tipo'):
            novo = {**novo, 'tipo_original': novo.get('tipo_original') or novo.get('tipo'), 'tipo': t2, 'reclassificacao': m2}
            motivos.append(m2)
        if motivos:
            campos = {k: novo[k] for k in ('tipo', 'dados', 'tipo_original', 'reclassificacao') if k in novo}
            _aplicar(v, idx, campos)
            rel['correcoes'].append({'evento': chave, 'motivos': motivos})
            ac = novo
        r = contrato.validar(ac)
        if r['estado'] != 'ok' and all(v['cenas'][k].get('tipo') in preparo.EDITORIAL for k in idx):
            r.update(estado='editorial', precisa_reparo=False)     # revelação/gancho/fechamento: a cena editorial mostra
        r['cenas'] = idx
        r['falas'] = [re.sub(r'\*', '', v['cenas'][k].get('fala') or '') for k in idx]
        rel['eventos'].append(r)
        if r['precisa_reparo']:
            rel['pendentes'].append(chave)
    return rel


# ───────────────────────── conserto (1 chamada) ─────────────────────────
PROMPT_REPARO = """Você corrige CONTRATOS VISUAIS de um vídeo curto de divulgação científica em português.
Cada acontecimento abaixo é CRÍTICO e foi declarado sem os dados que a composição exige. Para cada um, devolva o tipo e
os dados corretos usando SOMENTE os FATOS da pesquisa. Não invente etapas, nomes, números nem relações.

FATOS DA PESQUISA:
{fatos}

TIPOS POSSÍVEIS E DADOS EXIGIDOS (composição → campos de "dados"):
{tabela}

ACONTECIMENTOS A CORRIGIR:
{eventos}

Regras:
- a fala descreve uma sequência (perto → longe, antes → depois, causa → efeito)? tipo "processo" com "etapas" (2 a 4,
  curtas, cada uma com palavras de UMA linha dos FATOS);
- "observavel": false quando o que precisa ser visto não pode ser fotografado (moléculas, forças, elétrons, campos);
- não mude o sentido da fala; não troque o acontecimento por uma foto do assunto;
- se os FATOS não têm os dados, devolva "impossivel" com o motivo.

Responda SÓ com JSON:
{{"contratos": [{{"id": "...", "tipo": "...", "dados": {{...}}, "observavel": true|false,
  "base": ["trecho exato dos FATOS usado"], "motivo": "..."}} | {{"id": "...", "impossivel": "motivo"}}]}}
"""
TIPOS_REPARO = [t for t in contrato.TIPOS if t not in PROIBIDOS_NO_REPARO]


def montar_prompt(v: dict, pendentes: list[dict]) -> str:
    tabela = '\n'.join(f'  {t}: {contrato.requisitos_texto(t)}' for t in TIPOS_REPARO)
    evs = []
    for e in pendentes:
        ac = v['cenas'][e['cenas'][0]]['acontecimento']
        evs.append(json.dumps({'id': e['id'], 'fala': ' '.join(e['falas']), 'tipo_declarado': ac.get('tipo'),
                               'sujeito': ac.get('sujeito'), 'acao': ac.get('acao'), 'mostrar': ac.get('mostrar'),
                               'dados_declarados': ac.get('dados') or {}, 'problema': e['problema']}, ensure_ascii=False))
    return PROMPT_REPARO.format(fatos=str(v.get('fatos') or '')[:6000], tabela=tabela, eventos='\n'.join(evs))


def aceitar(ac: dict, prop: dict, linhas: list[dict], critico_original: bool) -> tuple[dict | None, str]:
    """Confere a proposta de conserto. Devolve (campos a aplicar, motivo) ou (None, motivo da recusa)."""
    if not isinstance(prop, dict):
        return None, 'resposta sem contrato'
    if prop.get('impossivel'):
        return None, f"IA: impossível com os fatos ({str(prop['impossivel'])[:120]})"
    novo = contrato.normalizar({'tipo': prop.get('tipo'), 'dados': prop.get('dados') if isinstance(prop.get('dados'), dict) else {}})
    tipo = novo.get('tipo')
    if tipo not in contrato.TIPOS:
        return None, f"tipo proposto inválido ({prop.get('tipo')!r})"
    if tipo in PROIBIDOS_NO_REPARO:
        return None, f'tipo proposto "{tipo}" troca o acontecimento por foto do assunto: recusado'
    cand = {**ac, 'tipo': tipo, 'dados': novo.get('dados') or {}}
    cand, _ = contrato.normalizar_dados(cand)
    comps = contrato.viaveis(cand['tipo'], cand['dados'], cand)
    if not comps:
        return None, f"dados propostos não servem a nenhuma composição de \"{cand['tipo']}\" ({contrato.requisitos_texto(cand['tipo'])})"
    rast = rastreio(cand['dados'], linhas)
    sem = [str(i['item']) for i in rast['itens'] if not i['ok']]
    if not rast['itens'] or sem:
        return None, 'dados sem rastreio na pesquisa (inventados?): ' + ('; '.join(sem[:4]) or 'nenhum item')
    campos = {'tipo': cand['tipo'], 'dados': cand['dados']}
    if cand.get('tipo_original') or cand['tipo'] != ac.get('tipo'):
        campos['tipo_original'] = ac.get('tipo_original') or ac.get('tipo')
    # observável só fica MAIS restrito: a IA não reabre a foto para algo que a escala física já fechou
    obs_atual = contrato.observabilidade(ac)
    if prop.get('observavel') is False or obs_atual != 'sim':
        campos['observavel'] = False if (prop.get('observavel') is False or obs_atual == 'nao') else 'parcial'
    if critico_original:                          # crítico continua crítico, qualquer que seja o tipo novo
        campos['obrigatoria'] = True
    campos['reparo'] = {'antes': {'tipo': ac.get('tipo'), 'dados': ac.get('dados') or {}},
                        'base': [str(b)[:160] for b in (prop.get('base') or [])][:4], 'motivo': str(prop.get('motivo') or '')[:200],
                        'rastreio': rast['itens'], 'composicao': comps[0]}
    return campos, f"{ac.get('tipo')} → {cand['tipo']} ({comps[0]}), {len(rast['itens'])} item(ns) rastreado(s)"


def _chamar_padrao(prompt: str):
    from src import gemini
    return gemini.json_(prompt, validar=lambda o: isinstance(o, dict) and isinstance(o.get('contratos'), list))


def reparar(v: dict, chamar=None) -> dict:
    """Pré-validação + no máximo UMA chamada de conserto. `chamar(prompt) -> dict` substitui a IA (testes offline).
    Modifica `v['cenas']` e grava o relatório em `v['_contratos']`."""
    rel = prevalidar(v)
    rel['reparo'] = {'chamadas': 0, 'pedidos': list(rel['pendentes']), 'aceitos': [], 'recusados': []}
    if rel['pendentes']:
        pend = [e for e in rel['eventos'] if e['id'] in rel['pendentes']]
        linhas = preparo.pesquisa(v)
        try:
            resp = (chamar or _chamar_padrao)(montar_prompt(v, pend))
            rel['reparo']['chamadas'] = 1
        except Exception as e:                   # sem conserto: o preparo bloqueia como antes (nunca piora)
            resp = None
            rel['reparo']['erro'] = str(e)[:200]
        props = {str(p.get('id')): p for p in ((resp or {}).get('contratos') or []) if isinstance(p, dict)}
        g, _ = grupos(v)
        for e in pend:
            idx = g[e['id']]
            ac = {**contrato.normalizar(v['cenas'][idx[0]]['acontecimento']), 'id': e['id']}
            campos, motivo = aceitar(ac, props.get(e['id']), linhas, e['critico']) if e['id'] in props else (None, 'sem resposta para este acontecimento')
            if campos:
                _aplicar(v, idx, campos)
                rel['reparo']['aceitos'].append({'evento': e['id'], 'motivo': motivo})
            else:
                rel['reparo']['recusados'].append({'evento': e['id'], 'motivo': motivo})
        # revalida depois do conserto (o relatório final é o que o preparo vai encontrar)
        depois = prevalidar(v)
        rel['depois'] = [{k: x[k] for k in ('id', 'tipo', 'estado', 'viaveis', 'observavel', 'problema')} for x in depois['eventos']]
        rel['pendentes_depois'] = depois['pendentes']
    else:
        rel['pendentes_depois'] = []
    v['_contratos'] = rel
    return rel


def resumo(rel: dict) -> str:
    r = rel.get('reparo') or {}
    linhas = [f"contratos: {len(rel['eventos'])} acontecimento(s) · {len(rel['correcoes'])} correção(ões) sem IA · "
              f"{len(rel['pendentes'])} pedido(s) de conserto · {r.get('chamadas', 0)} chamada · "
              f"{len(r.get('aceitos') or [])} aceito(s) · {len(r.get('recusados') or [])} recusado(s)"]
    for c in rel['correcoes']:
        linhas.append(f"  ↺ {c['evento']}: {'; '.join(c['motivos'])}")
    for a in r.get('aceitos') or []:
        linhas.append(f"  ✔ {a['evento']}: {a['motivo']}")
    for a in r.get('recusados') or []:
        linhas.append(f"  ✘ {a['evento']}: {a['motivo']}")
    return '\n'.join(linhas)
