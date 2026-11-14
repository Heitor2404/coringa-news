"""MODELO DE EVIDÊNCIA (experimental, V1) — interpretação de acontecimentos e seleção visual sem vocabulário do tema.

Status: experimental, em paralelo à V2.3. Não decide nada em produção. Liga só com EVIDENCIA_V1=sombra (grava o
resultado ao lado do preparo atual, sem trocar nenhuma decisão). Ver docs/EVIDENCIA_V1_EXPERIMENTAL.md.

Duas responsabilidades SEPARADAS:

  1. REPRESENTAÇÃO VISUAL — a imagem mostra o elemento do acontecimento na AÇÃO ou no ESTADO narrado?
     Níveis: PROVA > RELACIONADA > CONTEXTO > INCOMPATIVEL.
  2. VERIFICAÇÃO FACTUAL — números, citações, causas e superlativos da fala estão sustentados por uma linha da pesquisa
     com fonte? Imagem NUNCA verifica afirmação: a foto do deslizamento não comprova o terremoto de magnitude 5,1.

Sinais e famílias (a independência é declarada, não presumida):

  família REGISTRO — tudo que vem do MESMO registro da fonte: categorias, palavras-chave, data, descrição, título.
                     Categoria e data do mesmo arquivo NÃO são duas confirmações: contam como UMA.
  família VISAO    — leitura da imagem por IA. Catálogo e casamento usam o mesmo modelo (Gemini): contam como UMA.
                     Só é independente do registro se a IA NÃO viu legenda/nome do arquivo (`viu_legenda=False`).
                     Os prompts atuais (PROMPT_CATALOGO/PROMPT_CASAR) mostram a legenda → leitura "legado", não independente.
  roteirista       — a sugestão de imagem do roteiro não é evidência.

PROVA exige as DUAS famílias: vínculo forte no REGISTRO (categoria/palavra-chave curada do acontecimento, ou
categoria/identificador da entidade + data de criação compatível com a fase) E leitura VISUAL cega que confirma a ação
ou o estado exigido pelo tipo do acontecimento — e nenhum veto. Concordância dentro de uma família nunca soma.

Metadado desconhecido não confirma nada: sem data de criação, a data não entra; data de envio (upload) nunca entra;
data de publicação só serve como limite superior ("a foto existia antes disso").

Nada aqui conhece palavras de um assunto. As únicas listas são de GÊNERO de imagem (diagrama, pintura, memorial...),
de ESCRITA (árabe, cirílica...) e de GRAMÁTICA (marcadores de superlativo e causa) — iguais para qualquer tema.
"""
from __future__ import annotations

import copy
import datetime as dt
import os
import re
import unicodedata

NIVEIS = ('INCOMPATIVEL', 'CONTEXTO', 'RELACIONADA', 'PROVA')
ORDEM = {n: i for i, n in enumerate(NIVEIS)}
VERSAO = 'evidencia-v1-experimental'

FAMILIAS = {
    'registro': 'metadados do mesmo registro da fonte (categorias, palavras-chave, data, descrição, título): uma família só',
    'visao': 'leitura da imagem por IA; catálogo e casamento usam o mesmo modelo: uma família só; independente do registro '
             'apenas quando a IA não viu legenda nem nome do arquivo',
}


def ativo() -> bool:
    """Flag desligada por padrão. 'sombra' = calcula e grava, sem trocar nenhuma decisão do preparo atual."""
    return os.environ.get('EVIDENCIA_V1', '').strip().lower() == 'sombra'


# ───────────────────────── utilidades ─────────────────────────
def _n(s) -> str:
    s = unicodedata.normalize('NFKD', str(s or '').lower())
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'\s+', ' ', re.sub(r'[_]+', ' ', s)).strip()


def _sem_html(s) -> str:
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', str(s or ''))).strip()


def _min(a: str, b: str) -> str:
    return a if ORDEM[a] <= ORDEM[b] else b


# ───────────────────────── datas e intervalos ─────────────────────────
MESES = {'janeiro': 1, 'fevereiro': 2, 'marco': 3, 'abril': 4, 'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
         'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12,
         'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6, 'july': 7, 'august': 8,
         'september': 9, 'october': 10, 'november': 11, 'december': 12,
         'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'sept': 9, 'oct': 10,
         'nov': 11, 'dec': 12}


def _fim_mes(a: int, m: int) -> dt.date:
    return (dt.date(a + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1))


def _d(a, m=None, d=None) -> tuple[dt.date, dt.date, str] | None:
    try:
        if d:
            x = dt.date(a, m, d)
            return x, x, 'dia'
        if m:
            return dt.date(a, m, 1), _fim_mes(a, m), 'mes'
        return dt.date(a, 1, 1), dt.date(a, 12, 31), 'ano'
    except ValueError:
        return None


PRECISAO = {'dia': 0, 'mes': 1, 'ano': 2, 'decada': 3}


def intervalo(texto) -> dict:
    """Texto de data (português, inglês, ISO, EXIF, <time datetime>) → {inicio, fim, precisao, texto}.
    Sem data reconhecível → inicio=fim=None (desconhecida). Nunca inventa precisão."""
    bruto = str(texto or '')
    m = re.search(r'datetime="([^"]+)"', bruto)
    t = _n(_sem_html(m.group(1) if m else bruto))
    vazio = {'inicio': None, 'fim': None, 'precisao': None, 'texto': bruto[:80]}
    if not t:
        return vazio
    pedacos = []
    # ISO / EXIF: 1980-05-18, 1980:05:18 08:32:00, 2021-03
    for a, mo, di in re.findall(r'\b(1[0-9]{3}|20[0-9]{2})[-:/](\d{1,2})(?:[-:/](\d{1,2}))?(?!\d)', t):
        r = _d(int(a), int(mo), int(di) if di else None)
        if r:
            pedacos.append(r)
    nome_mes = '|'.join(sorted(MESES, key=len, reverse=True))
    # "18 de maio de 1980", "18 may 1980", "23 a 29 de marco de 2021"
    for d1, d2, mes, a in re.findall(rf'\b(\d{{1,2}})(?:\s*(?:a|-|e|to|–)\s*(\d{{1,2}}))?\s*(?:de\s+)?({nome_mes})\.?,?\s*(?:de\s+)?(1[0-9]{{3}}|20[0-9]{{2}})\b', t):
        r1 = _d(int(a), MESES[mes], int(d1))
        r2 = _d(int(a), MESES[mes], int(d2)) if d2 else None
        if r1:
            pedacos.append(r1)
        if r2:
            pedacos.append(r2)
    # "may 18, 1980"
    for mes, d1, a in re.findall(rf'\b({nome_mes})\.?\s+(\d{{1,2}}),?\s+(1[0-9]{{3}}|20[0-9]{{2}})\b', t):
        r = _d(int(a), MESES[mes], int(d1))
        if r:
            pedacos.append(r)
    if not pedacos:
        # "marco a maio de 1980", "marco de 2021", "inicio de julho de 2021"
        for m1, m2, a in re.findall(rf'\b({nome_mes})(?:\s+(?:a|-|to)\s+({nome_mes}))?\s+(?:de\s+)?(1[0-9]{{3}}|20[0-9]{{2}})\b', t):
            r1 = _d(int(a), MESES[m1])
            if r1:
                pedacos.append(r1)
            if m2:
                r2 = _d(int(a), MESES[m2])
                if r2:
                    pedacos.append(r2)
    if not pedacos:
        m = re.search(r'\b(?:decada de |the )?(1[0-9]{2}0|20[0-9]0)\'?s\b|\bdecada de (1[0-9]{2}0|20[0-9]0)\b', t)
        if m:
            a = int(m.group(1) or m.group(2))
            return {'inicio': dt.date(a, 1, 1), 'fim': dt.date(a + 9, 12, 31), 'precisao': 'decada', 'texto': bruto[:80]}
        anos = [int(x) for x in re.findall(r'\b(1[0-9]{3}|20[0-9]{2})\b', t)]
        for a in anos[:2]:
            pedacos.append(_d(a))
    if not pedacos:
        return vazio
    ini = min(p[0] for p in pedacos)
    fim = max(p[1] for p in pedacos)
    prec = max((p[2] for p in pedacos), key=lambda p: PRECISAO[p])
    if re.search(r'\b(antes de|before|ate|until)\b', t):           # "antes de 18 de maio": só o limite superior
        return {'inicio': None, 'fim': ini, 'precisao': prec, 'texto': bruto[:80], 'limite': 'superior'}
    if re.search(r'\b(depois de|apos|after|desde|since)\b', t):
        return {'inicio': fim, 'fim': None, 'precisao': prec, 'texto': bruto[:80], 'limite': 'inferior'}
    if re.search(r'\b(circa|c\.|cerca de|por volta de|aprox)', t) and prec != 'decada':
        ini, fim = dt.date(ini.year - 2, 1, 1), dt.date(fim.year + 2, 12, 31)
        prec = 'ano'
    return {'inicio': ini, 'fim': fim, 'precisao': prec, 'texto': bruto[:80]}


def fase(img: dict, ev: dict) -> str:
    """Momento da imagem em relação ao acontecimento: antes | durante | depois | sobreposta | desconhecida."""
    ii, fi, ie, fe = img.get('inicio'), img.get('fim'), ev.get('inicio'), ev.get('fim')
    if ii is None and fi is None:
        return 'desconhecida'
    if ie is None and fe is None:
        return 'desconhecida'
    if fi is not None and ie is not None and fi < ie:
        return 'antes'
    if ii is not None and fe is not None and ii > fe:
        return 'depois'
    if ii is not None and fi is not None and ie is not None and fe is not None and ie <= ii and fi <= fe:
        return 'durante'
    return 'sobreposta'


# ───────────────────────── o acontecimento normalizado ─────────────────────────
# O que a imagem precisa mostrar, pelo TIPO do contrato (tabela por tipo, nunca por assunto).
EXIGE = {
    'movimento': {'acao'}, 'deslocamento': {'acao'}, 'processo': {'acao'}, 'mecanismo': {'acao'}, 'nivel': {'acao'},
    'orbita': {'acao'},
    'transformacao': {'acao', 'estado_final'}, 'impacto': {'acao', 'estado_final'},
    'evento_historico': {'acao', 'estado_final'},
    'pessoa': {'entidade'}, 'lugar': {'entidade'}, 'ambiente': {'entidade'}, 'localizacao': {'entidade'},
    'territorio': {'entidade'}, 'documento': {'documento'},
    # números, comparações, séries, citações: imagem não representa — composição/editorial (só contexto)
}
HORIZONTE_ESTADO_FINAL = dt.timedelta(days=365)   # estado final fotografado até 1 ano depois do fim ainda é "depois"
JANELA_DATA = dt.timedelta(days=62)                # vínculo por data só vale para acontecimento datado com precisão


def exige(tipo: str, ac: dict) -> list[str]:
    """O que a imagem pode mostrar para representar o acontecimento. Tipo de AÇÃO que declara um estado final aceita
    também a imagem desse estado ("ficou de través" se vê no navio preso, não no instante do encalhe)."""
    base = set(EXIGE.get(tipo, set()))
    if 'acao' in base and str(ac.get('estado_final') or '').strip():
        base.add('estado_final')
    return sorted(base)


def _ac_de(cenas: list[dict], idx: list[int]) -> dict:
    return (cenas[idx[0]].get('acontecimento') or {}) if idx else {}


def acontecimento(bruto: dict, falas: list[str] | None = None, referencias: dict | None = None, ev_id: str | None = None,
                  critico: bool | None = None, tipo: str | None = None) -> dict:
    """Acontecimento do contrato → esquema da evidência. `referencias`: identidade de registro do acontecimento e das
    entidades ({evento: {nomes, categorias}, entidades: [{nome, categorias, ids}]}) — vem da pesquisa/Wikidata, nunca de
    uma lista do tema."""
    from src.v2 import contrato
    ac = contrato.normalizar(bruto)
    tp = tipo or ac.get('tipo') or 'desconhecido'
    refs = referencias or {}
    falas = [re.sub(r'\*', '', f or '') for f in (falas or [])]
    return {
        'id': ev_id or ac.get('id'), 'tipo': tp,
        'critico': contrato.critico(ac) if critico is None else critico,
        'sujeito': ac.get('sujeito') or bruto.get('quem'),
        'acao': ac.get('acao'), 'estado_inicial': ac.get('estado_inicial'), 'estado_final': ac.get('estado_final'),
        'mostrar': ac.get('mostrar'), 'onde': bruto.get('onde'),
        'intervalo': intervalo(bruto.get('quando') or (ac.get('dados') or {}).get('data')),
        'exige': exige(tp, ac),
        'falas': falas,
        'afirmacoes': afirmacoes(falas, tp),
        'referencias': {'evento': refs.get('evento') or {}, 'entidades': refs.get('entidades') or []},
    }


# ───────────────────────── verificação factual (separada da imagem) ─────────────────────────
SUPERLATIVO = re.compile(r'\b(maior|menor|primeir[oa]s?|ultim[oa]s?|unic[oa]s?|recorde|mais \w+ (?:do|da|de|ja)|jamais|nunca antes|ja registrad)')
CAUSA = re.compile(r'\b(porque|por causa|causou|causaram|provocou|provocaram|fez com que|levou a|desencade\w*|resultou|gracas a|devido)')


def afirmacoes(falas: list[str], tipo: str) -> list[dict]:
    """Afirmações verificáveis da fala (números, citação, superlativo, causa). Marcadores GRAMATICAIS, iguais para
    qualquer tema."""
    from src.v2.preparo import numeros
    out = []
    texto = ' '.join(falas)
    for x in numeros(texto):
        out.append({'tipo': 'numero', 'valor': x, 'texto': f'{x:g}'})
    for q in re.findall(r'["“]([^"”]{6,})["”]', texto):
        out.append({'tipo': 'citacao', 'texto': q})
    if tipo == 'citacao' and not any(a['tipo'] == 'citacao' for a in out):
        m = re.search(r':\s*(.{6,})$', texto.strip())
        if m:
            out.append({'tipo': 'citacao', 'texto': m.group(1).strip()})
    t = _n(texto)
    m = SUPERLATIVO.search(t)
    if m:
        out.append({'tipo': 'superlativo', 'texto': m.group(0)})
    m = CAUSA.search(t)
    if m:
        out.append({'tipo': 'causa', 'texto': m.group(0)})
    return out


def _tokens(s) -> set[str]:
    return {w for w in re.findall(r'[a-z0-9]{3,}', _n(s))}


def verificar_afirmacoes(ev: dict, linhas: list[dict], fonte_declarada: str | None = None) -> list[dict]:
    """Cada afirmação contra as linhas da pesquisa (texto + fonte). A imagem não participa."""
    from src.v2.preparo import rastrear
    out = []
    for a in ev.get('afirmacoes') or []:
        r = dict(a)
        if a['tipo'] == 'numero':
            achou = rastrear(a['valor'], fonte_declarada, linhas)
            r.update(status='sustentada' if achou else 'sem_fonte', **({'fonte': achou['fonte'], 'trecho': achou['trecho']} if achou else {}))
        elif a['tipo'] == 'citacao':
            alvo = _tokens(a['texto'])
            achou = next((ln for ln in linhas if alvo and len(alvo & _tokens(ln['texto'])) >= max(2, int(.8 * len(alvo)))), None)
            r.update(status='sustentada' if achou else 'sem_fonte', **({'fonte': achou['fonte'], 'trecho': achou['texto'][:200]} if achou else {}))
        else:
            # superlativo e causa: o código não decide sentido; fica marcado para a verificação textual (editor/humano)
            r.update(status='nao_verificada_automaticamente')
        out.append(r)
    return out


# ───────────────────────── registro da fonte (família REGISTRO) ─────────────────────────
# Origem da data, da mais forte para a mais fraca. Só 'captura' e 'criacao_declarada' situam a imagem no tempo.
ORIGENS_DATA = ('captura', 'criacao_declarada', 'publicacao', 'upload', 'desconhecida')

# Gênero da imagem pelo registro (categorias/título/palavras-chave): listas de GÊNERO, não de assunto.
GENERO = [
    ('gerada_por_ia', r'\b(ai[- ]generated|generated by ai|gerad[ao] por ia|midjourney|stable diffusion|dall-?e)\b'),
    ('reconstituicao_3d', r'\b(3d (render|model|reconstruction)|computer[- ]generated|cgi|reconstitui\w*|reconstruction|rendering|animation|animacao)\b'),
    ('ilustracao', r"\b(artist'?s? (concept|impression|rendering)|illustrations?|ilustrac\w*|drawings?|desenhos?|engravings?|gravuras?|lithographs?|litografias?|cartoons?|charges?)\b"),
    ('pintura', r'\b(paintings?|pinturas?|oil on canvas|oleo sobre tela|artworks?|watercolou?rs?|aquarelas?|frescoe?s?|murals?)\b'),
    ('diagrama', r'\b(diagrams?|diagramas?|schematics?|esquemas?|cross[- ]sections?|cortes? transvers\w*|infographics?|infograficos?)\b'),
    ('mapa', r'\b(maps?|mapas?|locator maps?)\b'),
    ('documento', r'\b(signs?|signage|posters?|cartaz(es)?|placas? (informativ\w*|de aviso)|newspapers?|jornais?|front pages?|documents?|documentos?|letters?|cartas?|screenshots?|capturas? de tela)\b'),
    ('objeto_ou_monumento', r'\b(memorials?|memoriais|monuments?|monumentos?|plaques?|placas? comemorativ\w*|commemorat\w*|museum exhibits?|exposic\w* de museu|replicas?)\b'),
]
FONTE_OBRA = {'met museum', 'art institute', 'cleveland museum'}


def _genero_registro(*textos) -> str | None:
    t = _n(' '.join(str(x or '') for x in textos))
    return next((g for g, pad in GENERO if re.search(pad, t)), None)


def _classificar_data_commons(campo: dict | str | None) -> tuple[str, dict]:
    """extmetadata.DateTimeOriginal → (origem, intervalo). source 'mediawiki-metadata' = EXIF da câmera (captura);
    'commons-desc-page' = campo date do {{Information}} (data de criação declarada, às vezes 'published'/'uploaded')."""
    if not campo:
        return 'desconhecida', intervalo(None)
    valor = campo.get('value') if isinstance(campo, dict) else campo
    fonte = (campo.get('source') if isinstance(campo, dict) else '') or ''
    t = _n(_sem_html(valor))
    iv = intervalo(valor)
    if iv['inicio'] is None and iv['fim'] is None:
        return 'desconhecida', iv
    if re.search(r'\b(published|publicad\w*|publication|first published)\b', t):
        return 'publicacao', iv
    if re.search(r'\b(uploaded|upload|carregad\w*|enviad\w*)\b', t):
        return 'upload', iv
    if fonte == 'mediawiki-metadata':
        return 'captura', iv
    return 'criacao_declarada', iv


def registro_commons(pagina: dict, ancestrais: list[str] | None = None) -> dict:
    """Página da API do Commons (prop=imageinfo&iiprop=extmetadata|timestamp, prop=categories) → registro normalizado."""
    info = (pagina.get('imageinfo') or [{}])[0]
    meta = info.get('extmetadata') or {}
    val = lambda k: _sem_html((meta.get(k) or {}).get('value'))
    cats = [c for c in val('Categories').split('|') if c] if val('Categories') else []
    cats += [re.sub(r'^Category:', '', c.get('title', c) if isinstance(c, dict) else c) for c in pagina.get('categories') or []]
    origem, iv = _classificar_data_commons(meta.get('DateTimeOriginal'))
    datas = {origem: iv} if origem != 'desconhecida' else {}
    if info.get('timestamp'):
        datas['upload'] = intervalo(info['timestamp'])
    titulo = str(pagina.get('title') or '').split(':', 1)[-1].rsplit('.', 1)[0]
    return _registro('Commons', titulo, list(dict.fromkeys(cats)), datas, val('ImageDescription') or val('ObjectName'),
                     val('Artist'), val('LicenseShortName'), ancestrais, pagina=pagina.get('fullurl') or pagina.get('pagina'))


def registro_nasa(d: dict) -> dict:
    """Item da NASA Image Library. date_created = data declarada pela NASA (às vezes a de arquivamento: 'Photo filed')."""
    datas = {}
    if d.get('date_created'):
        datas['criacao_declarada'] = intervalo(d['date_created'])
    return _registro('NASA', d.get('title'), list(d.get('keywords') or []), datas, d.get('description'),
                     d.get('photographer') or d.get('center'), 'domínio público (NASA)', None, pagina=d.get('nasa_id'),
                     obs=['data da NASA pode ser a de arquivamento ("filed"), não a de captura'] if re.search(r'\bfiled\b', _n(d.get('description'))) else [])


def registro_loc(it: dict) -> dict:
    datas = {'criacao_declarada': intervalo(it.get('date'))} if it.get('date') else {}
    subj = list(it.get('subject') or []) + list(it.get('subject_headings') or [])
    return _registro('Library of Congress', it.get('title'), subj, datas,
                     ' '.join(it.get('description') or []) if isinstance(it.get('description'), list) else it.get('description'),
                     ', '.join(it.get('contributor') or []) if isinstance(it.get('contributor'), list) else it.get('contributor'),
                     'sem restrição conhecida', None, pagina=it.get('url'))


def registro_openverse(h: dict) -> dict:
    """Openverse não devolve data: data desconhecida. Etiquetas são livres (do autor do envio): valem como descrição."""
    tags = ' '.join(t.get('name', '') for t in (h.get('tags') or []) if isinstance(t, dict))
    return _registro('Openverse', h.get('title'), [], {}, tags, h.get('creator'), h.get('license'), None,
                     pagina=h.get('foreign_landing_url'), etiquetas_livres=True)


def registro_legado(x: dict) -> dict:
    """Item do acervo atual (só ano, 220 caracteres de descrição, sem categorias). Ano de Commons/Wikidata/Wikipédia vem
    do DateTimeOriginal (criação declarada); NASA/LoC/museus, da data declarada da fonte; Openverse/iNaturalist/GBIF não têm."""
    fonte = str(x.get('fonte') or '')
    datas = {}
    if x.get('ano') and _n(fonte) not in ('openverse', 'inaturalist', 'gbif', 'pixabay video'):
        datas['criacao_declarada'] = intervalo(str(x['ano']))
    return _registro(fonte, x.get('titulo'), [], datas, x.get('desc'), (x.get('credito') or '')[:80], '', None,
                     etiquetas_livres=_n(fonte) == 'openverse', legado=True)


def _registro(fonte, titulo, categorias, datas, descricao, autor, licenca, ancestrais, pagina=None, obs=None,
              etiquetas_livres=False, legado=False) -> dict:
    return {'fonte': fonte, 'titulo': str(titulo or ''), 'categorias': [str(c) for c in categorias or []],
            'ancestrais': [str(c) for c in ancestrais or []], 'datas': datas, 'descricao': _sem_html(descricao)[:600],
            'autor': _sem_html(autor)[:120], 'licenca': licenca or '', 'pagina': pagina, 'obs': obs or [],
            'etiquetas_livres': etiquetas_livres, 'legado': legado}


def data_da_imagem(reg: dict) -> tuple[str, dict]:
    """A melhor data que SITUA a imagem no tempo (captura > criação declarada). Upload nunca. Publicação à parte."""
    for origem in ('captura', 'criacao_declarada'):
        iv = (reg.get('datas') or {}).get(origem)
        if iv and (iv.get('inicio') or iv.get('fim')):
            return origem, iv
    return 'desconhecida', intervalo(None)


def _casa_nome(alvo: str, cats: list[str]) -> str | None:
    """'categoria' se um nome de referência é uma categoria (ou está contido numa categoria) do registro."""
    a = _n(re.sub(r'^category:', '', alvo, flags=re.I))
    if len(a) < 4:
        return None
    for c in cats:
        cn = _n(re.sub(r'^category:', '', c, flags=re.I))
        if cn == a or (len(a) >= 8 and re.search(r'(^|\W)' + re.escape(a) + r'(\W|$)', cn)):
            return c
    return None


def vinculo(reg: dict, refs: dict) -> dict:
    """Família REGISTRO: o que o registro da fonte liga à imagem. Nomes próprios das referências (vindas da pesquisa), não
    vocabulário do tema. {evento: 'categoria'|'descricao'|None, entidade: ..., onde: 'categoria X'}."""
    cats = list(reg.get('categorias') or []) + list(reg.get('ancestrais') or [])
    texto = f"{reg.get('titulo', '')} {reg.get('descricao', '')}"
    out = {'evento': None, 'entidade': None, 'evidencia': []}
    curada = not reg.get('etiquetas_livres')
    evento = refs.get('evento') or {}
    for nome in list(evento.get('categorias') or []) + list(evento.get('nomes') or []):
        c = _casa_nome(nome, cats) if curada else None
        if c:
            out['evento'] = 'categoria'; out['evidencia'].append(f'categoria do acontecimento: "{c}"'); break
    if not out['evento']:
        for nome in list(evento.get('nomes') or []) + list(evento.get('categorias') or []):
            if len(_n(nome)) >= 8 and _n(nome) in _n(texto):
                out['evento'] = 'descricao'; out['evidencia'].append(f'acontecimento citado na descrição/título: "{nome}"'); break
    for ent in refs.get('entidades') or []:
        for nome in list(ent.get('categorias') or []) + list(ent.get('ids') or []):
            c = _casa_nome(nome, cats) if curada else None
            if c:
                out['entidade'] = 'categoria'; out['evidencia'].append(f'categoria da entidade: "{c}"'); break
        if out['entidade']:
            break
    if not out['entidade']:
        for ent in refs.get('entidades') or []:
            nomes = [ent.get('nome')] + list(ent.get('apelidos') or [])
            if any(n and len(_n(n)) >= 4 and re.search(r'(^|\W)' + re.escape(_n(n)) + r'(\W|$)', _n(texto)) for n in nomes):
                out['entidade'] = 'descricao'; out['evidencia'].append(f'entidade citada na descrição/título: "{ent.get("nome")}"'); break
    return out


# ───────────────────────── leitura visual (família VISAO) ─────────────────────────
PODE_PROVAR = {'foto', 'video_quadro', 'satelite_ou_aerea', 'sequencia'}
EXPLICA = {'diagrama', 'mapa', 'grafico', 'infografico'}
NUNCA_PROVA = {'pintura', 'desenho', 'ilustracao', 'ilustracao_digital', 'reconstituicao_3d', 'gerada_por_ia', 'arte', 'animacao'}
DOCUMENTO = {'documento', 'jornal', 'cartaz', 'captura_de_tela'}
CONSEQUENCIA = {'objeto_ou_monumento'}
ESCRITA_LIDA = {'latina', ''}          # o público do canal lê alfabeto latino
CONFERE = ('acao', 'estado_inicial', 'estado_final', 'consequencia', 'entidade', 'outro_estado', 'nao_mostra', 'incerto')


def visao_legada(x: dict, relacao_casamento: str | None = None) -> dict:
    """Catálogo atual (o Gemini VIU nome do arquivo e descrição): não é independente do registro e não compara estado
    com o acontecimento. Serve para gênero, texto sobreposto e 'genérica' — nunca para confirmar estado."""
    tipo = _n(x.get('tipo_img') or 'foto')
    natureza = {'foto': 'foto', 'pintura': 'pintura', 'desenho': 'desenho', 'cartaz': 'cartaz', 'jornal': 'jornal',
                'documento': 'documento', 'mapa': 'mapa', 'diagrama': 'diagrama'}.get(tipo, 'outro')
    if x.get('video'):
        natureza = 'video_quadro'
    mostra = _n(x.get('mostra'))
    escrita = next((e for e, pad in (('arabe', r'\barab'), ('cirilica', r'\b(russ|cirilic)'), ('chinesa', r'\bchines'),
                                     ('japonesa', r'\bjapones'), ('coreana', r'\bcorean'), ('hebraica', r'\bhebraic'),
                                     ('grega', r'\bgreg')) if re.search(pad, mostra)), '')
    tem_texto = bool(re.search(r'\b(texto|textos|legenda|legendas|rotulo|rotulos|inscric|escrit)', mostra))
    return {'origem': 'legado', 'viu_legenda': True, 'natureza': natureza, 'generica': bool(x.get('generica')),
            'texto_visivel': {'presente': tem_texto or bool(escrita), 'escrita': escrita if tem_texto or escrita else '',
                              'e_o_conteudo': tem_texto and natureza in EXPLICA | DOCUMENTO, 'sobreposto': bool(x.get('rotulado'))},
            'confere_com': 'incerto', 'classe_confere': None, 'confianca': 'baixa',
            # o casamento atual escolheu esta imagem como "fato": indício (viu a legenda), nunca confirmação
            'indicio_legado': str(relacao_casamento or '').lower() in ('fato', 'documento'),
            'descricao': x.get('mostra', '')}


def _visao_ok(vis: dict | None, exige: list[str]) -> tuple[bool, str]:
    if not vis:
        return False, 'sem leitura visual'
    if vis.get('origem') == 'legado' or vis.get('viu_legenda'):
        return False, 'leitura visual viu a legenda (não é independente do registro)'
    if vis.get('confere_com') not in exige:
        return False, f"leitura visual: \"{vis.get('confere_com')}\" (exigido: {' ou '.join(exige) or 'composição'})"
    if vis.get('classe_confere') is False:
        return False, 'leitura visual: elemento de outra classe'
    if vis.get('confianca') == 'baixa':
        return False, 'leitura visual com confiança baixa'
    return True, f"leitura visual cega confirma \"{vis.get('confere_com')}\""


# ───────────────────────── decisão (determinística, auditável) ─────────────────────────
def avaliar(ev: dict, reg: dict, vis: dict | None = None) -> dict:
    """Nível de REPRESENTAÇÃO de uma imagem para um acontecimento + todos os sinais, vetos e dependências registrados.
    Não verifica afirmações (ver verificar_afirmacoes)."""
    exige = list(ev.get('exige') or [])
    vis = vis or None
    vin = vinculo(reg, ev.get('referencias') or {})
    origem_data, iv_img = data_da_imagem(reg)
    pub = (reg.get('datas') or {}).get('publicacao')
    fs = fase(iv_img, ev.get('intervalo') or {})
    if fs in ('desconhecida', 'sobreposta') and pub and pub.get('fim') and ev['intervalo'].get('inicio') and pub['fim'] < ev['intervalo']['inicio']:
        fs, origem_data = 'antes', 'publicacao'          # publicada antes do acontecimento: só pode mostrar o antes
    vetos, deps, teto = [], [], 'PROVA'

    # natureza: o mais restritivo entre o registro e a leitura visual
    nat_reg = _genero_registro(reg.get('titulo'), ' '.join(reg.get('categorias') or []))
    if _n(reg.get('fonte')) in FONTE_OBRA and not nat_reg:
        nat_reg = 'pintura'
    nat_vis = (vis or {}).get('natureza')
    naturezas = [n for n in (nat_reg, nat_vis) if n]
    def peso(n):
        return 4 if n in NUNCA_PROVA else 3 if n in CONSEQUENCIA else 2 if n in EXPLICA else 1 if n in DOCUMENTO else 0
    natureza = max(naturezas, key=peso) if naturezas else 'desconhecida'
    if nat_reg and nat_vis and peso(nat_reg) != peso(nat_vis):
        deps.append(f'registro diz "{nat_reg}", leitura visual diz "{nat_vis}": vale o mais restritivo')
    if natureza in NUNCA_PROVA:
        teto = _min(teto, 'CONTEXTO'); vetos.append(f'{natureza}: arte/IA/reconstituição nunca prova')
    elif natureza in EXPLICA:
        teto = _min(teto, 'CONTEXTO'); vetos.append(f'{natureza}: explica, não registra o acontecimento')
    elif natureza in CONSEQUENCIA:
        teto = _min(teto, 'CONTEXTO'); vetos.append('objeto/monumento: consequência posterior, não o acontecimento')
    elif natureza in DOCUMENTO and 'documento' not in exige:
        teto = _min(teto, 'CONTEXTO'); vetos.append(f'{natureza}: registra um documento, não mostra o acontecimento')

    # texto que o público não lê, quando o texto é o conteúdo → incompatível
    tv = (vis or {}).get('texto_visivel') or {}
    if tv.get('presente') and tv.get('escrita') not in ESCRITA_LIDA and (tv.get('e_o_conteudo') or natureza in EXPLICA | DOCUMENTO):
        return _saida('INCOMPATIVEL', [f"texto em escrita {tv.get('escrita')} é o conteúdo da imagem: o público não lê"], ev, reg, vis, vin, origem_data, iv_img, fs, natureza, deps)

    # tempo (família REGISTRO): a fase da imagem contra a fase exigida pelo que a visão diz que ela mostra
    confere = (vis or {}).get('confere_com')
    alvo = confere if confere in ('acao', 'estado_inicial', 'estado_final') else ('acao' if 'acao' in exige else None)
    contradiz = False
    if alvo and fs in ('antes', 'depois', 'durante'):
        if alvo == 'acao' and fs != 'durante':
            contradiz = True
        elif alvo == 'estado_inicial' and fs == 'depois':
            contradiz = True
        elif alvo == 'estado_final' and fs == 'antes':
            contradiz = True
        elif alvo == 'estado_final' and fs == 'depois' and ev['intervalo'].get('fim') and iv_img.get('inicio') \
                and iv_img['inicio'] > ev['intervalo']['fim'] + HORIZONTE_ESTADO_FINAL:
            contradiz = True
    if contradiz:
        teto = _min(teto, 'CONTEXTO')
        vetos.append(f'imagem de fase "{fs}" ({origem_data}: {iv_img.get("texto")}) para fala que exige "{alvo}"')
        if confere in ('acao', 'estado_inicial', 'estado_final'):
            deps.append('leitura visual e data do registro discordam: vale a restrição')

    # tipo que imagem não representa (número, comparação, citação…)
    if not exige:
        teto = _min(teto, 'CONTEXTO'); vetos.append(f'tipo "{ev.get("tipo")}" se representa por composição/editorial, não por imagem')

    # vínculo do registro
    data_util = origem_data in ('captura', 'criacao_declarada') and iv_img.get('precisao') in ('dia', 'mes')
    ev_iv = ev.get('intervalo') or {}
    ev_datado = bool(ev_iv.get('inicio') and ev_iv.get('fim') and (ev_iv['fim'] - ev_iv['inicio']) <= JANELA_DATA)
    if exige == ['entidade']:
        r_forte = vin['entidade'] == 'categoria' or (vin['evento'] == 'categoria' and vin['entidade'] == 'descricao')
    else:
        fase_ok = (alvo == 'acao' and fs == 'durante') or (alvo == 'estado_final' and fs in ('durante', 'depois')) or (alvo == 'estado_inicial' and fs == 'antes')
        r_forte = vin['evento'] == 'categoria' or (vin['entidade'] == 'categoria' and data_util and ev_datado and fase_ok and not contradiz)
    r_algum = bool(vin['evento'] or vin['entidade'])
    if reg.get('legado'):
        deps.append('registro legado: categorias e data completa foram descartadas na coleta (só ano e 220 caracteres)')
    if origem_data == 'desconhecida':
        deps.append('data de criação desconhecida: não confirma nem contradiz (upload não conta)')

    v_ok, v_motivo = _visao_ok(vis, exige)
    if vis and (vis.get('origem') == 'legado' or vis.get('viu_legenda')):
        deps.append('leitura visual não é independente: a IA viu legenda/nome do arquivo')

    # incompatível: nada liga a imagem ao acontecimento, ou a visão diz que é outra coisa
    if vis and vis.get('generica') and not r_algum:
        return _saida('INCOMPATIVEL', ['imagem genérica sem vínculo de registro'], ev, reg, vis, vin, origem_data, iv_img, fs, natureza, deps)
    if vis and (vis.get('classe_confere') is False or vis.get('confere_com') == 'nao_mostra') and not r_algum:
        return _saida('INCOMPATIVEL', [v_motivo if vis.get('classe_confere') is False else 'leitura visual: não mostra o acontecimento'],
                      ev, reg, vis, vin, origem_data, iv_img, fs, natureza, deps)
    if not r_algum and not v_ok and (not vis or vis.get('confere_com') in (None, 'incerto')):
        return _saida('INCOMPATIVEL', ['nenhum sinal liga a imagem ao acontecimento'], ev, reg, vis, vin, origem_data, iv_img, fs, natureza, deps)

    motivos = []
    if v_ok and r_forte:
        nivel = 'PROVA'
        motivos = [v_motivo] + vin['evidencia'][:2] + ([f'data ({origem_data}) {iv_img.get("texto")}: fase "{fs}"'] if fs not in ('desconhecida',) else [])
    elif v_ok and r_algum:
        nivel, motivos = 'RELACIONADA', [v_motivo, 'vínculo do registro fraco: ' + '; '.join(vin['evidencia'][:2])]
    elif v_ok:
        nivel, motivos = 'RELACIONADA', [v_motivo, 'nenhum registro liga a imagem a ESTE acontecimento (pode ser outro caso parecido)']
    elif r_forte and (not vis or vis.get('confere_com') in (None, 'incerto') or vis.get('origem') == 'legado' or vis.get('viu_legenda')):
        nivel, motivos = 'RELACIONADA', vin['evidencia'][:2] + [v_motivo]
    elif r_algum and vis and vis.get('indicio_legado') and vis.get('confere_com') in (None, 'incerto'):
        nivel, motivos = 'RELACIONADA', vin['evidencia'][:2] + ['indício do casamento atual ("fato"), que viu a legenda: só revisão humana']
    elif vis and vis.get('confere_com') in ('acao', 'estado_inicial', 'estado_final', 'entidade', 'outro_estado', 'consequencia') or r_algum:
        nivel = 'CONTEXTO'
        motivos = [v_motivo] + vin['evidencia'][:2]
        if vis and vis.get('confere_com') == 'consequencia':
            motivos.append('mostra consequência, não o acontecimento')
    else:
        nivel, motivos = 'INCOMPATIVEL', [v_motivo]
    final = _min(nivel, teto)
    if final != nivel:
        motivos = vetos + motivos
    return _saida(final, motivos, ev, reg, vis, vin, origem_data, iv_img, fs, natureza, deps, vetos=vetos, nivel_sem_veto=nivel)


def _fmt_iv(iv: dict) -> str | None:
    if not iv or not (iv.get('inicio') or iv.get('fim')):
        return None
    return f"{iv.get('inicio') or '…'}..{iv.get('fim') or '…'} ({iv.get('precisao')})"


def _saida(nivel, motivos, ev, reg, vis, vin, origem_data, iv_img, fs, natureza, deps, vetos=None, nivel_sem_veto=None) -> dict:
    fams = []
    if vin.get('evento') == 'categoria' or vin.get('entidade') == 'categoria':
        fams.append('registro')
    if vis and vis.get('origem') != 'legado' and not vis.get('viu_legenda') and vis.get('confere_com') in (ev.get('exige') or []):
        fams.append('visao')
    return {'nivel': nivel, 'motivos': [m for m in motivos if m],
            'vetos': list(vetos or []), 'nivel_sem_veto': nivel_sem_veto or nivel,
            'familias_que_confirmam': fams,
            'sinais': {'registro': {'fonte': reg.get('fonte'), 'vinculo_evento': vin.get('evento'), 'vinculo_entidade': vin.get('entidade'),
                                    'evidencia': vin.get('evidencia'), 'data_origem': origem_data, 'data': _fmt_iv(iv_img),
                                    'fase_da_imagem': fs, 'legado': reg.get('legado', False)},
                       'visao': {k: (vis or {}).get(k) for k in ('origem', 'viu_legenda', 'confere_com', 'classe_confere', 'confianca', 'natureza')} if vis else None,
                       'natureza': natureza},
            'dependencias': deps,
            'nao_comprova': [a.get('texto') for a in ev.get('afirmacoes') or []],
            'representa': (ev.get('exige') or [None])}


# ───────────────────────── decisão por acontecimento ─────────────────────────
def forca(a: dict) -> int:
    """Desempate DENTRO do mesmo nível (nunca muda o nível): vínculo do registro, data na fase, indício do casamento."""
    r = a['sinais']['registro']
    pts = {'categoria': 3, 'descricao': 1}.get(r.get('vinculo_evento'), 0) + {'categoria': 2, 'descricao': 1}.get(r.get('vinculo_entidade'), 0)
    pts += 2 if r.get('fase_da_imagem') == 'durante' else 0
    pts += 2 if any('indício do casamento' in m for m in a.get('motivos') or []) else 0
    return pts
def decidir(ev: dict, candidatos: list[tuple[str, dict]], comp: str | None = None, editorial: str | None = None,
            verificacao: list[dict] | None = None) -> dict:
    """candidatos: [(id da imagem, avaliação)]. Ordem: composição com dados > PROVA > editorial > RELACIONADA (revisão
    humana se crítico) > CONTEXTO (só se não crítico) > bloqueio com o que falta."""
    ordenados = sorted(candidatos, key=lambda p: (-ORDEM[p[1]['nivel']], -len(p[1]['familias_que_confirmam']), -forca(p[1])))
    melhor = ordenados[0] if ordenados else None
    nivel = melhor[1]['nivel'] if melhor else None
    sem_fonte = [a for a in verificacao or [] if a.get('status') == 'sem_fonte']
    rep = {'verificacao_factual': verificacao or [], 'afirmacoes_sem_fonte': [a.get('texto') for a in sem_fonte]}
    if comp:
        rep.update(modo='composicao', comp=comp)
        if melhor and nivel == 'PROVA':
            rep['foto_de_apoio'] = melhor[0]
    elif melhor and nivel == 'PROVA':
        rep.update(modo='foto_prova', foto=melhor[0], nivel=nivel, motivos=melhor[1]['motivos'])
        if ev.get('tipo') == 'evento_historico':
            rep['dados_composicao'] = {'comp': 'foto.historica', 'img': melhor[0]}
    elif editorial:
        rep.update(modo='editorial', comp=editorial)
    elif melhor and nivel == 'RELACIONADA':
        rep.update(modo='foto_relacionada', foto=melhor[0], nivel=nivel, motivos=melhor[1]['motivos'])
        if ev.get('critico'):
            rep['revisao_humana'] = 'imagem ligada ao acontecimento, sem as duas famílias de evidência: ' + '; '.join(melhor[1]['motivos'][:2])
    elif melhor and nivel == 'CONTEXTO' and not ev.get('critico'):
        rep.update(modo='foto_contexto', foto=melhor[0], nivel=nivel, motivos=melhor[1]['motivos'])
    elif not ev.get('critico'):
        rep.update(modo='sem_imagem')
    else:
        exige = ' ou '.join(ev.get('exige') or []) or 'composição com dados'
        falta = [f'imagem com vínculo de REGISTRO a este acontecimento (categoria/palavra-chave da fonte, ou entidade + data '
                 f'de criação na fase) E leitura VISUAL cega que confirme "{exige}"']
        if melhor:
            falta.append(f'melhor candidata {melhor[0]}: {melhor[1]["nivel"]} — ' + '; '.join(melhor[1]['motivos'][:2]))
        rep.update(modo='bloqueio', faltam=falta)
    if sem_fonte and ev.get('critico'):
        rep['revisao_factual'] = 'afirmação sem fonte na pesquisa: ' + ', '.join(str(a.get('texto')) for a in sem_fonte)
    rep['candidatos'] = [{'imagem': i, 'nivel': a['nivel'], 'motivos': a['motivos'][:3]} for i, a in ordenados[:5]]
    return rep


def referencias_basicas(v: dict) -> dict:
    """Sem consulta à rede: entidades = nomes próprios que o PRÓPRIO roteiro declara (sujeito/quem/onde do contrato).
    Só geram vínculo fraco (nome no título/descrição). Categoria do acontecimento e da entidade vêm de
    `referencias` (pesquisa → Wikidata/Commons), quando a coleta as fornecer."""
    nomes = []
    for c in v.get('cenas') or []:
        ac = c.get('acontecimento') or {}
        for k in ('sujeito', 'quem', 'onde'):
            t = str(ac.get(k) or '')
            for m in re.findall(r"\b([A-ZÀ-Ý][\wÀ-ÿ'.-]+(?:\s+(?:de|da|do|of|the|St\.?)?\s*[A-ZÀ-Ý][\wÀ-ÿ'.-]+)*)", t):
                if len(m) >= 4 and m.lower() not in ('navio', 'canal'):
                    nomes.append(m.strip())
    vistos = list(dict.fromkeys(nomes))
    return {'evento': {}, 'entidades': [{'nome': n} for n in vistos[:8]]}


# ───────────────────────── preparo paralelo (não altera o roteiro) ─────────────────────────
EDITORIAL_COMPLETO = {'revelacao': 'revelacao.surpresa', 'gancho': 'abertura.pergunta', 'fechamento': 'encerramento.editorial',
                      'citacao': 'citacao'}


def preparar(v: dict, acervo: list[dict], registros: dict | None = None, visoes: dict | None = None,
             referencias: dict | None = None, rel_antigo: dict | None = None) -> dict:
    """Roda o preparo ATUAL numa cópia (tipos, dados e composições continuam os dele) e decide a representação de cada
    acontecimento com o modelo de evidência. `registros` {id_imagem: registro}; `visoes` {(id_evento, id_imagem): visão}
    ou {id_imagem: visão}; sem eles, usa o legado (catálogo atual). Devolve o relatório e as divergências."""
    from src.v2 import preparo as antigo
    rel_old = rel_antigo or antigo.preparar(copy.deepcopy(v), copy.deepcopy(acervo))
    linhas = antigo.pesquisa(v)
    registros, visoes = registros or {}, visoes or {}
    referencias = referencias or referencias_basicas(v)
    out = {'versao': VERSAO, 'eventos': [], 'bloqueios': [], 'revisoes': [], 'divergencias': []}
    usadas = set()
    for e_old in rel_old['eventos']:
        # pelo id do acontecimento (a decisão gravada de um piloto pode ter outra numeração de cenas)
        idx = [k for k, c in enumerate(v['cenas']) if (c.get('acontecimento') or {}).get('id') == e_old['id'] or c.get('evento') == e_old['id']] \
            or [k for k in e_old['cenas'] if k < len(v['cenas'])]
        bruto = _ac_de(v['cenas'], idx)
        ev = acontecimento(bruto, [v['cenas'][k].get('fala', '') for k in idx], referencias, e_old['id'], e_old['critico'], e_old['tipo'])
        ver = verificar_afirmacoes(ev, linhas, bruto.get('fonte'))
        cands = []
        for x in acervo:
            if not x.get('id'):
                continue
            reg = registros.get(x['id']) or registro_legado(x)
            rel_cas = next((v['cenas'][k].get('relacao') for k in idx if v['cenas'][k].get('foto') == x['id']), None)
            vis = visoes.get((ev['id'], x['id'])) or visoes.get(x['id']) or visao_legada(x, rel_cas)
            if 'confere_com' not in vis:
                vis = {**visao_legada(x, rel_cas), **vis}
            a = avaliar(ev, reg, vis)
            if x['id'] in usadas and a['nivel'] != 'PROVA':
                a = {**a, 'motivos': a['motivos'] + ['já usada em outro acontecimento']}
            cands.append((x['id'], a))
        cands.sort(key=lambda p: (-ORDEM[p[1]['nivel']], p[0] in usadas, -forca(p[1])))
        rep_old = e_old['representacao']
        comp = rep_old.get('comp') if rep_old.get('modo') == 'composicao' else None
        tipos_cena = {v['cenas'][k].get('tipo') for k in idx}
        editorial = None
        if len(tipos_cena) == 1:
            t = next(iter(tipos_cena))
            if t in EDITORIAL_COMPLETO and (t != 'citacao' or any(a['tipo'] == 'citacao' and a.get('status') == 'sustentada' for a in ver)):
                editorial = EDITORIAL_COMPLETO[t]
        if not editorial and rep_old.get('modo') == 'editorial':
            editorial = rep_old.get('comp')
        rep = decidir(ev, cands, comp, editorial, ver)
        if rep.get('foto'):
            usadas.add(rep['foto'])
        item = {'id': ev['id'], 'cenas': idx, 'tipo': ev['tipo'], 'critico': ev['critico'], 'exige': ev['exige'],
                'intervalo': _fmt_iv(ev['intervalo']), 'antigo': {'modo': rep_old.get('modo'), 'foto': e_old.get('foto')},
                'novo': rep}
        out['eventos'].append(item)
        if rep['modo'] == 'bloqueio':
            out['bloqueios'].append({'evento': ev['id'], 'cenas': idx, 'faltam': rep['faltam']})
        if rep.get('revisao_humana'):
            out['revisoes'].append({'evento': ev['id'], 'cenas': idx, 'problema': rep['revisao_humana']})
        if rep.get('revisao_factual'):
            out['revisoes'].append({'evento': ev['id'], 'cenas': idx, 'problema': rep['revisao_factual']})
        if (rep_old.get('modo'), e_old.get('foto')) != (rep['modo'], rep.get('foto')):
            out['divergencias'].append({'evento': ev['id'], 'antigo': f"{rep_old.get('modo')} {e_old.get('foto') or ''}".strip(),
                                        'novo': f"{rep['modo']} {rep.get('foto') or rep.get('comp') or ''}".strip()})
    return out


def resumo(rel: dict) -> str:
    l = [f"evidência ({rel['versao']}): {len(rel['eventos'])} acontecimento(s) · {len(rel['bloqueios'])} bloqueio(s) · "
         f"{len(rel['revisoes'])} revisão(ões) · {len(rel['divergencias'])} divergência(s) com o preparo atual"]
    for e in rel['eventos']:
        n = e['novo']
        l.append(f"  {e['id']} {e['tipo']}{' crítico' if e['critico'] else ''}: antigo {e['antigo']['modo']} {e['antigo']['foto'] or ''} → "
                 f"novo {n['modo']} {n.get('foto') or n.get('comp') or ''}".rstrip())
    return '\n'.join(l)
