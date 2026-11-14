"""CONTRATO DE ACONTECIMENTOS (V2.2) — o roteirista DECLARA o que cada cena precisa mostrar; o motor visual consulta
este contrato ANTES de qualquer padrão textual.

Por quê: na V2.1 o seletor dependia de expressões regulares. No conjunto de reserva, 6 de 16 frases (paráfrases como
"o ferro enferruja", "o sangue leva oxigênio dos pulmões até as células") viraram foto sem aviso. Mais padrões não
resolvem paráfrase; declarar o acontecimento resolve.

Campos de `cena['acontecimento']` (todos opcionais para compatibilidade; os antigos quem/onde/quando/recurso continuam):
  id             identificador estável do acontecimento (cenas que narram o mesmo fato repetem o id)
  tipo           um de TIPOS (abaixo)
  sujeito        objeto ou sujeito ("ferro", "navio", "sangue")
  acao           o que acontece ("oxida", "sobe", "transporta oxigênio")
  estado_inicial / estado_final   para transformações e movimentos
  mostrar        o que precisa aparecer na tela, em uma frase
  dados          parâmetros da composição (etapas, pontos, série, itens, forças…) — só fatos da pesquisa
  capacidade     composição pedida (opcional; precisa ser uma das capazes do tipo)
  fonte          de onde vêm os dados
  importancia    'critica' | 'apoio'
  obrigatoria    True quando a cena não pode ir ao ar sem a representação (padrão: True para tipos críticos)

Regra do motor: acontecimento declarado e crítico/obrigatório SEM composição capaz e com dados → LIMITAÇÃO registrada,
com os dados que faltam. Nunca foto, texto genérico ou diagrama inventado no lugar.
"""
from __future__ import annotations

import re

# tipo → (crítico?, composições capazes em ordem de preferência, dados exigidos por composição)
TIPOS: dict[str, dict] = {
    'mecanismo':          {'critico': True,  'comps': {'diagrama.explicativo': ['nos'], 'processo.etapas': ['etapas>=2'], 'forcas.vetores': ['forcas'], 'mecanismo.eclusa': ['sentido']}},
    'transformacao':      {'critico': True,  'comps': {'comparacao.antes_depois': ['img_antes', 'img_depois'], 'processo.etapas': ['etapas>=2']}},
    'movimento':          {'critico': True,  'comps': {'forcas.vetores': ['forcas'], 'mecanismo.nivel': ['de', 'ate'], 'animacao.quadros': ['cena']}},
    'nivel':              {'critico': True,  'comps': {'mecanismo.eclusa': ['sentido'], 'mecanismo.nivel': ['de', 'ate']}},
    'deslocamento':       {'critico': True,  'comps': {'mapa.rota': ['pontos>=2']}},
    'processo':           {'critico': True,  'comps': {'processo.etapas': ['etapas>=2'], 'diagrama.explicativo': ['nos']}},
    'evolucao_temporal':  {'critico': False, 'comps': {'grafico.temporal': ['serie>=4']}},
    'impacto':            {'critico': True,  'comps': {'evento.impacto': ['aneis']}},
    'orbita':             {'critico': True,  'comps': {'astronomia.orbita': []}},
    'escala':             {'critico': True,  'comps': {'comparacao.grandezas': ['itens>=2']}},
    'comparacao':         {'critico': False, 'comps': {'grafico.barras': ['itens>=2'], 'comparacao.grandezas': ['itens>=2']}},
    'proporcao':          {'critico': False, 'comps': {'proporcao': ['pct']}},
    'numero':             {'critico': False, 'comps': {'numero.animado': ['valor', 'fonte']}},
    'sequencia_historica': {'critico': False, 'comps': {'linha_tempo.historica': ['eventos>=2']}},
    'evento_historico':   {'critico': True,  'comps': {'foto.historica': ['img'], 'video.documental': ['video'], 'linha_tempo.historica': ['eventos>=2']}},
    'localizacao':        {'critico': False, 'comps': {'mapa.localizacao': ['pontos>=1']}},
    'territorio':         {'critico': False, 'comps': {'mapa.territorio': ['pais']}},
    'citacao':            {'critico': False, 'comps': {'citacao': ['texto', 'autor']}},
    'documento':          {'critico': False, 'comps': {'fonte.evidencia': ['veiculo', 'trecho'], 'foto.historica': ['img']}},
    # não são acontecimentos a desenhar: a foto/vídeo real do assunto é a representação certa
    'pessoa':             {'critico': False, 'comps': {'lower_third': ['nome'], 'foto.documental': []}},
    'lugar':              {'critico': False, 'comps': {'video.documental': ['video'], 'foto.documental': []}},
    'ambiente':           {'critico': False, 'comps': {'video.documental': ['video'], 'foto.documental': []}},
}
SINONIMOS = {'transformacao_quimica': 'transformacao', 'reacao': 'transformacao', 'reacao_quimica': 'transformacao',
             'transformacao_biologica': 'transformacao', 'maquina': 'mecanismo', 'trajeto': 'deslocamento', 'rota': 'deslocamento',
             'viagem': 'deslocamento', 'etapas': 'processo', 'explosao': 'impacto', 'erupcao': 'impacto', 'serie': 'evolucao_temporal',
             'linha_tempo': 'sequencia_historica', 'fenomeno_natural': 'impacto', 'mapa': 'localizacao', 'grafico': 'comparacao'}
GENERICAS = {'foto.documental', 'destaque.palavras', 'banner.discreto', 'lower_third', 'foto.sequencia'}   # não desenham acontecimento
CAMPOS = ('id', 'tipo', 'sujeito', 'acao', 'estado_inicial', 'estado_final', 'mostrar', 'dados', 'capacidade', 'fonte', 'importancia', 'obrigatoria', 'sincronia',
          # preenchidos pelo preparo (src/v2/preparo.py), antes da narração
          'representacao', 'tipo_original', 'reclassificacao', 'partes')


def _n(s) -> str:
    import unicodedata
    s = unicodedata.normalize('NFKD', str(s or '').lower())
    return ''.join(c for c in s if not unicodedata.combining(c)).strip().replace(' ', '_').replace('-', '_')


def normalizar(ac: dict | None) -> dict:
    """Mantém só os campos do contrato, com tipos coerentes. Tipo desconhecido fica registrado em `tipo_pedido`
    (o motor trata como acontecimento crítico sem composição — nunca o ignora)."""
    ac = dict(ac or {})
    out = {k: ac[k] for k in CAMPOS if k in ac and ac[k] not in (None, '', [], {})}
    if 'tipo' in out:
        t = _n(out['tipo']); t = SINONIMOS.get(t, t)
        if t in TIPOS:
            out['tipo'] = t
        else:
            out['tipo_pedido'] = str(ac['tipo'])[:40]; out['tipo'] = 'desconhecido'
    if not isinstance(out.get('dados', {}), dict):
        out.pop('dados', None)
    if 'importancia' in out:
        out['importancia'] = 'critica' if _n(out['importancia']) in ('critica', 'critico', 'alta', 'essencial') else 'apoio'
    if 'obrigatoria' in out:
        out['obrigatoria'] = bool(out['obrigatoria']) and str(out['obrigatoria']).lower() not in ('false', 'nao', 'não', '0')
    return out


def declarado(cena: dict) -> dict | None:
    ac = cena.get('acontecimento') if isinstance(cena.get('acontecimento'), dict) else None
    if not ac or not ac.get('tipo'):
        return None
    return normalizar(ac)


def critico(ac: dict) -> bool:
    if ac.get('tipo') == 'desconhecido':
        return True
    if 'obrigatoria' in ac:
        return bool(ac['obrigatoria'])
    if ac.get('importancia') == 'apoio':
        return False
    return TIPOS[ac['tipo']]['critico'] or ac.get('importancia') == 'critica'


def capazes(tipo: str) -> list[str]:
    return list((TIPOS.get(tipo) or {}).get('comps', {}))


def resolver_sincronia(ac: dict, palavras: list[dict], inicio_cena: float) -> dict:
    """`ac['sincronia']` = {parâmetro: [palavras ditas]} → `ac['dados'][parâmetro]` = [{nome, t}] com t = instante (na
    cena) em que a narração começa a dizer cada palavra. Palavra não encontrada fica de fora e é registrada."""
    import unicodedata
    tok = lambda x: re.sub(r'[^a-z0-9]', '', ''.join(c for c in unicodedata.normalize('NFKD', str(x).lower()) if not unicodedata.combining(c)))
    ac = dict(ac); dados = dict(ac.get('dados') or {}); faltou = []
    for chave, alvos in (ac.get('sincronia') or {}).items():
        out = []
        for nome in alvos:
            w = next((w for w in palavras if tok(w['w']).startswith(tok(nome)[:max(4, len(tok(nome)) - 2)])), None)
            if w:
                out.append({'nome': nome, 't': round(w['s'] - inicio_cena, 3)})
            else:
                faltou.append(nome)
        dados[chave] = out
    ac['dados'] = dados
    if faltou:
        ac['sincronia_faltou'] = faltou
    return ac


BLOCO_PROMPT = """
CONTRATO DE ACONTECIMENTOS (obrigatório em toda cena do tipo "historia"/"imagem"): além de quem/onde/quando/recurso,
preencha em "acontecimento":
  "id": o mesmo para cenas que narram o mesmo fato;
  "tipo": um de [mecanismo, transformacao, movimento, nivel, deslocamento, processo, evolucao_temporal, impacto, orbita,
          escala, comparacao, proporcao, numero, sequencia_historica, evento_historico, localizacao, territorio, citacao,
          documento, pessoa, lugar, ambiente];
  "sujeito", "acao", "estado_inicial", "estado_final": o que muda e como (ex.: ferro → ferrugem, por oxidação);
  "mostrar": o que precisa aparecer na tela, numa frase;
  "dados": só o que está nos FATOS, no formato da composição: etapas [..] | pontos [{nome, lon, lat}] | serie [{ano, valor}] |
           itens [{rotulo, valor}] | forcas [{nome, angulo, intensidade}] | eventos [{ano, texto}] | valor + fonte;
  "fonte": de onde vêm os dados; "importancia": "critica" ou "apoio"; "obrigatoria": true se a cena não pode ir ao ar
  sem mostrar o acontecimento; "sincronia": {parâmetro: [palavras da fala]} quando algo na tela deve acontecer no
  instante em que uma palavra é dita (ex.: {"vizinhos": ["Colômbia", "Brasil"]}).
Se o acontecimento não puder ser desenhado com os fatos disponíveis, declare-o mesmo assim (o motor registra a
limitação; não troque por uma foto qualquer).
"""
