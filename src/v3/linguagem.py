"""LINGUAGEM VISUAL DO CORINGA EXPLICA — a forma de cada acontecimento é decidida ANTES da câmera (16/11).

Uma identidade só, com técnicas tiradas de quatro referências (sem copiar material, marca, personagem nem projeto):
  gancho e progressão (Zack D. Films) · mapas e composição editorial (Vox Atlas) · mecanismos em 2D/2.5D
  (Primal Space) · inserção explicativa simples quando a foto não mostra o processo (Kurzgesagt — pontual; o canal
  não vira animação vetorial, isso é do NTC).

Formas:
  registro    foto/vídeo real relevante, enquadrado com qualidade
  mapa        localização, rota, propagação, território, comparação geográfica
  esquema     mecanismo, transformação, processo, relação física — ANIMADO (estados que mudam)
  documento   inscrição, carta, foto histórica, gravura ou fonte mostrada inteira e legível (composição editorial)
  comparacao  antes/depois, escalas, estados diferentes
  tipografia  só quando o número ou o texto É a informação principal

Sem IA: a decisão sai do tipo do acontecimento (contrato), das composições viáveis e da natureza da mídia do acervo.
Não há cota de recursos; a forma é justificada pelo que o acontecimento precisa mostrar.
"""
from __future__ import annotations

import re
import unicodedata

FORMAS = {
    'registro': {'nome': 'registro documental', 'comps': {'doc.plano', 'video.documental', 'foto.documental', 'foto.historica', 'foto.sequencia'},
                 'quando': 'pessoa, lugar, ambiente, impacto, acontecimento com registro real'},
    'mapa': {'nome': 'mapa explicativo', 'comps': {'mapa.localizacao', 'mapa.rota', 'mapa.territorio', 'doc.plano'},
             'quando': 'localização, rota, propagação, território, comparação geográfica'},
    'esquema': {'nome': 'esquema animado 2D/2.5D', 'comps': {'mecanismo.estados', 'mecanismo.eclusa', 'mecanismo.nivel', 'doc.eclusa', 'doc.molde',
                                                          'forcas.vetores', 'astronomia.orbita', 'animacao.quadros', 'processo.etapas', 'diagrama.explicativo'},
                'quando': 'mecanismo, transformação, processo, relação física'},
    'documento': {'nome': 'documento editorial', 'comps': {'doc.plano', 'fonte.evidencia', 'citacao', 'foto.historica'},
                  'quando': 'inscrição, carta, gravura, foto histórica ou fonte que precisa ser vista inteira'},
    'comparacao': {'nome': 'comparação visual', 'comps': {'comparacao.antes_depois', 'comparacao.grandezas', 'proporcao', 'grafico.barras'},
                   'quando': 'antes/depois, escalas, estados diferentes'},
    'tipografia': {'nome': 'tipografia/dados', 'comps': {'numero.animado', 'grafico.temporal', 'grafico.barras', 'linha_tempo.historica', 'destaque.palavras'},
                   'quando': 'o número ou o texto é a informação principal'},
}
# tipo de acontecimento (contrato) → forma preferida
FORMA_DO_TIPO = {
    'mecanismo': 'esquema', 'processo': 'esquema', 'movimento': 'esquema', 'nivel': 'esquema', 'orbita': 'esquema',
    'transformacao': 'esquema',
    'deslocamento': 'mapa', 'localizacao': 'mapa', 'territorio': 'mapa',
    'documento': 'documento', 'citacao': 'documento',
    'escala': 'comparacao', 'comparacao': 'comparacao', 'proporcao': 'comparacao',
    'numero': 'tipografia', 'evolucao_temporal': 'tipografia', 'sequencia_historica': 'tipografia',
    'pessoa': 'registro', 'lugar': 'registro', 'ambiente': 'registro', 'impacto': 'registro', 'evento_historico': 'registro',
}
# a forma "esquema" é obrigatória (foto com zoom não substitui) quando a AÇÃO é o essencial do acontecimento
ACAO_ESSENCIAL = {'mecanismo', 'processo', 'transformacao', 'movimento', 'nivel', 'orbita'}

REGRAS = [
    'GANCHO: nos primeiros segundos, o assunto grande na tela (registro forte ou ação em curso); nada de cartão de texto, '
    'nada de começar cheio e terminar pequeno.',
    'PROGRESSÃO: cada plano acrescenta uma informação nova; plano que repete o anterior sai.',
    'FORMA ANTES DA CÂMERA: escolha a forma pelo acontecimento (registro, mapa, esquema, documento, comparação, '
    'tipografia); só depois o enquadramento e o movimento.',
    'CÂMERA: fixa é o padrão. Aproximar só até o objeto principal. Recuar só para REVELAR algo nomeado em "revela", '
    'mantendo o quadro cheio e o objeto principal legível.',
    'MAPA: ensina — lugar, rota ou avanço em etapas, com rótulos legíveis no quadro vertical; mapa inteiro pequeno não ensina.',
    'MECANISMO: estados que mudam (sujeito, estado inicial, ação, resultado) em esquema animado; foto com zoom não explica um processo.',
    'DOCUMENTO: inteiro e legível — composição editorial (visão geral + detalhe ampliado), nunca cartão sobre fundo vazio.',
    'RETENÇÃO pela história, não por efeito: sem zoom, círculo ou transição para disfarçar mídia ruim.',
]

NATUREZAS = ('mapa', 'documento', 'gravura', 'pintura', 'video', 'foto')
_PADROES = [
    ('mapa', r'\b(map|mapa|carte|karte|plan of|plano de|atlas|chart of)\b'),
    ('documento', r'\b(plaque|placa|inscri|letter|carta|manuscri|document|newspaper|jornal|page|pagina|diario|diary|'
                  r'certificate|tratado|treaty|decree|edital|broadside|pamphlet|panfleto|signature|assinatura)\w*'),
    ('gravura', r'\b(engraving|gravura|woodcut|xilogravura|etching|lithograph|litografia|print|illustration|ilustracao|drawing|desenho)\w*'),
    ('pintura', r'\b(painting|pintura|oil on|oleo|fresco|afresco|watercolou?r|aquarela)\w*'),
]


def _sem_acento(s) -> str:
    return unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().lower()


def natureza(midia: dict) -> str:
    """Natureza da mídia do acervo pelo título/descrição (sem IA). Vídeo pela extensão/tipo."""
    if (midia or {}).get('natureza') in NATUREZAS:
        return midia['natureza']
    arq = str((midia or {}).get('arq') or '').lower()
    if (midia or {}).get('tipo') == 'video' or arq.endswith(('.mp4', '.webm', '.mov')):
        return 'video'
    txt = _sem_acento(' '.join(str((midia or {}).get(k) or '') for k in ('titulo', 'desc', 'legenda', 'mostra', 'credito')))
    for nat, rx in _PADROES:
        if re.search(rx, txt):
            return nat
    return 'foto'


def forma_do_evento(evento: dict, naturezas_disponiveis: set[str] | None = None) -> dict:
    """→ {forma, justificativa, comps}. `evento`: {tipo, critico, viaveis}. `naturezas_disponiveis`: das mídias do evento."""
    tipo = evento.get('tipo')
    viav = set(evento.get('viaveis') or [])
    nats = set(naturezas_disponiveis or [])
    forma = FORMA_DO_TIPO.get(tipo, 'registro')
    just = f"tipo '{tipo}' pede {FORMAS[forma]['nome']}"
    if forma == 'esquema' and tipo == 'transformacao' and 'comparacao.antes_depois' in viav:
        forma, just = 'comparacao', "transformação com antes/depois real do mesmo sujeito"
    if forma == 'mapa' and not (viav & FORMAS['mapa']['comps']) and 'mapa' not in nats:
        forma, just = 'registro', f"tipo '{tipo}' pede mapa, mas não há mapa viável nem mapa no acervo: registro do lugar"
    if forma == 'registro' and 'documento' in nats and tipo in ('evento_historico', None):
        just += ' (há documento da época: pode entrar como documento editorial)'
    if forma == 'tipografia' and not (viav & FORMAS['tipografia']['comps']):
        forma, just = 'registro', f"tipo '{tipo}' sem composição de dados viável: registro com o número na fala"
    comps = sorted((viav & FORMAS[forma]['comps']) | ({'doc.plano'} if forma in ('registro', 'documento', 'mapa') else set()))
    if forma == 'mapa' and 'mapa' not in nats:
        comps = [c for c in comps if c != 'doc.plano']
    return {'forma': forma, 'justificativa': just, 'comps': comps,
            'acao_essencial': tipo in ACAO_ESSENCIAL and bool(evento.get('critico'))}


def validar_plano(pl: dict, ev: dict | None, midia: dict | None) -> str | None:
    """Erro de forma do plano (para a correção do storyboard), ou None. Só o que é verificável sem julgamento."""
    if not ev:
        return None
    nat = natureza(midia) if midia else None
    f = forma_do_evento(ev, {nat} if nat else set())
    comp = pl.get('composicao')
    if f['acao_essencial'] and comp == 'doc.plano':
        return (f"{ev['id']} ({ev.get('tipo')}): a ação é o essencial — foto com zoom não substitui a explicação animada; "
                f"use {', '.join(c for c in f['comps'] if c != 'doc.plano') or 'mecanismo.estados'}")
    if f['forma'] == 'mapa' and comp == 'doc.plano' and nat and nat != 'mapa' and not pl.get('justificativa_forma'):
        return f"{ev['id']} pede mapa explicativo; a mídia escolhida é {nat} (justifique em 'justificativa_forma' ou use um mapa)"
    escolhida = pl.get('forma_visual')
    if escolhida and escolhida in FORMAS and comp and comp not in FORMAS[escolhida]['comps']:
        return f"forma '{escolhida}' não usa a composição {comp}"
    if escolhida and escolhida != f['forma'] and not pl.get('justificativa_forma'):
        return f"{ev['id']}: forma '{escolhida}' difere da indicada ('{f['forma']}': {f['justificativa']}) sem 'justificativa_forma'"
    return None


def texto_prompt() -> str:
    return '\n'.join(f'- {r}' for r in REGRAS)
