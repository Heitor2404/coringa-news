"""V2.5 — PLANO VISUAL EXECUTÁVEL e VINCULANTE (antes de fechar o roteiro; antes de narrar/renderizar).

Para cada acontecimento do roteiro (com o acervo já casado), roda o MESMO preparo do vídeo numa cópia e registra:
  fato (trecho + fonte da pesquisa) · sujeito/ação/local/época/resultado · recurso visual (id + o que mostra) ·
  tipo de representação (registro_direto | documento | contexto | mapa | dado | cronologia | esquema |
  ilustracao_identificada | editorial) · composição + dados obrigatórios · status REPRESENTÁVEL |
  REPRESENTÁVEL_COM_REVISÃO | INVIÁVEL · justificativa e limites.

O plano é RESTRIÇÃO: acontecimento INVIÁVEL não segue para a narração. No máximo UM ajuste de enfoque (1 chamada, só
para os inviáveis, preservando fatos e fontes); se continuar inviável, o acontecimento sai do roteiro (afirmação
retirada) quando isso não quebra a estrutura, ou o roteiro inteiro é recusado (o fluxo diário passa ao próximo tema).
"""
from __future__ import annotations

import copy
import json
import re

from src.v2 import contrato, estados

STATUS_OK, STATUS_REV, STATUS_NAO = 'REPRESENTÁVEL', 'REPRESENTÁVEL_COM_REVISÃO', 'INVIÁVEL'
ESTRUTURA = {'gancho', 'revelacao', 'fechamento'}
MAX_RETIRADAS = 2          # retirar mais que isso descaracteriza o roteiro: recusa (próximo tema)
ANAFORA = re.compile(r'^\s*(ess[ea]s?|isso|isto|ela|ele|eles|elas|por isso|assim|dessa|desse|nessa|nesse)\b', re.I)


def _tipo_rep(rep: dict) -> str | None:
    modo, comp = rep.get('modo'), rep.get('comp')
    if modo == 'foto_direta':
        return 'registro_direto'
    if modo in ('contexto', 'foto_contexto', 'foto_declarada'):
        return 'contexto'
    if modo == 'foto_ilustrativa':
        return 'ilustracao_identificada'
    if modo == 'editorial':
        return 'editorial'
    if modo == 'composicao':
        if comp in ('fonte.evidencia', 'citacao'):
            return 'documento'
        if str(comp).startswith('mapa.'):
            return 'mapa'
        if comp == 'linha_tempo.historica':
            return 'cronologia'
        if contrato.funcao_comp(comp) == 'ilustracao' or comp in contrato.DEMONSTRATIVAS or comp in contrato.TEXTUAIS:
            return 'esquema'
        return 'dado'
    return None


def construir(v: dict) -> dict:
    """Plano por acontecimento a partir de uma CÓPIA do roteiro (nada no roteiro muda aqui)."""
    from src.v2 import preparo, prevalidacao
    w = copy.deepcopy(v)
    rel = preparo.preparar(w)
    linhas = preparo.pesquisa(w)
    por_id = {x['id']: x for x in w.get('acervo') or []}
    from src.v2 import cobertura
    cob = {e['evento']: e for e in cobertura.avaliar(w)['eventos']}     # o que a tela AFIRMARIA confere com fala e pesquisa?
    for eid, c in cob.items():
        if c['resultado'] == 'bloqueio':
            for e in rel['eventos']:
                if e['id'] == eid and (e.get('representacao') or {}).get('modo') != 'bloqueio':
                    e['representacao'] = {'modo': 'bloqueio', 'faltam': [f"cobertura: {c['motivo']}"]}
    # 'estado' não verificável aqui é só porque o esquema ainda não foi renderizado (a prévia confere depois)
    revisoes = {r['evento'] for r in rel.get('revisoes') or []} | {
        k for k, c in cob.items() if c['resultado'] == 'revisao' and {x for x, y in c['verificacoes'].items() if y == 'nao_verificavel'} - {'estado'}
        or c['resultado'] == 'revisao' and c['verificacoes'].get('funcao') in ('contexto', 'ilustracao') and c.get('modo') != 'composicao'}
    plano = []
    for e in rel['eventos']:
        rep = e.get('representacao') or {}
        c0 = w['cenas'][e['cenas'][0]]
        ac = c0.get('acontecimento') or {}
        falas = ' '.join(re.sub(r'\*', '', w['cenas'][k].get('fala') or '') for k in e['cenas'])
        fato = prevalidacao.rastrear_texto(falas, linhas) if c0.get('tipo') not in ESTRUTURA else None
        x = por_id.get(rep.get('foto'))
        tipo_rep = _tipo_rep(rep)
        if rep.get('modo') == 'bloqueio' or tipo_rep is None and rep.get('modo') != 'sem_imagem':
            status = STATUS_NAO
        elif e['id'] in revisoes or tipo_rep in ('contexto', 'ilustracao_identificada'):
            status = STATUS_REV
        else:
            status = STATUS_OK if rep.get('modo') != 'sem_imagem' or not e['critico'] else STATUS_NAO
        plano.append({
            'evento': e['id'], 'cenas': e['cenas'], 'critico': e['critico'], 'tipo': e['tipo'], 'fala': falas[:200],
            'fato': {'trecho': fato['trecho'], 'fonte': fato['fonte']} if fato else None,
            'sujeito': ac.get('sujeito'), 'acao': ac.get('acao'), 'local': ac.get('onde'),
            'epoca': ac.get('quando'), 'resultado': ac.get('estado_final'),
            'recurso': ({'id': x['id'], 'mostra': x.get('mostra'), 'ano': x.get('ano'), 'credito': x.get('credito')} if x else None),
            'representacao': tipo_rep, 'composicao': rep.get('comp'), 'modo': rep.get('modo'),
            'dados_obrigatorios': contrato.requisitos_texto(e['tipo']) if e['tipo'] in contrato.TIPOS else None,
            'status': status,
            'justificativa': (rep.get('evidencia') or rep.get('fato') or '') if status != STATUS_NAO else '; '.join(map(str, rep.get('faltam') or e.get('faltam') or []))[:300],
            'limites': 'não prova o instante narrado' if tipo_rep in ('contexto', 'ilustracao_identificada') else
                       'esquema fora de escala, não é registro' if tipo_rep == 'esquema' else ''})
    return {'acontecimentos': plano, 'inviaveis': [p['evento'] for p in plano if p['status'] == STATUS_NAO]}


PROMPT_AJUSTE = """Você ajusta o ENFOQUE de um roteiro documental curto em português para que cada acontecimento crítico possa
ser MOSTRADO com os recursos que existem. Não invente fatos, números, nomes, imagens nem fontes.

FATOS DA PESQUISA (cada linha com a fonte):
{fatos}

RECURSOS VISUAIS DISPONÍVEIS (acervo real verificado):
{acervo}
Representações possíveis: registro direto (foto/vídeo do próprio fato) · documento (trecho de fonte) · contexto (foto
real do lugar/pessoa/objeto, identificada como contexto) · mapa (lugares com coordenadas) · cronologia (anos dos FATOS) ·
dado (números dos FATOS) · esquema (mecanismo invisível, com os campos do formato abaixo).
{formato}

ACONTECIMENTOS INVIÁVEIS (por que não podem ser mostrados como estão):
{inviaveis}

Para CADA um, devolva UMA opção: reescrever a fala (mesmo fato da pesquisa, outro enfoque que um recurso acima mostre,
com o contrato "acontecimento" completo e dados no formato) OU retirar a afirmação.
Formato: {{"ajustes": [{{"id": "e4", "acao": "reescrever", "fala": "...", "acontecimento": {{...}}, "foto": "a3"|null, "base": "trecho do FATO"}}
 | {{"id": "e7", "acao": "retirar", "motivo": "..."}}]}}"""


def _chamar_padrao(prompt):
    from src import gemini
    return gemini.json_(prompt, validar=lambda o: isinstance(o, dict) and isinstance(o.get('ajustes'), list))


def _aplicar(v: dict, ajustes: list[dict], plano: dict) -> list[str]:
    feitos, por = [], {p['evento']: p for p in plano['acontecimentos']}
    for a in ajustes or []:
        p = por.get(a.get('id'))
        if not p or p['status'] != STATUS_NAO:
            continue
        idx = p['cenas']
        if a.get('acao') == 'reescrever' and str(a.get('fala') or '').strip() and isinstance(a.get('acontecimento'), dict):
            c = v['cenas'][idx[0]]
            c['fala'] = a['fala'].strip()
            c['acontecimento'] = {**a['acontecimento'], 'id': a['id']}
            if a.get('foto'):
                c['foto'] = a['foto']
            for k in ('sub', 'n_sub', 'fala_ideia'):
                c.pop(k, None)
            for k in sorted(idx[1:], reverse=True):
                v['cenas'].pop(k)
            feitos.append(f"{a['id']}: reescrito ({str(a.get('base') or '')[:60]})")
    return feitos


def _retirar(v: dict, plano: dict) -> tuple[list[str], list[str]]:
    """Retira acontecimentos ainda inviáveis quando isso NÃO quebra a estrutura: não é gancho/revelação/fechamento, a
    fala seguinte não depende dela (anáfora) e sobram ≥ 4 acontecimentos narrativos."""
    retirados, impossiveis = [], []
    narrativos = [p for p in plano['acontecimentos'] if v['cenas'][p['cenas'][0]].get('tipo') not in ESTRUTURA]
    for p in sorted([p for p in plano['acontecimentos'] if p['status'] == STATUS_NAO], key=lambda p: -p['cenas'][0]):
        c0 = v['cenas'][p['cenas'][0]]
        prox = v['cenas'][p['cenas'][-1] + 1] if p['cenas'][-1] + 1 < len(v['cenas']) else None
        if c0.get('tipo') in ESTRUTURA or (prox and ANAFORA.match(re.sub(r'\*', '', prox.get('fala') or ''))) \
                or len(narrativos) - len(retirados) - 1 < 4 or len(retirados) >= MAX_RETIRADAS:
            impossiveis.append(p['evento']); continue
        for k in sorted(p['cenas'], reverse=True):
            v['cenas'].pop(k)
        retirados.append(p['evento'])
    return retirados, impossiveis


def vincular(v: dict, acervo_texto: str = '', chamar=None) -> dict:
    """Constrói o plano; se houver INVIÁVEL: 1 ajuste de enfoque → novo plano → retirada segura → ou recusa (ValueError).
    Grava o plano final em v['_plano_visual_exec'] (vai para o checkpoint do roteiro)."""
    from src.v2 import prevalidacao
    plano = construir(v)
    hist = {'inicial': [{k: p[k] for k in ('evento', 'status', 'representacao')} for p in plano['acontecimentos']], 'ajuste': None, 'retirados': []}
    if plano['inviaveis']:
        inv = [{'id': p['evento'], 'fala': p['fala'], 'tipo': p['tipo'], 'por_que': p['justificativa'][:200]} for p in plano['acontecimentos'] if p['status'] == STATUS_NAO]
        try:
            r = (chamar or _chamar_padrao)(PROMPT_AJUSTE.format(fatos=str(v.get('fatos') or '')[:9000], acervo=acervo_texto[:5000],
                                                                formato=contrato.FORMATO_CAMPOS, inviaveis=json.dumps(inv, ensure_ascii=False, indent=1)))
            feitos = _aplicar(v, (r or {}).get('ajustes') or [], plano)
        except Exception as e:                      # provedor fora: segue sem ajuste (sem retry)
            feitos = [f'ajuste indisponível: {str(e)[:80]}']
        hist['ajuste'] = feitos
        prevalidacao.prevalidar(v)                  # só correções determinísticas (sem IA) no que foi reescrito
        plano = construir(v)
        if plano['inviaveis']:
            ret, imp = _retirar(v, plano)
            hist['retirados'] = ret
            if ret:
                plano = construir(v)
            if plano['inviaveis']:
                v['_plano_visual_exec'] = {**plano, 'historico': hist}
                estados.registrar(v, 'PLANO_VISUAL_EXECUTAVEL', False, causa='inviáveis após 1 ajuste: ' + ', '.join(plano['inviaveis']),
                                  entradas={'cenas': v['cenas']})
                det = ' | '.join(f"{p['evento']}: {p['justificativa'][:120]}" for p in plano['acontecimentos'] if p['status'] == STATUS_NAO)
                raise ValueError(f'material ruim: roteiro visualmente inviável antes da narração (plano vinculante, 1 ajuste feito) — {det}')
    v['_plano_visual_exec'] = {**plano, 'historico': hist}
    estados.registrar(v, 'PLANO_VISUAL_EXECUTAVEL', True, entradas={'cenas': v['cenas']},
                      artefatos={'acontecimentos': len(plano['acontecimentos']), 'com_revisao': sum(p['status'] == STATUS_REV for p in plano['acontecimentos'])})
    return v['_plano_visual_exec']


def resumo(pl: dict) -> str:
    a = pl.get('acontecimentos') or []
    h = pl.get('historico') or {}
    return (f"plano visual: {len(a)} acontecimento(s) · {sum(p['status'] == STATUS_OK for p in a)} representável(is) · "
            f"{sum(p['status'] == STATUS_REV for p in a)} com revisão · {sum(p['status'] == STATUS_NAO for p in a)} inviável(is)"
            + (f" · ajuste: {'; '.join(h['ajuste'])}" if h.get('ajuste') else '') + (f" · retirados: {', '.join(h['retirados'])}" if h.get('retirados') else '')
            + ''.join(f"\n  {p['evento']} {p['tipo']}: {p['status']} · {p['representacao'] or '-'}"
                      f"{' ' + p['composicao'] if p.get('composicao') else ''}{' ' + p['recurso']['id'] if p.get('recurso') else ''}"
                      f"{' · fonte: ' + p['fato']['fonte'] if p.get('fato') else ''}" for p in a))
