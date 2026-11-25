"""E202/E203 — DIRETOR VISUAL AUTÔNOMO MULTITEMA (fatos → acontecimento → modalidade → cena declarativa → MP4).

Amplia o que já existe, sem arquitetura paralela:
  * provedores de IA do projeto (src.gemini._em_cascata: Claude Code por assinatura quando ligado → Gemini → reservas);
  * acervo comprovado (ponte_biblioteca + diretor_roteiro.candidatos) decide se "registro_real" é possível;
  * ATLAS continua sendo o motor cartográfico: mapa só com clipe/comprovante ATLAS do próprio caso;
  * CAD/solver continua backend especializado: só com fonte CAD aprovada no caso;
  * cena declarativa (cena_declarativa_e202) → SceneGraph v2 → FilmeEditorial (mesmo compositor das outras cenas);
  * auditoria por contrato_visual_comum (mesma rubrica do ATLAS/FILME) + regras geométricas verificáveis.

Uma chamada de direção + no máximo UMA correção dirigida com as violações medidas em código. Respostas ficam em
cache por sha256 do pedido (benchmarks/e202/cache), com proveniência; a reprodução não chama IA de novo.
Nada aqui publica, envia ao Telegram ou aprova visualmente: aprovação é humana.
"""
from __future__ import annotations

import argparse
import hashlib
import math
import json
import os
import re
import sys
import time
from pathlib import Path

from src.v4.formatos import cena_declarativa_e202 as CD
from src.v4.formatos import formas_e202 as F

RAIZ = Path(__file__).resolve().parents[3]
CACHE = Path(os.getenv('E202_CACHE') or RAIZ / 'benchmarks/e202/cache')
MODALIDADES = ('cena_declarativa', 'mapa_atlas', 'registro_real', 'cad')
VERBOS = ('LOCALIZAR', 'MOSTRAR', 'DEMONSTRAR', 'CONECTAR', 'COMPARAR', 'REVELAR')
PALAVRAS_POR_S = 2.6           # mesma convenção do diretor V4 (src/v4/diretor.esqueleto)


# ───────────────────────── disponibilidade REAL de cada modalidade ─────────────────────────
def disponibilidade(caso: dict) -> dict:
    """O que existe de verdade para este caso, antes de pedir qualquer coisa ao modelo."""
    from src.v4.formatos import diretor_roteiro, ponte_biblioteca
    bib = ponte_biblioteca.catalogo()
    midia = []
    for f in caso.get('fatos') or []:
        for tipo in ('lugar', 'ambiente', 'evento_historico'):
            for c in diretor_roteiro.candidatos({'acontecimento': {'sujeito': caso.get('sujeito') or caso['pergunta']}}, tipo, bib):
                if c not in midia:
                    midia.append(c)
    return {
        'cena_declarativa': {'disponivel': True, 'motivo': 'compilador genérico E202 + FilmeEditorial'},
        'registro_real': {'disponivel': bool(midia), 'candidatos': midia,
                          'motivo': 'acervo comprovado' if midia else 'nenhuma mídia comprovada com identidade do assunto'},
        'mapa_atlas': {'disponivel': bool(caso.get('atlas_clipes')),
                       'motivo': 'clipe ATLAS com comprovante' if caso.get('atlas_clipes') else
                       'sem clipe/comprovante ATLAS para este lugar (ATLAS não foi executado para o caso)'},
        'cad': {'disponivel': bool(caso.get('cad_fonte_aprovada')),
                'motivo': 'fonte CAD aprovada' if caso.get('cad_fonte_aprovada') else 'sem fonte CAD aprovada (não exigida)'},
    }


# ───────────────────────── pedido ao modelo ─────────────────────────
VOCABULARIO = """AÇÕES (tempo em fração 0–1 do beat: "inicio","fim"):
- aparecer {alvo}                      - sair {alvo}
- girar {alvo, graus: -180 a 180} rotação relativa do objeto inteiro, não articulação anatômica
- mover {alvo, para: <ator>|esquerda|direita|cima|baixo|centro, absorver?: true}
- fluxo {de, para, item:{rotulo, cor:"#RRGGBB", forma?}, quantidade 4–12, efeito_no_destino?: "pulsar"}
     partículas saem de "de" e são absorvidas por "para" (substância, energia, informação, pessoas…)
- acumular {de?, para, item, quantidade}  partículas ficam DENTRO de "para"
- filtrar {de, filtro, para, passa:{item}, retido:{item}, quantidade}  parte atravessa, parte fica presa no filtro
- tingir {alvo, de_saturacao 0–1, para_saturacao 0–1} intensidade da cor do próprio ator, OU {alvo, para_cor:"#RRGGBB", intensidade 0–1} mudança de cor
- afastar {a, b, distancia 0.15–0.4, preencher_com?:{rotulo, cor, forma?}}  dois atores se separam; o vão é preenchido
- transformar {de, para}               um ator vira outro no mesmo lugar
- revelar_interior {alvo, interior}    o exterior fica translúcido e mostra o que há dentro
- destacar {alvo}                      anel de atenção (NÃO conta como demonstração)
RELAÇÕES espaciais (opcional): {"tipo":"sobre"|"dentro"|"ao_lado","a":<ator>,"b":<ator>}
FORMAS de ator:
- {"tipo":"icone","termos_en":["nome-exato-do-catálogo", "alternativa"],"alternativa":"<primitiva>"}
- {"tipo":"geo","nome_en":"<nome do país em inglês, Natural Earth>"}  contorno REAL Natural Earth de país/território (só para localizar/identificar)
- {"tipo":"primitiva","nome":"bloco|camada|recipiente|filtro|particula|fluido|celula|anel","cor":"#RRGGBB"}
- {"tipo":"svg_ia","d":"<path SVG simples em caixa 0..100>","cor":"#RRGGBB"}  último recurso"""

REGRAS = """REGRAS (verificadas em código; violar gera correção):
1. Use SÓ os fatos listados; cite os ids em cada beat. Nenhum número, data, nome, dimensão ou mecanismo fora deles.
2. Respeite os LIMITES do caso. Representação é ESQUEMA ILUSTRATIVO identificado, não reconstrução exata.
3. Cada beat precisa de AÇÃO VISÍVEL que demonstre causa → consequência (fluxo, tingir, afastar, filtrar, acumular,
   transformar, mover, revelar_interior, girar). Card, texto, seta ou ícone parado NÃO substituem ação.
4. Gancho: o 1º beat começa com o protagonista em quadro e uma pergunta/contradição forte; nada de introdução lenta.
5. Progressão: cada beat acrescenta informação nova; o último beat é o payoff (resposta clara).
6. Escolha a modalidade pelo ACONTECIMENTO e pela disponibilidade REAL abaixo; nunca peça modalidade indisponível.
   Mapa inventado é proibido; contorno geo é dado real e serve para localizar sem desenhar limites inexistentes.
7. Ícones: use nomes EXATOS do catálogo. Se nenhum representa fielmente o objeto (ex.: um órgão ausente), use primitiva
   com rótulo apenas se a forma for reconhecível e fiel; caso contrário solicite referência apropriada ou desenho próprio fundamentado. Nunca substitua objeto real por emoji parecido. Confira as cores da forma: o estado inicial não pode antecipar o resultado.
8. Narração em português do Brasil, frases curtas e faladas, 8–15 palavras por beat. 3–4 beats (≈ 12–18 s no total).
9. Rótulos curtos (≤ 22 caracteres). Até 6 atores por cena, no máximo 4 participantes essenciais por beat.
10. Câmera por beat: "foco" (ator) + "enquadramento" detalhe|medio|geral + "motivo". Termine com "geral" no payoff.
11. ESTADO INICIAL VISÍVEL: se algo muda (cor, posição, forma), o 1º quadro mostra o ANTES. O protagonista não pode
    exibir o resultado antes da causa (ex.: comece com de_saturacao baixa e só depois aumente).
12. COERÊNCIA ESPACIAL: o que acontece num lugar acontece NELE. Use relações (dentro/sobre/ao_lado) e preencher_com;
    não crie ator solto para algo que já é preenchimento, partícula ou parte de outro ator.
13. O "foco" da câmera deve ser um ator que PARTICIPA da ação principal do beat (para a ação não sair do quadro)."""

SAIDA = """Responda SÓ com JSON:
{"titulo":"pergunta curta ≤ 40 caracteres",
 "acontecimento_central":"o que precisa ser VISTO acontecer",
 "referencias_visuais":["convenções visuais que você usou (ex.: corte esquemático, fluxo de partículas)"],
 "cenas":[{"id":"c1","verbo":"DEMONSTRAR|LOCALIZAR|MOSTRAR|CONECTAR|COMPARAR|REVELAR",
   "acontecimento":"...","modalidade":"cena_declarativa|mapa_atlas|registro_real|cad","justificativa_modalidade":"...",
   "atores":[{"id":"a_z_0_9","rotulo":"...","papel":"protagonista|origem|destino|meio|produto|contexto","forma":{...},"fatos":["id"]}],
   "relacoes":[],
   "beats":[{"fala":"...","etapa":"rótulo curto da etapa","fatos":["id"],"acoes":[{"verbo":"...","inicio":0.0,"fim":1.0,...}],
             "camera":{"foco":"<ator>","enquadramento":"detalhe|medio|geral","motivo":"..."}}]}]}"""


def catalogo_icones() -> str:
    return ' '.join(sorted(F._icones()))


def prompt(caso: dict, disp: dict, correcoes: list[dict] | None = None, anterior: dict | None = None,
           alvo: tuple[int, int] = (9, 14)) -> str:
    fatos = '\n'.join(f"- {f['id']}: {f['texto']} [fonte: {f['fonte']}]" for f in caso['fatos'])
    limites = '\n'.join(f'- {x}' for x in caso.get('limites') or [])
    d = '\n'.join(f"- {k}: {'DISPONÍVEL' if v['disponivel'] else 'INDISPONÍVEL'} ({v['motivo']})" for k, v in disp.items())
    episodio = caso.get('alvo_duracao')
    if episodio:
        alvo = tuple(episodio)
        pedido_txt = (f'Transforme os fatos abaixo em UM EPISÓDIO de {alvo[0]}–{alvo[1]} s, com 5–7 CENAS encadeadas (cada cena '
                      'com seus atores e 2–3 beats), que MOSTRE os acontecimentos acontecendo.')
    else:
        pedido_txt = f'Transforme os fatos abaixo em UMA cena animada de {alvo[0]}–{alvo[1]} s que MOSTRE o acontecimento acontecendo.'
    base = f"""Você é o DIRETOR VISUAL do Coringa Explica (documentário vertical 9:16, Reels/TikTok/Shorts, pt-BR).
{pedido_txt}

PERGUNTA: {caso['pergunta']}

FATOS VERIFICADOS (únicos permitidos):
{fatos}

LIMITES DO CASO:
{limites}

MODALIDADES (disponibilidade verificada em código):
{d}

{VOCABULARIO}

{REGRAS}

CATÁLOGO DE ÍCONES (Fluent Emoji Flat, MIT; nomes exatos):
{catalogo_icones()}

{SAIDA}"""
    if episodio:
        base += f"""

MODO EPISÓDIO (substitui a regra 8 no que conflitar): 5–7 cenas; 2–3 beats por cena; total ≈ {alvo[0]}–{alvo[1]} s
({int(alvo[0] * 2.4)}–{int(alvo[1] * 2.4)} palavras). Cena 1 = gancho com contradição; meio = causa → mecanismo → consequência,
cada cena com informação nova; última cena = virada/payoff que ecoa o gancho. Use TODOS os fatos relevantes, sem inventar.
Atores podem repetir entre cenas com o MESMO id quando forem a mesma coisa."""
    if correcoes:
        base += ('\n\nSUA RESPOSTA ANTERIOR violou regras verificadas em código. Corrija SÓ o necessário e devolva o JSON inteiro:\n'
                 + '\n'.join(f"- [{c['regra']}] {c['texto']}" for c in correcoes)
                 + '\n\nANTERIOR:\n' + json.dumps(anterior, ensure_ascii=False)[:20000])
    return base


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode('utf8')).hexdigest()


def pedir_ia(texto: str, registro: list[dict], cache: Path = CACHE, permitir_chamada: bool = True) -> dict:
    """Cache por sha256 do pedido; sem cache, cadeia de provedores do projeto. Registra cada chamada."""
    h = _sha(texto)
    arq = cache / f'{h}.json'
    if arq.exists():
        c = json.loads(arq.read_text(encoding='utf8'))
        registro.append({'pedido_sha256': h, 'origem': 'cache', 'provedor': c.get('provedor'), 'chamada_nova': False})
        return c['json']
    if not permitir_chamada:
        raise RuntimeError(f'E202-SEM-CACHE: pedido {h[:12]} não está no cache e chamadas de IA estão desligadas')
    from src import claude, gemini
    t0 = time.time()
    falhas, bruto, prov = [], None, None
    # ordem explícita (padrão: Gemini grátis → Claude Code por assinatura, ambos já usados pelo projeto)
    for nome in [x.strip() for x in os.getenv('E202_PROVEDORES', 'gemini,claude').split(',') if x.strip()]:
        try:
            if nome == 'gemini':
                antigo = os.environ.get('USAR_CLAUDE')
                os.environ['USAR_CLAUDE'] = '0'          # a cascata do Gemini não deve pular para o Claude sozinha
                try:
                    bruto = gemini.texto(texto)
                finally:
                    if antigo is None:
                        os.environ.pop('USAR_CLAUDE', None)
                    else:
                        os.environ['USAR_CLAUDE'] = antigo
                prov = 'gemini_cascata' + ('+' + '+'.join(gemini.RESERVAS_USADAS) if getattr(gemini, 'RESERVAS_USADAS', None) else '')
            elif nome == 'claude':
                os.environ['USAR_CLAUDE'] = '1'
                if not claude.disponivel():
                    raise RuntimeError('Claude Code indisponível (sem token/CLI)')
                bruto = claude.pedir(texto)
                prov = f'claude_code:{claude.MODELO}'
            else:
                raise RuntimeError(f'provedor desconhecido {nome}')
            if bruto and bruto.strip():
                break
        except Exception as e:
            falhas.append(f'{nome}: {type(e).__name__}: {str(e)[:160]}')
            bruto = None
    if not bruto:
        raise RuntimeError('E202-SEM-PROVEDOR: ' + ' | '.join(falhas))
    obj = gemini.extrair_json(bruto)
    item = {'pedido_sha256': h, 'provedor': prov, 'falhas_antes': falhas, 'segundos': round(time.time() - t0, 1), 'data': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'caracteres_pedido': len(texto), 'caracteres_resposta': len(bruto), 'json': obj}
    cache.mkdir(parents=True, exist_ok=True)
    arq.write_text(json.dumps(item, ensure_ascii=False, indent=1) + '\n', encoding='utf8')
    registro.append({k: v for k, v in item.items() if k != 'json'} | {'origem': 'chamada', 'chamada_nova': True})
    return obj


# ───────────────────────── verificação do plano ─────────────────────────
def estimar_duracoes(cena: dict) -> list[float]:
    return [max(1.6, len(re.findall(r'\w+', str(b.get('fala') or ''))) / PALAVRAS_POR_S + .25) for b in cena.get('beats') or []]


def verificar(plano: dict, caso: dict, disp: dict) -> tuple[list[dict], dict]:
    """violações + compilações de teste (durações estimadas). Nada aqui olha frames: isso é a auditoria visual."""
    probs, comp = [], {}
    cenas = plano.get('cenas') if isinstance(plano, dict) else None
    if not isinstance(cenas, list) or not cenas:
        return [CD._p('P-SEM-CENAS', 'plano sem cenas')], comp
    if not str(plano.get('titulo') or '').strip() or len(str(plano['titulo'])) > 44:
        probs.append(CD._p('P-TITULO', 'título vazio ou > 44 caracteres'))
    for c in cenas:
        cid = str(c.get('id') or '?')
        mod = c.get('modalidade')
        if mod not in MODALIDADES:
            probs.append(CD._p('P-MODALIDADE', f'modalidade {mod} desconhecida', cid)); continue
        if not disp[mod]['disponivel']:
            probs.append(CD._p('P-MODALIDADE-INDISPONIVEL', f"{mod}: {disp[mod]['motivo']}", cid)); continue
        if c.get('verbo') not in VERBOS:
            probs.append(CD._p('P-VERBO', f"verbo {c.get('verbo')} fora de {VERBOS}", cid))
        if mod != 'cena_declarativa':
            continue                     # outras modalidades usam suas próprias pontes (ATLAS/acervo/CAD)
        geo = [a for a in c.get('atores') or [] if (a.get('forma') or {}).get('tipo') == 'geo']
        for a in geo:
            if a.get('papel') not in ('protagonista', 'contexto', 'destino', 'origem'):
                probs.append(CD._p('P-GEO-PAPEL', f"contorno geo {a.get('id')} só localiza/identifica", cid))
        try:
            comp[cid] = CD.compilar(c, estimar_duracoes(c), caso['fatos'], titulo=str(plano.get('titulo') or ''))
            comp[cid]['alertas_geometria'] = geometria(comp[cid]['scene_graph'], cid)   # defeito do compilador, não do modelo
        except CD.CenaInvalida as e:
            probs += e.problemas
        except Exception as e:        # erro do compilador é defeito NOSSO: registrar sem culpar o modelo
            probs.append(CD._p('P-COMPILADOR', f'{type(e).__name__}: {str(e)[:200]}', cid))
    return probs, comp


def _tela(a: dict, st: dict, cam: dict) -> tuple[float, float, float, float]:
    vx, vy, vw, vh = a['view']
    f = a['size'] / max(vw, vh)
    cx, cy = (CD.CAIXA[0] + CD.CAIXA[2]) / 2, (CD.CAIXA[1] + CD.CAIXA[3]) / 2
    x, y = cx + (st['x'] - cam['x']) * cam['zoom'], cy + (st['y'] - cam['y']) * cam['zoom']
    w, h = vw * f * cam['zoom'] * st['scale'] * st['sx'], vh * f * cam['zoom'] * st['scale'] * st['sy']
    rad = math.radians(st.get('angle', 0))
    w, h = abs(math.cos(rad))*w + abs(math.sin(rad))*h, abs(math.sin(rad))*w + abs(math.cos(rad))*h
    return x - w / 2, y - h / 2, x + w / 2, y + h / 2


def _interp(ks: list[dict], t: float, props) -> dict:
    for i in range(1, len(ks)):
        if t < ks[i]['t']:
            l, r = ks[i - 1], ks[i]
            p = (t - l['t']) / (r['t'] - l['t'])
            return {k: l[k] + (r[k] - l[k]) * p for k in props}
    return {k: ks[-1][k] for k in props}


def geometria(sg: dict, cid: str = '') -> list[dict]:
    """Regras de direção verificáveis no grafo (Lemo DIRECTOR §8/§10 reimplementadas):
    sujeito do beat ≥ 1/3 da altura da área visual no meio do beat; essenciais dentro da área segura; nada vazio."""
    out = []
    ts = [b['t'] for b in sg['beats']]
    dur = sg['camera'][-1]['t']
    ts_fim = ts[1:] + [dur]
    props = ('x', 'y', 'scale', 'sx', 'sy', 'opacity', 'angle')
    altura = CD.CAIXA[3] - CD.CAIXA[1]
    for k, (t0, t1) in enumerate(zip(ts, ts_fim)):
        t = t0 + (t1 - t0) * .6
        cam = _interp(sg['camera'], t, ('x', 'y', 'zoom'))
        vis = []
        for a in sg['actors']:
            if a['layer'] != 'essencial':
                continue
            st = _interp(a['states'], t, props)
            if st['opacity'] < .5:
                continue
            vis.append((a, _tela(a, st, cam)))
        if not vis:
            out.append(CD._p('G-VAZIO', f'beat {k + 1}: nenhum ator essencial visível', cid)); continue
        foco = set(sg['beats'][k].get('foco_ids') or [])
        principal = sg['beats'][k].get('foco_principal')
        geral = sg['beats'][k].get('enquadramento') == 'geral'
        alvo_h = [b[3] - b[1] for a, b in vis if a['id'] == principal] or [max((b[3] - b[1] for a, b in vis if a['id'] in foco), default=0)]
        maior = max(alvo_h)
        minimo = .20 if geral else 1 / 3       # plano geral (revelação do conjunto) tolera sujeito menor; regra fixada na E202
        if maior < altura * minimo - 1:
            out.append(CD._p('G-SUJEITO-PEQUENO', f'beat {k + 1}: ator em foco ocupa {maior / altura:.0%} da altura (< {minimo:.0%})', cid))
        for a, (x0, y0, x1, y1) in vis:
            if a['id'] not in foco:
                continue
            area = max(1.0, (x1 - x0) * (y1 - y0))
            ix = max(0.0, min(x1, CD.CAIXA[2]) - max(x0, CD.CAIXA[0])) * max(0.0, min(y1, CD.CAIXA[3] + 30) - max(y0, CD.CAIXA[1]))
            if a['id'] == principal and ix / area < .97:
                out.append(CD._p('G-FOCO-CORTADO', f'beat {k + 1}: foco {a["id"]} só {ix / area:.0%} dentro da área segura', cid))
            elif ix / area < .5:
                out.append(CD._p('G-FORA-DA-AREA', f'beat {k + 1}: {a["id"]} só {ix / area:.0%} dentro da área segura', cid))
    return out


# ───────────────────────── direção completa ─────────────────────────
def dirigir(caso: dict, permitir_chamada: bool = True, cache: Path = CACHE) -> dict:
    disp = disponibilidade(caso)
    reg: list[dict] = []
    p1 = prompt(caso, disp)
    plano = pedir_ia(p1, reg, cache, permitir_chamada)
    probs, comp = verificar(plano, caso, disp)
    hist = [{'rodada': 1, 'violacoes': probs}]
    if probs:
        p2 = prompt(caso, disp, probs, plano)
        plano2 = pedir_ia(p2, reg, cache, permitir_chamada)
        probs2, comp2 = verificar(plano2, caso, disp)
        hist.append({'rodada': 2, 'violacoes': probs2})
        if len(probs2) <= len(probs):
            plano, probs, comp = plano2, probs2, comp2
    estado = 'PLANO_COMPILADO' if not probs and comp else 'BLOQUEADO'
    alertas = [g for x in comp.values() for g in x.get('alertas_geometria') or []]
    return {'caso': caso['id'], 'estado': estado, 'plano': plano, 'violacoes_finais': probs, 'alertas_geometria': alertas, 'historico': hist,
            'disponibilidade': disp, 'chamadas_ia': reg, 'compilado': comp,
            'aprovacao_humana': 'PENDENTE', 'publicar': False}


# ───────────────────────── FilmeEditorial ─────────────────────────
def palavras_de_caps(caps: list[dict]) -> list[dict]:
    out = []
    for bl in caps:
        ws = bl['words']
        for k, w in enumerate(ws):
            fim = ws[k + 1]['s'] if k + 1 < len(ws) else bl['end']
            out.append({'w': w['w'], 's': float(w['s']), 'e': round(float(fim), 3)})
    return out


def _cenas_decl(plano: dict) -> list[dict]:
    return [c for c in plano['cenas'] if c.get('modalidade') == 'cena_declarativa']


def filme(resultado: dict, caso: dict, duracoes: list[float] | None = None, palavras: list[dict] | None = None,
          audio: str | None = None) -> dict:
    """Cenas declarativas em sequência → props do FilmeEditorial (mesmo compositor das outras modalidades).
    `duracoes` = um valor por beat de TODAS as cenas, na ordem; `palavras` em tempo absoluto do áudio."""
    plano = resultado['plano']
    cenas = _cenas_decl(plano)
    if len(cenas) != len(plano['cenas']):
        raise ValueError('E204-MODALIDADE-SEM-PONTE: não descartar cenas não declarativas')
    if not cenas:
        raise ValueError('plano sem cena declarativa')
    nbeats = [len(c['beats']) for c in cenas]
    dur = duracoes or [d for c in cenas for d in estimar_duracoes(c)]
    if len(dur) != sum(nbeats):
        raise ValueError(f'durações ({len(dur)}) ≠ beats ({sum(nbeats)})')
    shots, provs, t0, k = [], [], 0.0, 0
    for c, n in zip(cenas, nbeats):
        d_c = dur[k:k + n]; k += n
        t1 = t0 + sum(d_c)
        pal = None
        if palavras:
            pal = [{**w, 's': round(w['s'] - t0, 3), 'e': round(w['e'] - t0, 3)} for w in palavras if t0 - 1e-6 <= w['s'] < t1 - 1e-6]
        comp = CD.compilar(c, d_c, caso['fatos'], pal, titulo=str(plano.get('titulo') or ''))
        sg = comp['scene_graph']
        ini = round(t0, 4)
        fim = round(t0 + comp['duracao'], 4)            # mesmo arredondamento dos estados (t ≤ duração)
        shots.append({'id': c['id'], 'start': ini, 'end': fim, 'type': 'scene_graph', 'evidence': 'explainer',
                      'subject': str(c.get('acontecimento') or plano.get('acontecimento_central') or '')[:120],
                      'lead': c.get('verbo', 'DEMONSTRAR'), 'headline': sg['headline'],
                      'source': sg['source'], 'source_display': ', '.join(_dominio(u) for u in sg['sources']),
                      'scene_graph': sg,
                      'direcao_visual': {'verbo': c.get('verbo'), 'referente': c.get('acontecimento'),
                                         'aprendizado': c['beats'][-1]['fala'], 'provas': sorted({f for b in c['beats'] for f in b['fatos']})},
                      'estados_esperados': [], 'cues': []})
        provs.append({'cena': c['id'], **comp['proveniencia']})
        t0 = fim
    props = {'formato': 'filme_editorial', 'duracao': round(t0, 4), 'shots': shots, 'preview': True, 'private_review_only': True}
    if audio:
        props['scene_narration_asset'] = audio
    return {'props': props, 'proveniencia': provs[0] if len(provs) == 1 else {'cenas': provs, 'legendas': provs[0]['legendas']}}



# E205: triagem documental anterior à escolha de renderer.
def triagem_documental(necessidades: list[dict], fatos: list[dict], biblioteca: dict | None = None) -> list[dict]:
    """Recebe necessidades editoriais, não desenhos. Candidatos não são prova de ação.
    Falta de acervo gera pedido de pesquisa, nunca conversão automática em esquema.
    """
    from src.v4.formatos import diretor_roteiro, ponte_biblioteca
    bib = ponte_biblioteca.catalogo() if biblioteca is None else biblioteca
    ids_fatos = {f['id'] for f in fatos}
    vistos = set()
    out = []
    for n in necessidades:
        cid = n.get('id')
        if not isinstance(cid, str) or not cid or cid in vistos:
            raise ValueError('E205-ID')
        vistos.add(cid)
        refs = n.get('fatos')
        if not isinstance(refs, list) or not refs or not all(isinstance(x, str) and x in ids_fatos for x in refs):
            raise ValueError('E205-FATOS')
        sujeito = str(n.get('sujeito') or '').strip()
        mostrar = str(n.get('mostrar') or '').strip()
        tipo = n.get('necessidade')
        if not sujeito or not mostrar or tipo not in ('registro', 'territorio', 'lacuna_explicativa'):
            raise ValueError('E205-NECESSIDADE')
        evidencia = n.get('evidencia_visual') or 'indefinida'
        if evidencia not in ('movimento','estatica','contexto','indefinida'):
            raise ValueError('E246-EVIDENCIA')
        candidatos = diretor_roteiro.candidatos({'acontecimento': {'sujeito': sujeito}}, 'ambiente', bib)
        candidatos.sort(key=lambda x: (x.get('natureza') != 'video', x['asset_id']))
        geo = None
        if tipo == 'territorio':
            destino, estado = 'mapa_atlas', 'SOLICITAR_ATLAS'
            objetivo = n.get('objetivo_geografico') or 'a_definir'
            politicas = {
                'a_definir': ('verificar_objetivo',),
                'localizacao': ('contexto', 'regiao'),
                'relevo': ('regiao', 'detalhe', 'elevação_verificada'),
                'rota': ('regiao', 'trajeto_verificado'),
                'territorio': ('limites_verificados',),
                'comparacao': ('contexto', 'escala_comparavel'),
            }
            if not isinstance(objetivo,str) or objetivo not in politicas:
                raise ValueError('E237-OBJETIVO-GEOGRAFICO')
            geo = {'objetivo': objetivo, 'recursos_candidatos': list(politicas[objetivo]),
                   'pesquisar_localizacao': True, 'verificar_epoca': True,
                   'revisar_fontes_e_geometria': True, 'pronto_para_render': False,
                   'aproximacao': 'SOMENTE_SE_AJUDA_EXPLICACAO',
                   'estado': 'PESQUISAR_E_VALIDAR_GEOGRAFIA'}
        elif tipo == 'registro':
            destino = 'registro_real'
            estado = 'REVISAR_CANDIDATOS' if candidatos else 'PESQUISAR_MIDIA'
        else:
            lacuna = str(n.get('lacuna') or '').strip()
            if not lacuna:
                raise ValueError('E205-SEM-LACUNA')
            # A lacuna é hipótese editorial até a revisão das mídias/referências.
            destino, estado = 'cena_declarativa', 'REVISAR_LACUNA_E_REFERENCIAS'
        out.append({'id': cid, 'fatos': refs, 'sujeito': sujeito, 'mostrar': mostrar,
                    'necessidade': tipo, 'evidencia_visual': evidencia, 'modalidade_proposta': destino, 'estado': estado,
                    'candidatos': candidatos, 'lacuna': n.get('lacuna'),
                    **({'solicitacao_atlas': geo} if geo is not None else {}),
                    'pesquisa': {'consultas': [sujeito + ' ' + mostrar, sujeito],
                                 'consultas_en': [q.strip() for q in (n.get('consultas_en') or [])[:2]
                                                  if isinstance(q, str) and 2 <= len(q.strip()) <= 120],
                                 'verificar_direitos': True, 'inspecionar_conteudo': True},
                    'politica_complemento': 'REAVALIAR_APOS_INSPECAO_DE_MIDIA',
                    'fallback_sem_animacao_adequada': 'REPLANEJAR_MIDIA_REAL_OU_DECLARAR_LACUNA',
                    'pronto_para_render': False})
    if not out:
        raise ValueError('E205-SEM-NECESSIDADES')
    return out



def planejar_documental(caso: dict, permitir_chamada: bool = True, cache: Path = CACHE, *, pesquisar_midia=False, biblioteca_global=None) -> dict:
    """Autoria das necessidades ANTES da escolha de assets/renderers.
    Usa o provedor/cache existente. Não aceita URL ou licença fornecida pelo modelo.
    """
    fatos = caso['fatos']
    texto = """Você é o diretor documental do Coringa Explica. Mídia real primeiro.
Para cada fato, identifique o que precisa ser visto, não desenhe a narração.
Use registro para filmagem/foto real; territorio para localização, fronteira, rota ou relevo factual no ATLAS;
lacuna_explicativa somente para uma ação específica que registros não mostram (descreva a lacuna).
A animação só complementa a explicação de funcionamento ou ação que mídia real não demonstra, após busca sem registro adequado ou impossibilidade física de filmar. Se uma animação adequada não existir, replaneje com mídia real/contexto identificado ou declare a lacuna. Nunca use modelo reprovado como fallback. Não gere URLs, assets, desenhos, licenças ou geometrias.
Quando a localização ou relação espacial for indispensável, considere abrir com mapa; caso contrário, priorize o registro real mais informativo. Para territorio indique objetivo_geografico: localizacao, relevo, rota, territorio ou comparacao. Não invente coordenadas ou trajetos: o motor deve pesquisar e verificar a região, a época e a fonte antes de adquirir mapas. Relevo exige elevação verificada, rota e fronteira exigem geometria documentada. Não obrigue aproximação.
Para cada necessidade de mídia real indique evidencia_visual: movimento se exige ação observável, estatica se basta aparência/estrutura, contexto se basta ambiente, indefinida se não souber. Nunca trate fotografia como prova de movimento. Inclua duas consultas curtas e distintas em inglês para mídia real. Não invente fatos.
Responda JSON {"necessidades_visuais":[{"id":"n1","fatos":["id existente"],"sujeito":"...","mostrar":"...",
"necessidade":"registro|territorio|lacuna_explicativa","evidencia_visual":"movimento|estatica|contexto|indefinida","objetivo_geografico":"apenas para territorio: localizacao|relevo|rota|territorio|comparacao","lacuna":"... somente se necessária","consultas_en":["...","..."]}]}.
Pergunta: """ + str(caso['pergunta']) + "\nFatos: " + json.dumps(fatos, ensure_ascii=False) + "\nLimites: " + json.dumps(caso.get('limites') or [], ensure_ascii=False)
    registro = []
    resposta = pedir_ia(texto, registro, cache, permitir_chamada)
    necessidades = resposta['necessidades_visuais']
    triagem = triagem_documental(necessidades, fatos)
    resultado = {'triagem': triagem, 'chamadas_ia': registro, 'publicar': False}
    if pesquisar_midia:
        resultado['pesquisa_audiovisual'] = pesquisar_triagem(triagem, biblioteca_global=biblioteca_global)
    return resultado


def pesquisar_triagem(triagem, *, biblioteca_global=None, fontes=None, inspecionar=None, max_buscas=6):
    """Opt-in bridge: never replace the existing render/rights gates."""
    from src.v4 import acervo_v4
    return [acervo_v4.pesquisar_cobertura(n,biblioteca=biblioteca_global,fontes=fontes,
            inspecionar=inspecionar,max_buscas=max_buscas) for n in triagem]




def selecionar_complemento(necessidade: dict, revisao: dict, referencias: list[dict],
                            *, pesquisar_cad=False, getter_cad=None) -> dict:
    """E217: bridge documentary inspection -> existing evidence/solver route E40.
    Only a reviewed specific action can request CAD or a grounded schematic.
    Neither search metadata nor an LLM assertion constitutes verified motion.
    """
    from src.v4.formatos import politica_animacao as PA, rota_explicativa_e40 as E40
    if (necessidade.get('necessidade')!='lacuna_explicativa'
        or not necessidade.get('id') or not necessidade.get('mostrar')
        or not necessidade.get('lacuna') or not necessidade.get('fatos')):
        raise ValueError('E217-NECESSIDADE')
    if (revisao.get('id')!=necessidade['id'] or revisao.get('acao')!=necessidade['mostrar']
        or revisao.get('fatos')!=necessidade['fatos']
        or type(revisao.get('midia_adequada')) is not bool
        or not isinstance(revisao.get('justificativa'),str) or not revisao['justificativa'].strip()):
        raise ValueError('E217-REVISAO')
    if revisao.get('origem') not in ('CURADORIA_HUMANA','REVISAO_MIDIA_VERIFICADA'):
        raise ValueError('E217-ORIGEM-REVISAO')
    base={'id':necessidade['id'],'acao':necessidade['mostrar'],'fatos':necessidade['fatos'],
          'lacuna':necessidade['lacuna'],'publicar':False,'pronto_para_render':False,
          'aprovacao_visual':'PENDENTE'}
    if revisao['midia_adequada']:
        return {**base,'decisao':'USAR_MIDIA_REAL'}
    motivo=revisao.get('motivo')
    if motivo not in ('BUSCA_SEM_REGISTRO_ADEQUADO','IMPOSSIVEL_FILMAR'):
        return {**base,'decisao':'PESQUISAR_OU_REPLANEJAR_MIDIA_REAL'}
    if motivo=='BUSCA_SEM_REGISTRO_ADEQUADO':
        consultas=revisao.get('consultas_executadas')
        if not isinstance(consultas,list) or not consultas or not all(isinstance(q,str) and q.strip() for q in consultas):
            raise ValueError('E217-SEM-BUSCA')
    alvo=revisao.get('alvo_tecnico')
    if not isinstance(alvo,str) or not alvo.strip():
        raise ValueError('E217-ALVO')
    contorno=revisao.get('exige_contorno_industrial')
    if type(contorno) is not bool:
        raise ValueError('E217-CONTORNO')
    # Match the actual explanatory action as well as the technical subject.
    # References are curator/solver outputs, not arbitrary model proposals.
    compativeis=[r for r in referencias if isinstance(r,dict)
                  and r.get('acao_revisada')==necessidade['mostrar']
                  and r.get('fatos_revisados')==necessidade['fatos']]
    rota=E40.planejar(compativeis,contorno,alvo=alvo)
    base.update(rota=rota,referencias_fora_do_escopo=len(referencias)-len(compativeis))
    if rota['decisao'] is not None:
        c=compativeis[rota['decisao']['indice']]
        renderer='cad_preview' if c['tipo']=='cad_real' else 'scene_graph:coringa.scene_graph.private.v2'
        decisao=PA.decidir_complemento(midia_adequada=False,acao=necessidade['mostrar'],
            lacuna=necessidade['lacuna'],motivo_lacuna=motivo,renderer=renderer)
        return {**base,'decisao':decisao,'renderer_proposto':renderer,
                'referencia':c,'proximo':'VINCULAR_GEOMETRIA_E_RENDER_VERIFICADO'}
    if pesquisar_cad:
        from src.v4.formatos import pesquisa_cad_e34 as E34
        q=revisao.get('consulta_cad')
        if not isinstance(q,str) or not q.strip():
            raise ValueError('E217-CONSULTA-CAD')
        # Respect the bounded existing discovery and its stop-on-block behavior.
        rel=E34.discover_many([q],limit=3,**({'getter':getter_cad} if getter_cad else {}))[0]
        base['pesquisa_cad']=rel
        if rel['candidates']:
            return {**base,'decisao':'REVISAR_FONTE_CAD_ANTES_DO_SOLVER'}
    return {**base,'decisao':'REPLANEJAR_MIDIA_REAL_OU_DECLARAR_LACUNA'}


def preparar_misto(resultado: dict, caso: dict, plano_documental: dict, destino: Path,
                   public_root: Path, duracoes: list[float], downloader=None,
                   palavras: list[dict] | None = None, audio: str | None = None) -> dict:
    """Primeira ponte privada E205: mídia/ATLAS pelo preflight original; esquemas
    pelo compilador E202; todos intercalados na ordem e tempos da mesma narrativa.
    Entrada documental vem da curadoria, não de caminhos/URLs inventados pela IA.
    Áudio opcional e palavras medidas usam o relógio global, sem duplicar legendas.
    """
    from src.v4.formatos import filme_editorial as FILME
    cenas = resultado['plano']['cenas']
    ids = [c['id'] for c in cenas]
    if not ids or len(set(ids)) != len(ids):
        raise ValueError('E205-CENAS')
    if plano_documental.get('tipo') != 'PROVA_VISUAL_PRIVADA' or plano_documental.get('publicar') is not False:
        raise ValueError('E205-PRIVADO')
    if len(duracoes) != sum(len(c['beats']) for c in cenas) or any(
            not isinstance(d, (int, float)) or isinstance(d, bool) or not math.isfinite(d) or d <= 0 for d in duracoes):
        raise ValueError('E205-TEMPOS')
    externos = [c for c in cenas if c['modalidade'] != 'cena_declarativa']
    if not externos or len(externos) == len(cenas):
        raise ValueError('E205-NAO-MISTO')
    origem = plano_documental.get('shots') or []
    if [s['id'] for s in origem] != [c['id'] for c in externos]:
        raise ValueError('E205-ORDEM-MIDIA')
    tipos = {'registro_real': ('photo', 'video'), 'mapa_atlas': ('atlas_map',)}
    for c, s in zip(externos, origem):
        if s.get('type') not in tipos.get(c['modalidade'], ()):
            raise ValueError('E205-MODALIDADE')
    # Checa a duração ANTES de baixar e renderizar. Não estica nem acelera o original.
    partes, k = {}, 0
    for c in cenas:
        n = len(c['beats'])
        if not n or any(not str(b.get('fala') or '').strip() for b in c['beats']):
            raise ValueError('E205-FALA')
        partes[c['id']] = duracoes[k:k+n]
        k += n
    for s in origem:
        if abs((s['end'] - s['start']) - sum(partes[s['id']])) > .001:
            raise ValueError('E205-DURACAO-MIDIA')
    destino = Path(destino)
    preparado = FILME.preparar(plano_documental, destino / 'documental', public_root, downloader=downloader)
    if preparado.get('pronto') is not True:
        raise ValueError('E205-PREFLIGHT')
    base = json.loads(Path(preparado['props']).read_text(encoding='utf8'))
    if [s['id'] for s in base['shots']] != [c['id'] for c in externos]:
        raise ValueError('E205-PREFLIGHT-ORDEM')
    midias = {s['id']: s for s in base['shots']}
    shots, provs, t = [], [], 0.0
    for c in cenas:
        ds = partes[c['id']]
        if c['modalidade'] == 'cena_declarativa':
            local = [{**w, 's': round(w['s']-t, 4), 'e': round(min(w['e'], t+sum(ds))-t, 4)}
                     for w in palavras or [] if t <= w['s'] < t+sum(ds)]
            trecho = filme({'plano': {**resultado['plano'], 'cenas': [c]}}, caso, ds, local or None)
            s = trecho['props']['shots'][0]
            provs.append({'id': c['id'], 'proveniencia': trecho['proveniencia']})
        else:
            s = dict(midias[c['id']])
        fim = round(t + sum(ds), 4)
        shots.append({**s, 'start': t, 'end': fim})
        t = fim
    props = {**base, 'shots': shots, 'duracao': t, 'preview': True, 'private_review_only': True}
    # O perfil cartográfico original não foi recertificado para safe_area_profile.
    if any(s['type'] == 'atlas_map' for s in shots):
        props.pop('safe_area_profile', None)
    from src.v4.formatos import politica_animacao as PA
    if props.get('animation_policy_mode')==PA.LEGACY:
        raise ValueError('E211-LEGADO-NAO-ENTRA-EM-DOCUMENTARIO')
    PA.exigir(props['shots'], modo=props.get('animation_policy_mode'), privado=True)
    if audio or palavras:
        if not audio or not palavras:
            raise ValueError('E207-AUDIO-E-PALAVRAS')
        from src.v4.formatos import legenda_sync as LS
        # Agrupamento GLOBAL; só o compositor de mídia real usa esta camada.
        # O scene_graph v2 mantém sua própria legenda medida.
        pal = LS.destacar_atlas(palavras, {'titulo': resultado['plano'].get('titulo'),
                                           'narracao': {'fatos': caso['fatos']}}, maximo=3)
        grupos = [{'start': max(0., g['ini']), 'end': min(t, g['fim']),
                   'words': [{'w': w['w'], 'hl': w.get('hl', False)}
                             for w in pal[g['i0']:g['i0']+g['n']]]}
                  for g in LS.grupos(pal, maximo=3)]
        props = anexar_audio_documental(props, audio, grupos, public_root, 'PALAVRAS_MEDIDAS')
    destino.mkdir(parents=True, exist_ok=True)
    (destino / 'props.json').write_text(json.dumps(props, ensure_ascii=False, indent=2), encoding='utf8')
    return {'props': props, 'proveniencia': {'documental': str(destino / 'documental' / 'midias.json'),
                                           'esquemas': provs},
            'estado': 'MONTAGEM_PRIVADA_COM_AUDIO' if audio else 'MONTAGEM_PRIVADA_SEM_AUDIO', 'publicar': False, 'aprovacao_humana': 'PENDENTE'}




def retimar_documental(plano: dict, plano_documental: dict, duracoes: list[float]) -> dict:
    """Atualiza somente cortes da timeline após a voz. Não altera velocidade,
    timestamps originais, cues ou duração de clipe ATLAS autenticado.
    Se o material não couber, exige nova decupagem/render do mapa.
    """
    import copy
    cenas = plano['cenas']
    if len(duracoes) != sum(len(c['beats']) for c in cenas):
        raise ValueError('E209-BEATS')
    if any(not isinstance(x,(int,float)) or isinstance(x,bool) or not math.isfinite(x) or x<=0 for x in duracoes):
        raise ValueError('E209-TEMPOS')
    p = copy.deepcopy(plano_documental)
    externos = [c for c in cenas if c['modalidade'] != 'cena_declarativa']
    if [s['id'] for s in p['shots']] != [c['id'] for c in externos]:
        raise ValueError('E209-ORDEM')
    k,t=0,0.
    shots={s['id']:s for s in p['shots']}
    for c in cenas:
        n=len(c['beats'])
        d=round(sum(duracoes[k:k+n]),4)
        k+=n
        if c['modalidade']=='cena_declarativa':
            continue
        s=shots[c['id']]
        if s['type']=='atlas_map':
            # A duração do mapa vem da prova, não da sugestão do roteiro.
            m=p['media'][s['asset']]
            q=json.loads(Path(m['atlas_proof']).read_text(encoding='utf8'))
            if abs(d-float(q['duracao_s']))>.05:
                raise ValueError('E209-ATLAS-RETIMAR: '+s['id'])
        if s['type']=='video':
            m=p['media'][s['asset']]
            if m.get('duration_s') is not None and float(s.get('source_in_seconds') or 0)+d>float(m['duration_s'])+.05:
                raise ValueError('E209-VIDEO-CURTO: '+s['id'])
        if any(float(x['at'])>=d for x in s.get('cues') or []):
            raise ValueError('E209-CUE-FORA: '+s['id'])
        s['start'],s['end']=t,round(t+d,4)
        t=s['end']
    p['duracao']=t
    return p


def anexar_audio_documental(props: dict, audio: str, grupos: list[dict], public_root: Path, metodo: str) -> dict:
    """Áudio privado autenticado e legendas em tempo absoluto. Nenhuma alteração da cadência."""
    import wave
    if props.get('preview') is not True or props.get('private_review_only') is not True:
        raise ValueError('E207-PRIVADO')
    from src.v4.formatos import politica_animacao as PA
    if props.get('animation_policy_mode')==PA.LEGACY:
        raise ValueError('E211-LEGADO-NAO-ENTRA-EM-DOCUMENTARIO')
    PA.exigir(props['shots'], modo=props.get('animation_policy_mode'), privado=True)
    if metodo not in ('PALAVRAS_MEDIDAS', 'FRASES_MEDIDAS_LAB'):
        raise ValueError('E207-METODO')
    if not isinstance(audio, str) or not re.fullmatch(r'e202/[0-9a-f]{64}\.wav', audio):
        raise ValueError('E207-ASSET')
    raiz = Path(public_root).resolve()
    p = (raiz / audio).resolve()
    if not p.is_relative_to(raiz) or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != p.stem:
        raise ValueError('E207-HASH')
    with wave.open(str(p), 'rb') as w:
        dur = w.getnframes()/w.getframerate()
    total = float(props['duracao'])
    if abs(dur-total) > .08:
        raise ValueError(f'E207-DURACAO-AUDIO: {dur:.3f} x {total:.3f}')
    if not grupos:
        raise ValueError('E207-SEM-LEGENDAS')
    prev = 0.
    for g in grupos:
        a,b = g['start'],g['end']
        ws = g.get('words')
        if (not all(isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x) for x in (a,b))
                or a < prev-.001 or b <= a or b > total+.001 or not isinstance(ws,list) or not ws
                or len(ws)>6 or any(not isinstance(w.get('w'),str) or not w['w'].strip() for w in ws)
                or sum(bool(w.get('hl')) for w in ws)>1):
            raise ValueError('E207-LEGENDA')
        prev = b
    # Every non-declarative shot must actually have a caption interval.
    for s in props['shots']:
        if s['type'] != 'scene_graph' and not any(g['start']<s['end'] and g['end']>s['start'] for g in grupos):
            raise ValueError('E207-CENA-SEM-LEGENDA: '+s['id'])
    return {**props, 'scene_narration_asset': audio, 'documentary_captions': grupos,
            'documentary_caption_origin': metodo}


def _dominio(u: str) -> str:
    m = re.match(r'https://(?:www\.)?([^/]+)', u)
    return m.group(1) if m else u


def auditoria_contrato(props: dict) -> dict:
    """Mesma rubrica do ATLAS/FILME (contrato_visual_comum.auditar): estrutura declarada; visão e humano à parte."""
    from src.v4.formatos import contrato_visual_comum as CV
    return CV.auditar(props)


PROMPT_VISAO = """Você revisa quadros de um vídeo vertical do canal Coringa Explica. Avalie SÓ o que está nas imagens.
Pergunta do vídeo: {pergunta}
O que o espectador precisa ver acontecer: {acontecimento}
Imagens: quadros em ordem temporal (um por etapa).
Verifique também: cada ícone representa FIELMENTE o rótulo (não um objeto parecido)? o estado inicial aparece antes
da mudança (o resultado não aparece antes da causa)? as partes que interagem estão no mesmo lugar?
Responda JSON: {{"referente_visivel":bool,"aprendizado_demonstrado":bool,"enquadramento_adequado":bool,
"imagem_celular_legivel":bool,"acao_ou_relacao_visivel":bool,"icones_fieis":bool,"estados_coerentes":bool,"problemas":["defeito concreto e onde"],
"correcoes":[{{"beat":n,"tipo":"enquadramento|forma|acao|rotulo","descricao":"..."}}]}}"""


def _visao_claude(jpgs: list[bytes], texto: str) -> dict:
    """Mesma revisão pelo Claude Code da assinatura, lendo os quadros como arquivos (só a ferramenta Read,
    numa pasta temporária com apenas as imagens). Usado quando o Gemini (visão) está indisponível."""
    import subprocess
    import tempfile
    from src import claude, gemini
    if not claude.disponivel():
        os.environ['USAR_CLAUDE'] = '1'
        if not claude.disponivel():
            raise RuntimeError('Claude Code indisponível para visão')
    with tempfile.TemporaryDirectory() as d:
        nomes = []
        for k, b in enumerate(jpgs):
            n = f'q{k + 1}.jpg'
            Path(d, n).write_bytes(b)
            nomes.append(n)
        pedido = (texto + '\n\nAs imagens estão nesta pasta, em ordem: ' + ', '.join(nomes)
                  + '. Abra CADA uma com a ferramenta Read antes de responder. Responda SOMENTE o JSON pedido.')
        cmd = ['claude', '-p', '--model', claude.MODELO, '--output-format', 'json', '--max-turns', str(len(nomes) + 4),
               '--allowedTools', 'Read', '--disallowedTools', 'Bash,Edit,Write,Glob,Grep,WebFetch,WebSearch,Task,NotebookEdit,TodoWrite']
        r = subprocess.run(cmd, input=pedido, capture_output=True, text=True, timeout=420, cwd=d, env=claude._ambiente())
    saida = json.loads(r.stdout)
    if isinstance(saida, list):
        saida = next((x for x in reversed(saida) if isinstance(x, dict) and x.get('type') == 'result'), {})
    if saida.get('is_error') or not str(saida.get('result') or '').strip():
        raise RuntimeError(f"visão Claude falhou: {str(saida.get('result') or saida.get('subtype'))[:200]}")
    obj = gemini.extrair_json(str(saida['result']))
    obj['_provedor'] = f'claude_code:{claude.MODELO}'
    obj['_credito_usd'] = float(saida.get('total_cost_usd') or 0)
    return obj


def revisao_visual(jpgs: list[bytes], caso: dict, plano: dict) -> dict:
    """Visão automatizada com a rubrica comum (Claude por padrão). Não é aprovação; serve para correção dirigida."""
    from src import gemini
    from src.v4.formatos import contrato_visual_comum as CV
    texto = PROMPT_VISAO.format(pergunta=caso['pergunta'], acontecimento=plano.get('acontecimento_central', ''))
    tentativas = []
    r = None
    for prov in [x.strip() for x in os.getenv('E202_VISAO', 'claude').split(',') if x.strip()]:
        try:
            r = gemini.json_visao(texto, jpgs, leve=False) if prov == 'gemini' else _visao_claude(jpgs, texto)
            if isinstance(r, dict):
                r.setdefault('_provedor', 'gemini' if prov == 'gemini' else r.get('_provedor'))
                break
        except Exception as e:
            tentativas.append(f'{prov}: {type(e).__name__}: {str(e)[:160]}')
            r = None
    if r is None:
        raise RuntimeError('visão indisponível: ' + ' | '.join(tentativas))
    verbo = plano['cenas'][0].get('verbo', 'DEMONSTRAR')
    falhas = CV.julgar_inspecao(verbo, False, r)
    for campo in ('icones_fieis', 'estados_coerentes'):
        if r.get(campo) is not True:
            falhas.append('V-' + campo + ': confirmação obrigatória ausente')
    if not str(r.get('_provedor', '')).startswith('claude_code:'):
        falhas.append('V-REVISAO-RIGOROSA-PENDENTE: Gemini não substitui Claude')
    return {'resposta': r, 'falhas': falhas, 'tentativas': tentativas}


# ───────────────────────── CLI ─────────────────────────
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description='E202 diretor visual autônomo (privado)')
    sub = ap.add_subparsers(dest='cmd', required=True)
    d = sub.add_parser('dirigir'); d.add_argument('entrada'); d.add_argument('saida'); d.add_argument('--caso', action='append')
    d.add_argument('--sem-ia', action='store_true', help='só cache; falha se faltar')
    m = sub.add_parser('filme'); m.add_argument('resultado'); m.add_argument('entrada'); m.add_argument('saida')
    m.add_argument('--narracao', help='json com duracoes e palavras medidas'); m.add_argument('--audio')
    tr = sub.add_parser('triagem-documental')
    tr.add_argument('entrada', help='JSON com fatos e necessidades_visuais')
    tr.add_argument('saida')
    mx = sub.add_parser('montagem-mista')
    mx.add_argument('resultado'); mx.add_argument('caso'); mx.add_argument('plano_documental')
    mx.add_argument('duracoes'); mx.add_argument('saida'); mx.add_argument('public_root')
    mx.add_argument('--narracao', help='JSON com duracoes/palavras e audio autenticado')
    mx.add_argument('--retimar', action='store_true')
    aq = sub.add_parser('pesquisa-documental')
    aq.add_argument('entrada', help='JSON: fatos + necessidades_visuais, ou caso com pergunta e fatos')
    aq.add_argument('saida'); aq.add_argument('--autor-ia', action='store_true')
    aq.add_argument('--sem-ia', action='store_true')
    a = ap.parse_args(argv)
    if a.cmd == 'pesquisa-documental':
        from src.v4.formatos import garimpo_visual
        ent = json.loads(Path(a.entrada).read_text(encoding='utf8'))
        destino = Path(a.saida)
        destino.mkdir(parents=True, exist_ok=True)
        if a.autor_ia:
            plano = planejar_documental(ent, permitir_chamada=not a.sem_ia)
        else:
            plano = {'triagem': triagem_documental(ent['necessidades_visuais'], ent['fatos']),
                     'chamadas_ia': [], 'publicar': False}
        (destino / 'triagem.json').write_text(json.dumps(plano, ensure_ascii=False, indent=2), encoding='utf8')
        garimpo_visual.pesquisar_triagem(plano['triagem'], destino)
        return 0
    if a.cmd == 'triagem-documental':
        ent = json.loads(Path(a.entrada).read_text(encoding='utf8'))
        r = triagem_documental(ent['necessidades_visuais'], ent['fatos'])
        Path(a.saida).write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding='utf8')
        return 0
    if a.cmd == 'montagem-mista':
        def ler(p):
            return json.loads(Path(p).read_text(encoding='utf8'))
        res, caso, doc = ler(a.resultado), ler(a.caso), ler(a.plano_documental)
        n = ler(a.narracao) if a.narracao else {}
        ds = n.get('duracoes') or ler(a.duracoes)
        if a.retimar:
            doc = retimar_documental(res['plano'], doc, ds)
        preparar_misto(res, caso, doc, Path(a.saida), Path(a.public_root), ds,
                       palavras=n.get('palavras'), audio=n.get('audio'))
        return 0
    if a.cmd == 'dirigir':
        ent = json.loads(Path(a.entrada).read_text(encoding='utf8'))
        out = Path(a.saida); out.mkdir(parents=True, exist_ok=True)
        ok = True
        for caso in ent['cases']:
            if a.caso and caso['id'] not in a.caso:
                continue
            try:
                r = dirigir(caso, permitir_chamada=not a.sem_ia)
            except Exception as e:
                r = {'caso': caso['id'], 'estado': 'ERRO_IA', 'erro': f'{type(e).__name__}: {str(e)[:300]}'}
            comp = r.pop('compilado', None) or {}
            r['compilado_resumo'] = {k: v['proveniencia'] for k, v in comp.items()}
            (out / f"{caso['id']}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1) + '\n', encoding='utf8')
            print('E202-DIRECAO', json.dumps({'caso': caso['id'], 'estado': r['estado'],
                                             'violacoes': [v['regra'] for v in r.get('violacoes_finais') or []],
                                             'chamadas': r.get('chamadas_ia')}, ensure_ascii=False))
            ok &= r['estado'] == 'PLANO_COMPILADO'
        return 0 if ok else 2
    if a.cmd == 'filme':
        res = json.loads(Path(a.resultado).read_text(encoding='utf8'))
        ent = json.loads(Path(a.entrada).read_text(encoding='utf8'))
        caso = next(c for c in ent['cases'] if c['id'] == res['caso'])
        dur = pal = None
        if a.narracao:
            n = json.loads(Path(a.narracao).read_text(encoding='utf8'))
            dur, pal = n['duracoes'], n['palavras']
        f = filme(res, caso, dur, pal, a.audio)
        Path(a.saida).write_text(json.dumps(f['props'], ensure_ascii=False) + '\n', encoding='utf8')
        print('E202-FILME', json.dumps({'caso': caso['id'], 'duracao': f['props']['duracao'],
                                       'legendas': f['proveniencia']['legendas']}, ensure_ascii=False))
        return 0
    return 1


if __name__ == '__main__':
    sys.exit(main())
