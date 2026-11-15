"""IDENTIDADE DOCUMENTAL (V2.4) — quem/o quê um acontecimento nomeia × o que uma imagem documenta.

Usado pelo preparo V2.3 (decisão) e pela Evidência V1 (sombra). Sem IA, sem rede, sem vocabulário de tema: só
estrutura de nomes (nomes próprios, nome científico binomial), metadados da fonte (título, descrição, crédito) e
escala física. Origem: piloto 43654018515 da lagartixa, em que

  - o sujeito institucional ("NASA") impedia a foto do objeto visível (o robô Astrobee) — instituição responsável
    não é objeto visual: ela documenta a imagem pelo crédito, não aparece nela;
  - um desenho de OUTRA espécie (Tarentola mauretanica) podia representar a espécie narrada (Hemidactylus mabouia);
  - a Evidência V1 ligava qualquer foto da espécie a qualquer acontecimento do vídeo (a lagartixa do Kruger para a
    fala do Astrobee), porque as entidades eram as do VÍDEO, não as do acontecimento.
"""
from __future__ import annotations

import re
import unicodedata

# palavras com maiúscula que não são nomes (início de frase, artigos, títulos genéricos)
NAO_NOME = {'a', 'o', 'as', 'os', 'um', 'uma', 'em', 'no', 'na', 'nos', 'nas', 'de', 'da', 'do', 'e', 'essa', 'esse', 'essas',
            'esses', 'esta', 'este', 'isso', 'isto', 'ela', 'ele', 'elas', 'eles', 'sem', 'com', 'para', 'por', 'segue', 'se',
            'foto', 'fotografia', 'imagem', 'the', 'an', 'of', 'astronauta', 'cientistas', 'segundo', 'quando', 'como', 'mas'}
# escala que uma foto comum não registra; micrografia registra
MICRO = re.compile(r'\b(microscop\w*|nanometr\w*|nanoscop\w*|celula\w*|celular\w*|molecul\w*|atom\w*)')
MICROGRAFIA = re.compile(r'\b(micrograf\w*|microscopi\w* eletronic\w*|eletronic\w* de varredura|microscopio|sem image|'
                         r'scanning electron|micrograph\w*|microscopy)')
EPITETO = re.compile(r'(a|ae|us|um|is|i|ii|ens|ex|ix)$')
BINOMIO = re.compile(r'\b([A-Z][a-z]{2,})\s+([a-z]{3,})\b')


def _n(s) -> str:
    s = unicodedata.normalize('NFKD', str(s or '').lower())
    return ''.join(c for c in s if not unicodedata.combining(c))


def _texto(x) -> str:
    if isinstance(x, dict):
        return ' '.join(_texto(v) for v in x.values())
    if isinstance(x, (list, tuple)):
        return ' '.join(_texto(v) for v in x)
    return str(x or '')


def nomes_proprios(texto: str, inicio_de_frase: bool = True) -> list[str]:
    """Sequências de palavras com maiúscula ("Suni Williams", "Estação Espacial", "NASA", "Astrobee").
    `inicio_de_frase=False` descarta a 1ª palavra de cada frase (fala: "Essas almofadas…")."""
    out = []
    for frase in re.split(r'(?<=[.!?])\s+|\n', str(texto or '')):
        palavras = frase.split()
        for i, w in enumerate(palavras):
            limpo = re.sub(r"^[^\wÀ-ÿ]+|[^\wÀ-ÿ]+$", '', w)
            if not limpo or not limpo[0].isupper() or _n(limpo) in NAO_NOME or len(limpo) < 3:
                continue
            if i == 0 and not inicio_de_frase and not (limpo.isupper() and len(limpo) >= 3):
                continue
            out.append(limpo)
    # junta vizinhos ("Suni" "Williams")
    juntos, texto_n = [], ' '.join(str(texto or '').split())
    for nome in dict.fromkeys(out):
        juntos.append(nome)
    pares = re.findall(r"\b([A-ZÀ-Ý][\wÀ-ÿ'-]{2,}(?:\s+[A-ZÀ-Ý][\wÀ-ÿ'-]{2,})+)", texto_n)
    for p in pares:
        partes = [w for w in p.split() if _n(w) not in NAO_NOME]
        if len(partes) >= 2:
            juntos.append(' '.join(partes))
    return list(dict.fromkeys(juntos))


def binomios(texto: str, campos: list[str] | None = None) -> set[str]:
    """Nomes científicos (Gênero espécie) MARCADOS como tal — "espécie/species X y", "(X y", ou um campo/categoria
    que é inteiro um binômio. Sem marca, "Ever Given levava" ou "Flickr images" seriam falsos táxons."""
    out = set()
    t = str(texto or '')
    marcados = re.findall(r'(?:esp[ée]cie|species|g[êe]nero|genus)\s+(?:de\s+|do\s+|da\s+)?' + BINOMIO.pattern, t, flags=0) \
        + re.findall(r'\(\s*' + BINOMIO.pattern, t)
    for c in campos or []:
        m = re.fullmatch(r'\s*' + BINOMIO.pattern + r'(?:\s*\([^)]*\))?\s*', str(c or ''))
        if m:
            marcados.append(m.groups())
    for g, e in marcados:
        if _n(g) in NAO_NOME or _n(e) in NAO_NOME or not EPITETO.search(e):
            continue
        out.add(f'{_n(g)} {_n(e)}')
    return out


def do_acontecimento(ac: dict, falas: list[str] | None = None) -> dict:
    """Identidade DESTE acontecimento: nomes próprios e nomes científicos que o contrato e as falas dele declaram."""
    campos = ' . '.join(str(ac.get(k) or '') for k in ('sujeito', 'quem', 'onde', 'acao', 'mostrar', 'estado_final'))
    dados = _texto({k: v for k, v in (ac.get('dados') or {}).items() if isinstance(v, (str, list))})
    # 1ª palavra de campo/frase com maiúscula não é nome ("Trecho do canal"); sigla e nome composto continuam
    nomes = nomes_proprios(campos, False) + nomes_proprios(dados, False) + [n for f in falas or [] for n in nomes_proprios(f, inicio_de_frase=False)]
    nomes = [n for n in dict.fromkeys(nomes) if len(_n(n)) >= 4]
    tax = binomios(campos + ' ' + dados + ' ' + ' '.join(falas or []),
                   [ac.get('sujeito'), ac.get('quem')] + [v for v in (ac.get('dados') or {}).values() if isinstance(v, str)])
    escala = ' '.join(str(ac.get(k) or '') for k in ('sujeito', 'acao', 'estado_final', 'mostrar')) + ' ' + _texto(ac.get('dados')) + ' ' + ' '.join(falas or [])
    return {'nomes': nomes, 'taxons': tax, 'micro': bool(MICRO.search(_n(escala)))}


def _contem(nome: str, texto_n: str) -> bool:
    a = _n(nome)
    return len(a) >= 3 and re.search(r'(^|[^a-z0-9])' + re.escape(a) + r'($|[^a-z0-9])', texto_n) is not None


def da_imagem(x: dict) -> dict:
    """O que o item do acervo DOCUMENTA: o que mostra (catálogo + título + descrição da fonte) e quem assina
    (crédito/fonte/autor)."""
    mostra = ' '.join(str(x.get(k) or '') for k in ('mostra', 'titulo', 'desc', 'descricao', 'legenda'))
    credito = ' '.join(str(x.get(k) or '') for k in ('credito', 'fonte', 'autor'))
    return {'mostra_n': _n(mostra), 'credito_n': _n(credito),
            'taxons': binomios(mostra, [x.get('titulo')] + list(x.get('categorias') or [])),
            'micrografia': bool(MICROGRAFIA.search(_n(mostra + ' ' + str(x.get('tipo_img') or ''))))}


def confrontar(ident: dict, x: dict) -> dict:
    """Identidade do acontecimento × imagem.
    visiveis    nomes do acontecimento que a imagem MOSTRA (objeto/pessoa/lugar)
    assinantes  nomes que só aparecem no CRÉDITO (instituição responsável: documenta, não é objeto visual)
    conflito    a imagem é de outro táxon nomeado (o acontecimento nomeia um e a imagem nomeia outro)
    escala      o acontecimento fala de escala microscópica e a imagem não é micrografia (mostra só o visível)"""
    im = da_imagem(x)
    visiveis = [n for n in ident['nomes'] if _contem(n, im['mostra_n'])]
    assinantes = [n for n in ident['nomes'] if n not in visiveis and _contem(n, im['credito_n'])]
    conflito = None
    if ident['taxons'] and im['taxons'] and not (ident['taxons'] & im['taxons']):
        conflito = f"imagem de {', '.join(sorted(im['taxons']))}; o acontecimento é de {', '.join(sorted(ident['taxons']))}"
    return {'visiveis': visiveis, 'assinantes': assinantes, 'conflito': conflito,
            'nomeia': bool(ident['nomes']), 'escala': bool(ident['micro'] and not im['micrografia'])}
