"""PREPARO DO ROTEIRO (correção do piloto Ever Given) — validação OBRIGATÓRIA dos acontecimentos ANTES da narração.

O piloto mostrou o roteirista declarando o tipo certo de acontecimento sem os dados no formato que a composição exige,
e o problema só aparecia depois de 11 minutos de produção. Aqui, logo depois do roteiro e do casamento com o acervo
(sem nenhuma chamada de IA nova), cada acontecimento sai com:

  - id estável, o MESMO em todos os planos em que a fala foi dividida (`partes` = quantos planos);
  - tipo semântico revisto (com `tipo_original` e o motivo da reclassificação);
  - dados no formato da composição, resolvidos só com o que já foi verificado (pesquisa com fonte, catálogo do acervo,
    Natural Earth local) — nada inventado;
  - fonte rastreável (o número aparece numa linha da pesquisa atribuída àquela fonte);
  - `representacao`: composicao | foto_direta | foto_declarada | editorial | foto_contexto | bloqueio.

Foto/vídeo REAL representa acontecimento crítico quando mostra diretamente o que é narrado (assunto + estado ou ação
descritos no catálogo do acervo + época compatível). Diagrama sem relação com o que foi declarado e imagem com texto em
escrita incompatível (árabe, chinês…) são recusados; quando há alternativa válida no acervo, ela entra no lugar.

Acontecimento crítico que continua sem representação → BLOQUEIO antecipado com a lista exata do que falta.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from src.v2 import contrato


def _n(s) -> str:
    s = unicodedata.normalize('NFKD', str(s or '').lower())
    return ''.join(c for c in s if not unicodedata.combining(c))


def _palavras(s) -> set[str]:
    return {w for w in re.findall(r'[a-z0-9]+', _n(s)) if len(w) >= 4 and w not in VAZIAS}


VAZIAS = {'para', 'pela', 'pelo', 'como', 'mais', 'muito', 'esta', 'este', 'essa', 'esse', 'uma', 'umas', 'com', 'sem', 'que',
          'imagem', 'foto', 'fotografia', 'vista', 'visto', 'mostrando', 'mostra', 'cima', 'seus', 'suas', 'dele', 'dela',
          'ainda', 'entre', 'sobre', 'apos', 'antes', 'depois', 'onde', 'quando', 'tipico', 'tecnico', 'navio', 'canal'}

# estados/ações VISÍVEIS (a foto mostra o fato quando o catálogo descreve o mesmo estado que a narração)
ESTADOS = {
    'preso': ('encalh', 'atravess', 'travess', 'ental', 'preso', 'presa', 'bloque', 'travou', 'travad', 'imobiliz', 'margens opostas'),
    'liberado': ('liberad', 'liberto', 'libert', 'desencalh', 'reflutu', 'flutuando livre', 'solto', 'desobstru', 'destrav'),
    'espera': ('aguard', 'esperav', 'espera ', 'na fila', 'parados', 'engarraf', 'acumul'),
    'navegando': ('naveg', 'mar aberto', 'em rota', 'zarp'),
    'porto': ('porto', 'atracad', 'cais', 'guindaste'),
    'resgate': ('rebocad', 'draga', 'escavad', 'escava'),
}
FORCA = re.compile(r'\b(vent|corrente|onda|mare|empurr|arrast|forca|tempestade|rajada)')
ESCRITA_INCOMPATIVEL = re.compile(r'\b(arabe|chines|japones|coreano|russo|cirilic|hebraico|grego|hindi|tailandes|persa|farsi)')
COM_TEXTO = re.compile(r'\b(texto|textos|legenda|legendas|rotulo|rotulos|inscric|escrit)')
DESENHO = ('diagrama', 'mapa', 'infografico', 'grafico', 'esquema', 'ilustracao')
# tipos cuja essência uma foto real pode mostrar; os outros (abstratos/quantitativos) precisam da composição
FOTO_PODE = {'impacto', 'deslocamento', 'movimento', 'mecanismo', 'transformacao', 'processo', 'evento_historico', 'localizacao',
             'pessoa', 'lugar', 'ambiente', 'documento', 'territorio'}
EDITORIAL = {'revelacao': 'revelacao.surpresa', 'gancho': 'abertura.pergunta', 'fechamento': 'encerramento.editorial'}
MOEDA = [(r'US\$|d[oó]lar', 'USD'), (r'R\$|reais|real\b', 'BRL'), (r'€|euro', 'EUR'), (r'£|libra', 'GBP')]
ESCALA = {'mil': 1e3, 'milhao': 1e6, 'milhoes': 1e6, 'bilhao': 1e9, 'bilhoes': 1e9, 'trilhao': 1e12, 'trilhoes': 1e12}


# ───────────────────────── números e fontes ─────────────────────────
def numeros(txt) -> list[float]:
    """Números escritos com algarismos: 20.124 · 9,6 · 369 · 80%. Horários (15h05, 15:05) não contam."""
    t = re.sub(r'\b\d{1,2}[h:]\d{2}\b', ' ', str(txt or ''))
    out = []
    for m in re.finditer(r'(?<![\w.,])(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d+))?', t):
        inteiro = m.group(1).replace('.', '')
        out.append(float(inteiro + ('.' + m.group(2) if m.group(2) else '')))
    return out


def dinheiro(s) -> dict | None:
    """'US$ 916 milhões' → {valor: 916, unidade: 'milhões', moeda: 'USD'}. Sem moeda reconhecível → None."""
    s = str(s or '')
    moeda = next((iso for pad, iso in MOEDA if re.search(pad, s, re.I)), None)
    ns = numeros(s)
    if not moeda or not ns:
        return None
    esc = next((w for w in re.findall(r'[a-zçõã]+', _n(s)) if w in ESCALA), '')
    unidade = {'mil': 'mil', 'milhao': 'milhão', 'milhoes': 'milhões', 'bilhao': 'bilhão', 'bilhoes': 'bilhões'}.get(esc, '')
    return {'valor': ns[0], 'unidade': unidade, 'moeda': moeda}


def pesquisa(v: dict) -> list[dict]:
    """Linhas de fato da pesquisa (v['fatos']): '- texto. [tag] (Fonte)' → {texto, fonte, numeros}."""
    out = []
    for ln in str(v.get('fatos') or '').splitlines():
        ln = ln.rstrip()
        if not re.match(r'\s*-\s', ln) or not ln.endswith(')'):
            continue
        prof, i = 0, len(ln) - 1                 # último grupo entre parênteses BALANCEADO: "(Wikipedia (inglês))"
        while i >= 0:
            prof += {')': 1, '(': -1}.get(ln[i], 0)
            if prof == 0:
                break
            i -= 1
        if i <= 0:
            continue
        texto = re.sub(r'^\s*-\s*(?:★\s*)?', '', ln[:i]).strip()
        out.append({'texto': texto, 'fonte': ln[i + 1:-1].strip(), 'numeros': numeros(texto)})
    return out


def _mesma_fonte(a, b) -> bool:
    a, b = _n(a), _n(b)
    return bool(a and b) and (a in b or b in a)


def rastrear(valor: float, fonte_declarada: str | None, linhas: list[dict]) -> dict | None:
    """A linha da pesquisa que contém o número (preferindo a da fonte declarada). None = sem fonte rastreável."""
    cand = [ln for ln in linhas if any(abs(x - valor) < 1e-6 for x in ln['numeros'])]
    if not cand:
        return None
    melhor = next((ln for ln in cand if fonte_declarada and _mesma_fonte(ln['fonte'], fonte_declarada)), cand[0])
    return {'fonte': melhor['fonte'], 'trecho': melhor['texto'][:200]}


# ───────────────────────── imagens do acervo ─────────────────────────
def _grupos(txt) -> set[str]:
    t = ' ' + _n(txt) + ' '
    return {g for g, chaves in ESTADOS.items() if any(c in t for c in chaves)}


def _ano(s) -> int | None:
    m = re.search(r'\b(1[5-9]\d\d|20\d\d)\b', str(s or ''))
    return int(m.group(1)) if m else None


def avaliar_imagem(x: dict, ac: dict, cena: dict, ano_evento: int | None) -> dict:
    """Compatibilidade e força de representação de um item do acervo para o acontecimento (só o catálogo, sem IA).
    forca: 3 mostra o fato (assunto + estado/ação narrados + época) · 2 é o que o roteiro pediu · 1 contexto do assunto ·
    0,5 sem o assunto. Incompatível: texto em escrita que o público não lê; diagrama/mapa sem relação com o pedido."""
    mostra = f"{x.get('mostra', '')} {x.get('titulo', '')}"
    tipo = _n(x.get('tipo_img') or 'foto')
    desenho = any(d in tipo for d in DESENHO)
    if ESCRITA_INCOMPATIVEL.search(_n(x.get('mostra'))) and (COM_TEXTO.search(_n(x.get('mostra'))) or desenho):
        return {'compativel': False, 'forca': 0, 'motivos': [f"texto em escrita incompatível com o vídeo em português ({x.get('mostra', '')[:70]})"]}
    sujeito = _palavras(ac.get('sujeito') or '') - {'casco', 'frota', 'equipes', 'trecho', 'receita'}
    pedido = f"{ac.get('mostrar', '')} {cena.get('mostrar', '')}"
    comum = (_palavras(pedido) & _palavras(mostra)) - sujeito - MIDIA     # o nome do assunto e o tipo de imagem não provam nada
    if desenho and len(comum) < 2:
        return {'compativel': False, 'forca': 0, 'motivos': [f"{tipo} sem relação com o que a cena pede (\"{pedido.strip()[:60]}\")"]}
    if x.get('generica') or x.get('ia'):
        return {'compativel': True, 'forca': 1, 'motivos': ['imagem genérica: só contexto']}
    if sujeito and not sujeito & _palavras(mostra):
        return {'compativel': True, 'forca': .5, 'motivos': ['sem o assunto do acontecimento']}
    ano_img = x.get('ano') if isinstance(x.get('ano'), int) else _ano(x.get('ano'))
    outra_epoca = bool(ano_evento and ano_img and abs(ano_img - ano_evento) > 1)
    evento = ' '.join(str(ac.get(k) or '') for k in ('acao', 'estado_final', 'mostrar')) + ' ' + str(cena.get('mostrar') or '') + ' ' + ' '.join(cena.get('_falas') or [])
    estado = _grupos(ac.get('estado_final')) or _grupos(evento)
    vistos = _grupos(mostra)
    if not desenho and not outra_epoca and estado & vistos:
        return {'compativel': True, 'forca': 3, 'motivos': [f"mostra o fato: {', '.join(sorted(estado & vistos))} ({x.get('mostra', '')[:80]})"]
                + (['ano da imagem não informado no acervo'] if not ano_img else [])}
    epoca = [f'foto de {ano_img}, acontecimento de {ano_evento}'] if outra_epoca else []
    if len(comum) >= 2:
        return {'compativel': True, 'forca': 2, 'motivos': [f"é o que o roteiro pediu ({', '.join(sorted(comum))})"] + epoca}
    return {'compativel': True, 'forca': 1, 'motivos': ['contexto do assunto'] + epoca}


MIDIA = {'satelite', 'aerea', 'aproximada', 'lateral', 'detalhe', 'fotografia', 'retrato', 'close'}


# ───────────────────────── reclassificação ─────────────────────────
def _contagens(dados: dict) -> dict:
    return {k: v for k, v in (dados or {}).items() if isinstance(v, (int, float)) or (isinstance(v, str) and re.fullmatch(r'\s*[\d.,]+\s*', v))}


def reclassificar(ac: dict, cena: dict) -> tuple[str, str | None]:
    tipo, dados = ac.get('tipo'), ac.get('dados') or {}
    texto = _n(' '.join(str(ac.get(k) or '') for k in ('acao', 'mostrar', 'estado_final')) + ' ' + str(ac.get('_quem') or ''))
    lugares = [dados.get(k) for k in ('origem', 'destino') if dados.get(k)] + list(dados.get('pontos') or [])
    if tipo == 'movimento' and dados.get('origem') and dados.get('destino'):
        return 'deslocamento', 'movimento entre dois lugares é deslocamento (rota)'
    if tipo == 'deslocamento' and len(lugares) < 2 and FORCA.search(texto):
        return 'movimento', 'deslocamento local causado por força (vento/corrente), não rota geográfica'
    if tipo == 'citacao' and not (dados.get('texto') and dados.get('autor')) and any(dinheiro(v) for v in dados.values()):
        return 'numero', 'valor em dinheiro sem texto/autor: é um número (cobrança/valor), não citação'
    cont = _contagens(dados)
    if tipo in ('processo', 'mecanismo', 'transformacao') and cont and len(cont) == len(dados) and not any(k in dados for k in ('etapas', 'nos', 'forcas')):
        return 'numero', 'dados são só contagens: a fala enumera quantidades, não descreve etapas'
    if tipo == 'evolucao_temporal' and not (isinstance(dados.get('serie'), list) and len(dados['serie']) >= 4):
        if cena.get('tipo') in EDITORIAL:
            return 'evolucao_temporal', None          # fica: a cena editorial (revelação) mostra a afirmação
        if len(cont) == 1:
            return 'numero', 'um único valor não é série temporal'
    return tipo, None


# ───────────────────────── dados no formato da composição ─────────────────────────
def _dados_numero(ac: dict, linhas: list[dict], v: dict) -> tuple[dict | None, list[str]]:
    dados = ac.get('dados') or {}
    faltam = []
    moneys = [(k, dinheiro(x)) for k, x in dados.items() if dinheiro(x)]
    cont = _contagens(dados)
    if moneys:
        chave, m = moneys[0]
        valor = {'valor': m['valor'], 'unidade': m['unidade'], 'moeda': m['moeda']}
        resto = [f"{k.replace('_', ' ')}: {x}" for k, x in dados.items() if k != chave]
        rot = str(ac.get('acao') or ac.get('mostrar') or chave).replace('_', ' ')
        if re.search(r'exig|cobr|indeniz|pedi', _n(rot)):
            valor['natureza'], valor['natureza_txt'] = 'historico', f"VALOR EXIGIDO{' · ' + str(_ano(ac.get('_quando'))) if _ano(ac.get('_quando')) else ''}"
        elif _ano(ac.get('_quando')):
            valor['natureza'] = 'historico'
        alvo = m['valor']
    elif cont:
        chave, bruto = next(iter(cont.items()))
        alvo = float(str(bruto).replace('.', '').replace(',', '.')) if isinstance(bruto, str) else float(bruto)
        valor = {'valor': int(alvo) if alvo == int(alvo) else alvo, 'unidade': chave.replace('_', ' ')}
        resto = [f"{x} {k.replace('_', ' ')}" for k, x in list(cont.items())[1:]]
        rot = str(ac.get('acao') or ac.get('mostrar') or '')
    else:
        return None, ['valor numérico nos dados']
    r = rastrear(alvo, ac.get('fonte'), linhas)
    if not r:
        faltam.append(f'fonte rastreável para o número {alvo:g} (não aparece na pesquisa)')
        return None, faltam
    valor.update(rotulo=rot[:40], contexto='; '.join(resto)[:90], fonte=r['fonte'], rastreio=r['trecho'])
    return valor, faltam


def _pontos_locais(nomes: list[str]) -> list[dict]:
    """Coordenadas só do Natural Earth local (cidades). Nome não achado fica de fora."""
    try:
        from src.v2 import geo
        cidades = geo.camada('cidades')
    except Exception:
        return []
    out = []
    for nome in nomes:
        alvo = _n(nome)
        f = next((f for f in cidades if alvo in (_n(f['properties'].get('name')), _n(f['properties'].get('nameascii')))), None)
        if f:
            lon, lat = f['geometry']['coordinates'][:2]
            out.append({'nome': nome, 'lon': lon, 'lat': lat})
    return out


# ───────────────────────── o preparo ─────────────────────────
def preparar(v: dict, acervo: list[dict] | None = None) -> dict:
    """Valida e completa os acontecimentos do roteiro `v` (modifica `v['cenas']` e `v['fontes']`). Devolve o relatório:
    {eventos: [...], bloqueios: [...], revisoes: [...], trocas: [...], fontes_adicionadas: [...]}."""
    acervo = acervo if acervo is not None else (v.get('acervo') or [])
    por_id = {x['id']: x for x in acervo}
    linhas = pesquisa(v)
    fontes = v.setdefault('fontes', [])
    rel = {'eventos': [], 'bloqueios': [], 'revisoes': [], 'trocas': [], 'fontes_adicionadas': []}
    ano_geral = _ano(re.search(r'ÉPOCA/LUGAR:([^\n]*)', str(v.get('fatos') or '')).group(1)) if re.search(r'ÉPOCA/LUGAR:', str(v.get('fatos') or '')) else None

    # 1) id estável: fragmentos da mesma ideia (mesmo `evento` ou mesmo id declarado) formam UM acontecimento
    grupos, ordem = {}, []
    for k, c in enumerate(v['cenas']):
        bruto = c.get('acontecimento') if isinstance(c.get('acontecimento'), dict) else None
        if not bruto or not bruto.get('tipo'):
            continue
        chave = bruto.get('id') or c.get('evento') or f'cena{k}'
        if chave not in grupos:
            grupos[chave] = []; ordem.append(chave)
        grupos[chave].append(k)

    usadas = {}
    for chave in ordem:
        idx = grupos[chave]
        c0 = v['cenas'][idx[0]]
        bruto = c0['acontecimento']
        ac = contrato.normalizar(bruto)
        ac['id'] = chave
        ac['partes'] = len(idx)
        ac['_quem'], ac['_quando'] = bruto.get('quem'), bruto.get('quando')
        cena_ctx = {'mostrar': c0.get('mostrar'), 'tipo': c0.get('tipo'), '_falas': [re.sub(r'[*]', '', v['cenas'][k].get('fala', '')) for k in idx]}
        ev = {'id': chave, 'cenas': idx, 'tipo_original': ac.get('tipo'), 'critico': contrato.critico(ac) if ac.get('tipo') != 'desconhecido' else True}

        # 2) tipo
        novo, motivo = reclassificar(ac, cena_ctx)
        if novo != ac.get('tipo'):
            ac['tipo_original'], ac['tipo'], ac['reclassificacao'] = ac.get('tipo'), novo, motivo
        ev['tipo'] = ac['tipo']; ev['reclassificacao'] = motivo
        ano_evento = _ano(bruto.get('quando')) or _ano((ac.get('dados') or {}).get('data')) or ano_geral

        # 3) dados no formato da composição (só com o verificado)
        faltam = []
        if ac['tipo'] == 'numero':
            valor, f = _dados_numero(ac, linhas, v)
            faltam += f
            if valor:
                ac['dados'] = {**valor}
                ac['fonte'] = valor['fonte']
        elif ac['tipo'] == 'deslocamento':
            d = ac.get('dados') or {}
            pts = _pontos_locais([d[k] for k in ('origem', 'destino') if d.get(k)])
            if len(pts) >= 2:
                ac['dados'] = {**d, 'pontos': pts}
            else:
                faltam.append('coordenadas de origem e destino (' + ', '.join(str(d.get(k)) for k in ('origem', 'destino') if d.get(k)) + ') no Natural Earth local')
        # fonte do acontecimento: precisa estar na pesquisa; se está lá e não na lista do vídeo, entra na lista
        fonte = ac.get('fonte')
        if fonte:
            atrib = next((ln['fonte'] for ln in linhas if _mesma_fonte(ln['fonte'], fonte)), None)
            if atrib and not any(_mesma_fonte(atrib, x) for x in fontes):
                fontes.append(atrib); rel['fontes_adicionadas'].append(atrib)
            if not atrib:
                ev['fonte_nao_rastreada'] = fonte
        # números ditos na cena de número (tipo 'numero' do roteiro): fonte rastreada vai para a cena
        for k in idx:
            c = v['cenas'][k]
            if c.get('tipo') == 'numero' and c.get('valor') is not None:
                try:
                    r = rastrear(float(c['valor']), c.get('fonte') or ac.get('fonte'), linhas)
                except (TypeError, ValueError):
                    r = None
                if r:
                    c['fonte'] = r['fonte']
                    if not any(_mesma_fonte(r['fonte'], x) for x in fontes):
                        fontes.append(r['fonte']); rel['fontes_adicionadas'].append(r['fonte'])
                else:
                    faltam.append(f"fonte rastreável para o número {c['valor']} dito na cena {k}")
        # capacidade apresentada como carga (ex.: "levava vinte mil contêineres" com dado de capacidade)
        d = ac.get('dados') or {}
        if any('capacidad' in _n(kk) for kk in d) and re.search(r'\b(levava|transportava|carregava|trazia)\b', _n(' '.join(cena_ctx['_falas']))):
            rel['revisoes'].append({'evento': chave, 'cenas': idx, 'problema': 'capacidade apresentada como carga transportada',
                                    'evidencia': f"fala: \"{' '.join(cena_ctx['_falas'])[:80]}\"; dado: {next(str(d[kk]) for kk in d if 'capacidad' in _n(kk))}"})

        # 4) imagens: a escolhida, a sugerida pelo roteirista e as do acervo
        atual = por_id.get(c0.get('foto'))
        sug = por_id.get(c0.get('visual'))
        aval = lambda x: avaliar_imagem(x, ac, cena_ctx, ano_evento)
        av_atual = aval(atual) if atual else None
        escolhida, av_esc, troca = atual, av_atual, None
        if atual and not av_atual['compativel']:
            troca = {'evento': chave, 'cenas': idx, 'de': atual['id'], 'motivo': '; '.join(av_atual['motivos'])}
            escolhida, av_esc = None, None
        pode_foto = ac['tipo'] in FOTO_PODE
        comp = _composicao_viavel(ac)
        if not comp and (escolhida is None or (pode_foto and av_esc['forca'] < 3)):
            vistos, avs = set(), []
            for x in ([sug] if sug else []) + list(acervo):
                if x.get('arq') and x['id'] not in vistos:
                    vistos.add(x['id'])
                    a = aval(x)
                    if a['compativel'] and a['forca'] >= 1:
                        avs.append((x, a))
            # preferência: mostra o fato > o que o roteiro pediu > sugestão do roteirista > ainda não usada
            avs.sort(key=lambda p: (-p[1]['forca'], p[0] is not sug, p[0]['id'] in usadas))
            if avs and (escolhida is None or avs[0][1]['forca'] > av_esc['forca']):
                novo_x, novo_av = avs[0]
                troca = {'evento': chave, 'cenas': idx, 'de': (atual or {}).get('id'), 'para': novo_x['id'],
                         'motivo': ((troca or {}).get('motivo', '') + ' → ' if troca else '') + '; '.join(novo_av['motivos'])}
                escolhida, av_esc = novo_x, novo_av
        if troca:
            rel['trocas'].append(troca)
        if escolhida is not None:
            usadas.setdefault(escolhida['id'], []).append(chave)
            for k in idx:
                v['cenas'][k]['foto'] = escolhida['id']
                v['cenas'][k]['credito'] = escolhida.get('credito')
                v['cenas'][k]['acervo_id'] = escolhida['id']
        elif atual is not None:                      # a imagem que havia era incompatível e não há outra: sem imagem
            for k in idx:
                v['cenas'][k]['foto'] = None
                v['cenas'][k]['_sem_imagem'] = True

        # 5) representação
        # ordem: composição com dados > foto real que mostra o fato > cena editorial do roteiro > imagem pedida > contexto
        if comp:
            rep = {'modo': 'composicao', 'comp': comp}
        elif escolhida is not None and pode_foto and av_esc['forca'] >= 3:
            rep = {'modo': 'foto_direta', 'foto': escolhida['id'], 'evidencia': '; '.join(av_esc['motivos'])}
        elif all(v['cenas'][k].get('tipo') in EDITORIAL for k in idx) or (c0.get('tipo') == 'numero' and not any('cena' in f for f in faltam)):
            rep = {'modo': 'editorial', 'comp': EDITORIAL.get(c0.get('tipo'), 'numero.animado')}
        elif escolhida is not None and av_esc['forca'] >= 2:
            rep = {'modo': 'foto_declarada', 'foto': escolhida['id'], 'evidencia': '; '.join(av_esc['motivos'])}
            if ev['critico']:
                rel['revisoes'].append({'evento': chave, 'cenas': idx, 'problema': 'acontecimento crítico representado pela imagem que o roteiro pediu, sem mostrar o estado narrado',
                                        'evidencia': rep['evidencia']})
        elif not ev['critico']:
            rep = {'modo': 'foto_contexto' if escolhida is not None else 'sem_imagem', 'foto': (escolhida or {}).get('id')}
        else:
            capazes = ', '.join(f"{cp} ({', '.join(req)})" for cp, req in contrato.TIPOS.get(ac['tipo'], {}).get('comps', {}).items())
            falta_img = (f"foto/vídeo real que mostre \"{ac.get('estado_final') or ac.get('mostrar')}\"" if pode_foto
                         else 'composição com dados (este tipo não se mostra com foto)')
            rep = {'modo': 'bloqueio', 'faltam': faltam + [f'dados para uma composição capaz: {capazes or "nenhuma"}', falta_img]}
            rel['bloqueios'].append({'evento': chave, 'cenas': idx, 'tipo': ac['tipo'], 'mostrar': ac.get('mostrar'), 'faltam': rep['faltam']})
        ac['representacao'] = rep
        ev.update(representacao=rep, faltam=faltam, foto=(escolhida or {}).get('id'), dados=ac.get('dados'))
        for key in ('_quem', '_quando'):
            ac.pop(key, None)
        for k in idx:                                # o MESMO contrato (id, tipo, dados, representação) em todos os planos
            c = v['cenas'][k]
            bruto_k = c.get('acontecimento') or {}
            c['acontecimento'] = {**{kk: bruto_k[kk] for kk in ('quem', 'onde', 'quando', 'recurso') if kk in bruto_k}, **ac}
        rel['eventos'].append(ev)
    return rel


def _composicao_viavel(ac: dict) -> str | None:
    from src.v2 import capacidades
    comps = contrato.TIPOS.get(ac.get('tipo'), {}).get('comps', {})
    p = dict(ac.get('dados') or {})
    ctx = _n(' '.join(str(ac.get(k) or '') for k in ('acao', 'mostrar')))
    for comp, reqs in comps.items():
        if comp in contrato.GENERICAS:
            continue
        if all(capacidades._tem(r, p, ctx) for r in reqs):
            return comp
    return None


def resumo(rel: dict) -> str:
    linhas = [f"preparo: {len(rel['eventos'])} acontecimento(s) · {len(rel['bloqueios'])} bloqueio(s) · {len(rel['revisoes'])} revisão(ões) · "
              f"{len(rel['trocas'])} troca(s) de imagem" + (f" · fontes adicionadas: {', '.join(rel['fontes_adicionadas'])}" if rel['fontes_adicionadas'] else '')]
    for e in rel['eventos']:
        r = e['representacao']
        linhas.append(f"  {e['id']} {e['tipo']}{' (era ' + e['tipo_original'] + ')' if e.get('reclassificacao') else ''}"
                      f"{' crítico' if e['critico'] else ''} → {r['modo']}{' ' + r.get('comp', '') if r.get('comp') else ''}"
                      f"{' ' + str(r.get('foto')) if r.get('foto') else ''}")
    for b in rel['bloqueios']:
        linhas.append(f"  ✘ {b['evento']} ({b['tipo']}, cenas {b['cenas']}): falta " + ' | '.join(b['faltam']))
    return '\n'.join(linhas)
