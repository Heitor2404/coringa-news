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
MOVIMENTOS = {'revelar', 'aproximar', 'localizar', 'acompanhar', 'explicar', 'comparar', 'fixo'}
CAMPOS = ('evento_id', 'fato_id', 'fonte', 'funcao_narrativa', 'recurso_visual', 'funcao_documental', 'objeto_principal',
          'regiao_de_interesse', 'plano_inicial', 'plano_final', 'acao_visual', 'movimento_camera', 'anotacoes',
          'composicao', 'transicao', 'tempo_inicio', 'tempo_fim', 'criterio_de_validacao')
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
- Não repita a mesma foto em planos seguidos; varie enquadramento e transição.
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
        # objeto muito mais largo que o quadro vertical (um corpo deitado, uma ponte): mostra a largura inteira e deixa a
        # cópia desfocada da foto preencher em cima e embaixo, em vez de cortar uma fatia sem sentido
        x, y, w, h = base
        w2 = min(1.0, w * (1 + m * .4)); h2 = min(1.0, max(h * (1 + m), w2 / asp * .5))
        return [round(min(max(0.0, x + w / 2 - w2 / 2), 1 - w2), 4), round(min(max(0.0, y + h / 2 - h2 / 2), 1 - h2), 4), round(w2, 4), round(h2, 4)]
    return _expandir(base, m, asp)


def camera(mov: str, ini: list, fim: list, dur: float, t0: float = 0.0) -> list[dict]:
    """Enquadramentos-chave em tempo local da cena. Sem intenção ('fixo'): leve respiração de 3% (não é movimento
    narrativo; evita a imagem congelada). Movimento dura o plano inteiro, com assentamento no fim."""
    if mov == 'fixo' or ini == fim:
        x, y, w, h = fim
        return [{'t': 0, 'caixa': fim}, {'t': dur, 'caixa': [x + w * .015, y + h * .015, w * .97, h * .97], 'ease': 'linear'}]
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


def montar(storyboard: dict, acervo: dict, regioes: dict, palavras: list[dict], fatos_ids: set[str] | None = None) -> tuple[list[dict], list[dict]]:
    """→ (cenas V2, registro por plano). Plano inválido NÃO vira cena: entra no registro com o motivo (o chamador bloqueia)."""
    cenas, reg = [], []
    planos = storyboard['planos']
    for i, pl in enumerate(planos):
        r = {'evento_id': pl.get('evento_id'), 'composicao': pl.get('composicao'), 'erros': [], 'limitacoes': []}
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
                r['limitacoes'].append(f"objeto '{pl['objeto_principal']}' não localizado pela visão: câmera usa o foco da foto, sem anotação nele")
            def enq(v, padrao):
                # "detalhe" (do objeto principal) ou {"objeto": "<outro objeto localizado>", "enquadramento": "detalhe"}
                if isinstance(v, dict):
                    o = obs.get(v.get('objeto') or '') or {}
                    if not o.get('caixa'):
                        r['limitacoes'].append(f"enquadramento em '{v.get('objeto')}' sem região: uso o objeto principal")
                    return enquadramento(v.get('enquadramento') or 'objeto', o.get('caixa') or roi, foco, wh)
                return enquadramento(v or padrao, roi, foco, wh)
            loc = pl.get('movimento_camera') == 'localizar'
            ini = enq(pl.get('plano_inicial'), 'detalhe' if loc else 'geral')
            fim = enq(pl.get('plano_final'), 'geral' if loc else 'objeto')
            def pouco(a_, b_):                    # mudança de tamanho < 15% e de centro < 6% da foto
                return abs(a_[2] - b_[2]) / max(a_[2], b_[2]) < .15 and abs((a_[0] + a_[2] / 2) - (b_[0] + b_[2] / 2)) < .06 \
                    and abs((a_[1] + a_[3] / 2) - (b_[1] + b_[3] / 2)) < .06
            if pl.get('movimento_camera') not in ('fixo', None) and pouco(ini, fim):
                # o enquadramento pedido não gera movimento perceptível: aperta até o detalhe; se ainda não der, percorre
                # a foto na horizontal passando pelo assunto (intenção mantida: chegar ao objeto)
                det = enquadramento('detalhe', roi, foco, wh)
                if not pouco(ini, det):
                    fim = det if not loc else fim
                    if loc:
                        ini = det
                    r['limitacoes'].append('movimento pedido era imperceptível: câmera vai até o detalhe do objeto')
                else:
                    fx, fy, fw, fh = fim
                    ref = (roi or foco or fim)
                    lado = -1 if ref[0] + ref[2] / 2 > .5 else 1
                    ini = [round(min(max(0.0, fx + lado * fw * .35), 1 - fw), 4), fy, fw, fh]
                    r['limitacoes'].append('objeto já ocupa o quadro: o movimento vira percurso lateral até ele')
            anot = []
            for an in pl.get('anotacoes') or []:
                t = tempo_da_palavra(palavras, pl.get('fala', ''), an.get('na_palavra', ''), a, b) if an.get('na_palavra') else None
                t0 = (t - a) if t is not None else min(dur * .35, 1.2)
                if an.get('na_palavra') and t is None:
                    r['limitacoes'].append(f"palavra '{an['na_palavra']}' não encontrada na narração alinhada: anotação em {t0:.1f}s")
                o = obs.get(an.get('alvo') or '') or {}
                if an['tipo'] in ('seta', 'trajeto'):
                    o2 = obs.get(an.get('ate') or '') or {}
                    if o.get('ancoravel') and an.get('ate_desvio'):
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
                                     'curva': an.get('curva', .18), 'desenho': an.get('desenho', 1.4)})
                    else:
                        r['limitacoes'].append(f"{an['tipo']} '{an.get('alvo')}' → '{an.get('ate')}' sem as duas regiões localizadas: anotação retirada")
                    continue
                if not o.get('ancoravel'):
                    r['limitacoes'].append(f"anotação em '{an.get('alvo')}' retirada: a visão não localizou o objeto com confiança")
                    continue
                tipo = an['tipo']
                cx_, fx = o['caixa'], fim
                fora = max(0.0, fx[0] - cx_[0]) + max(0.0, cx_[0] + cx_[2] - fx[0] - fx[2]) + max(0.0, fx[1] - cx_[1]) + max(0.0, cx_[1] + cx_[3] - fx[1] - fx[3])
                if tipo in ('circulo', 'contorno') and fora > .15 * (cx_[2] + cx_[3]):
                    tipo = 'ponto'                   # região maior que o quadro final: contorno sairia da tela → marcador no centro
                    r['limitacoes'].append(f"'{an.get('alvo')}' não cabe no quadro final: {an['tipo']} virou marcador com rótulo")
                anot.append({'tipo': tipo, 'caixa': o['caixa'], 't0': round(t0, 2), 'texto': an.get('texto', ''),
                             't1': an.get('t1'), 'lado': an.get('lado')})
            sc['params'] = {'img': x.get('arq'), 'wh': wh, 'cam': camera(pl.get('movimento_camera') or 'fixo', ini, fim, dur),
                            'anot': anot, 'tratamento': pl.get('tratamento') or x.get('tratamento') or 'atual',
                            'selo': {'funcao': pl['funcao_documental'], 'texto': pl.get('selo_texto', '')},
                            'credito': x.get('credito_curto') or x.get('credito', '')[:70]}
            r['camera'] = {'inicial': ini, 'final': fim, 'roi': roi, 'origem_roi': alvo.get('origem') if roi else (rg.get('foco') or {}).get('origem')}
            r['anotacoes'] = len(anot)
        else:
            p = dict(pl.get('params') or {})
            for k, v in list((pl.get('tempos_palavras') or {}).items()):     # tempos internos da composição pela fala
                t = tempo_da_palavra(palavras, pl.get('fala', ''), v, a, b)
                if t is None:
                    r['limitacoes'].append(f"passo '{k}' ('{v}') não encontrado na narração")
                else:
                    p.setdefault('tempos', {})[k] = round(t - a, 2)
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
