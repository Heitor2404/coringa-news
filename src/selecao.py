"""SELEÇÃO COM EVIDÊNCIA (plano-mestre, etapa E — 12/11/2026). Sem chamada nova: só código sobre o que já existe.

A escolha do Gemini (casar) é HIPÓTESE, não prova de que a imagem mostra o fato. Aqui ela é conferida com os metadados
do próprio acervo (ano, tipo, pessoas, lugar, título, fonte, licença, resolução):
  - "fato"/"documento" precisam de ano compatível com o acontecimento (quando os dois têm ano) e, no documento, de ser um
    papel de verdade (tipo do catálogo ou título); "pessoa"/"lugar" precisam do nome no catálogo ou no título;
  - o que não se confirma é rebaixado para "tema" (contextual) com o motivo registrado — nunca apagado em silêncio;
  - autenticidade sem como conferir (o fato tem ano e a imagem não) fica marcada "não verificada".
O ranqueamento das reservas (preencher; abaixo de RECUSA = recusa) usa pertinência ao que a frase afirma, proveniência, clareza (nota do catálogo),
resolução, licença e diversidade. Cada escolha e cada recusa guardam o motivo (vão para o storyboard: c['sb']['escolha']).
"""
import re
import unicodedata

ANO = re.compile(r'\b(1[0-9]{3}|20[0-9]{2})\b')
PAPEL = re.compile(r'newspaper|journal|gazette|letter|document|manuscript|telegram|jornal|carta|documento|manuscrito|'
                   r'le petit|le figaro|le matin|deed|contract|certificate|poster|cartaz', re.I)
TIPOS_PAPEL = ('documento', 'jornal', 'manuscrito', 'carta', 'cartaz', 'mapa_antigo')
FONTES_ARQUIVO = ('commons', 'wikipedia', 'loc', 'met', 'nasa', 'smithsonian', 'europeana', 'artic', 'cleveland',
                  'inaturalist', 'gbif', 'wikidata')
MIN_LADO = 600
RECUSA = -1.0            # reserva com menos pontos que isso não entra (sem proveniência + baixa resolução, p. ex.)
JANELA_FATO = 2           # foto "do fato" tirada até 2 anos do acontecimento
JANELA_PAPEL = 3


def _tok(s) -> set[str]:
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().lower()
    return {w for w in re.findall(r'[a-z0-9]{3,}', s)} - {'the', 'and', 'des', 'les', 'del', 'van', 'von', 'com', 'para'}


def _ano_evento(c: dict) -> int | None:
    m = ANO.search(str((c.get('acontecimento') or {}).get('quando') or ''))
    return int(m.group(1)) if m else None


def _ano_item(x: dict) -> int | None:
    try:
        return int(x.get('ano')) if x.get('ano') else None
    except (TypeError, ValueError):
        m = ANO.search(str(x.get('ano')))
        return int(m.group(1)) if m else None


def _texto(x: dict) -> str:
    return f"{x.get('titulo', '')} {x.get('mostra', '')} {x.get('desc', '')}"


def verificar(x: dict, c: dict, rel: str | None) -> tuple[str | None, list[str], bool]:
    """(relação conferida, motivos, verificada). Rebaixa para 'tema' o que os metadados não confirmam."""
    motivos, verificada = [], True
    ac = c.get('acontecimento') or {}
    ae, ai = _ano_evento(c), _ano_item(x)
    if rel in ('fato', 'documento'):
        janela = JANELA_FATO if rel == 'fato' else JANELA_PAPEL
        if ae and ai and abs(ai - ae) > janela:
            motivos.append(f'o Gemini disse "{rel}", mas a imagem é de {ai} e o fato de {ae}')
            return 'tema', motivos, verificada
        if ae and not ai:
            motivos.append(f'"{rel}" sem ano na imagem: autenticidade não verificada')
            verificada = False
        if rel == 'documento' and not (str(x.get('tipo_img') or '').lower() in TIPOS_PAPEL or PAPEL.search(_texto(x))):
            motivos.append('o Gemini disse "documento", mas o catálogo não mostra papel/jornal')
            return 'tema', motivos, verificada
    elif rel == 'diagrama':
        if str(x.get('tipo_img') or '').lower() not in ('diagrama', 'desenho'):
            motivos.append('o Gemini disse "diagrama", mas o catálogo não marca a imagem como diagrama')
            return 'tema', motivos, verificada
    elif rel in ('pessoa', 'lugar'):
        alvo = _tok(ac.get('quem') if rel == 'pessoa' else ac.get('onde'))
        meta = _tok(' '.join(x.get('pessoas') or []) if rel == 'pessoa' else x.get('lugar')) | _tok(_texto(x))
        if alvo and not (alvo & meta):
            motivos.append(f'o Gemini disse "{rel}", mas o catálogo não identifica "{ac.get("quem") if rel == "pessoa" else ac.get("onde")}"')
            return 'tema', motivos, verificada
    return rel, motivos, verificada


def pontuar(x: dict, c: dict) -> tuple[float, list[str]]:
    """Pontos de uma reserva para a frase c (maior = melhor) e o porquê."""
    from . import acontecimentos as acont
    sb = c.get('sb') or {}
    p, m = 0.0, []
    lig = acont.ligacao(x, c)
    if lig:
        p += 3; m.append(f'mesma {lig} do fato')
    alvo = _tok(sb.get('intencao_visual') or c.get('mostrar') or c.get('busca'))
    comum = alvo & _tok(_texto(x))
    if comum:
        p += min(2.0, 0.7 * len(comum)); m.append('mostra: ' + ', '.join(sorted(comum)[:3]))
    ae, ai = _ano_evento(c), _ano_item(x)
    if ae and ai:
        if abs(ai - ae) <= JANELA_PAPEL:
            p += 1; m.append(f'mesma época ({ai})')
        elif ai > ae + 10:
            p -= 1; m.append(f'imagem posterior ({ai})')
    if str(x.get('fonte') or '').lower().split(':')[0] in FONTES_ARQUIVO or x.get('credito'):
        p += 0.5
    else:
        p -= 1; m.append('sem proveniência')
    amb = acont.ambiente(c)
    contexto = sb.get('proposito') in ('abertura', 'contexto', 'ligacao')
    if x.get('generica') and not amb:                  # em frase de ambiente, imagem genérica de época é o certo
        p -= 1 if contexto else 3                      # em frase de contexto, foto do assunto é contexto honesto
        m.append('genérica')
    lado = min(int(x.get('w') or 0), int(x.get('h') or 0))
    if 0 < lado < MIN_LADO:
        p -= 1.5; m.append(f'resolução baixa ({lado}px)')
    p += (float(x.get('nota') or 5) - 5) * 0.3
    if x.get('video') and amb:
        p += 2; m.append('vídeo de ambiente')
    return round(p, 2), m


# ───────────── a mídia MOSTRA o acontecimento narrado? (Etapa 3, 13/11/2026) ─────────────
# O catálogo marca "genérica" (não é foto específica de um evento/pessoa) — mas para fenômeno natural isso não diz se a
# imagem representa a frase: um polvo REALMENTE camuflado é "genérico" e ainda assim mostra a camuflagem. O critério passa
# a ser o conteúdo: o que a imagem mostra (catálogo, campo "mostra"/título) contém o que a cena precisa deixar visível
# (sb.intencao_visual / mostrar), descontado o assunto do vídeo ("polvo" sozinho não prova nada) e palavras de enquadramento.
ENQUADRAMENTO = {'foto', 'fotog', 'image', 'imagem', 'video', 'close', 'detal', 'plano', 'cena', 'mostr', 'visto', 'vista',
                 'fundo', 'ambie', 'regis', 'exemp', 'tipo', 'parte', 'grand', 'peque', 'muito', 'algun', 'sobre'}


def assunto(v: dict) -> frozenset:
    """Raízes do assunto do vídeo (não provam que a imagem mostra o fato)."""
    from . import editorial
    p = v.get('plano') or {}
    return frozenset(editorial.raizes(p.get('assunto') or v.get('assunto') or ''))


def mostra_o_fato(x: dict, c: dict, excluir=frozenset()) -> tuple[bool, list[str]]:
    """(mostra?, raízes em comum). Compara o que a mídia mostra com o que a cena precisa mostrar — sem IA."""
    from . import editorial
    sb = c.get('sb') or {}
    alvo_txt = sb.get('intencao_visual') or c.get('mostrar') or ''   # o que PRECISA estar visível — a fala cita lugares e nomes que a imagem não precisa provar
    alvo = editorial.raizes(alvo_txt) - set(excluir) - ENQUADRAMENTO
    visto = editorial.raizes(f"{x.get('mostra', '')} {x.get('titulo', '')}") - set(excluir) - ENQUADRAMENTO
    comum = sorted(alvo & visto)
    return bool(comum), comum


def registrar(c: dict, foto: str | None, rel: str | None, motivos: list[str], verificada: bool = True,
              rejeitadas: list[dict] | None = None):
    c['_escolha'] = {'foto': foto, 'relacao': rel, 'motivos': motivos[:4], 'verificada': verificada,
                     'rejeitadas': (rejeitadas or [])[:5]}
