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

import json
import re

# tipo → (crítico?, composições capazes em ordem de preferência, dados exigidos por composição)
TIPOS: dict[str, dict] = {
    'mecanismo':          {'critico': True,  'comps': {'mecanismo.estados': ['esquema'], 'diagrama.explicativo': ['nos'], 'processo.etapas': ['etapas>=2'], 'forcas.vetores': ['forcas'], 'mecanismo.eclusa': ['sentido']}},
    'transformacao':      {'critico': True,  'comps': {'mecanismo.estados': ['esquema'], 'comparacao.antes_depois': ['img_antes', 'img_depois'], 'processo.etapas': ['etapas>=2']}},
    # V2.5: movimento NÃO é nível (velocidade de 22 nós virava "caixa d'água a 22 m"): nível só para nível/altura de líquido
    'movimento':          {'critico': True,  'comps': {'forcas.vetores': ['forcas'], 'animacao.quadros': ['cena']}},
    'nivel':              {'critico': True,  'comps': {'mecanismo.eclusa': ['sentido'], 'mecanismo.nivel': ['de', 'ate']}},
    'deslocamento':       {'critico': True,  'comps': {'mapa.rota': ['pontos>=2']}},
    'processo':           {'critico': True,  'comps': {'mecanismo.estados': ['esquema'], 'processo.etapas': ['etapas>=2'], 'diagrama.explicativo': ['nos']}},
    'evolucao_temporal':  {'critico': False, 'comps': {'grafico.temporal': ['serie>=4']}},
    'impacto':            {'critico': True,  'comps': {'evento.impacto': ['aneis']}},
    'orbita':             {'critico': True,  'comps': {'astronomia.orbita': []}},
    'escala':             {'critico': True,  'comps': {'comparacao.grandezas': ['itens>=2']}},
    'comparacao':         {'critico': False, 'comps': {'grafico.barras': ['itens>=2'], 'comparacao.grandezas': ['itens>=2']}},
    'proporcao':          {'critico': False, 'comps': {'proporcao': ['pct']}},
    'numero':             {'critico': False, 'comps': {'numero.animado': ['valor', 'fonte']}},
    'sequencia_historica': {'critico': False, 'comps': {'linha_tempo.historica': ['eventos>=2']}},
    'evento_historico':   {'critico': True,  'comps': {'foto.historica': ['img'], 'video.documental': ['video'], 'linha_tempo.historica': ['eventos>=2'],
                                                     'fonte.evidencia': ['veiculo', 'trecho']}},   # V2.5: DOCUMENTAÇÃO do fato
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
          'observavel', 'funcao_visual', 'reparo',
          # V2.4: plano visual direcionado aceito (src/v2/planejamento.py) — foto genérica como ILUSTRAÇÃO identificada
          'plano_visual')


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
    'mecanismo.estados': 'ilustracao', 'diagrama.explicativo': 'ilustracao', 'processo.etapas': 'ilustracao', 'forcas.vetores': 'ilustracao',
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
    # V2.5 (piloto céu azul): o roteirista escreveu o NOME da composição como caminho ("numero.animado" →
    # {"numero": {"animado": {...}}}); o conteúdo é o mesmo — achata, sem acrescentar nada
    for comp in list((TIPOS.get(ac.get('tipo')) or {}).get('comps', {})):
        a_, _, b_ = comp.partition('.')
        if isinstance(dados.get(a_), dict) and isinstance(dados[a_].get(b_), dict) and len(dados) == 1:
            dados = dict(dados[a_][b_]); motivos.append(f'dados aninhados como "{comp}" achatados')
            break
    ac['dados'] = dados
    tipo = ac.get('tipo')
    # V2.5 (piloto Pisa): "escala"/"comparação" com UM item numérico é um número (não há o que comparar)
    its = dados.get('itens') if isinstance(dados.get('itens'), list) else None
    if tipo in ('escala', 'comparacao') and its and len(its) == 1 and isinstance(its[0], dict) and str(its[0].get('valor', '')).strip():
        ac['tipo_original'], ac['tipo'] = tipo, 'numero'
        dados = {'valor': its[0]['valor'], 'rotulo': its[0].get('rotulo') or its[0].get('nome') or '', **({'fonte': ac['fonte']} if ac.get('fonte') else {})}
        ac['dados'] = dados; tipo = 'numero'
        motivos.append('comparação com um só item é um número')
    # V2.5 (piloto Titanic): "pessoa" com o nome no sujeito/quem e "dados" vazio — o nome JÁ está no contrato; copiá-lo
    # para dados.nome não inventa nada (a identificação na tela usa a foto real; sem foto continua barrado)
    if tipo == 'pessoa' and not str(dados.get('nome') or '').strip():
        nome = str(ac.get('sujeito') or ac.get('quem') or '').strip()
        if nome and len(nome) <= 40 and nome[:1].isupper():
            dados['nome'] = nome; motivos.append(f'nome da pessoa vem do sujeito ("{nome}")')
    etapas = [str(e).strip() for e in dados.get('etapas') or [] if isinstance(e, str) and str(e).strip()
              and not re.fullmatch(r'[\d.,%\s]+', str(e))]
    if tipo in DINAMICOS and not viaveis(tipo, dados, ac) and len(set(etapas)) >= 2 \
            and not any(k in dados for k in ('de', 'ate', 'sentido', 'forcas', 'cena')):
        ac['tipo_original'], ac['tipo'] = tipo, 'processo'
        ac['reclassificacao'] = f'"{tipo}" só com {len(set(etapas))} etapas textuais (sem de/até/sentido): é a sequência de um processo'
        motivos.append(ac['reclassificacao'])
    return ac, motivos


FORMATO_CAMPOS = """FORMATO DE CADA CAMPO (o que não estiver neste formato é recusado e a cena é barrada):
  esquema (mecanismo/processo/transformação que a câmera não vê — moléculas, luz, forças, órgãos, peças internas):
    {"objetos": [{"id": "a", "forma": "superficie|corpo|cerdas|ramos|particulas|seta", "rotulo": "PALAVRA DA FALA",
                  "x": 0-1, "y": 0-1, "w": 0-1, "h": 0-1}],          ← 2 a 7 objetos, x/y = centro na área do desenho
     "estados": [{"rotulo": "INÍCIO EM POUCAS PALAVRAS", "objetos": {"a": {"dx": 0, "dy": -0.3, "escala": 1.2, "rot": 0, "opacidade": 1}},
                  "relacoes": [{"de": "a", "para": "b", "tipo": "atracao|repulsao|contato|empurra", "forca": 0-1, "rotulo": "≤ 16"}]}]}
    ← 2 a 4 estados DIFERENTES (algo se move, aparece, cresce ou passa a se relacionar); rótulos com as palavras da fala.
    Exemplo (vulcão): objetos CROSTA (superficie, y 0.3) e MAGMA (corpo, y 0.8); estado 1 "MAGMA ACUMULA";
    estado 2 "PRESSÃO EMPURRA A CROSTA" com MAGMA dy -0.3 e relação MAGMA→CROSTA "empurra" rotulo "PRESSÃO".
  forcas: [{"nome": "Peso", "angulo": -90, "intensidade": 0-1}]  (ângulo em graus, 90 = para cima; nome de força física)
  itens: [{"rotulo": "Brasil", "valor": 3.7}] (número de verdade)   serie: [[1950, 2.5], [1970, 3.7], …] (≥ 4 pontos)
  eventos: [{"ano": 1904, "texto": "≤ 46"}]   pontos: [{"nome": "...", "lon": -79.5, "lat": 9.0}]
  valor: número (sem texto) + "fonte"   pct: número 0–100   de/ate: números   aneis: [{"raio_km": 30, "rotulo": "..."}]
  nos/etapas: rótulos CURTOS (≤ 24 letras); frase inteira não é etapa
Se os FATOS não têm o número/valor/coordenada, NÃO declare tipo numérico: use o tipo que os FATOS sustentam ou deixe vazio.
COMO CADA ACONTECIMENTO CRÍTICO SERÁ MOSTRADO (escolha ANTES de escrever a fala; sem um destes, não escreva o acontecimento):
  REGISTRO DIRETO — foto/vídeo do ACERVO que é do próprio fato (identidade e época compatíveis): cite o id em "foto";
  DOCUMENTO — trecho de fonte da pesquisa (tipo "documento" ou "evento_historico" com dados {"veiculo", "trecho"});
  CONTEXTO — foto real do ACERVO da pessoa/lugar/objeto do fato; a tela dirá que NÃO é o instante narrado;
  EXPLICAÇÃO — mapa, cronologia, dado ou esquema com dados da pesquisa;
  RECONSTRUÇÃO — só identificada como tal, sem detalhes inventados (posição, diálogo, movimento).
Fato sem fonte na pesquisa não entra (nem como ilustração). Não afirme que uma foto mostra uma ação que ela não mostra."""


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
""" + FORMATO_CAMPOS + "\n"


# ═════════════════════════ V2.4 — composição que DEMONSTRA × composição que só ESCREVE ═════════════════════════
# Auditoria do MP4 43730252500 (2/10): processo.etapas, diagrama.explicativo e forcas.vetores receberam frases do
# contrato e viraram cartões com números e ícones genéricos. Para um mecanismo CRÍTICO, só conta como representação
# a composição que mostra objetos, estado inicial, mudança, relação e resultado.
DEMONSTRATIVAS = {'mecanismo.estados', 'mecanismo.eclusa', 'mecanismo.nivel', 'astronomia.orbita', 'evento.impacto',
                  'comparacao.antes_depois', 'animacao.quadros', 'forcas.vetores'}
TEXTUAIS = {'processo.etapas', 'diagrama.explicativo'}
EXIGE_DEMONSTRACAO = {'mecanismo'}   # 'como funciona' crítico: cartão de texto/ícones não representa
FORMAS_ESQUEMA = {'superficie', 'corpo', 'cerdas', 'ramos', 'particulas', 'seta'}
RELACOES_ESQUEMA = {'atracao', 'repulsao', 'contato', 'empurra'}


def esquema_problemas(esq) -> list[str]:
    """Confere o esquema de mecanismo.estados: objetos identificados, ≥ 2 estados DIFERENTES, relações entre objetos
    existentes. Lista vazia = representável. (Geometria certa não prova semântica: a prévia renderizada confere o
    resto — src/v2/previa.py.)"""
    if not isinstance(esq, dict):
        return ['esquema ausente']
    ob = [o for o in esq.get('objetos') or [] if isinstance(o, dict)]
    es = [e for e in esq.get('estados') or [] if isinstance(e, dict)]
    p = []
    ids = [o.get('id') for o in ob]
    if not 2 <= len(ob) <= 7:
        p.append(f'{len(ob)} objeto(s) (2–7)')
    if len(set(ids)) != len(ids) or not all(ids):
        p.append('objetos sem id único')
    for o in ob:
        if o.get('forma') not in FORMAS_ESQUEMA:
            p.append(f"forma desconhecida: {o.get('forma')!r}")
    if not any(str(o.get('rotulo') or '').strip() for o in ob):
        p.append('nenhum objeto identificado (rótulo)')
    if not 2 <= len(es) <= 4:
        p.append(f'{len(es)} estado(s) (2–4)')
    if any(not str(e.get('rotulo') or '').strip() for e in es):
        p.append('estado sem rótulo')
    for e in es:
        for oid in (e.get('objetos') or {}):
            if oid not in ids:
                p.append(f'estado cita objeto inexistente: {oid}')
        for r in e.get('relacoes') or []:
            if r.get('de') not in ids or r.get('para') not in ids:
                p.append(f"relação entre objetos inexistentes: {r.get('de')} → {r.get('para')}")
            if (r.get('tipo') or 'atracao') not in RELACOES_ESQUEMA:
                p.append(f"relação desconhecida: {r.get('tipo')!r}")

    def assinatura(e):
        return (json.dumps(e.get('objetos') or {}, sort_keys=True), json.dumps(sorted((r.get('de'), r.get('para'), r.get('tipo'), r.get('forca'), r.get('n'))
                                                                                    for r in e.get('relacoes') or []), default=str))
    if len(es) >= 2 and len({assinatura(e) for e in es}) < len(es):
        p.append('estados iguais: nada muda na tela')
    return p


def demonstra(comp: str | None) -> bool:
    return comp in DEMONSTRATIVAS


def estruturado(comp: str, dados: dict) -> bool:
    """Diagrama/etapas com RÓTULOS (nó/etapa que cabe como título: ≤ 24 caracteres, ou etapa com título e texto) —
    não frases inteiras do contrato despejadas na composição (a causa do 2/10 do MP4 43730252500: "deslocamento
    temporário da nuvem eletrônica em uma molécula" virou nó com ícone genérico)."""
    d = dados or {}
    rot = lambda x: str((x.get('rotulo') or x.get('nome') or '') if isinstance(x, dict) else x or '').strip()
    if comp == 'diagrama.explicativo':
        nos = d.get('nos') or []
        return len(nos) >= 2 and all(0 < len(rot(n)) <= 24 for n in nos)
    if comp == 'processo.etapas':
        et = d.get('etapas') or []
        ok = lambda e: (isinstance(e, dict) and 0 < len(str(e.get('titulo') or '').strip()) <= 24 and str(e.get('texto') or '').strip()) \
            or (not isinstance(e, dict) and 0 < len(rot(e)) <= 24)
        return len(et) >= 2 and all(ok(e) for e in et)
    return True


def comp_aceita(ac: dict, comp: str, dados: dict | None = None) -> bool:
    """Mecanismo CRÍTICO não é representado por composição que só escreve frases soltas (etapas/nós montados a partir
    de strings do contrato). Diagrama/etapas autorados continuam valendo; mecanismo.estados vem primeiro."""
    if comp in TEXTUAIS and ac.get('tipo') in EXIGE_DEMONSTRACAO and critico(ac):
        return estruturado(comp, ac.get('dados') if dados is None else dados)
    return True


# V2.5: O QUE VAI PARA A TELA — uma definição só para montagem, prévia e cobertura (antes cada uma montava a sua)
COM_TITULO = {'mecanismo.estados', 'forcas.vetores', 'diagrama.explicativo', 'processo.etapas', 'mecanismo.nivel', 'evento.impacto',
              'astronomia.orbita', 'comparacao.grandezas', 'grafico.barras', 'grafico.temporal', 'linha_tempo.historica', 'mapa.rota'}


UNIDADES_TEXTO = re.compile(r'^(km²|km2|km/h|km|metros?|m²|m³/s|m³|m|cm|mm|quil[ôo]metros?(\s+por\s+hora)?|cent[íi]metros?|graus(\s+celsius)?|°c|'
                            r'toneladas?|t|kg|quilos?|litros?|anos?|dias?|horas?|minutos?|segundos?|pessoas|habitantes|mortos|v[íi]timas|'
                            r'turistas|visitantes|casas|navios|degraus|andares|esp[ée]cies|%)\b', re.I)


def unidade_no_texto(valor, textos) -> str:
    """V2.5: a unidade de um número declarado sem unidade vem do PRÓPRIO texto que o sustenta ("33 km" → km); nunca inventada."""
    from src.v2 import cobertura as _cob
    try:
        alvo = float(valor)
    except (TypeError, ValueError):
        return ''
    for t in textos or []:
        t = str(t or '')
        for m in re.finditer(r'\d[\d.,]*(\s+(milh[õo]es|bilh[õo]es|mil)\b)?', t):
            vs = [n for n, _ in _cob.valores(m.group(0))]
            if vs and abs(vs[0] - alvo) <= 1e-9 * max(1.0, abs(alvo)):
                u = UNIDADES_TEXTO.match(t[m.end():].lstrip(' de').strip())
                if u:
                    return u.group(0)
        # número por extenso ("trinta e três quilômetros"): a unidade escrita logo depois, e o número imediatamente antes dela
        for u in re.finditer(r'\b[a-zA-Zçãõâáàéêíóôú²³/%°]+\b', t):
            if not UNIDADES_TEXTO.fullmatch(u.group(0)) or re.search(r'\d', t[max(0, u.start() - 50):u.start()]):
                continue
            antes = re.sub(r'\s+de\s*$', ' ', t[max(0, u.start() - 50):u.start()])
            vs = _cob.valores(antes)
            if vs and abs(vs[-1][0] - alvo) <= 1e-9 * max(1.0, abs(alvo)) and re.search(r'\w+\s*$', antes):
                return u.group(0)
    return ''


def params_tela(ac: dict, comp: str, dados: dict | None = None, textos: list | None = None) -> dict:
    """Dados do contrato + título da cena (o "mostrar" do roteiro, ≤ 36) quando a composição tem título e o contrato não
    trouxe um: o sujeito precisa estar ESCRITO na tela (auditoria: forças sobre uma caixa sem dizer que era o avião)."""
    p = dict(ac.get('dados') or {} if dados is None else dados)
    if comp in COM_TITULO and not str(p.get('titulo') or '').strip():
        t = re.sub(r'\s+', ' ', str(ac.get('mostrar') or ac.get('sujeito') or '')).strip()
        if t:
            t = t[:36].rsplit(' ', 1)[0] if len(t) > 36 else t
            p['titulo'] = re.sub(r'(\s+(e|de|da|do|das|dos|a|o|as|os|em|com|para|por|no|na|nos|nas|ao|à))+$', '', t, flags=re.I)   # nunca termina em conectivo
    if comp == 'numero.animado':
        if str(p.get('unidade') or '').strip().lower() in ('valor', 'numero', 'número', 'quantidade', 'unidade', 'total', 'n'):
            p['unidade'] = ''                     # rótulo genérico do roteirista não é unidade ("1.517 valor")
        if not str(p.get('unidade') or '').strip() and p.get('valor') not in (None, ''):
            p['unidade'] = unidade_no_texto(p.get('valor'), textos)   # "33" sozinho não diz nada; "33 km" da fala/pesquisa diz
        if not str(p.get('rotulo') or '').strip():
            t = re.sub(r'\s+', ' ', str(ac.get('mostrar') or ac.get('sujeito') or '')).strip()
            p['rotulo'] = (t[:32].rsplit(' ', 1)[0] if len(t) > 32 else t).upper()   # número nunca sem dizer O QUE mede
    return p
