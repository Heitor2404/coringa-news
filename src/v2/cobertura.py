"""V2.5 — COBERTURA SEMÂNTICA: o que a fala manda mostrar × o que o plano visual efetivamente representa.

Geometria certa e estados diferentes não bastam (uma seta sem objeto, um mapa sem o lugar, cartões em sequência
"renderizam"). Para cada acontecimento CRÍTICO, antes da narração, registra:
  afirmação narrada · elementos necessários (sujeito, estado inicial/final, o que mostrar) · elementos representados
  (o que a composição escreve/desenha, ou o que a foto do acervo mostra pelo catálogo) · mudança exigida × produzida
  (medida na prévia renderizada) · fonte/justificativa · resultado (aprovado | revisao | bloqueio) e o motivo.

Se a composição escolhida não cobre o acontecimento, tenta UMA alternativa entre as composições capazes do tipo cujos
dados o contrato já tem (sem IA, sem inventar dado). Se nenhuma serve, BLOQUEIO com a limitação — nunca imagem,
relação ou fato inventado. Sem rede, sem custo.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from src.v2 import contrato

PARE = set('para pelo pela pelos pelas como quando onde entre sobre depois antes mais menos muito muita muitos muitas '
           'esse essa isso este esta isto aquele aquela seus suas dele dela eles elas fica ficam está estão sendo foram '
           'cena mostrar mostra esquema imagem foto vídeo video'.split())
PARE3 = set('que dos das uma com por sem nao sao seu sua foi ser tem era num nas nos aos ate the and mas ela ele'.split())
TECNICOS = set('id forma cor tipo lado preso_a img video arq lon lat raio x y w h dx dy escala rot opacidade polar forca n angulo intensidade '
               'casas voltas excentricidade max zero area ordenar destaque virada tempos de_x wh img_wh recorte foco momento2 limpa'.split())
COBERTURA_MIN = .5


def _raizes(t, numeros: bool = False) -> set[str]:
    t = unicodedata.normalize('NFKD', str(t or '').lower())
    t = ''.join(c for c in t if not unicodedata.combining(c))
    r = {w[:5] for w in re.findall(r'[a-z]{3,}', t) if w not in PARE and w not in PARE3}
    if numeros:                                  # números contam (o gráfico/nível mostra o valor que a fala diz)
        r |= {n.replace('.', '').replace(',', '.').rstrip('0').rstrip('.') or '0' for n in re.findall(r'\d[\d.,]*', t)}
    return r


def _textos(x) -> list[str]:
    if isinstance(x, dict):
        return [s for k, v in x.items() if k not in TECNICOS for s in _textos(v)]
    if isinstance(x, list):
        return [s for v in x for s in _textos(v)]
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return [str(x)]
    return [x] if isinstance(x, str) else []


ESCALA = {'mil': 1e3, 'mi': 1e6, 'milhao': 1e6, 'milhoes': 1e6, 'milhões': 1e6, 'bi': 1e9, 'bilhao': 1e9, 'bilhoes': 1e9, 'bilhões': 1e9}


def _nums_dado(x) -> list[float]:
    """Números de um dado ESTRUTURADO: int/float são lidos como número (2.5 é dois e meio, não 25); texto vai pelo leitor PT."""
    if isinstance(x, dict):
        return [n for k, v in x.items() if k not in TECNICOS for n in _nums_dado(v)]
    if isinstance(x, list):
        return [n for v in x for n in _nums_dado(v)]
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return [float(x)]
    return [n for n, _ in valores(x)] if isinstance(x, str) else []


def necessarios(ac: dict) -> set[str]:
    return _raizes(' '.join(str(ac.get(k) or '') for k in ('sujeito', 'estado_inicial', 'estado_final')))


DADOS = {'grafico.barras', 'grafico.temporal', 'comparacao.grandezas', 'numero.animado', 'proporcao', 'linha_tempo.historica',
         'mecanismo.nivel', 'evento.impacto', 'astronomia.orbita'}
MAPAS = {'mapa.rota', 'mapa.localizacao', 'mapa.territorio'}
RELACAO = re.compile(r'\b(atrai|atrac|empur|repel|repul|puxa)')          # sobre raízes de 5 letras ("atravessa" ≠ atração)
COMPARA = {'comparacao.grandezas', 'grafico.barras'}
MIDIA = {'video.documental', 'foto.documental', 'foto.historica', 'lower_third', 'foto.sequencia'}
OK, FALHA, NA, NV = 'ok', 'falha', 'nao_se_aplica', 'nao_verificavel'


def _rotulos(params: dict) -> list[str]:
    """Rótulos que a tela ESCREVE (itens, pontos, eventos, objetos do esquema…), sem números e campos técnicos."""
    out = []
    def rec(x, k=''):
        if isinstance(x, dict):
            for kk, vv in x.items():
                if kk in ('rotulo', 'nome', 'texto', 'titulo', 'pais', 'autor', 'centro') and isinstance(vv, str):
                    out.append(vv)
                elif kk not in TECNICOS:
                    rec(vv, kk)
        elif isinstance(x, list):
            for vv in x:
                rec(vv, k)
        elif isinstance(x, str) and k in ('etapas', 'nos', 'eventos', 'itens', 'forcas'):
            out.append(x)                    # etapa/nó escrito como texto simples também é rótulo na tela
    rec({k: v for k, v in (params or {}).items() if k not in ('titulo', 'kicker', 'fonte', 'conclusao', 'nota')})
    out += [v for k, v in (params or {}).items() if k in ('pais', 'autor', 'centro') and isinstance(v, str)]
    return [r for r in out if _raizes(r)]


def _numeros(t) -> set[str]:
    return {n.replace('.', '').replace(',', '.').rstrip('0').rstrip('.') or '0' for n in re.findall(r'\d[\d.,]*', str(t or ''))}


def _numeros_params(params) -> set[str]:
    return {x for s in _textos(params or {}) for x in _numeros(s)}


_UN = {'zero': 0, 'um': 1, 'uma': 1, 'dois': 2, 'duas': 2, 'tres': 3, 'quatro': 4, 'cinco': 5, 'seis': 6, 'sete': 7, 'oito': 8,
       'nove': 9, 'dez': 10, 'onze': 11, 'doze': 12, 'treze': 13, 'quatorze': 14, 'catorze': 14, 'quinze': 15, 'dezesseis': 16,
       'dezessete': 17, 'dezoito': 18, 'dezenove': 19, 'vinte': 20, 'trinta': 30, 'quarenta': 40, 'cinquenta': 50, 'sessenta': 60,
       'setenta': 70, 'oitenta': 80, 'noventa': 90, 'cem': 100, 'cento': 100, 'duzentos': 200, 'duzentas': 200, 'trezentos': 300,
       'trezentas': 300, 'quatrocentos': 400, 'quatrocentas': 400, 'quinhentos': 500, 'quinhentas': 500, 'seiscentos': 600,
       'seiscentas': 600, 'setecentos': 700, 'setecentas': 700, 'oitocentos': 800, 'oitocentas': 800, 'novecentos': 900, 'novecentas': 900}
_MULT = {'mil': 1e3, 'milhao': 1e6, 'milhoes': 1e6, 'bilhao': 1e9, 'bilhoes': 1e9}
APROX = re.compile(r'\b(mais de|menos de|cerca de|quase|aproximadamente|perto de|em torno de|uns|umas|mais ou menos|ate)\s*$')


def valores(t: str) -> list[tuple[float, bool]]:
    """Números de uma fala — com dígitos ou POR EXTENSO ("mil e quinhentas") — e se a fala os aproxima ("mais de")."""
    t = unicodedata.normalize('NFKD', str(t or '').lower())
    t = ''.join(c for c in t if not unicodedata.combining(c))
    out, usados = [], []
    for m in re.finditer(r'\d[\d.]*(?:,\d+)?(?:\s*\b(milhoes|milhao|bilhoes|bilhao|mil)\b)?', t):
        usados.append((m.start(), m.end()))
        n = float(m.group(0).split()[0].replace('.', '').replace(',', '.'))
        if m.group(1):
            n *= _MULT[m.group(1)]
        out.append((n, bool(APROX.search(t[:m.start()]))))
    toks = [m for m in re.finditer(r'[a-z]+', t) if not any(a <= m.start() < b for a, b in usados)]
    i = 0
    while i < len(toks):
        w = toks[i].group(0)
        if w in _UN or w in _MULT:
            ini, total, parte, ult = toks[i].start(), 0.0, 0.0, float('inf')
            while i < len(toks) and (toks[i].group(0) in _UN or toks[i].group(0) in _MULT or toks[i].group(0) == 'e'):
                w = toks[i].group(0)
                if w in _UN:
                    if _UN[w] >= ult:                 # "três e quarenta": a ordem cresce → é outro número (23h40)
                        break
                    parte += _UN[w]; ult = _UN[w]
                elif w in _MULT:
                    total += (parte or 1) * _MULT[w]; parte = 0; ult = float('inf')
                i += 1
            if i < len(toks) and toks[i].group(0) in _UN and (total + parte):
                out.append((total + parte, bool(APROX.search(t[:ini]))))
                continue
            n = total + parte
            if n and not (n == 1 and total == 0):     # "um"/"uma" sozinho é artigo, não número
                out.append((n, bool(APROX.search(t[:ini]))))
            continue
        i += 1
    return out


def _confere(dito: tuple[float, bool], dados: list[float]) -> bool:
    n, aprox = dito
    return any(abs(n - d) < 1e-9 or (aprox and d and abs(n - d) / abs(d) <= .1) for d in dados)


def _nomes_proprios(t: str) -> set[str]:
    return {_raizes(w).pop() for w in re.findall(r'(?<!^)(?<![.!?] )\b[A-ZÁÉÍÓÚÂÊÔ][a-záéíóúâêôãõç]{2,}', str(t or '').strip()) if _raizes(w)}


def avaliar_evento(ac: dict, fala: str, comp: str | None, params: dict, foto: dict | None, previa_ev: dict | None, assunto: str = '',
                   linhas: list | None = None) -> dict:
    """Contrato ESTRUTURADO de correspondência (V2.5). Cada verificação é ok | falha | nao_verificavel | nao_se_aplica.
    Identidade (sujeito), tempo e dados são NECESSÁRIOS: uma falha bloqueia, nenhuma outra compensa. O que não dá para
    provar sem olhar (ação numa foto, relação num esquema) vai para revisão humana — nunca para aprovação automática."""
    modo = (ac.get('representacao') or {}).get('modo')
    fala_l = re.sub(r'\*', '', fala or '')
    dito = ' '.join([fala_l, str(ac.get('mostrar') or ''), str(ac.get('sujeito') or '')])
    sujeito = _raizes(ac.get('sujeito'))
    rot = _rotulos(params)
    rot_r = [_raizes(r) for r in rot]
    ch = {k: NA for k in ('sujeito', 'acao', 'estado', 'tempo', 'lugar', 'dados', 'relacao', 'funcao')}
    det = {}
    if modo == 'editorial':
        return _fim(ac, fala_l, comp, modo, ch, 'aprovado', 'cena editorial: resume o que já foi mostrado', det)
    if comp in contrato.TEXTUAIS and not contrato.comp_aceita(ac, comp, params):
        ch['acao'] = FALHA
        return _fim(ac, fala_l, comp, modo, ch, 'bloqueio', 'mecanismo crítico só escrito na tela', det)
    eh_foto = modo in ('foto_direta', 'foto_declarada', 'foto_ilustrativa', 'contexto', 'foto_contexto') or comp == 'foto'
    if eh_foto and foto:
        vis = _raizes(' '.join(str(foto.get(k) or '') for k in ('mostra', 'titulo', 'legenda', 'credito')))
        pl = ac.get('plano_visual') if isinstance(ac.get('plano_visual'), dict) else {}
        if modo == 'foto_ilustrativa' and pl.get('foto') == foto.get('id'):
            vis |= _raizes(pl.get('parte'))          # o que o plano visual APROVADO diz que a ilustração mostra
        pedido = _raizes(ac.get('mostrar'))
        nomes_pedido = _nomes_proprios(str(ac.get('mostrar') or '')) | _nomes_proprios(str(ac.get('acao') or ''))
        if sujeito & vis:
            ch['sujeito'] = OK
        elif len(pedido & vis) >= 2 and nomes_pedido & vis:
            ch['sujeito'] = OK; det['sujeito'] = 'identidade pela descrição do que a cena pede (nome próprio + contexto no catálogo)'
        elif modo == 'contexto' and _raizes(assunto) & vis:
            ch['sujeito'] = OK; det['sujeito'] = 'foto do assunto central (contexto), não do sujeito do instante'
        else:
            ch['sujeito'] = FALHA; det['sujeito'] = f"a foto mostra \"{str(foto.get('mostra') or '')[:60]}\", não {ac.get('sujeito')}"
        ano_ev = next((int(a) for a in re.findall(r'\b(1[5-9]\d\d|20\d\d)\b', ' '.join(str(ac.get(k) or '') for k in ('quando',)) + ' ' + str((ac.get('dados') or {}).get('ano') or ''))), None)
        ano_f = foto.get('ano')
        if ano_ev and ano_f:
            ok_t = abs(int(ano_f) - ano_ev) <= 3
            ch['tempo'] = OK if ok_t or modo in ('contexto', 'foto_ilustrativa') else FALHA
            if not ok_t:
                det['tempo'] = f'foto de {ano_f}, fato de {ano_ev}' + (' (declarada como contexto)' if ch['tempo'] == OK else '')
        elif modo == 'foto_direta':
            ch['tempo'] = NV
        est = _raizes(ac.get('estado_final')) - sujeito
        ch['acao'] = OK if modo == 'foto_direta' and (not est or est & vis) else NV
        ch['funcao'] = 'prova' if modo == 'foto_direta' else 'contexto' if modo in ('contexto', 'foto_contexto', 'foto_declarada') else 'ilustracao'
    elif comp in MAPAS:
        ditos = _raizes(dito)
        hit = [r for r in rot_r if r & ditos]
        # nome de lugar tem sinônimos e partes (praça × catedral × cidade): sem prova por palavras → revisão, não bloqueio
        # (coordenada/país inválido já bloqueia no preparo)
        ch['lugar'] = OK if rot_r and len(hit) == len(rot_r) else NV
        if ch['lugar'] != OK:
            det['lugar'] = f"na tela: {', '.join(rot)[:80]} · ditos: {len(hit)}/{len(rot_r)}"
    elif comp == 'citacao':
        autor = _raizes((params or {}).get('autor'))
        ch['sujeito'] = OK if autor and (autor & (sujeito | _raizes(dito))) else FALHA
        from src.v2 import prevalidacao
        ch['dados'] = OK if prevalidacao.rastrear_texto(str((params or {}).get('texto') or ''), linhas or []) else NV
        ch['funcao'] = 'documento'
    elif comp in MIDIA:
        ch['sujeito'] = NV; det['sujeito'] = 'mídia sem catálogo que descreva o conteúdo: conferir assistindo'
        ch['funcao'] = 'contexto'
    elif comp in DADOS or comp == 'fonte.evidencia':
        # a TELA não pode afirmar número que nem a fala nem a pesquisa sustentam (a fala pode citar mais do que a tela)
        ditos_v = valores(fala_l)
        fatos_v = [x for ln in (linhas or []) for x, _ in valores(ln.get('texto'))]
        dados_v = [x for k_, s_ in (params or {}).items() if k_ not in ('fonte', 'nota', 'titulo', 'kicker', 'conclusao', 'casas', 'max', 'zero', 'unidade')
                   for x in _nums_dado({k_: s_})]
        esc = ESCALA.get(str((params or {}).get('unidade') or '').strip().lower().rstrip('.'), 1.0)   # "2,5" com unidade "bi"
        na_pesquisa = lambda d: any(abs(d - f) < 1e-9 or abs(d * esc - f) <= 1e-9 * max(1.0, abs(f)) for f in fatos_v)
        sobra = {f'{d:g}' for d in dados_v if d != 0 and not any(_confere(x, [d]) or _confere(x, [d * esc]) for x in ditos_v) and not na_pesquisa(d)}
        nf = {f'{d:g}' for d in dados_v if any(_confere(x, [d]) for x in ditos_v)}
        ditos = _raizes(dito)
        hit = [r for r in rot_r if r & ditos]
        if sobra:
            ch['dados'] = FALHA; det['dados'] = f"número na tela sem apoio na fala nem na pesquisa: {', '.join(sorted(sobra))}"
        elif rot_r and not hit and not nf:
            ch['dados'] = FALHA; det['dados'] = f"nada do que a tela rotula é dito: {', '.join(rot)[:80]}"
        elif rot_r and not hit:                  # o VALOR confere; o rótulo é paráfrase: um humano confere o texto
            ch['dados'] = NV; det['dados'] = f"valor confere, rótulo não é dito literalmente: {', '.join(rot)[:60]}"
        if ch['dados'] == NA:
            estranhos = _nomes_proprios(fala_l) - set().union(*rot_r, sujeito, _raizes(ac.get('mostrar'))) if rot_r and comp in COMPARA else set()
            ch['dados'] = NV if (rot_r and len(hit) < len(rot_r)) or estranhos else OK
            if ch['dados'] == NV:
                det['dados'] = f"rótulos ditos {len(hit)}/{len(rot_r)}" + (f"; a fala cita {', '.join(sorted(estranhos))} que não está nos dados" if estranhos else '')
        if comp == 'fonte.evidencia':
            ch['funcao'] = 'documento'
    else:                                                    # esquema / demonstração
        nec = necessarios(ac)
        desenhado = set().union(*rot_r) if rot_r else set()
        titulo = _raizes(' '.join(str((params or {}).get(k) or '') for k in ('titulo', 'kicker')))
        # o título IDENTIFICA o sujeito; o DESENHO precisa ser do acontecimento (rótulo do que é desenhado ∩ fala/estados)
        ident = not sujeito or bool(sujeito & (desenhado | titulo)) or bool(nec & desenhado)
        coerente = bool(desenhado & (nec | _raizes(fala_l))) if desenhado else False
        ch['sujeito'] = OK if ident and coerente else FALHA
        if ch['sujeito'] == FALHA:
            det['sujeito'] = (f"o desenho rotula {', '.join(rot)[:60]}, nada disso é dito ou é estado do acontecimento" if ident
                              else f"a tela não identifica {ac.get('sujeito')} (rotula {', '.join(rot)[:50]})")
        muda = bool(ac.get('estado_inicial')) and _raizes(ac.get('estado_inicial')) != _raizes(ac.get('estado_final'))
        prod = None
        if previa_ev and previa_ev.get('medidas'):
            m = previa_ev['medidas']
            prod = max(m.get('dif_ini_fim', 0), m.get('dif_ini_meio', 0)) >= 2 or m.get('frac_mudou', 0) >= .004
        ch['estado'] = (OK if prod else FALHA if prod is False else NV) if muda and contrato.demonstra(comp) else NA
        if RELACAO.search(_raizes_txt(fala_l)):
            esq = (params or {}).get('esquema') or {}
            tem = any(e.get('relacoes') for e in esq.get('estados') or [] if isinstance(e, dict)) or bool((params or {}).get('forcas'))
            ch['relacao'] = OK if tem else NV
        ch['funcao'] = 'ilustracao'
    falhas = [k for k, x in ch.items() if x == FALHA]
    if falhas:
        return _fim(ac, fala_l, comp, modo, ch, 'bloqueio', 'falha necessária: ' + '; '.join(det.get(k, k) for k in falhas), det)
    if not contrato.critico(ac):                 # apoio: só falha necessária barra; o resto fica registrado
        return _fim(ac, fala_l, comp, modo, ch, 'aprovado', 'apoio: nenhuma falha necessária' + (' (há itens não verificáveis)' if NV in ch.values() else ''), det)
    if NV in ch.values() or ch['funcao'] in ('contexto', 'ilustracao') and eh_foto:
        why = [det.get(k, k) for k, x in ch.items() if x == NV] + (['imagem é contexto/ilustração, não prova'] if eh_foto and ch['funcao'] != 'prova' else [])
        return _fim(ac, fala_l, comp, modo, ch, 'revisao', 'não comprovável sem olhar: ' + '; '.join(why), det)
    return _fim(ac, fala_l, comp, modo, ch, 'aprovado', 'todas as verificações necessárias conferem', det)


def _raizes_txt(t):
    return ' '.join(sorted(_raizes(t)))


def _fim(ac, fala, comp, modo, ch, res, motivo, det):
    return {'evento': ac.get('id'), 'tipo': ac.get('tipo'), 'afirmacao': fala[:160], 'comp': comp, 'modo': modo, 'verificacoes': ch,
            'detalhes': det, 'fonte': ac.get('fonte'), 'resultado': res, 'motivo': motivo,
            'cobertura': sum(1 for x in ch.values() if x == OK) / max(1, sum(1 for x in ch.values() if x != NA))}


def _alternativa(ac: dict, atual: str | None) -> str | None:
    """UMA alternativa entre as composições capazes do tipo cujos dados o contrato JÁ tem (ordem do contrato)."""
    from src.v2 import capacidades
    p = dict(ac.get('dados') or {})
    for comp, reqs in contrato.TIPOS.get(ac.get('tipo'), {}).get('comps', {}).items():
        if comp == atual or comp in contrato.GENERICAS or not contrato.comp_aceita(ac, comp, p):
            continue
        if all(capacidades._tem(r, p, '') for r in reqs):
            return comp
    return None


def avaliar(v: dict, previa_rel: dict | None = None, pasta=None) -> dict:
    """Cobertura de todos os acontecimentos críticos do roteiro já preparado. Muda `representacao` só quando troca para
    UMA alternativa que cobre melhor; devolve {eventos, bloqueios, revisoes} no formato do preparo."""
    from src.v2 import preparo
    linhas = preparo.pesquisa(v)
    por_id = {x['id']: x for x in v.get('acervo') or []}
    pv = {e['evento']: e for e in (previa_rel or {}).get('eventos') or []}
    rel, vistos = {'eventos': [], 'bloqueios': [], 'revisoes': [], 'alternativas': []}, set()
    for i, c in enumerate(v.get('cenas') or []):
        ac = c.get('acontecimento') if isinstance(c.get('acontecimento'), dict) else None
        rep0 = (ac or {}).get('representacao') or {}
        # críticos sempre; de apoio quando a tela afirma DADOS (número, mapa, gráfico): afirmação factual também se confere
        if not ac or not ac.get('id') or ac['id'] in vistos or not (contrato.critico(ac) or rep0.get('modo') == 'composicao'):
            continue
        vistos.add(ac['id'])
        idx = [k for k, x in enumerate(v['cenas']) if (x.get('acontecimento') or {}).get('id') == ac['id']]
        fala = ' '.join(v['cenas'][k].get('fala') or '' for k in idx)
        rep = ac.get('representacao') or {}
        comp = rep.get('comp') if rep.get('modo') == 'composicao' else ('foto' if rep.get('foto') else None)
        foto = por_id.get(rep.get('foto') or c.get('foto'))
        assunto = ' '.join(str(v.get(k) or '') for k in ('titulo', 'pergunta'))
        usa_foto = comp == 'foto' or rep.get('modo', '').startswith('foto') or rep.get('modo') == 'contexto'
        tela = contrato.params_tela(ac, comp) if comp and comp != 'foto' else ac.get('dados') or {}
        r = avaliar_evento(ac, fala, comp, tela, foto if usa_foto else None, pv.get(ac['id']), assunto, linhas)
        if r['resultado'] == 'bloqueio' and rep.get('modo') == 'composicao':
            alt = _alternativa(ac, comp)
            if alt:                                  # a troca SÓ vale depois de renderizada e validada de novo
                from src.v2 import previa as _pv
                try:
                    rr = _pv.renderizar(alt, dict(ac.get('dados') or {}), Path(pasta or '/tmp/_cobertura'), f"{ac['id']}_alt")
                    rr['params'] = ac.get('dados') or {}
                    prob = _pv.problemas(alt, rr)
                except Exception as e:
                    rr, prob = None, [f'render da alternativa falhou: {str(e)[:80]}']
                r2 = avaliar_evento(ac, fala, alt, ac.get('dados') or {}, None, {'medidas': (rr or {}).get('medidas')}, assunto, linhas)
                if prob:
                    r2 = {**r2, 'resultado': 'bloqueio', 'motivo': 'alternativa renderizada com defeito: ' + '; '.join(prob)}
                rel['alternativas'].append({'evento': ac['id'], 'de': comp, 'para': alt, 'resultado': r2['resultado']})
                if r2['resultado'] != 'bloqueio':
                    for k in idx:
                        v['cenas'][k]['acontecimento']['representacao'] = {'modo': 'composicao', 'comp': alt}
                    r = {**r2, 'motivo': f"alternativa: {comp} → {alt} ({r2['motivo']})"}
        rel['eventos'].append(r)
        if r['resultado'] == 'bloqueio':
            rel['bloqueios'].append({'evento': ac['id'], 'cenas': idx, 'tipo': ac['tipo'], 'mostrar': ac.get('mostrar'),
                                     'faltam': [f"cobertura: {r['motivo']}"]})
        elif r['resultado'] == 'revisao':
            rel['revisoes'].append({'evento': ac['id'], 'cenas': idx, 'problema': f"cobertura: {r['motivo']}"[:200], 'evidencia': json.dumps(r['verificacoes'])})
    return rel


def resumo(rel: dict) -> str:
    return f"cobertura: {len(rel['eventos'])} crítico(s) · {len(rel['bloqueios'])} bloqueio(s) · {len(rel['revisoes'])} revisão(ões)" + ''.join(
        f"\n  {e['evento']} {e['comp'] or e['modo'] or '-'}: {e['resultado']} — {e['motivo'][:150]}" for e in rel['eventos'])
