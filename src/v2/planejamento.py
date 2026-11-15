"""PLANEJAMENTO VISUAL DIRECIONADO (V2.4) — o último recurso antes do bloqueio, UMA tentativa por execução.

Para quem: acontecimento CRÍTICO e OBSERVÁVEL que, depois de consultado o acervo final, continua sem imagem específica
(nenhuma com força ≥ 2) e sem composição viável. É o caso do e2 do piloto 43700052750 ("Hemidactylus mabouia usa
lamelas nos dedos"): o desenho do acervo é de outra espécie; as fotos da espécie não mostram as lamelas.

A IA (uma chamada para todos os pendentes) só pode propor, a partir dos FATOS já coletados e do catálogo do acervo:
  composicao        tipo + dados para uma composição didática; aceita só com cada item rastreado na pesquisa
                    (as mesmas travas do conserto de contratos: crítico continua crítico, nada inventado);
  foto_ilustrativa  uma foto GENÉRICA do acervo que mostra a estrutura narrada, como ILUSTRAÇÃO explicitamente
                    identificada na tela ("imagem ilustrativa") — nunca prova do acontecimento nem da espécie.
                    Aceita só se: a imagem existe no acervo e não é IA; não é de outro táxon nomeado; não é foto de
                    espécie identificada (essa é registro da espécie) e está catalogada como genérica; tem licença de
                    reutilização no crédito; o `trecho_imagem` está LITERALMENTE no catálogo/título/descrição da
                    fonte; o `trecho_fato` está literalmente nos FATOS e compartilha palavras com a fala;
  impossivel        e o bloqueio continua.

Sem solução fiel, nada muda: o preparo bloqueia como antes. Tudo fica em `v['_plano_visual']`.
Só com MOTOR_VISUAL=v2 (chamado em main.montar_video, antes do preparo).
"""
from __future__ import annotations

import copy
import json
import re

from src.v2 import contrato, identidade, preparo, prevalidacao

LICENCA = re.compile(r'\b(cc[ -]?by|cc0|cc[ -]by-sa|creative commons|dom[ií]nio p[uú]blico|public domain|pd-|nasa|noaa|usgs|pixabay)', re.I)
ROTULO = {'especie': 'imagem ilustrativa · não identifica a espécie', 'fato': 'imagem ilustrativa · não é registro do fato'}

PROMPT = """Você planeja a imagem de acontecimentos CRÍTICOS de um vídeo curto de divulgação científica em português.
Nenhuma imagem do acervo mostra especificamente o que a fala afirma, e o contrato não tem dados para uma composição.
Para cada acontecimento, escolha UMA saída, usando SOMENTE os FATOS e o catálogo do ACERVO abaixo. Não invente nada.

FATOS DA PESQUISA:
{fatos}

ACERVO (id · tipo · o que mostra · título/descrição da fonte):
{acervo}

COMPOSIÇÕES POSSÍVEIS (tipo: composição → campos de "dados"):
{tabela}

ACONTECIMENTOS:
{eventos}

Saídas:
- "composicao": tipo + dados de uma composição didática; cada etapa/nó/força com palavras de UMA linha dos FATOS.
- "foto_ilustrativa": uma foto do ACERVO que mostra a estrutura/anatomia narrada de forma GENÉRICA. Ela aparece com o
  aviso "imagem ilustrativa" e NUNCA prova a espécie nem o acontecimento. Proibido: imagem de outra espécie nomeada,
  desenho de outra espécie, imagem que só mostra o animal/objeto sem a estrutura narrada.
  "trecho_imagem" = trecho LITERAL do catálogo/título/descrição dessa imagem que mostra a estrutura;
  "trecho_fato" = trecho LITERAL dos FATOS que sustenta a fala.
- "impossivel": quando nada disso é fiel.

Responda SÓ com JSON:
{{"planos": [{{"id": "...", "saida": "composicao", "tipo": "...", "dados": {{...}}, "base": ["..."]}} |
  {{"id": "...", "saida": "foto_ilustrativa", "foto": "a?", "parte": "...", "trecho_imagem": "...", "trecho_fato": "..."}} |
  {{"id": "...", "saida": "impossivel", "motivo": "..."}}]}}
"""


def pendentes(v: dict) -> list[dict]:
    """Críticos observáveis que o preparo bloquearia com o acervo FINAL (simulação em cópia, sem IA)."""
    rel = preparo.preparar(copy.deepcopy(v), copy.deepcopy(v.get('acervo') or []))
    ev = {e['id']: e for e in rel['eventos']}
    out = []
    for b in rel['bloqueios']:
        e = ev.get(b['evento']) or {}
        if e.get('observavel') == 'sim' and e.get('critico'):
            out.append({'id': b['evento'], 'cenas': b['cenas'], 'faltam': b['faltam']})
    return out


def _texto_norm(s) -> str:
    return re.sub(r'\s+', ' ', identidade._n(s)).strip(' .,;:')


def _acervo_txt(acervo: list[dict]) -> str:
    linhas = []
    for x in acervo:
        if x.get('ia'):
            continue
        linhas.append(f"{x['id']} · {x.get('tipo_img') or 'foto'} · {str(x.get('mostra') or '')[:160]} · "
                      f"{str(x.get('titulo') or '')[:80]} / {str(x.get('desc') or '')[:260]}")
    return '\n'.join(linhas)


def montar_prompt(v: dict, pend: list[dict]) -> str:
    evs = []
    for p in pend:
        c0 = v['cenas'][p['cenas'][0]]
        ac = c0.get('acontecimento') or {}
        evs.append(json.dumps({'id': p['id'], 'fala': ' '.join(re.sub(r'\*', '', v['cenas'][k].get('fala') or '') for k in p['cenas']),
                               'tipo': ac.get('tipo'), 'sujeito': ac.get('sujeito'), 'mostrar': ac.get('mostrar'),
                               'dados': ac.get('dados') or {}, 'falta': p['faltam'][-2:]}, ensure_ascii=False))
    tabela = '\n'.join(f'  {t}: {contrato.requisitos_texto(t)}' for t in prevalidacao.TIPOS_REPARO)
    return PROMPT.format(fatos=str(v.get('fatos') or '')[:6000], acervo=_acervo_txt(v.get('acervo') or []), tabela=tabela,
                         eventos='\n'.join(evs))


def aceitar_foto(prop: dict, ac: dict, falas: list[str], v: dict) -> tuple[dict | None, str]:
    por_id = {x['id']: x for x in v.get('acervo') or []}
    x = por_id.get(str(prop.get('foto') or ''))
    if not x:
        return None, f"foto {prop.get('foto')!r} não está no acervo"
    if x.get('ia'):
        return None, 'imagem de IA não ilustra fato científico'
    conf = identidade.confrontar(identidade.do_acontecimento(ac, falas), x)
    if conf['conflito']:
        return None, f"outra identidade: {conf['conflito']}"
    im = identidade.da_imagem(x)
    if im['taxons']:
        return None, f"foto de espécie identificada ({', '.join(sorted(im['taxons']))}): é registro da espécie, não ilustração genérica"
    if not x.get('generica') and 'desenho' not in identidade._n(x.get('tipo_img')):
        return None, 'imagem não catalogada como genérica: ilustração só com imagem genérica da estrutura'
    if not LICENCA.search(str(x.get('credito') or '') + ' ' + str(x.get('fonte') or '')):
        return None, f"licença de reutilização não verificada no crédito ({str(x.get('credito') or '')[:60]})"
    ti = _texto_norm(prop.get('trecho_imagem'))
    meta = _texto_norm(' '.join(str(x.get(k) or '') for k in ('mostra', 'titulo', 'desc')))
    if len(ti) < 8 or ti not in meta:
        return None, 'trecho_imagem não está literalmente no catálogo/descrição da imagem'
    ident = identidade.do_acontecimento(ac, falas)
    so_nome = prevalidacao._raizes(' '.join(ident['nomes']) + ' ' + ' '.join(ident['taxons']))
    if len(prevalidacao._raizes(prop.get('trecho_imagem')) - so_nome) < 2:
        return None, 'trecho_imagem só nomeia a espécie/entidade: não mostra a estrutura narrada'
    tf = _texto_norm(prop.get('trecho_fato'))
    linhas = [ln for ln in preparo.pesquisa(v) if tf and tf in _texto_norm(ln['texto'])]
    if len(tf) < 8 or not linhas:
        return None, 'trecho_fato não está literalmente nos FATOS'
    fala_r = prevalidacao._raizes(' '.join(falas) + ' ' + str(ac.get('mostrar') or ''))
    if not (prevalidacao._raizes(tf) & fala_r):
        return None, 'trecho_fato não sustenta esta fala (nenhuma palavra em comum)'
    rotulo = ROTULO['especie'] if identidade.do_acontecimento(ac, falas)['taxons'] else ROTULO['fato']
    plano = {'modo': 'foto_ilustrativa', 'foto': x['id'], 'parte': str(prop.get('parte') or '')[:120],
             'trecho_imagem': str(prop.get('trecho_imagem'))[:200], 'trecho_fato': str(prop.get('trecho_fato'))[:200],
             'fonte_fato': linhas[0]['fonte'], 'credito': x.get('credito'), 'rotulo': rotulo, 'nao_prova': True}
    return {'plano_visual': plano}, f"foto ilustrativa {x['id']} ({plano['parte'][:60]})"


def _chamar_padrao(prompt: str):
    from src import gemini
    return gemini.json_(prompt, validar=lambda o: isinstance(o, dict) and isinstance(o.get('planos'), list))


def planejar(v: dict, chamar=None) -> dict:
    """No máximo UMA chamada para todos os pendentes. Modifica os contratos de `v['cenas']` só com planos aceitos."""
    rel = {'pendentes': [], 'chamadas': 0, 'aceitos': [], 'recusados': []}
    pend = pendentes(v)
    rel['pendentes'] = [p['id'] for p in pend]
    if pend:
        try:
            resp = (chamar or _chamar_padrao)(montar_prompt(v, pend))
            rel['chamadas'] = 1
        except Exception as e:                       # sem plano: o preparo bloqueia como antes
            resp, rel['erro'] = None, str(e)[:200]
        props = {str(p.get('id')): p for p in ((resp or {}).get('planos') or []) if isinstance(p, dict)}
        linhas = preparo.pesquisa(v)
        for p in pend:
            idx = p['cenas']
            falas = [re.sub(r'\*', '', v['cenas'][k].get('fala') or '') for k in idx]
            ac = {**contrato.normalizar(v['cenas'][idx[0]]['acontecimento']), 'id': p['id']}
            prop = props.get(p['id'])
            if not prop:
                campos, motivo = None, 'sem resposta para este acontecimento'
            elif prop.get('saida') == 'composicao':
                campos, motivo = prevalidacao.aceitar(ac, prop, linhas, True)
            elif prop.get('saida') == 'foto_ilustrativa':
                campos, motivo = aceitar_foto(prop, ac, falas, v)
            else:
                campos, motivo = None, f"IA: impossível ({str(prop.get('motivo') or '')[:120]})"
            if campos:
                prevalidacao._aplicar(v, idx, campos)
                rel['aceitos'].append({'evento': p['id'], 'motivo': motivo, **({'plano': campos['plano_visual']} if 'plano_visual' in campos else {})})
            else:
                rel['recusados'].append({'evento': p['id'], 'motivo': motivo})
    v['_plano_visual'] = rel
    return rel


def resumo(rel: dict) -> str:
    l = [f"plano visual: {len(rel['pendentes'])} pendente(s) · {rel['chamadas']} chamada · {len(rel['aceitos'])} aceito(s) · {len(rel['recusados'])} recusado(s)"]
    l += [f"  ✔ {a['evento']}: {a['motivo']}" for a in rel['aceitos']] + [f"  ✘ {a['evento']}: {a['motivo']}" for a in rel['recusados']]
    return '\n'.join(l)
