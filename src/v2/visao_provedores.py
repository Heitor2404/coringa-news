"""PROVEDORES DE VISÃO (Evidência V1, experimental, só modo sombra) — adaptador comum Gemini → NVIDIA.

- Uma tarefa (catálogo cego ou casamento cego) = UMA chamada por provedor, sem nova tentativa.
- Fallback Gemini → NVIDIA (OpenRouter, nvidia/nemotron-3.5-super-vl:free) só por indisponibilidade/limite (429, 503,
  504, timeout). Se os dois falharem: leitura INCERTA (a regra nunca dá PROVA sem visão).
- Teto de chamadas por vídeo (`Orcamento`). Custo: os dois endpoints usados são gratuitos; chamada paga não existe aqui.
- Dupla leitura (os dois provedores) só para acontecimentos críticos ou ambíguos. Concordância NÃO vira segunda família:
  as duas leituras continuam sendo a família VISÃO. Discordância relevante → leitura incerta marcada (revisão humana).
- Privacidade (endpoint grátis da NVIDIA registra o uso e pede para não enviar informação confidencial): a NVIDIA só
  recebe imagens cujo catálogo cego NÃO aponta pessoa, rosto, multidão, documento, tela ou texto como conteúdo.
  Sem catálogo da imagem → não envia (conservador). Prompt cego: nunca vai legenda, nome de arquivo, fonte ou autor.
- Tudo registrado: provedor, modelo, latência, erro, motivo do fallback, imagens retidas, discordâncias.
"""
from __future__ import annotations

import base64
import json
import os
import re
import time

GEMINI_MODELO = os.environ.get('EVIDENCIA_GEMINI_MODELO', 'gemini-3.5-flash-lite')     # o que respondeu a todos os testes
NVIDIA_MODELO = 'nvidia/nemotron-3.5-super-vl:free'
TIMEOUT_S = 90
TETO_PADRAO = 4                       # chamadas de visão por vídeo (catálogo + casamento + dupla leitura)
INDISPONIVEL = re.compile(r'\b(429|500|502|503|504)\b|UNAVAILABLE|RESOURCE_EXHAUSTED|DEADLINE|timed? ?out|Timeout', re.I)
PESSOAL = re.compile(r'\b(pessoa|pessoas|rosto|rostos|face|multid|crian|homem|mulher|gente|retrato|astronauta|selfie|'
                     r'documento|tela|placa de carro|cracha|passaporte)', re.I)


class Orcamento:
    def __init__(self, teto: int = TETO_PADRAO):
        self.teto, self.usadas, self.registro = teto, 0, []

    def pode(self) -> bool:
        return self.usadas < self.teto


# ───────────────────────── provedores (uma chamada, sem nova tentativa) ─────────────────────────
def _gemini(prompt: str, imagens: list[bytes]) -> str:
    from google import genai
    from google.genai import types
    chave = os.environ.get('GEMINI_API_KEY')
    if not chave:
        raise RuntimeError('sem GEMINI_API_KEY')
    cli = genai.Client(api_key=chave, http_options=types.HttpOptions(timeout=TIMEOUT_S * 1000))
    partes = []
    for k, b in enumerate(imagens):
        partes += [f'IMAGEM {k}:', types.Part.from_bytes(data=b, mime_type='image/jpeg')]
    partes.append(prompt)
    r = cli.models.generate_content(model=GEMINI_MODELO, contents=partes,
                                    config=types.GenerateContentConfig(response_mime_type='application/json', temperature=0.2))
    return r.text


def _nvidia(prompt: str, imagens: list[bytes]) -> str:
    import requests
    chave = os.environ.get('OPENROUTER_API_KEY', '').strip()
    if not chave:
        raise RuntimeError('sem OPENROUTER_API_KEY')
    conteudo = []
    for k, b in enumerate(imagens):
        conteudo += [{'type': 'text', 'text': f'IMAGEM {k}:'},
                     {'type': 'image_url', 'image_url': {'url': 'data:image/jpeg;base64,' + base64.b64encode(b).decode()}}]
    conteudo.append({'type': 'text', 'text': prompt})
    r = requests.post('https://openrouter.ai/api/v1/chat/completions', timeout=TIMEOUT_S,
                      headers={'Authorization': f'Bearer {chave}', 'X-Title': 'coringa-evidencia-sombra'},
                      json={'model': NVIDIA_MODELO, 'temperature': 0.2, 'response_format': {'type': 'json_object'},
                            'messages': [{'role': 'user', 'content': conteudo}]})
    if r.status_code != 200:
        raise RuntimeError(f'{r.status_code} {r.text[:200]}')
    return r.json()['choices'][0]['message']['content']


PROVEDORES = {'gemini': (_gemini, lambda: GEMINI_MODELO), 'nvidia': (_nvidia, lambda: NVIDIA_MODELO)}


def extrair(texto: str) -> dict | None:
    """JSON da resposta (tolerante a cerca de código ```json)."""
    if not texto:
        return None
    t = re.sub(r'^```(?:json)?|```$', '', texto.strip(), flags=re.M).strip()
    try:
        return json.loads(t)
    except Exception:
        m = re.search(r'\{.*\}', t, re.S)
        try:
            return json.loads(m.group(0)) if m else None
        except Exception:
            return None


def permitido_nvidia(catalogo_img: dict | None) -> tuple[bool, str]:
    """Restrição conservadora para o endpoint grátis: sem catálogo, ou com pessoa/rosto/documento/texto → não envia."""
    if not catalogo_img:
        return False, 'sem catálogo cego da imagem: não envio ao endpoint grátis'
    txt = f"{catalogo_img.get('elemento_principal', '')} {catalogo_img.get('conteudo', '')} {catalogo_img.get('natureza', '')}"
    if PESSOAL.search(txt):
        return False, 'imagem com pessoa/rosto/documento: não envio ao endpoint grátis'
    tv = catalogo_img.get('texto_visivel') or {}
    if tv.get('presente') and tv.get('e_o_conteudo'):
        return False, 'imagem cujo conteúdo é texto: não envio ao endpoint grátis'
    return True, ''


def ler(prompt: str, imagens: list[bytes], orc: Orcamento, ordem=('gemini', 'nvidia'), tarefa: str = 'casamento',
        bloqueio_por_provedor: dict | None = None, chamadores: dict | None = None) -> dict:
    """Uma leitura com fallback. `bloqueio_por_provedor` {provedor: motivo} impede um provedor (ex.: privacidade).
    `chamadores` substitui as funções reais (testes offline). Devolve {provedor, modelo, texto, json, tentativas}."""
    fns = chamadores or {k: f for k, (f, _) in PROVEDORES.items()}
    tentativas, anterior = [], None
    for prov in ordem:
        modelo = PROVEDORES[prov][1]()
        if (bloqueio_por_provedor or {}).get(prov):
            tentativas.append({'provedor': prov, 'modelo': modelo, 'pulado': bloqueio_por_provedor[prov]})
            continue
        if not orc.pode():
            tentativas.append({'provedor': prov, 'modelo': modelo, 'pulado': f'teto de {orc.teto} chamadas atingido'})
            break
        orc.usadas += 1
        t = time.time()
        try:
            txt = fns[prov](prompt, imagens)
            j = extrair(txt)
            reg = {'provedor': prov, 'modelo': modelo, 'segundos': round(time.time() - t, 1), 'json_valido': j is not None,
                   **({'fallback_de': anterior} if anterior else {})}
            tentativas.append(reg)
            orc.registro.append({'tarefa': tarefa, **reg})
            if j is not None:
                return {'provedor': prov, 'modelo': modelo, 'texto': txt, 'json': j, 'tentativas': tentativas}
            break                                       # JSON inválido NÃO troca de provedor: leitura incerta
        except Exception as e:
            reg = {'provedor': prov, 'modelo': modelo, 'segundos': round(time.time() - t, 1), 'erro': str(e)[:200]}
            tentativas.append(reg)
            orc.registro.append({'tarefa': tarefa, **reg})
            if not INDISPONIVEL.search(str(e)) and 'sem ' not in str(e):
                break                                   # erro que não é de disponibilidade: não troca de provedor
            anterior = {'provedor': prov, 'motivo': str(e)[:80]}
    return {'provedor': None, 'modelo': None, 'texto': None, 'json': None, 'tentativas': tentativas, 'incerta': True}


# ───────────────────────── combinação no contrato da Evidência V1 ─────────────────────────
GRUPO = {'acao': 'mostra', 'estado_final': 'mostra', 'estado_inicial': 'antes', 'entidade': 'entidade', 'consequencia': 'depois',
         'outro_estado': 'nao', 'nao_mostra': 'nao', 'incerto': 'incerto'}


def avaliacoes(leitura: dict, ordem_imagens: list[str]) -> dict:
    """{(acontecimento, imagem): avaliação} de uma leitura de casamento, com o provedor anotado."""
    out = {}
    for a in ((leitura.get('json') or {}).get('avaliacoes') or []):
        try:
            img = ordem_imagens[int(a.get('imagem'))]
        except (TypeError, ValueError, IndexError):
            continue
        out[(str(a.get('acontecimento')), img)] = {**a, 'provedor': leitura.get('provedor'), 'modelo': leitura.get('modelo')}
    return out


def combinar(a: dict | None, b: dict | None) -> dict | None:
    """Duas leituras do MESMO par (acontecimento, imagem). Concordância relevante → mantém (ainda família VISÃO, uma só).
    Discordância relevante (uma diz que mostra, a outra não, ou classes diferentes) → incerto + discordância registrada."""
    if not b:
        return a
    if not a:
        return b
    ga, gb = GRUPO.get(a.get('confere_com'), 'incerto'), GRUPO.get(b.get('confere_com'), 'incerto')
    rel = (ga != gb and 'mostra' in (ga, gb)) or (a.get('classe_confere') is not None and b.get('classe_confere') is not None
                                                  and a.get('classe_confere') != b.get('classe_confere'))
    leituras = [{k: x.get(k) for k in ('provedor', 'modelo', 'confere_com', 'classe_confere', 'confianca', 'movimento_visivel')} for x in (a, b)]
    if rel:
        return {'confere_com': 'incerto', 'classe_confere': None, 'confianca': 'baixa', 'discordancia': leituras,
                'provedor': 'dupla_discordante'}
    base = dict(a)
    if a.get('confere_com') != b.get('confere_com'):        # mesmo grupo, campos vizinhos: o mais conservador
        base['confere_com'] = 'estado_final' if {a.get('confere_com'), b.get('confere_com')} == {'acao', 'estado_final'} else a.get('confere_com')
    base['confianca'] = min((a.get('confianca'), b.get('confianca')), key=lambda c: {'alta': 2, 'media': 1}.get(c, 0))
    base['dupla_concordante'] = leituras
    base['provedor'] = 'dupla_concordante'
    return base


def precisa_dupla(ev: dict, leitura_par: dict | None, catalogo_img: dict | None) -> bool:
    """Crítico com leitura que pode virar PROVA, ou leitura ambígua (confiança não alta, catálogo discordante)."""
    if not leitura_par:
        return False
    mostra = leitura_par.get('confere_com') in (ev.get('exige') or [])
    ambigua = leitura_par.get('confianca') != 'alta' or (
        catalogo_img is not None and leitura_par.get('confere_com') == 'acao' and catalogo_img.get('acao_em_curso') is False
        and leitura_par.get('movimento_visivel') is not False)
    return (bool(ev.get('critico')) and mostra) or ambigua


def para_visao(par: dict | None, catalogo_img: dict | None) -> dict | None:
    """Leitura (simples ou combinada) + catálogo → visão no formato que evidencia.avaliar consome."""
    if not par and not catalogo_img:
        return None
    par = par or {}
    cat = catalogo_img or {}
    v = {'origem': 'visao_' + str(par.get('provedor') or 'catalogo'), 'viu_legenda': False,
         'natureza': cat.get('natureza'), 'generica': bool(cat.get('generica')), 'texto_visivel': cat.get('texto_visivel') or {},
         'confere_com': par.get('confere_com', 'incerto'), 'classe_confere': par.get('classe_confere'),
         'confianca': par.get('confianca', 'baixa'), 'movimento_visivel': par.get('movimento_visivel'),
         'catalogo': {'natureza': cat.get('natureza'), 'generica': bool(cat.get('generica')),
                      'acao_em_curso': cat.get('acao_em_curso')} if cat else None}
    for k in ('discordancia', 'dupla_concordante', 'provedor', 'modelo'):
        if par.get(k):
            v[k] = par[k]
    return v


# ───────────────────────── leitura de um roteiro inteiro (modo sombra) ─────────────────────────
def _so_permitidas(ids: list[str], catalogo: dict) -> tuple[list[str], dict]:
    ok, retidas = [], {}
    for i in ids:
        pode, motivo = permitido_nvidia(catalogo.get(i))
        if pode:
            ok.append(i)
        else:
            retidas[i] = motivo
    return ok, retidas


def _texto_eventos(eventos: list[dict]) -> str:
    return '\n'.join(f"{e['id']}: elemento={e.get('sujeito')}; ação={e.get('acao')}; antes={e.get('estado_inicial') or '-'}; "
                     f"depois={e.get('estado_final') or '-'}" for e in eventos)


def ler_roteiro(eventos: list[dict], imagens: dict[str, bytes], prompt_catalogo: str, prompt_casar: str,
                orc: Orcamento | None = None, chamadores: dict | None = None) -> dict:
    """Catálogo cego (só Gemini: sem catálogo não há como checar privacidade para a NVIDIA) → casamento (Gemini → NVIDIA
    só com imagens permitidas) → dupla leitura do OUTRO provedor só para pares críticos/ambíguos. Devolve
    {visoes: {(evento, imagem): visão}, registro: [...], catalogo: {...}}."""
    orc = orc or Orcamento()
    ids = list(imagens)
    reg = {'chamadas': orc.registro, 'retidas_nvidia': {}, 'discordancias': [], 'dupla': []}
    cat = ler(prompt_catalogo.format(n=len(ids)), [imagens[i] for i in ids], orc, ordem=('gemini',), tarefa='catalogo', chamadores=chamadores)
    catalogo = {}
    for a in ((cat.get('json') or {}).get('imagens') or []):
        try:
            catalogo[ids[int(a.get('i'))]] = a
        except (TypeError, ValueError, IndexError):
            pass
    pares = {}
    ok_nv, retidas = _so_permitidas(ids, catalogo)
    reg['retidas_nvidia'] = retidas
    p1 = ler(prompt_casar.format(n=len(ids), primeiro='0', acontecimentos=_texto_eventos(eventos)), [imagens[i] for i in ids], orc,
             ordem=('gemini',), tarefa='casamento', chamadores=chamadores)
    falha1 = next((t.get('erro', '') for t in reversed(p1.get('tentativas') or []) if t.get('erro')), '')
    if not catalogo:
        reg['catalogo'] = 'catálogo indisponível: nenhuma imagem pode ir ao endpoint grátis (privacidade não verificada); leitura incerta'
    if p1.get('json') is not None:
        pares = avaliacoes(p1, ids)
    elif ok_nv and falha1 and (INDISPONIVEL.search(falha1) or 'sem ' in falha1):   # fallback só por indisponibilidade/limite
        p1 = ler(prompt_casar.format(n=len(ok_nv), primeiro='0', acontecimentos=_texto_eventos(eventos)), [imagens[i] for i in ok_nv],
                 orc, ordem=('nvidia',), tarefa='casamento_fallback', chamadores=chamadores)
        pares = avaliacoes(p1, ok_nv) if p1.get('json') is not None else {}
    # dupla leitura: o OUTRO provedor, só nos pares que pedem
    por_id = {e['id']: e for e in eventos}
    pedir = [(e, i) for (e, i), a in pares.items() if e in por_id and precisa_dupla(por_id[e], a, catalogo.get(i))]
    if pedir:
        outro = 'nvidia' if p1.get('provedor') == 'gemini' else 'gemini'
        imgs2 = sorted({i for _, i in pedir})
        if outro == 'nvidia':
            imgs2, _ = _so_permitidas(imgs2, catalogo)
        evs2 = [por_id[e] for e in sorted({e for e, i in pedir if i in imgs2})]
        if imgs2 and evs2:
            p2 = ler(prompt_casar.format(n=len(imgs2), primeiro='0', acontecimentos=_texto_eventos(evs2)), [imagens[i] for i in imgs2],
                     orc, ordem=(outro,), tarefa='dupla_leitura', chamadores=chamadores)
            segundo = avaliacoes(p2, imgs2) if p2.get('json') is not None else {}
            for k in pedir:
                if k in segundo:
                    c = combinar(pares[k], segundo[k])
                    reg['dupla'].append({'par': list(k), 'resultado': c.get('provedor')})
                    if c.get('discordancia'):
                        reg['discordancias'].append({'par': list(k), 'leituras': c['discordancia']})
                    pares[k] = c
    visoes = {k: para_visao(a, catalogo.get(k[1])) for k, a in pares.items()}
    for i in ids:                                   # imagem sem par lido: só o catálogo (confere incerto)
        visoes.setdefault(i, para_visao(None, catalogo.get(i)))
    return {'visoes': visoes, 'registro': reg, 'catalogo': catalogo}


def sombra(v: dict, acervo: list[dict], referencias: dict | None = None, chamadores: dict | None = None,
           prompts: tuple[str, str] | None = None) -> tuple[dict, dict]:
    """Leitura cega do acervo (catálogo → casamento → dupla leitura) com os prompts experimentais do cofre."""
    from src import cofre
    from src.v2 import evidencia as E
    eventos, vistos = [], set()
    for c in v.get('cenas') or []:
        ac = c.get('acontecimento') or {}
        if ac.get('tipo') and ac.get('id') and ac['id'] not in vistos:
            vistos.add(ac['id'])
            eventos.append(E.acontecimento(ac, [c.get('fala', '')], referencias, ac['id']))
    imagens = {}
    for x in acervo:
        if x.get('id') and x.get('arq') and os.path.exists(x['arq']):
            with open(x['arq'], 'rb') as f:
                imagens[x['id']] = f.read()
    if not imagens or not eventos:
        return {}, {'motivo': 'sem imagens ou acontecimentos'}
    p_cat, p_cas = prompts or (cofre.prompt('PROMPT_CATALOGO_EVIDENCIA'), cofre.prompt('PROMPT_CASAR_EVIDENCIA'))
    if p_cat.startswith('[') or p_cas.startswith('['):
        return {}, {'motivo': 'prompts experimentais ausentes do cofre: nenhuma chamada'}
    r = ler_roteiro(eventos, imagens, p_cat, p_cas, chamadores=chamadores)
    return r['visoes'], r['registro']


def executar_sombra(v: dict, acervo: list[dict], chamadores: dict | None = None, get=None, ler_visao: bool = True,
                    prompts: tuple[str, str] | None = None) -> dict:
    """O MESMO caminho do main.py em modo sombra: acervo → metadados reais → referências → catálogo → casamento →
    dupla leitura → Evidência V1 → relatório. Trabalha em CÓPIAS: nunca altera `v` nem o acervo."""
    import copy
    from src.v2 import evidencia as E
    from src.v2 import evidencia_registros as ER
    v2, ac2 = copy.deepcopy(v), copy.deepcopy(acervo)
    regs, res_regs = ER.registros(ac2, get=get, pausa=0 if get else ER.PAUSA)
    refs, res_refs = ER.referencias(v2, get=get, pausa=0 if get else ER.PAUSA)
    visoes, reg_visao = ({}, None)
    if ler_visao:
        visoes, reg_visao = sombra(v2, ac2, refs, chamadores=chamadores, prompts=prompts)
    rel = E.preparar(v2, ac2, registros=regs, visoes=visoes, referencias=refs)
    rel['registros'] = res_regs
    rel['referencias'] = {'resumo': res_refs, 'entidades': [{k: e.get(k) for k in ('nome', 'categorias', 'ids')} for e in refs['entidades']]}
    rel['visao'] = reg_visao
    return rel
