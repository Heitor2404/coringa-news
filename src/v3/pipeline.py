"""Diretor automático V3.1 no fluxo real (MOTOR_VISUAL=v3, chamado por main.montar_video).

Ordem: roteiro definitivo (já pesquisado) → biblioteca global (cataloga o acervo do vídeo e recupera mídia já catalogada)
→ contexto recuperado (receitas, erros pertinentes, composições viáveis, licenças) → STORYBOARD PELO MODELO (1 chamada;
no máximo 1 correção dirigida pelos erros do validador) → validação por código → regiões (visão só para o que a
biblioteca ainda não sabe) → narração → tempos pela fala alinhada → montagem (src/v2/diretor.montar) → prévia por
quadros (palco, sem MP4) → MP4 → fiscal técnico e editorial → registro para feedback.

Regras que bloqueiam o vídeo (sem MP4): acontecimento crítico sem plano válido; plano crítico que só tem erros; prévia com
erro de página. O storyboard usado na montagem é exatamente o que o modelo devolveu (com as correções registradas).
"""
from __future__ import annotations

import copy
import json
import os
import re
import time
from pathlib import Path

from src.v2 import diretor
from src.v3 import receitas as receitas_mod

TRANSICOES = {'corte', 'dissolve', 'zoom', 'mascara', 'deslize', 'whip', 'iris', 'preto'}
FUNCOES_NARR = {'gancho', 'contexto', 'mecanismo', 'consequencia', 'revelacao', 'fechamento'}
COMPS_FOTO = {'doc.plano'}
COMPS_ESPECIAIS = {   # composições que o diretor pode pedir com parâmetros próprios (conferidos aqui)
    'doc.eclusa': 'esquema de eclusas em degraus (params: degraus, desnivel_m, alto, baixo — números dos FATOS)',
    'doc.molde': 'esquema de molde/vazio preenchido (params: rotulos {camada, vazio, gesso, molde})',
    'comparacao.antes_depois': 'duas fotos reais do MESMO assunto em datas diferentes (params: img_antes, img_depois = ids do ACERVO, rotulo_antes, rotulo_depois ≤ 18)',
    'video.documental': 'clipe real do acervo (recurso_visual tipo video)',
}
MAX_TEXTO, MAX_SELO = 34, 40
ANO = re.compile(r'^(1[0-9]{3}|20[0-9]{2})$')

PROMPT = """Você é o diretor de um documentário curto vertical (9:16, {plataforma}). Pergunta central: {pergunta}
Escreva o STORYBOARD: um plano por trecho (ou parte de trecho) da narração, cobrindo TODOS os trechos, em ordem.
Responda só JSON: {{"planos": [...]}}.

Regras de direção (obrigatórias):
- A foto/vídeo real relevante é o elemento principal. Não cubra fotografia com cartão de texto.
- Todo movimento tem intenção (revelar, aproximar, localizar, acompanhar, explicar, comparar); sem intenção: "fixo".
- Anotação só sobre objeto que está NA foto ("objeto_principal"/"alvo" serão localizados pela visão; se não achar, cai).
- Mecanismo/processo é mostrado por composição que ANIMA a ação (veja as viáveis de cada acontecimento), não por cartões.
- Selo honesto: REGISTRO (foto do próprio fato, ano compatível), CONTEXTO (lugar/objeto relacionado, não o instante),
  DOCUMENTO, ESQUEMA, RECONSTRUÇÃO, REPRESENTAÇÃO HISTÓRICA (gravura/pintura de época).
- Não invente fatos nem números: todo número na tela está nos FATOS, com unidade. Rótulo ≤ 34 caracteres, selo ≤ 40.
- Não repita a mesma foto em planos seguidos; no máximo 2 usos por vídeo. Varie transições: {transicoes}.
- "na_palavra": palavra exata da narração em que a anotação aparece.
{erros}

Receitas de direção recuperadas para este vídeo (padrões; não copie fatos):
{receitas}

Contrato de cada plano:
{{"trechos": [índices dos trechos da narração que o plano cobre; um trecho pode ser dividido em 2 planos com "comeca_na_palavra"],
 "comeca_na_palavra": "<opcional: palavra do trecho onde este plano começa>", "evento_id", "fato_id" (id dos FATOS), "receita" (id),
 "funcao_narrativa" (gancho|contexto|mecanismo|consequencia|revelacao|fechamento),
 "recurso_visual": {{"tipo": "foto|composicao|video", "id": "<id do ACERVO ou da composição>"}}, "composicao",
 "funcao_documental", "objeto_principal", "plano_inicial", "plano_final" (geral|contexto|objeto|detalhe ou {{"objeto": "<outro objeto>", "enquadramento": "detalhe"}}),
 "acao_visual", "movimento_camera", "anotacoes": [{{"tipo": "circulo|contorno|foco|seta|trajeto|ponto", "alvo", "ate" (seta), "texto", "na_palavra"}}],
 "params_do_contrato": true (para composição viável de um acontecimento: os dados vêm do contrato), "params": {{...}} (só composições especiais),
 "tempos_palavras": {{"<passo>": "<palavra>"}} (opcional), "transicao", "selo_texto", "criterio_de_validacao": ["..."]}}

COMPOSIÇÕES ESPECIAIS: {especiais}
ACONTECIMENTOS (id · tipo · crítico · trechos · o que mostrar · composições viáveis com os dados do contrato):
{eventos}
FATOS (id: texto): {fatos}
ACERVO (id · tipo · o que mostra · ano · licença · usos anteriores): {acervo}
NARRAÇÃO (índice: trecho): {falas}"""

PROMPT_CORRECAO = """O storyboard abaixo foi conferido por código e tem estes problemas (plano: problema):
{erros}
Corrija SÓ o necessário e devolva o storyboard inteiro no mesmo formato JSON {{"planos": [...]}}. Mesmas regras e mesmo acervo.
STORYBOARD: {sb}"""


# ---------------------------------------------------------------- entradas do diretor
def falas_de(v: dict) -> list[str]:
    return [re.sub(r'\s+', ' ', str(c.get('fala') or '').replace('*', '')).strip() for c in v['cenas']]


def eventos_de(v: dict) -> list[dict]:
    from src.v2 import contrato
    ev = {}
    for i, c in enumerate(v['cenas']):
        ac = contrato.declarado(c)
        if not ac or not ac.get('id'):
            continue
        e = ev.setdefault(ac['id'], {'id': ac['id'], 'tipo': ac.get('tipo'), 'critico': contrato.critico(ac), 'trechos': [],
                                     'mostrar': str(ac.get('mostrar') or ac.get('sujeito') or '')[:120], 'ac': ac})
        e['trechos'].append(i)
        try:
            e['viaveis'] = [x for x in contrato.viaveis(ac.get('tipo'), ac.get('dados') or {}, ac) if contrato.comp_aceita(ac, x)]
        except Exception:
            e['viaveis'] = []
    return list(ev.values())


def fatos_numerados(fatos) -> list[tuple[str, str]]:
    linhas = [l.strip(' -•*\t') for l in str(fatos or '').splitlines()]
    linhas = [l for l in linhas if len(l) > 25 and not l.isupper()]
    return [(f'f{i + 1}', l[:260]) for i, l in enumerate(linhas)]


def acervo_diretor(v: dict, bib, video: str, tema: str) -> tuple[dict, dict]:
    """Acervo que o diretor enxerga: o do vídeo (ids de produção, catalogados na biblioteca) + mídia da biblioteca global
    relevante ao tema que veio de OUTROS vídeos (ids cm-…). → (acervo para diretor.montar, registro de reuso)."""
    from src.v3 import biblioteca as B
    base = {}
    for x in v.get('acervo') or []:
        if x.get('arq') and Path(x['arq']).exists():
            base[x['id']] = x
    ing = B.ingerir_acervo(bib, list(base.values()), video=video, tema=tema)
    out = {}
    for alias, x in base.items():
        g = bib.obter(ing['mapa'][alias])
        ent = _entrada(g, x['arq'], alias)
        ent['credito'] = str(x.get('credito') or g.get('atribuicao') or '')
        out[alias] = ent
    consulta = ' '.join([tema, str(v.get('titulo') or '')] + [e['mostrar'] for e in eventos_de(v)])
    globais = []
    for g in bib.buscar(consulta, limite=10):
        if g['id'] in ing['mapa'].values():
            continue
        usos_outros = [u for u in bib.usos(g['id']) if u['video'] != video]
        if not usos_outros:
            continue
        p = bib.recuperar(g['id'])
        if p:
            out[g['id']] = _entrada(g, str(p), g['id'])
            globais.append({'id': g['id'], 'pontos': g['pontos'], 'termos': g['termos'], 'de_videos': sorted({u['video'] for u in usos_outros})})
    return out, {'reuso_no_proprio_acervo': ing['reusos'], 'recuperadas_de_outros_videos': globais, 'estat': dict(bib.estat)}


def _entrada(g: dict, arq: str, alias: str) -> dict:
    cred = g.get('atribuicao') or ''
    return {'id': alias, 'global': g['id'], 'arq': arq, 'wh': [g.get('largura') or 1600, g.get('altura') or 1000], 'sha': g['sha256'],
            'ano': g.get('ano'), 'mostra': g.get('mostra') or g.get('descricao') or g.get('titulo'), 'credito': cred, 'ia': bool(g.get('ia')),
            'tipo': g.get('tipo'), 'uso_comercial': g.get('uso_comercial'),
            'credito_curto': re.sub(r'\s*,?\s*via Wikimedia Commons', ' · Wikimedia Commons', cred)[:70]}


def montar_prompt(v: dict, acervo: dict, bib=None, plataforma: str = 'Reels, TikTok, Shorts') -> tuple[str, dict]:
    from src.v3 import memoria
    falas = falas_de(v)
    evs = eventos_de(v)
    tipos = {e['tipo'] for e in evs if e.get('tipo')}
    funcoes = {'gancho', 'revelacao', 'fechamento'} | ({'mecanismo'} if tipos & {'mecanismo', 'processo', 'nivel'} else set()) | {'contexto', 'consequencia'}
    comps = COMPS_FOTO | set(COMPS_ESPECIAIS) | {c for e in evs for c in e.get('viaveis') or []}
    rs = receitas_mod.recuperar(tipos, funcoes, comps)
    errs = memoria.erros_pertinentes(tipos)
    regras = memoria.regras_para_producao(tipos)
    linhas_err = [f"- [{e['id']}] {e['regra_diretor']}" for e in errs] + [f"- [{r['id']}] {r['texto']}" for r in regras]
    fat = fatos_numerados(v.get('fatos'))
    usos = {}
    if bib:
        for k, x in acervo.items():
            usos[k] = len([u for u in bib.usos(x['global'])])
    ac_txt = '\n'.join(f"{k} · {x.get('tipo') or 'foto'} · {str(x.get('mostra') or '')[:110]} · {x.get('ano') or '?'} · "
                       f"{'comercial ok' if x.get('uso_comercial') == 'sim' else 'licença não liberada: NÃO USE'} · usos={usos.get(k, 0)}"
                       for k, x in acervo.items() if not x.get('ia'))
    ev_txt = '\n'.join(f"{e['id']} · {e['tipo']} · {'CRÍTICO' if e['critico'] else 'apoio'} · trechos {e['trechos']} · {e['mostrar']} · "
                       f"viáveis: {', '.join(e.get('viaveis') or []) or 'nenhuma (use foto real)'}" for e in evs)
    p = (PROMPT.replace('{plataforma}', plataforma).replace('{pergunta}', str(v.get('pergunta') or v.get('titulo') or ''))
         .replace('{transicoes}', ', '.join(sorted(TRANSICOES)))
         .replace('{erros}', ('Erros já corrigidos que NÃO podem voltar:\n' + '\n'.join(linhas_err)) if linhas_err else '')
         .replace('{receitas}', receitas_mod.texto_prompt(rs) or '(nenhuma)')
         .replace('{especiais}', '; '.join(f'{k}: {d}' for k, d in COMPS_ESPECIAIS.items()))
         .replace('{eventos}', ev_txt or '(sem contrato de acontecimentos)')
         .replace('{fatos}', '\n'.join(f'{i}: {t}' for i, t in fat)[:9000])
         .replace('{acervo}', ac_txt[:7000])
         .replace('{falas}', '\n'.join(f'{i}: {f}' for i, f in enumerate(falas))))
    ctx = {'receitas': [r['id'] for r in rs], 'receitas_estado': {r['id']: r['estado'] for r in rs}, 'erros': [e['id'] for e in errs],
           'regras_editoriais': [r['id'] for r in regras], 'eventos': [{k: e[k] for k in ('id', 'tipo', 'critico', 'trechos', 'viaveis')} for e in evs],
           'fatos_ids': [i for i, _ in fat], 'acervo_ids': list(acervo), 'tamanho_prompt': len(p)}
    return p, ctx


# ---------------------------------------------------------------- validação por código (sem IA)
def _numeros(txt: str) -> list[str]:
    return re.findall(r'\d+(?:[.,]\d+)*', str(txt or ''))


def _num_norm(s: str) -> str:
    return s.replace('.', '').replace(',', '.')


def _texto_tem_numero(n: str, base: str) -> bool:
    alvo = _num_norm(n)
    return any(_num_norm(x) == alvo for x in _numeros(base))


def _tem_unidade(txt: str, n: str) -> bool:
    from src.v2.contrato import UNIDADES_TEXTO
    i = txt.find(n)
    depois = txt[i + len(n):].strip() if i >= 0 else ''
    return bool(UNIDADES_TEXTO.match(depois)) or depois.startswith(('mil', 'milh', 'bilh', 'x', '×', '%', 'º', '°'))


def validar_storyboard(sb: dict, v: dict, acervo: dict, ctx: dict) -> list[tuple[int | None, str]]:
    """Problemas objetivos (plano, problema). Complementa diretor.validar (fato, função, IA, crédito, ano)."""
    from src.v2 import contrato
    falas = falas_de(v)
    base_num = ' '.join([str(v.get('fatos') or '')] + falas)
    evs = {e['id']: e for e in ctx['eventos']}
    pls = sb.get('planos') or []
    out = []
    cobertos = set()
    usos = {}
    for i, pl in enumerate(pls):
        tr = pl.get('trechos')
        if not isinstance(tr, list) or not tr or not all(isinstance(t, int) and 0 <= t < len(falas) for t in tr):
            out.append((i, f'trechos inválidos: {tr}'))
            tr = []
        cobertos.update(tr)
        if pl.get('funcao_narrativa') not in FUNCOES_NARR:
            out.append((i, f"função narrativa inválida: {pl.get('funcao_narrativa')}"))
        if (pl.get('transicao') or 'corte') not in TRANSICOES:
            out.append((i, f"transição inexistente: {pl.get('transicao')}"))
        comp = pl.get('composicao')
        rv = pl.get('recurso_visual') or {}
        ev = evs.get(pl.get('evento_id'))
        if comp not in COMPS_FOTO | set(COMPS_ESPECIAIS) and not (ev and comp in (ev.get('viaveis') or [])):
            out.append((i, f"composição {comp} não é viável para {pl.get('evento_id')} (viáveis: {', '.join((ev or {}).get('viaveis') or []) or 'nenhuma'})"))
        if rv.get('tipo') in ('foto', 'video'):
            x = acervo.get(rv.get('id'))
            if x and x.get('uso_comercial') != 'sim':
                out.append((i, f"mídia {rv.get('id')} sem licença comercial verificada"))
            if rv.get('id'):
                usos.setdefault(rv['id'], []).append(i)
        if ev and ev['critico'] and ev['tipo'] in contrato.EXIGE_DEMONSTRACAO and comp in contrato.TEXTUAIS | COMPS_FOTO \
                and pl.get('funcao_documental') != 'REGISTRO' and not any(
                    p2.get('evento_id') == ev['id'] and (contrato.demonstra(p2.get('composicao')) or p2.get('composicao') in ('doc.eclusa', 'doc.molde'))
                    for p2 in pls):
            out.append((i, f"{ev['id']} é mecanismo crítico: precisa de composição que demonstre (viáveis: {', '.join(ev.get('viaveis') or []) or 'nenhuma'}), não só foto/cartão"))
        textos = [a.get('texto') or '' for a in pl.get('anotacoes') or []]
        for t in textos:
            if len(t) > MAX_TEXTO:
                out.append((i, f'rótulo com {len(t)} caracteres (máx. {MAX_TEXTO}): "{t}"'))
        if len(str(pl.get('selo_texto') or '')) > MAX_SELO:
            out.append((i, f'selo com mais de {MAX_SELO} caracteres'))
        for t in textos + [str(pl.get('selo_texto') or '')] + [str(x) for x in (pl.get('params') or {}).values() if isinstance(x, (int, float, str))]:
            for n in _numeros(t):
                if ANO.match(n.replace('.', '')):
                    continue
                if not _texto_tem_numero(n, base_num):
                    out.append((i, f'número {n} ("{t[:40]}") não está nos fatos nem na fala'))
                elif t in textos and not _tem_unidade(t, n):
                    out.append((i, f'número {n} sem unidade no rótulo "{t}"'))
        for an in pl.get('anotacoes') or []:
            if an.get('tipo') not in ('circulo', 'contorno', 'foco', 'seta', 'trajeto', 'ponto'):
                out.append((i, f"anotação de tipo desconhecido: {an.get('tipo')}"))
    for k, ix in usos.items():
        if len(ix) > 2:
            out.append((ix[2], f'foto {k} usada {len(ix)} vezes (máx. 2)'))
        for a, b in zip(ix, ix[1:]):
            if b == a + 1:
                out.append((b, f'foto {k} repetida em planos seguidos'))
    falta = [t for t in range(len(falas)) if t not in cobertos]
    if falta:
        out.append((None, f'trechos da narração sem plano: {falta}'))
    for e in ctx['eventos']:
        if e['critico'] and not any(p.get('evento_id') == e['id'] for p in pls):
            out.append((None, f"acontecimento crítico {e['id']} sem plano"))
    return out


# ---------------------------------------------------------------- modelo
def chamar_modelo(prompt: str) -> tuple[dict | None, dict]:
    """Uma chamada. DIRETOR_MODELO=claude (padrão: Claude Code pela assinatura, modelo de roteiro) | gemini (cota grátis)."""
    from src.gemini import extrair_json
    qual = (os.getenv('DIRETOR_MODELO') or 'claude').lower()
    t0 = time.time()
    meta = {'modelo': qual, 'tamanho_prompt': len(prompt)}
    try:
        if qual == 'gemini':
            from src import gemini
            r = gemini.json_(prompt)
            meta.update(resposta_bruta=json.dumps(r, ensure_ascii=False), usd=0.0)
        else:
            from src import claude
            antes = claude.GASTO['usd']
            txt = claude.pedir(prompt)
            meta.update(resposta_bruta=txt, usd=round(claude.GASTO['usd'] - antes, 4), modelo=f'claude/{claude.MODELO}')
            r = extrair_json(txt)
    except Exception as e:
        meta.update(erro=f'{type(e).__name__}: {str(e)[:300]}', segundos=round(time.time() - t0, 1))
        if qual != 'gemini' and os.getenv('GEMINI_API_KEY'):          # Claude fora (limite/assinatura): 1 chamada no Gemini grátis
            os.environ['DIRETOR_MODELO'] = 'gemini'
            try:
                r2, m2 = chamar_modelo(prompt)
            finally:
                os.environ['DIRETOR_MODELO'] = qual
            m2['substituiu'] = meta
            return r2, m2
        return None, meta
    meta['segundos'] = round(time.time() - t0, 1)
    if not isinstance(r, dict) or not isinstance(r.get('planos'), list):
        meta['erro'] = 'resposta sem lista de planos'
        return None, meta
    return r, meta


def storyboard_automatico(v: dict, acervo: dict, bib=None, chamar=None) -> tuple[dict | None, dict]:
    """1 chamada + no máximo 1 correção dirigida. → (storyboard, registro completo para auditoria)."""
    chamar = chamar or chamar_modelo
    prompt, ctx = montar_prompt(v, acervo, bib)
    sb, m1 = chamar(prompt)
    reg = {'prompt': prompt, 'contexto_recuperado': ctx, 'chamadas': [m1], 'resposta_original': copy.deepcopy(sb), 'correcoes': []}
    if sb is None:
        reg['erro'] = m1.get('erro')
        return None, reg
    fatos_ids = set(ctx['fatos_ids'])
    erros = validar_storyboard(sb, v, acervo, ctx) + [(i, e) for i, pl in enumerate(sb['planos'])
                                                       for e in diretor.validar({**pl, 'tempo_inicio': 0, 'tempo_fim': 9}, fatos_ids, acervo)]
    reg['erros_validacao_1'] = [{'plano': i, 'erro': e} for i, e in erros]
    if erros:
        lista = '\n'.join(f"{'geral' if i is None else i}: {e}" for i, e in erros)
        sb2, m2 = chamar(PROMPT_CORRECAO.replace('{erros}', lista).replace('{sb}', json.dumps(sb, ensure_ascii=False)) + '\n\n(Contexto original:)\n' + prompt[:14000])
        reg['chamadas'].append(m2)
        if sb2 is not None:
            reg['correcoes'].append({'tipo': 'correcao_dirigida_pelo_modelo', 'erros': lista, 'resposta': copy.deepcopy(sb2)})
            sb = sb2
        erros = validar_storyboard(sb, v, acervo, ctx) + [(i, e) for i, pl in enumerate(sb['planos'])
                                                           for e in diretor.validar({**pl, 'tempo_inicio': 0, 'tempo_fim': 9}, fatos_ids, acervo)]
    reg['erros_finais'] = [{'plano': i, 'erro': e} for i, e in erros]
    reg['consumo'] = {'chamadas': len(reg['chamadas']), 'usd': round(sum(c.get('usd') or 0 for c in reg['chamadas']), 4),
                      'segundos': round(sum(c.get('segundos') or 0 for c in reg['chamadas']), 1),
                      'caracteres_prompt': sum(c.get('tamanho_prompt') or 0 for c in reg['chamadas'])}
    return sb, reg


# ---------------------------------------------------------------- execução do storyboard
def objetos_pedidos(pl: dict) -> list[str]:
    obs = [pl.get('objeto_principal')]
    for an in pl.get('anotacoes') or []:
        obs += [an.get('alvo'), an.get('ate')]
    for k in ('plano_inicial', 'plano_final'):
        if isinstance(pl.get(k), dict):
            obs.append(pl[k].get('objeto'))
    return list(dict.fromkeys(o for o in obs if o))


def localizar_regioes(sb: dict, acervo: dict, bib, chamar_visao=None) -> dict:
    out = {}
    for pl in sb['planos']:
        rv = pl.get('recurso_visual') or {}
        x = acervo.get(rv.get('id')) if rv.get('tipo') == 'foto' else None
        if not x or pl.get('composicao') != 'doc.plano':
            continue
        feito = bib.localizar(Path(x['arq']), objetos_pedidos(pl), chamar_visao)
        out.setdefault(x['sha'], {'objetos': {}}).update({k: v for k, v in feito.items() if k != 'objetos'})
        out[x['sha']]['objetos'].update(feito.get('objetos') or {})
    return out


def aplicar_tempos(sb: dict, tempos: list[tuple[float, float]], palavras: list[dict], dur: float) -> list[str]:
    """Cada plano recebe o intervalo dos trechos que cobre (narração alinhada). Trecho dividido entre planos: corta na
    palavra pedida; sem a palavra, divide igualmente (registrado). Planos contíguos do 0 até o fim do áudio."""
    avisos = []
    grupos = {}
    for i, pl in enumerate(sb['planos']):
        tr = pl.get('trechos') or []
        if tr:
            grupos.setdefault(tuple(tr), []).append(i)
    for tr, ix in grupos.items():
        a, b = tempos[tr[0]][0], tempos[tr[-1]][1]
        cortes = [a]
        for k, i in enumerate(ix[1:], start=1):
            w = sb['planos'][i].get('comeca_na_palavra')
            t = diretor.tempo_da_palavra(palavras, '', w, a, b) if w else None
            if t is None or t <= cortes[-1] + 1.2:
                t = a + (b - a) * k / len(ix)
                avisos.append(f'plano {i}: divisão do trecho {list(tr)} por tempo igual (palavra {w!r} não achada)')
            cortes.append(t)
        cortes.append(b)
        for k, i in enumerate(ix):
            sb['planos'][i]['tempo_inicio'], sb['planos'][i]['tempo_fim'] = round(cortes[k], 3), round(cortes[k + 1], 3)
    pls = [p for p in sb['planos'] if 'tempo_inicio' in p]
    pls.sort(key=lambda p: p['tempo_inicio'])
    if pls:
        pls[0]['tempo_inicio'] = 0.0
        pls[-1]['tempo_fim'] = round(dur, 3)
        for p, q in zip(pls, pls[1:]):
            p['tempo_fim'] = q['tempo_inicio']
    sb['planos'] = pls
    return avisos


def preparar_params(sb: dict, v: dict, acervo: dict) -> list[str]:
    """Composições não-foto: parâmetros do CONTRATO do acontecimento (nunca inventados) ou dos especiais conferidos."""
    from src.v2 import contrato
    evs = {e['id']: e for e in eventos_de(v)}
    falas = falas_de(v)
    avisos = []
    for i, pl in enumerate(sb['planos']):
        comp = pl.get('composicao')
        if comp == 'doc.plano':
            continue
        ev = evs.get(pl.get('evento_id'))
        if pl.get('params_do_contrato') and ev:
            pl['params'] = contrato.params_tela(ev['ac'], comp, textos=[falas[t] for t in pl.get('trechos') or []] + [str(v.get('fatos') or '')])
        elif comp == 'comparacao.antes_depois':
            p = dict(pl.get('params') or {})
            for k in ('img_antes', 'img_depois'):
                x = acervo.get(p.get(k))
                if not x:
                    avisos.append(f'plano {i}: {k} {p.get(k)} não está no acervo')
                p[k] = x['arq'] if x else None
            pl['params'] = p
        elif comp == 'video.documental':
            x = acervo.get((pl.get('recurso_visual') or {}).get('id'))
            pl['params'] = {'video': x['arq'] if x else None, 'credito': (x or {}).get('credito_curto', '')}
        pl['params'] = {k: val for k, val in (pl.get('params') or {}).items() if val is not None}
    return avisos


def _status_criticos(reg: list[dict], ctx: dict, sb: dict) -> list[str]:
    ok = {r['evento_id'] for r in reg if not r['erros']}
    return [e['id'] for e in ctx['eventos'] if e['critico'] and e['id'] not in ok]


def montar_video(v: dict, pasta: Path, nome: str, trab: Path, musica: Path | None = None, chamar=None, chamar_visao=None,
                 narrar=None, renderizar=None) -> dict:
    """Executa o fluxo V3.1 inteiro para um roteiro pronto. → dict com mp4 (ou None), bloqueios e caminhos dos registros."""
    from src.v3 import biblioteca as B, fiscal_editorial
    dest = pasta / f'{nome}-v3'
    dest.mkdir(parents=True, exist_ok=True)
    T = {}
    t0 = time.time()
    bib = B.Biblioteca()
    tema = str((v.get('_pauta') or {}).get('tema') or v.get('titulo') or nome)
    acervo, reuso = acervo_diretor(v, bib, nome, tema)
    T['biblioteca_s'] = round(time.time() - t0, 2)
    t0 = time.time()
    sb, sreg = storyboard_automatico(v, acervo, bib, chamar)
    T['diretor_s'] = round(time.time() - t0, 2)
    _gravar(dest / 'storyboard_ia.json', {**sreg, 'reuso_biblioteca': reuso})
    res = {'mp4': None, 'bloqueios': [], 'revisoes': [], 'pasta': str(dest), 'tempos': T, 'reuso': reuso,
           'consumo_diretor': sreg.get('consumo')}
    if sb is None:
        res['bloqueios'].append(f"diretor sem storyboard: {sreg.get('erro')}")
        _gravar(dest / 'resultado.json', res)
        return res
    for e in sreg.get('erros_finais') or []:
        if e['plano'] is not None and 0 <= e['plano'] < len(sb['planos']):
            sb['planos'][e['plano']].setdefault('_erros', []).append(e['erro'])
        else:
            res['revisoes'].append(f"storyboard: {e['erro']}")
    t0 = time.time()
    if chamar_visao is None and os.getenv('GEMINI_API_KEY'):
        from src import gemini
        chamar_visao = lambda pr, ims: gemini.json_visao(pr, ims, leve=False)   # noqa: E731
    regioes = localizar_regioes(sb, acervo, bib, chamar_visao)
    T['regioes_s'] = round(time.time() - t0, 2)
    res['regioes'] = {'reusadas': bib.estat['regioes_reusadas'], 'novas': bib.estat['regioes_novas']}
    # narração (depois do storyboard: a direção não depende de tempo inventado)
    t0 = time.time()
    if narrar is None:
        from src import voz
        narrar = lambda cenas, tr: voz.narrar(cenas, tr)   # noqa: E731
    audio, tempos, caps, dur = narrar(v['cenas'], trab)
    T['narracao_s'] = round(time.time() - t0, 2)
    palavras = diretor.palavras_da_narracao(caps)
    avisos = aplicar_tempos(sb, tempos, palavras, dur) + preparar_params(sb, v, acervo)
    _, ctx = montar_prompt(v, acervo, bib)
    cenas, reg = diretor.montar(sb, acervo, regioes, palavras, set(ctx['fatos_ids']))
    for r, pl in zip(reg, sb['planos']):
        r['receita'] = pl.get('receita')
        r['trechos'] = pl.get('trechos')
        r['erros'] += [e for e in pl.get('_erros') or [] if e not in r['erros']]
    validos = {i for i, r in enumerate(reg) if not r['erros']}
    cenas = [c for c in cenas if c['origem'][0] in validos]      # erro do validador V3.1 que sobrou à correção: plano sai
    # plano não-crítico inválido sai e o vizinho cobre o tempo (registrado); crítico sem plano válido bloqueia
    falt = _status_criticos(reg, ctx, sb)
    for e in falt:
        res['bloqueios'].append(f'acontecimento crítico {e} sem plano válido (ERR-011)')
    for k in range(1, len(cenas)):
        cenas[k - 1]['end'] = cenas[k]['start'] if cenas[k]['start'] > cenas[k - 1]['end'] else cenas[k - 1]['end']
    if cenas:
        cenas[0]['start'], cenas[-1]['end'] = 0.0, round(dur, 3)
    for c in cenas:
        rv = (c.get('direcao') or {}).get('recurso_visual') or {}
        x = acervo.get(rv.get('id'))
        if x:
            bib.registrar_uso(x['global'], nome, rv.get('id'), cenas.index(c), (c.get('direcao') or {}).get('funcao_documental') or '',
                              (c.get('direcao') or {}).get('evento_id') or '')
    dados = {'duration': dur, 'meta': {'motor': 'v2', 'plataforma': 'todas', 'titulo': v.get('titulo'), 'categoria': v.get('categoria', ''),
                                       'serie': v.get('serie', ''), 'parte': v.get('parte', 0), 'marca': '@coringa.explica',
                                       'pergunta': v.get('pergunta') or '', 'fontes': list(v.get('fontes') or [])},
             'scenes': cenas, 'captions': caps}
    _gravar(dest / 'direcao.json', {'storyboard_usado': sb, 'registro': reg, 'avisos': avisos})
    _gravar(dest / 'v2_dados.json', dados)
    if res['bloqueios']:                     # bloqueio objetivo: nem prévia nem MP4 (nada caro para um vídeo recusado)
        _gravar(dest / 'resultado.json', res)
        bib.exportar_manifesto(dest / 'biblioteca_manifesto.jsonl')
        bib.fechar()
        return res
    # prévia por quadros (sem MP4): erro de página ou geometria aparece aqui, barato
    t0 = time.time()
    prev = previa_quadros(dados, dest, trab)
    T['previa_s'] = round(time.time() - t0, 2)
    res['previa'] = {'erros_pagina': prev['erros_pagina'], 'problemas_geometria': len(prev['problemas_geometria'])}
    _gravar(dest / 'previa_geometria.json', prev['problemas_geometria'])
    if prev['erros_pagina']:
        res['revisoes'].append(f"página: {'; '.join(map(str, prev['erros_pagina'][:3]))}")
    t0 = time.time()
    saida = pasta / f'{nome}.mp4'
    if renderizar is None:
        from src.render import render
        renderizar = lambda d, a, s, tr, m: render.renderizar(copy.deepcopy(d), a, s, tr / '_render_v3', musica=m)   # noqa: E731
    renderizar(dados, audio, saida, trab, musica)
    T['render_s'] = round(time.time() - t0, 1)
    t0 = time.time()
    fis = fiscal_editorial.avaliar(saida, dados, reg, ctx, v, sreg)
    T['fiscal_s'] = round(time.time() - t0, 1)
    _gravar(dest / 'fiscal_v3.json', fis)
    (dest / 'fiscal_v3.md').write_text(fiscal_editorial.texto(fis), encoding='utf-8')
    fiscal_editorial.folha_contato(saida, dados, dest / 'folha_contato.jpg')
    res.update(mp4=str(saida), bloqueios=res['bloqueios'] + [a['problema'] for a in fis['achados'] if a['classe'] == 'bloqueio'],
               revisoes=res['revisoes'] + [a['problema'] for a in fis['achados'] if a['classe'] == 'revisao'], fiscal=fis['resumo'])
    (dest / 'feedback_modelo.csv').write_text(
        'video,t (mm:ss),categoria,gravidade,texto\n' + ''.join(f"{nome},{int(c['start'] // 60)}:{c['start'] % 60:04.1f},,," + '\n' for c in cenas),
        encoding='utf-8')
    bib.exportar_manifesto(dest / 'biblioteca_manifesto.jsonl')
    _gravar(dest / 'resultado.json', res)
    bib.fechar()
    return res


def previa_quadros(dados: dict, dest: Path, trab: Path) -> dict:
    from src.v2 import palco
    erros, geo = [], []
    try:
        with palco.abrir(palco.preparar(copy.deepcopy(dados)), trab / '_palco_v3') as pg:
            geo = palco.medir(pg, dados['duration'], .5)
            for k, sc in enumerate(dados['scenes']):
                palco.capturar(pg, round(sc['start'] + (sc['end'] - sc['start']) * .7, 2), dest / f'previa_{k:02d}.jpg', 80)
            erros = list(pg.erros) + list(pg.evaluate('V2.avisos') or [])
    except Exception as e:
        erros.append(f'prévia falhou: {str(e)[:200]}')
    return {'erros_pagina': erros, 'problemas_geometria': geo}


def _gravar(arq: Path, obj):
    arq.write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
