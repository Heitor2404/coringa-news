"""Diretor audiovisual (V3): transforma o STORYBOARD (contrato de direção, um plano por acontecimento ou ideia) em cenas
do palco V2 — câmera, anotações, tempos — e recusa o plano que não se sustenta.

Ordem do fluxo: pesquisa → fatos comprovados → recursos disponíveis → DIREÇÃO E STORYBOARD → roteiro definitivo →
narração → edição (este módulo) → render → controle de qualidade (src/v2/fiscal_av.py).

Quem escreve o storyboard: um modelo de linguagem com o PROMPT_DIRETOR (uma chamada por vídeo), ou uma pessoa. Quem
decide se ele é executável: este módulo, sem IA. Cada campo do contrato muda a montagem real:

  evento_id / fato_id / fonte   → rastreio (o fato precisa existir na pesquisa; senão o plano é recusado)
  funcao_narrativa              → ritmo (gancho e revelação têm entrada mais curta; contexto aceita plano mais longo)
  recurso_visual                → arquivo da foto/composição; foto IA ou sem crédito → recusa
  funcao_documental             → selo na tela (REGISTRO, CONTEXTO, DOCUMENTO, ESQUEMA, RECONSTRUÇÃO, REPRESENTAÇÃO HISTÓRICA)
  objeto_principal              → região pedida à visão; sem região localizada não há anotação, só enquadramento
  regiao_de_interesse           → caixa usada pela câmera e pelas anotações (preenchida a partir da visão)
  plano_inicial / plano_final   → enquadramentos-chave da câmera (geral, contexto, objeto, detalhe, ou caixa explícita)
  acao_visual                   → o que muda no plano (o fiscal confere que a imagem não ficou parada)
  movimento_camera              → revelar | aproximar | localizar | acompanhar | explicar | comparar | fixo
  anotacoes                     → círculo/contorno/foco/seta/trajeto ancorados numa região e numa PALAVRA da narração
  composicao                    → doc.plano, doc.eclusa ou uma composição V2 existente (dados, mapa, linha do tempo…)
  transicao                     → dissolve, corte, zoom… (a mesma transição seguida demais vira aviso)
  tempo_inicio / tempo_fim      → da narração: "na_palavra" (texto da fala) vira segundo exato pelo alinhamento
  criterio_de_validacao         → regras medidas no render (ocupação do objeto, anotação dentro da área segura, …)
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

FUNCOES_DOC = {'REGISTRO', 'CONTEXTO', 'DOCUMENTO', 'ESQUEMA', 'RECONSTRUÇÃO', 'REPRESENTAÇÃO HISTÓRICA', 'EDITORIAL'}
TEMPOS_POR_NOME = {'doc.eclusa', 'doc.molde'}     # composições V3 que leem `tempos` como {passo: segundo}
MOVIMENTOS = {'revelar', 'aproximar', 'localizar', 'acompanhar', 'explicar', 'comparar', 'fixo'}
CAMPOS = ('evento_id', 'fato_id', 'fonte', 'funcao_narrativa', 'recurso_visual', 'funcao_documental', 'objeto_principal',
          'regiao_de_interesse', 'plano_inicial', 'plano_final', 'acao_visual', 'movimento_camera', 'anotacoes',
          'composicao', 'transicao', 'layout', 'tempo_inicio', 'tempo_fim', 'criterio_de_validacao')
OBRIGATORIOS = ('evento_id', 'fato_id', 'funcao_narrativa', 'recurso_visual', 'funcao_documental', 'acao_visual',
                'composicao', 'tempo_inicio', 'tempo_fim')

PROMPT_DIRETOR = """Você é o diretor de um documentário curto vertical (9:16). Para cada trecho da narração, escreva UM plano
seguindo o contrato abaixo. Responda só JSON: {"planos": [...]}.

Regras de direção:
- A foto real relevante é o elemento principal. Não cubra fotografia com cartão de texto.
- Todo movimento de câmera tem intenção (revelar, aproximar, localizar, acompanhar, explicar, comparar). Sem intenção: "fixo".
- Anotação só sobre um objeto que está NA FOTO (a visão vai localizar "objeto_principal"; se não achar, a anotação cai).
- Mecanismo (como algo funciona) é mostrado por uma composição que ANIMA a ação (ex.: doc.eclusa), não por cartões.
- Diferencie: REGISTRO (a foto é do próprio fato), CONTEXTO (lugar/objeto relacionado, não o instante),
  DOCUMENTO, ESQUEMA (desenho didático), RECONSTRUÇÃO (identificada), REPRESENTAÇÃO HISTÓRICA (gravura/pintura de época).
- Uma foto atual de ruína não é registro de um acontecimento antigo. Não invente fatos, detalhes de ação nem fontes.
- Não repita a mesma foto em planos seguidos; varie o enquadramento. Transição: corte, salvo motivo narrativo.
- "na_palavra": cite a palavra da narração em que a anotação deve aparecer.

Contrato de cada plano:
{"evento_id", "fato_id" (id do fato da pesquisa), "fonte", "funcao_narrativa" (gancho|contexto|mecanismo|consequencia|revelacao|fechamento),
 "fala" (o trecho exato da narração), "recurso_visual": {"tipo": "foto|composicao", "id": "<id do acervo ou da composição>"},
 "funcao_documental", "objeto_principal", "plano_inicial", "plano_final" (geral|contexto|objeto|detalhe),
 "acao_visual", "movimento_camera", "anotacoes": [{"tipo": "circulo|contorno|foco|seta|trajeto", "alvo": "<objeto>", "ate": "<objeto, p/ seta>", "texto": "<≤ 34>", "na_palavra": "<palavra>"}],
 "composicao", "transicao", "selo_texto" (≤ 40: lugar/ano/natureza), "criterio_de_validacao": ["..."]}

FATOS: {fatos}
ACERVO (id · o que mostra · ano · crédito): {acervo}
NARRAÇÃO (trechos): {falas}"""


def _n(s: str) -> str:
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9 ]+', ' ', s).strip()


# ---------------------------------------------------------------- tempos a partir da narração
def palavras_da_narracao(legendas: list[dict]) -> list[dict]:
    """legendas do src.voz (blocos com words [{w, s}]) → lista de {w, s} em ordem."""
    out = []
    for b in legendas or []:
        for w in b.get('words') or []:
            out.append({'w': _n(w.get('w')), 's': float(w.get('s', b.get('start', 0)))})
    return out


def tempo_da_palavra(palavras: list[dict], fala: str, palavra: str, ini: float, fim: float) -> float | None:
    """Primeira ocorrência de `palavra` dentro do intervalo do plano (tolerância de 0,2 s)."""
    alvo = _n(palavra).split()
    if not alvo:
        return None
    ws = [p for p in palavras if ini - .2 <= p['s'] <= fim + .2]
    for i in range(len(ws)):                   # 1º: a palavra exata ("desce" não é "descer")
        if [w['w'] for w in ws[i:i + len(alvo)]] == alvo:
            return ws[i]['s']
    for w in ws:                               # palavra composta alinhada como um token ("segunda feira")
        if ' ' in w['w'] and w['w'].split()[:len(alvo)] == alvo:
            return w['s']
    if len(alvo) == 1:                         # 2º: flexão da mesma palavra (fecham/fecha), mesmo radical de 5 letras e tamanho parecido
        for w in ws:
            if w['w'][:5] == alvo[0][:5] and abs(len(w['w']) - len(alvo[0])) <= 2:
                return w['s']
    return None


# ---------------------------------------------------------------- enquadramentos
def _expandir(c, m, aspecto):
    """Caixa com a proporção EXATA da tela (aspecto = largura/altura em coordenadas normalizadas da foto), contendo a
    região expandida por `m`. Se não couber na foto, encolhe mantendo a proporção (o centro manda). Nunca devolve
    uma caixa que deixaria faixas vazias na tela."""
    x, y, w, h = c
    cx, cy = x + w / 2, y + h / 2
    w, h = w * (1 + m), h * (1 + m)
    if w / h < aspecto:
        w = h * aspecto
    elif w / aspecto <= 1:
        h = w / aspecto
    else:                                      # região larga demais para o quadro vertical: enquadra pela altura dela
        w = h * aspecto                        # (um trecho da região, centrado; a câmera pode percorrê-la)
    k = min(1.0, 1 / w, 1 / h)                 # cabe na foto
    w, h = w * k, h * k
    x, y = min(max(0.0, cx - w / 2), 1 - w), min(max(0.0, cy - h / 2), 1 - h)
    return [round(x, 4), round(y, 4), round(w, 4), round(h, 4)]


def enquadramento(nome, roi: list | None, foco: list | None, wh) -> list:
    """geral = o maior recorte vertical da foto (sem faixas), centrado no assunto · contexto = objeto com bastante ar ·
    objeto = objeto ocupando o quadro · detalhe = bem perto. A proporção é a da tela acima da legenda (1080×1540)."""
    if isinstance(nome, list):
        return nome
    iw, ih = wh
    asp = (1080 / 1540) * ih / iw              # largura/altura normalizadas que dão 1080×1540 na tela
    base = roi or foco or [0.25, 0.25, 0.5, 0.5]
    if nome == 'geral':
        return _expandir(base, 50, asp)        # expande até bater nos limites da foto
    m = {'contexto': 1.6, 'objeto': .45, 'detalhe': .12}.get(nome, .45)
    if nome in ('objeto', 'contexto') and base[2] / base[3] > 2.2 * asp:
        # objeto muito mais largo que o quadro vertical (um corpo deitado, uma ponte): mostra a largura inteira; o
        # diretor escolhe o layout 'integral' (margem intencional) em vez de cortar uma fatia sem sentido
        x, y, w, h = base
        w2 = min(1.0, w * (1 + m * .4)); h2 = min(1.0, max(h * (1 + m), w2 / asp * .5))
        return [round(min(max(0.0, x + w / 2 - w2 / 2), 1 - w2), 4), round(min(max(0.0, y + h / 2 - h2 / 2), 1 - h2), 4), round(w2, 4), round(h2, 4)]
    return _expandir(base, m, asp)


def camera(mov: str, ini: list, fim: list, dur: float, t0: float = 0.0) -> list[dict]:
    """Enquadramentos-chave em tempo local da cena. 'fixo' = UM enquadramento, sem transformação no tempo (Plano Mestre
    §4.2: nada de zoom automático para esconder slide). Movimento dura o plano inteiro, com assentamento no fim."""
    if mov == 'fixo' or ini == fim:
        return [{'t': 0, 'caixa': fim}]
    if mov in ('localizar',):                  # começa no objeto e recua para mostrar onde ele está
        return [{'t': 0, 'caixa': ini}, {'t': max(.6, t0), 'caixa': ini}, {'t': dur * .92, 'caixa': fim}]
    return [{'t': 0, 'caixa': ini}, {'t': dur * .9, 'caixa': fim}]


# ---------------------------------------------------------------- validação e execução
def validar(plano: dict, fatos_ids: set[str], acervo: dict) -> list[str]:
    erros = [f'campo obrigatório ausente: {c}' for c in OBRIGATORIOS if plano.get(c) in (None, '', [])]
    if plano.get('fato_id') and fatos_ids and plano['fato_id'] not in fatos_ids:
        erros.append(f"fato {plano['fato_id']} não está na pesquisa")
    if plano.get('funcao_documental') not in FUNCOES_DOC:
        erros.append(f"função documental inválida: {plano.get('funcao_documental')}")
    if plano.get('movimento_camera', 'fixo') not in MOVIMENTOS:
        erros.append(f"movimento sem intenção conhecida: {plano.get('movimento_camera')}")
    rv = plano.get('recurso_visual') or {}
    if rv.get('tipo') == 'foto':
        x = acervo.get(rv.get('id'))
        if not x:
            erros.append(f"foto {rv.get('id')} não está no acervo")
        elif x.get('ia'):
            erros.append(f"foto {rv.get('id')} é gerada por IA: não entra como imagem real")
        elif not x.get('credito'):
            erros.append(f"foto {rv.get('id')} sem crédito/licença registrados")
        if plano.get('funcao_documental') == 'REGISTRO' and x and x.get('ano') and plano.get('ano_do_fato') \
                and abs(int(x['ano']) - int(plano['ano_do_fato'])) > 2:
            erros.append(f"foto de {x['ano']} não é REGISTRO de um fato de {plano['ano_do_fato']}")
    if (plano.get('tempo_fim') or 0) - (plano.get('tempo_inicio') or 0) < 1.2:
        erros.append('plano curto demais (< 1,2 s) para ser lido')
    return erros


IMPACTOS = ('aceitavel', 'revisao', 'bloqueio')


def degradar(r: dict, impacto: str, codigo: str, texto: str, essencial: bool = False) -> None:
    """V3.1-resgate: toda perda/substituição feita para a execução seguir fica REGISTRADA com o impacto editorial.
    aceitavel = não muda o sentido; revisao = pode comprometer legibilidade/ritmo/direção (olho humano obrigatório);
    bloqueio = elimina ou distorce o acontecimento (o chamador replaneja ou bloqueia). `essencial` = o elemento perdido
    era a demonstração pedida para o acontecimento."""
    assert impacto in IMPACTOS
    r.setdefault('degradacoes', []).append({'impacto': impacto, 'codigo': codigo, 'texto': texto, 'essencial': essencial})
    r.setdefault('limitacoes', []).append(texto)


def montar(storyboard: dict, acervo: dict, regioes: dict, palavras: list[dict], fatos_ids: set[str] | None = None) -> tuple[list[dict], list[dict]]:
    """→ (cenas V2, registro por plano). Plano inválido NÃO vira cena: entra no registro com o motivo (o chamador bloqueia)."""
    cenas, reg = [], []
    planos = storyboard['planos']
    for i, pl in enumerate(planos):
        r = {'evento_id': pl.get('evento_id'), 'composicao': pl.get('composicao'), 'erros': [], 'limitacoes': [], 'degradacoes': [],
             'critico': bool(pl.get('critico'))}
        r['erros'] = validar(pl, fatos_ids or set(), acervo)
        a, b = float(pl['tempo_inicio']), float(pl['tempo_fim'])
        dur = b - a
        rv = pl.get('recurso_visual') or {}
        sc = {'comp': pl['composicao'], 'start': round(a, 3), 'end': round(b, 3), 'transicao': pl.get('transicao') or 'corte',
              'fala': pl.get('fala', ''), 'origem': [i], 'direcao': {k: pl.get(k) for k in CAMPOS}}
        if pl['composicao'] == 'doc.plano':
            x = acervo.get(rv.get('id')) or {}
            wh = x.get('wh') or [1600, 1000]
            rg = regioes.get(x.get('sha'), {}) if x else {}
            obs = rg.get('objetos') or {}
            alvo = obs.get(pl.get('objeto_principal') or '') or {}
            roi = alvo.get('caixa') if alvo.get('visivel') else None
            foco = (rg.get('foco') or {}).get('caixa')
            if pl.get('objeto_principal') and not roi:
                degradar(r, 'bloqueio' if pl.get('critico') else 'revisao', 'OBJETO-NAO-LOCALIZADO',
                         f"objeto '{pl['objeto_principal']}' não localizado: câmera no foco da foto, sem anotação nele", essencial=True)
            def enq(v, padrao):
                # "detalhe" (do objeto principal) ou {"objeto": "<outro objeto localizado>", "enquadramento": "detalhe"}
                if isinstance(v, dict):
                    o = obs.get(v.get('objeto') or '') or {}
                    if not o.get('caixa'):
                        degradar(r, 'revisao', 'ENQUADRAMENTO-SEM-REGIAO', f"enquadramento em '{v.get('objeto')}' sem região: uso o objeto principal")
                    return enquadramento(v.get('enquadramento') or 'objeto', o.get('caixa') or roi, foco, wh)
                return enquadramento(v or padrao, roi, foco, wh)
            loc = pl.get('movimento_camera') == 'localizar'
            ini = enq(pl.get('plano_inicial'), 'detalhe' if loc else 'geral')
            fim = enq(pl.get('plano_final'), 'geral' if loc else 'objeto')
            def pouco(a_, b_):                    # mudança de tamanho < 15% e de centro < 6% da foto
                return abs(a_[2] - b_[2]) / max(a_[2], b_[2]) < .15 and abs((a_[0] + a_[2] / 2) - (b_[0] + b_[2] / 2)) < .06 \
                    and abs((a_[1] + a_[3] / 2) - (b_[1] + b_[3] / 2)) < .06
            if pl.get('movimento_camera') not in ('fixo', None) and pouco(ini, fim) and not pl.get('camera_chaves'):
                # V3.1-resgate: movimento sem percurso perceptível. Aproximar até o detalhe do PRÓPRIO objeto mantém a
                # intenção; não dá → plano FIXO (antes: percurso lateral inventado, só para a imagem andar).
                det = enquadramento('detalhe', roi, foco, wh)
                if roi and not pouco(ini, det):
                    fim = det if not loc else fim
                    if loc:
                        ini = det
                    degradar(r, 'aceitavel', 'MOVIMENTO-ATE-DETALHE', 'movimento pedido era imperceptível: câmera vai até o detalhe do objeto')
                else:
                    ini = fim
                    pl = {**pl, 'movimento_camera': 'fixo'}
                    sc['direcao']['movimento_camera'] = 'fixo'
                    degradar(r, 'aceitavel', 'MOVIMENTO-VIRA-FIXO', 'movimento sem percurso perceptível: plano fixo (nenhum movimento inventado)')
            anot = []

            def _t1(an):                          # a anotação sai na palavra pedida (evita acúmulo de rótulos)
                if an.get('t1_palavra'):
                    t = tempo_da_palavra(palavras, pl.get('fala', ''), an['t1_palavra'], a, b)
                    return round(t - a, 2) if t is not None else None
                return an.get('t1')
            for an in pl.get('anotacoes') or []:
                t = tempo_da_palavra(palavras, pl.get('fala', ''), an.get('na_palavra', ''), a, b) if an.get('na_palavra') else None
                t0 = (t - a) if t is not None else min(dur * .35, 1.2)
                if an.get('na_palavra') and t is None:
                    degradar(r, 'revisao', 'SINCRONIA-PALAVRA', f"palavra '{an['na_palavra']}' não encontrada na narração alinhada: anotação em {t0:.1f}s (fora de sincronia)")
                o = obs.get(an.get('alvo') or '') or {}
                if an['tipo'] in ('seta', 'trajeto'):
                    o2 = obs.get(an.get('ate') or '') or {}
                    dv = an.get('ate_desvio')
                    if dv is not None and not (isinstance(dv, (list, tuple)) and len(dv) == 2 and all(isinstance(x, (int, float)) for x in dv)):
                        degradar(r, 'bloqueio' if an.get('essencial') else 'revisao', 'ANOTACAO-RETIRADA',
                                 f"ate_desvio inválido ({dv!r}) em '{an.get('alvo')}': seta retirada (ERR-018)", bool(an.get('essencial')))
                        continue
                    if o.get('ancoravel') and dv:
                        # seta de ESQUEMA que parte de um objeto localizado numa direção dada (ex.: "para cima" = coluna
                        # de cinzas). O desvio é direção didática, não posição de algo na foto: o rótulo precisa dizer "esquema".
                        c1 = o['caixa']
                        de = [c1[0] + c1[2] / 2, c1[1] + c1[3] * .2]
                        para = [min(.98, max(.02, de[0] + an['ate_desvio'][0])), min(.98, max(.02, de[1] + an['ate_desvio'][1]))]
                        anot.append({'tipo': an['tipo'], 'de': de, 'para': para, 't0': round(t0, 2), 'texto': an.get('texto', ''),
                                     'curva': an.get('curva', 0), 'desenho': an.get('desenho', 1.4)})
                        if 'esquema' not in _n(an.get('texto')):
                            r['erros'].append(f"seta com direção dada em '{an.get('alvo')}' precisa dizer que é esquema no rótulo")
                        continue
                    if o.get('ancoravel') and o2.get('ancoravel'):
                        c1, c2 = o['caixa'], o2['caixa']
                        de = [c1[0] + c1[2] / 2, c1[1] + c1[3] * .55]
                        para = [c2[0] + c2[2] / 2, c2[1] + c2[3] * .35]
                        anot.append({'tipo': an['tipo'], 'de': de, 'para': para, 't0': round(t0, 2), 'texto': an.get('texto', ''),
                                     'curva': an.get('curva', .18), 'desenho': an.get('desenho', 1.4), 't1': _t1(an)})
                    else:
                        degradar(r, 'bloqueio' if an.get('essencial') else 'revisao', 'ANOTACAO-RETIRADA',
                                 f"{an['tipo']} '{an.get('alvo')}' → '{an.get('ate')}' sem as duas regiões localizadas: anotação retirada", bool(an.get('essencial')))
                    continue
                if not o.get('ancoravel'):
                    degradar(r, 'bloqueio' if an.get('essencial') else 'revisao', 'ANOTACAO-RETIRADA',
                             f"anotação em '{an.get('alvo')}' retirada: objeto não localizado com confiança", bool(an.get('essencial')))
                    continue
                tipo = an['tipo']
                cx_, fx = o['caixa'], fim
                fora = max(0.0, fx[0] - cx_[0]) + max(0.0, cx_[0] + cx_[2] - fx[0] - fx[2]) + max(0.0, fx[1] - cx_[1]) + max(0.0, cx_[1] + cx_[3] - fx[1] - fx[3])
                if tipo in ('circulo', 'contorno') and fora > .15 * (cx_[2] + cx_[3]):
                    tipo = 'ponto'                   # região maior que o quadro final: contorno sairia da tela → marcador no centro
                    degradar(r, 'aceitavel', 'ANOTACAO-VIRA-MARCADOR', f"'{an.get('alvo')}' não cabe no quadro final: {an['tipo']} virou marcador com rótulo")
                anot.append({'tipo': tipo, 'caixa': o['caixa'], 't0': round(t0, 2), 'texto': an.get('texto', ''),
                             't1': _t1(an), 'lado': an.get('lado')})
            cam = camera(pl.get('movimento_camera') or 'fixo', ini, fim, dur)
            if pl.get('camera_chaves'):               # câmera que muda de enquadramento NA PALAVRA (não no meio do plano)
                cam, atual = [{'t': 0, 'caixa': ini}], ini
                for ch in pl['camera_chaves']:
                    t = tempo_da_palavra(palavras, pl.get('fala', ''), ch.get('na_palavra', ''), a, b) if ch.get('na_palavra') else None
                    if t is None:
                        degradar(r, 'revisao', 'SINCRONIA-PALAVRA', f"chave de câmera em '{ch.get('na_palavra')}' não achada: chave ignorada")
                        continue
                    novo = enq({'objeto': ch['objeto'], 'enquadramento': ch.get('enquadramento') or 'objeto'} if ch.get('objeto') else ch.get('enquadramento'), 'geral')
                    tr = t - a
                    # Plano Mestre §4.2: pausa mínima de 0,5 s entre dois movimentos (sem para-e-anda) e duração mínima
                    # pela distância (zoom ≤ ~45%/s, pan ≤ 700 px/s no pico) — não acelera porque a palavra mudou
                    from src.v3 import geometria as _g
                    ini_mov = max(cam[-1]['t'] + (.5 if len(cam) > 1 else 0), tr)
                    d_mov = max(float(ch.get('dur', 1.4)), _g.duracao_minima(atual, novo, wh))
                    if ini_mov - tr > .6:
                        degradar(r, 'revisao', 'SINCRONIA-PALAVRA', f"câmera em '{ch.get('na_palavra')}' começa {ini_mov - tr:.1f}s depois da palavra (movimento anterior)")
                    if ini_mov > dur - .4:            # não sobra tempo nem para começar: a chave cai (nada de tempo fora de ordem)
                        degradar(r, 'revisao', 'MOVIMENTO-SEM-TEMPO', f"chave de câmera em '{ch.get('na_palavra')}' não cabe no plano: ignorada")
                        continue
                    if ini_mov + d_mov > dur + .01:
                        degradar(r, 'revisao', 'MOVIMENTO-SEM-TEMPO', f"movimento em '{ch.get('na_palavra')}' precisa de {d_mov:.1f}s e o plano só tem {max(0, dur - ini_mov):.1f}s")
                    cam += [{'t': round(ini_mov, 2), 'caixa': atual}, {'t': round(min(dur, ini_mov + d_mov), 2), 'caixa': novo}]
                    atual = novo
                if cam[-1]['t'] < dur:
                    cam.append({'t': round(dur, 2), 'caixa': atual})
            avanco = None
            if pl.get('avanco'):                      # área revelada em etapas, cada etapa na palavra da fala
                et = []
                for e in pl['avanco'].get('etapas') or []:
                    t = tempo_da_palavra(palavras, pl.get('fala', ''), e.get('na_palavra', ''), a, b) if e.get('na_palavra') else None
                    if e.get('na_palavra') and t is None:
                        degradar(r, 'revisao', 'SINCRONIA-PALAVRA', f"etapa do avanço em '{e['na_palavra']}' não achada na narração: tempo proporcional")
                        t = a + dur * (len(et) + 1) / (len(pl['avanco']['etapas']) + 1)
                    et.append({'t': round((t if t is not None else a) - a, 2), 'centro': e['centro'], 'raio': float(e['raio']), 'dur': e.get('dur', 1.6)})
                avanco = {'etapas': et, **({'base': pl['avanco']['base']} if pl['avanco'].get('base') else {})}
            # Plano Mestre §4.1: layout explícito. 'cobrir' (a foto cobre o quadro em todo o caminho) quando toda caixa
            # cabe; senão 'integral' (documento/mapa inteiro, com margem intencional). Nunca silencioso.
            from src.v3 import geometria
            documento = pl.get('funcao_documental') in ('DOCUMENTO', 'REPRESENTACAO_HISTORICA', 'REPRESENTAÇÃO HISTÓRICA', 'ESQUEMA') \
                or x.get('tipo') in ('mapa', 'documento', 'gravura')
            layout, pior = geometria.escolher_layout([k['caixa'] for k in cam], wh, pl.get('layout'), documento)
            if layout == 'cobrir' and pior < .9:
                essencial = bool(roi) and min(geometria.visivel(roi, wh, 'cobrir'), 1.0) < .9
                degradar(r, 'revisao', 'ENQUADRAMENTO-CORTADO',
                         f"layout 'cobrir' pedido: só {pior:.0%} do enquadramento cabe no quadro vertical", essencial)
            elif layout == 'cobrir' and geometria.nat(wh) > geometria.SMAX:
                degradar(r, 'revisao', 'RESOLUCAO-BAIXA', f"foto de {wh[0]}×{wh[1]} precisa de {geometria.nat(wh):.1f}× para cobrir o quadro: imagem macia")
            elif layout == 'integral' and not pl.get('layout'):
                baixa = geometria.nat(wh) > geometria.SMAX * 1.12
                degradar(r, 'revisao' if baixa or not documento else 'aceitavel', 'LAYOUT-INTEGRAL',
                         f"foto de {wh[0]}×{wh[1]} sem resolução para cobrir o quadro: inteira, com margem (troque a mídia se puder)" if baixa else
                         f"enquadramento mais largo que o quadro ({pior:.0%} caberia cobrindo): imagem inteira com margem intencional")
            if sc['transicao'] == 'zoom' and len(cam) > 1 and cam[1]['caixa'] != cam[0]['caixa']:
                sc['transicao'] = 'corte'            # zoom de transição sobre zoom de câmera: não empilha (Plano Mestre §4.2)
                degradar(r, 'aceitavel', 'TRANSICAO-ZOOM-EMPILHADA', "transição 'zoom' num plano com câmera em movimento: virou corte")
            sc['params'] = {'img': x.get('arq'), 'wh': wh, 'cam': cam, 'layout': layout,
                            'anot': anot, 'tratamento': pl.get('tratamento') or x.get('tratamento') or 'atual',
                            'selo': {'funcao': pl['funcao_documental'], 'texto': pl.get('selo_texto', '')},
                            'credito': x.get('credito_curto') or x.get('credito', '')[:70]}
            if avanco:
                sc['params']['avanco'] = avanco
            r['camera'] = {'inicial': ini, 'final': fim, 'roi': roi, 'origem_roi': alvo.get('origem') if roi else (rg.get('foco') or {}).get('origem')}
            r['anotacoes'] = len(anot)
        else:
            p = dict(pl.get('params') or {})
            for k, v in list((pl.get('tempos_palavras') or {}).items()):     # tempos internos da composição pela fala
                t = tempo_da_palavra(palavras, pl.get('fala', ''), v, a, b)
                if t is None:
                    degradar(r, 'revisao', 'SINCRONIA-PALAVRA', f"passo '{k}' ('{v}') não encontrado na narração: tempo padrão da composição")
                else:
                    p.setdefault('tempos', {})[k] = round(t - a, 2)
            if isinstance(p.get('tempos'), dict) and pl['composicao'] not in TEMPOS_POR_NOME:
                # V3.1 (ERR-020): as composições V2 leem `tempos` como LISTA (um instante por etapa, em ordem); um dicionário
                # virava NaN e empilhava os textos. Lista ordenada; com contagem diferente das etapas, a composição usa o padrão.
                ts = sorted(p['tempos'].values())
                n = len(p.get('etapas') or []) or None
                if n is None or len(ts) == n:
                    p['tempos'] = ts
                else:
                    p.pop('tempos')
                    degradar(r, 'revisao', 'SINCRONIA-ETAPAS', f"{len(ts)} tempos para {n} etapas: a composição usa o espaçamento padrão")
            sc['params'] = p
        r['tempo'] = [a, b]
        reg.append(r)
        if not r['erros']:
            cenas.append(sc)
    return cenas, reg


def acervo_de_checkpoint(ck: Path) -> dict:
    """Acervo do checkpoint com o necessário para dirigir: arquivo, tamanho real, sha256, crédito, ano, se é IA."""
    import hashlib
    from PIL import Image
    a = json.loads((ck / 'acervo.json').read_text(encoding='utf-8'))
    a = list(a.get('acervo', a) if isinstance(a, dict) else a)
    try:                                       # o roteiro pode ter completado o acervo (fotos extras da etapa de roteiro)
        vr = json.loads((ck / 'roteiro.json').read_text(encoding='utf-8')).get('v') or {}
        ids = {x.get('id') for x in a}
        a += [x for x in vr.get('acervo') or [] if x.get('id') not in ids]
    except Exception:
        pass
    out = {}
    for x in a:
        arq = ck / x['arq'] if x.get('arq') else None
        if not arq or not arq.exists():
            continue
        try:
            wh = list(Image.open(arq).size)
        except Exception:
            continue
        ia = bool(re.search(r'\bai[ -]generated\b|gerad[ao] por ia', f"{x.get('desc', '')} {x.get('titulo', '')}", re.I))
        cred = str(x.get('credito') or '')
        out[x['id']] = {'id': x['id'], 'arq': str(arq), 'wh': wh, 'sha': hashlib.sha256(arq.read_bytes()).hexdigest(),
                        'ano': x.get('ano'), 'mostra': x.get('mostra') or x.get('desc'), 'credito': cred, 'ia': ia,
                        'credito_curto': re.sub(r'\s*,?\s*via Wikimedia Commons', ' · Wikimedia Commons', cred)[:70]}
    return out


def storyboard_por_ia(fatos: str, acervo: dict, falas: list[str], chamar) -> dict:
    """UMA chamada ao modelo (Gemini gratuito ou Claude) com o PROMPT_DIRETOR. Sem nova tentativa: plano inválido é
    recusado por `validar`/`montar`, e o chamador decide (recusar o vídeo, nunca preencher com cartão)."""
    ac = '\n'.join(f"{x['id']} · {str(x.get('mostra') or '')[:90]} · {x.get('ano') or '?'} · {x.get('credito_curto') or ''}"
                   for x in acervo.values() if not x.get('ia'))
    r = chamar(PROMPT_DIRETOR.replace('{fatos}', fatos[:9000]).replace('{acervo}', ac[:6000])
               .replace('{falas}', json.dumps(falas, ensure_ascii=False)))
    if not isinstance(r, dict) or not isinstance(r.get('planos'), list):
        raise ValueError('diretor: resposta sem lista de planos')
    return r


def tempos_por_fala(storyboard: dict, tempos_cenas: list[tuple[float, float]], falas: list[str]) -> dict:
    """Depois da narração: cada plano recebe o intervalo das falas que ele cobre (pela fala exata)."""
    alvo = [_n(f) for f in falas]
    for pl in storyboard['planos']:
        f = _n(pl.get('fala'))
        idx = [i for i, a in enumerate(alvo) if a and (a in f or f in a)]
        if idx:
            pl['tempo_inicio'], pl['tempo_fim'] = tempos_cenas[idx[0]][0], tempos_cenas[idx[-1]][1]
    return storyboard
