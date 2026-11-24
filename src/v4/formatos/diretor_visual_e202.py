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
   transformar, mover, revelar_interior). Card, texto, seta ou ícone parado NÃO substituem ação.
4. Gancho: o 1º beat começa com o protagonista em quadro e uma pergunta/contradição forte; nada de introdução lenta.
5. Progressão: cada beat acrescenta informação nova; o último beat é o payoff (resposta clara).
6. Escolha a modalidade pelo ACONTECIMENTO e pela disponibilidade REAL abaixo; nunca peça modalidade indisponível.
   Mapa inventado é proibido; contorno geo é dado real e serve para localizar sem desenhar limites inexistentes.
7. Ícones: use nomes EXATOS do catálogo. Se nenhum representa fielmente o objeto (ex.: um órgão ausente), use primitiva
   com rótulo — nunca um ícone de outra coisa só porque parece.
8. Narração em português do Brasil, frases curtas e faladas, 8–15 palavras por beat. 3–4 beats (≈ 12–18 s no total).
9. Rótulos de ator curtos (≤ 22 caracteres) em português. Até 6 atores por cena.
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
    base = f"""Você é o DIRETOR VISUAL do Coringa Explica (documentário vertical 9:16, Reels/TikTok/Shorts, pt-BR).
Transforme os fatos abaixo em UMA cena animada de {alvo[0]}–{alvo[1]} s que MOSTRE o acontecimento acontecendo.

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
    props = ('x', 'y', 'scale', 'sx', 'sy', 'opacity')
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


def filme(resultado: dict, caso: dict, duracoes: list[float] | None = None, palavras: list[dict] | None = None,
          audio: str | None = None) -> dict:
    """Uma cena declarativa → props do FilmeEditorial (mesmo compositor das outras modalidades)."""
    plano = resultado['plano']
    cena = next(c for c in plano['cenas'] if c.get('modalidade') == 'cena_declarativa')
    dur = duracoes or estimar_duracoes(cena)
    comp = CD.compilar(cena, dur, caso['fatos'], palavras, titulo=str(plano.get('titulo') or ''))
    sg = comp['scene_graph']
    total = round(comp['duracao'], 4)          # mesmo arredondamento dos estados (t ≤ duração)
    shot = {'id': cena['id'], 'start': 0, 'end': total, 'type': 'scene_graph', 'evidence': 'explainer',
            'subject': str(plano.get('acontecimento_central') or cena.get('acontecimento') or '')[:120],
            'lead': cena.get('verbo', 'DEMONSTRAR'), 'headline': sg['headline'],
            'source': sg['source'], 'source_display': ', '.join(_dominio(u) for u in sg['sources']),
            'scene_graph': sg,
            'direcao_visual': {'verbo': cena.get('verbo'), 'referente': cena.get('acontecimento'),
                               'aprendizado': cena['beats'][-1]['fala'], 'provas': sorted({f for b in cena['beats'] for f in b['fatos']})},
            'estados_esperados': [], 'cues': []}
    props = {'formato': 'filme_editorial', 'duracao': total, 'shots': [shot], 'preview': True, 'private_review_only': True}
    if audio:
        props['scene_narration_asset'] = audio
    return {'props': props, 'proveniencia': comp['proveniencia']}


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
"imagem_celular_legivel":bool,"acao_ou_relacao_visivel":bool,"problemas":["defeito concreto e onde"],
"correcoes":[{{"beat":n,"tipo":"enquadramento|forma|acao|rotulo","descricao":"..."}}]}}"""


def revisao_visual(jpgs: list[bytes], caso: dict, plano: dict) -> dict:
    """Visão automatizada (Gemini) com a rubrica comum. Não é aprovação; serve para UMA correção dirigida."""
    from src import gemini
    from src.v4.formatos import contrato_visual_comum as CV
    texto = PROMPT_VISAO.format(pergunta=caso['pergunta'], acontecimento=plano.get('acontecimento_central', ''))
    r = gemini.json_visao(texto, jpgs, leve=False)
    verbo = plano['cenas'][0].get('verbo', 'DEMONSTRAR')
    return {'resposta': r, 'falhas': CV.julgar_inspecao(verbo, False, r)}


# ───────────────────────── CLI ─────────────────────────
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description='E202 diretor visual autônomo (privado)')
    sub = ap.add_subparsers(dest='cmd', required=True)
    d = sub.add_parser('dirigir'); d.add_argument('entrada'); d.add_argument('saida'); d.add_argument('--caso', action='append')
    d.add_argument('--sem-ia', action='store_true', help='só cache; falha se faltar')
    m = sub.add_parser('filme'); m.add_argument('resultado'); m.add_argument('entrada'); m.add_argument('saida')
    m.add_argument('--narracao', help='json com duracoes e palavras medidas'); m.add_argument('--audio')
    a = ap.parse_args(argv)
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
