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
          'representacao', 'tipo_original', 'reclassificacao', 'partes',
          # V2.4: o que precisa ser visto pode ser fotografado? (declarado pelo roteirista; ver observabilidade())
          'observavel', 'funcao_visual', 'reparo')


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


# ═════════════════════════ V2.4 — pré-validação dos contratos visuais (piloto da lagartixa) ═════════════════════════
# Nas duas execuções do piloto (43643345166, 43646047814) o roteirista declarou mecanismos SEM os dados que a composição
# exige (proporção com etapas; mecanismo com `{}`; nível com 2 etapas) e o problema só aparecia no preparo, depois de
# pesquisa + acervo + roteiro (~460 s). Aqui o contrato é conferido LOGO DEPOIS do roteiro, com a mesma tabela TIPOS
# que o motor usa — uma fonte só para o prompt, a pré-validação e o preparo.

# FUNÇÃO VISUAL — o que a tela faz pelo acontecimento. Ilustração EXPLICA e nunca é evidência de nada.
#   evidencia  foto/vídeo real que registra o que é narrado (só ela pode chegar a PROVA na Evidência V1)
#   ilustracao esquema didático de um mecanismo/processo (forças, moléculas, etapas); dados rastreados na pesquisa
#   dado       número, gráfico, mapa, linha do tempo, citação: composição com dado verificado
FUNCAO_COMP = {
    'diagrama.explicativo': 'ilustracao', 'processo.etapas': 'ilustracao', 'forcas.vetores': 'ilustracao',
    'mecanismo.eclusa': 'ilustracao', 'mecanismo.nivel': 'ilustracao', 'animacao.quadros': 'ilustracao',
    'astronomia.orbita': 'ilustracao', 'evento.impacto': 'ilustracao',
    'comparacao.antes_depois': 'evidencia', 'foto.historica': 'evidencia', 'video.documental': 'evidencia',
    'foto.documental': 'evidencia',
}


def funcao_comp(comp: str | None) -> str | None:
    if not comp:
        return None
    return FUNCAO_COMP.get(comp, 'dado')


# OBSERVABILIDADE — o elemento que precisa aparecer existe numa escala que a câmera registra? Lista de ESCALA FÍSICA
# (partículas, forças, campos), igual para qualquer tema; nunca vocabulário de um assunto. O que o roteirista declara
# (`observavel`) vale primeiro. "Microscópico" NÃO entra: micrografia é registro real (evidência).
INVISIVEL = re.compile(r'\b(molecul\w*|atomo\w*|atomic\w*|eletron\w*|eletric\w* estatic\w*|ion|ions|ionic\w*|dipol\w*|quantic\w*|'
                       r'proton\w*|neutron\w*|nuclear|nucleo atomico|forca\w*|campo (?:magnetic|eletric|gravitac)\w*|gravidade|'
                       r'energia|ligac\w* quimic\w*|carga\w* eletric\w*|van der waals|nanometr\w*|radiac\w*|eletromagnet\w*)\b')


def _sem_acento(s) -> str:
    import unicodedata
    s = unicodedata.normalize('NFKD', str(s or '').lower())
    return ''.join(c for c in s if not unicodedata.combining(c))


def observabilidade(ac: dict) -> str:
    """'sim' | 'nao' | 'parcial'. 'nao': o próprio sujeito é invisível à câmera (força, moléculas, elétrons).
    'parcial': o sujeito é visível (a pata, as cerdas), mas a ação narrada acontece em escala invisível ("criam forças
    de Van der Waals") — a foto pode mostrar a estrutura, nunca o mecanismo. Declarado pelo roteirista vale primeiro."""
    dec = ac.get('observavel')
    if isinstance(dec, bool):
        return 'sim' if dec else 'nao'
    if isinstance(dec, str) and _n(dec) in ('sim', 'true', 'nao', 'false', 'parcial'):
        return {'true': 'sim', 'false': 'nao'}.get(_n(dec), _n(dec))
    sujeito = _sem_acento(ac.get('sujeito') or ac.get('quem') or '')
    if INVISIVEL.search(sujeito):
        return 'nao'
    acao = _sem_acento(' '.join(str(ac.get(k) or '') for k in ('acao', 'estado_inicial', 'estado_final', 'mostrar')))
    if INVISIVEL.search(acao) and ac.get("tipo") in MECANISMOS:
        return 'parcial'
    return 'sim'


MECANISMOS = {"mecanismo", "processo", "transformacao", "movimento", "nivel", "orbita"}
DINAMICOS = {'nivel', 'movimento'}             # descrevem mudança: 2 etapas textuais já são uma sequência (antes → depois)
FOTO_PODE = {'impacto', 'deslocamento', 'movimento', 'mecanismo', 'transformacao', 'processo', 'evento_historico', 'localizacao',
             'pessoa', 'lugar', 'ambiente', 'documento', 'territorio'}      # mesmo conjunto do preparo
SINONIMOS_DADOS = {'passos': 'etapas', 'fases': 'etapas', 'estagios': 'etapas', 'sequencia': 'etapas', 'etapa': 'etapas',
                   'elementos': 'nos', 'partes': 'nos', 'vetores': 'forcas', 'forca': 'forcas'}


def _ctx(ac: dict) -> str:
    return _sem_acento(' '.join(str(ac.get(k) or '') for k in ('acao', 'mostrar')))


def viaveis(tipo: str, dados: dict, ac: dict | None = None) -> list[str]:
    """Composições do tipo cujos requisitos os dados satisfazem (genéricas e foto ficam de fora)."""
    from src.v2 import capacidades
    out = []
    for comp, reqs in (TIPOS.get(tipo) or {}).get('comps', {}).items():
        if comp in GENERICAS:
            continue
        if all(capacidades._tem(r, dados or {}, _ctx(ac or {})) for r in reqs):
            out.append(comp)
    return out


def requisitos_texto(tipo: str) -> str:
    comps = [(c, r) for c, r in (TIPOS.get(tipo) or {}).get('comps', {}).items() if c not in GENERICAS]
    return ' | '.join(f"{c} → {', '.join(r) or 'sem dados'}" for c, r in comps) or 'foto/vídeo real'


def validar(ac: dict) -> dict:
    """Confere UM contrato contra a tabela TIPOS (sem IA, sem rede). Devolve
    {estado: ok|foto|invalido, critico, observavel, viaveis, faltam, problema, precisa_reparo}.
      ok       há composição viável com os dados declarados
      foto     sem composição, mas o tipo se mostra com foto real e o elemento é observável (o preparo decide no acervo)
      invalido sem composição e foto não serve (tipo abstrato, ou fenômeno não observável)"""
    tipo = ac.get('tipo')
    dados = ac.get('dados') or {}
    obs = observabilidade(ac)
    crit = critico(ac) if tipo in TIPOS or tipo == 'desconhecido' else True
    out = {'id': ac.get('id'), 'tipo': tipo, 'critico': crit, 'observavel': obs, 'viaveis': [], 'faltam': {}, 'problema': None}
    if tipo not in TIPOS:
        out.update(estado='invalido', problema=f'tipo desconhecido ({ac.get("tipo_pedido")!r})', precisa_reparo=crit)
        return out
    from src.v2 import capacidades
    out['viaveis'] = viaveis(tipo, dados, ac)
    out['faltam'] = {c: [r for r in reqs if not capacidades._tem(r, dados, _ctx(ac))]
                     for c, reqs in TIPOS[tipo]['comps'].items() if c not in GENERICAS}
    if out['viaveis']:
        out['estado'] = 'ok'
    elif tipo in FOTO_PODE and obs == 'sim':
        out['estado'] = 'foto'
    else:
        out['estado'] = 'invalido'
    if out['estado'] != 'ok':
        out['problema'] = ('sem dados' if not dados else
                           f"dados ({', '.join(sorted(dados))}) não servem a nenhuma composição de \"{tipo}\"")
        if obs != 'sim':
            out['problema'] += f'; fenômeno {"não observável" if obs == "nao" else "em escala não observável"}: só ILUSTRAÇÃO com dados'
    # conserto só para o que o preparo BLOQUEARIA com certeza: crítico sem composição e sem foto possível. Mecanismo
    # observável (a pata, a engrenagem) fica para o acervo: uma foto real dele é evidência e vale mais que um esquema.
    out['precisa_reparo'] = bool(crit and out['estado'] == 'invalido')
    return out


def normalizar_dados(ac: dict) -> tuple[dict, list[str]]:
    """Correções DETERMINÍSTICAS, sem inventar nada: nome de campo sinônimo (passos → etapas) e tipo dinâmico (nível,
    movimento) cujos dados são só uma sequência textual de ≥ 2 etapas → processo. Devolve (contrato, motivos)."""
    ac = dict(ac); dados = dict(ac.get('dados') or {}); motivos = []
    for k in list(dados):
        alvo = SINONIMOS_DADOS.get(_n(k))
        if alvo and alvo not in dados and isinstance(dados[k], list):
            dados[alvo] = dados.pop(k); motivos.append(f'campo "{k}" é "{alvo}"')
    ac['dados'] = dados
    tipo = ac.get('tipo')
    etapas = [str(e).strip() for e in dados.get('etapas') or [] if isinstance(e, str) and str(e).strip()
              and not re.fullmatch(r'[\d.,%\s]+', str(e))]
    if tipo in DINAMICOS and not viaveis(tipo, dados, ac) and len(set(etapas)) >= 2 \
            and not any(k in dados for k in ('de', 'ate', 'sentido', 'forcas', 'cena')):
        ac['tipo_original'], ac['tipo'] = tipo, 'processo'
        ac['reclassificacao'] = f'"{tipo}" só com {len(set(etapas))} etapas textuais (sem de/até/sentido): é a sequência de um processo'
        motivos.append(ac['reclassificacao'])
    return ac, motivos


def bloco_prompt() -> str:
    """BLOCO_PROMPT da V2.4 (só com MOTOR_VISUAL=v2): o mesmo contrato, com os dados EXIGIDOS por tipo gerados da tabela
    TIPOS (antes o roteirista não sabia, p.ex., que "nivel" exige de/até ou sentido) e o campo `observavel`."""
    linhas = '\n'.join(f'  {t}: {requisitos_texto(t)}' for t in TIPOS)
    return BLOCO_PROMPT + f"""
DADOS EXIGIDOS POR TIPO (composição → campos de "dados"; "etapas>=2" = lista com pelo menos 2 etapas):
{linhas}
Regras: (1) declare o tipo cujos dados os FATOS têm — se a fala descreve uma sequência (perto → longe, antes → depois),
o tipo é "processo" com "etapas"; (2) cada etapa/nó/força usa palavras de uma linha dos FATOS, sem acrescentar nada;
(3) "observavel": false quando o que precisa ser visto não pode ser fotografado (moléculas, átomos, elétrons, forças,
campos, cargas): a cena será uma ILUSTRAÇÃO explicativa, que precisa de "dados"; uma foto nunca mostra isso;
(4) se for crítico e os FATOS não tiverem os dados, deixe "dados" vazio (o sistema barra) — não invente;
(5) precisão: grandeza que DIMINUI com a distância ou o tempo (força, atração, sinal) "enfraquece rapidamente" — não diga
que "some"/"desaparece" se os FATOS não disserem que ela chega a zero.
"""
