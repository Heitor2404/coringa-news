"""STORYBOARD SEMÂNTICO do Coringa Explica (plano-mestre, etapa D — 12/11/2026).

UMA estrutura por cena (`c['sb']`), criada do roteiro (sem chamada nova) e completada pelo pipeline:
  roteiro  → construir(v): narracao, evento, proposito (função do bloco), intencao visual, requisitos, mídia preferida,
             alternativas aceitáveis, fallback e gatilho de rejeição — conforme o MODO do plano editorial;
  acervo   → atualizar_midia(v): o que de fato entrou, nível de evidência (direto / explicativo / contextual /
             ilustrativo / sem_midia), se a mídia EXPLICA a frase e as limitações;
  montagem → registrar_tempos(cenas): span da narração; motivo de movimento e de transição (descritivos; quem decide a
             montagem é a etapa G).
Relação com o TEMA ≠ capacidade de EXPLICAR a frase: foto de Paris contextualiza Paris, mas não mostra uma falsificação;
o retrato de uma pessoa não representa a ação dela. Mídia contextual continua permitida (abertura, ambientação, ligação)
quando registrada como contextual. Ausência de foto NUNCA vira cartão de palavras automaticamente: vira a próxima
alternativa do modo, ou o gatilho "replanejar".
Só registro nesta etapa: não muda escolha de imagem, montagem, fiscal antigo nem publicação.
"""
import re

VERSAO = 1
NIVEIS = ('direto', 'explicativo', 'contextual', 'ilustrativo', 'sem_midia')
INFOGRAFICOS = {'numero', 'cards', 'escala', 'lista', 'mapa', 'linha_tempo', 'comparacao', 'citacao', 'revelacao', 'simulacao'}
CENTRAIS = {'mecanismo', 'evidencia', 'payoff', 'virada', 'comparacao', 'consequencia'}   # sem explicação = problema
CONTEXTUAIS_OK = {'abertura', 'contexto', 'ligacao', 'fechamento'}                      # contexto basta aqui

# mídia preferida por recurso pedido no acontecimento
POR_RECURSO = {'foto': 'foto_do_fato', 'video': 'video_do_fato', 'documento': 'documento', 'jornal': 'documento',
               'retrato': 'retrato', 'lugar': 'foto_do_lugar', 'objeto': 'foto_do_objeto', 'mapa': 'mapa',
               'linha_tempo': 'linha_tempo', 'numero': 'grafico', 'ia': 'ilustracao', 'ambiente': 'video_ambiente'}
POR_TIPO = {'mapa': 'mapa', 'linha_tempo': 'linha_tempo', 'numero': 'grafico', 'comparacao': 'grafico', 'escala': 'grafico',
            'cards': 'grafico', 'lista': 'grafico', 'citacao': 'citacao', 'simulacao': 'diagrama', 'revelacao': 'revelacao'}
# alternativas aceitáveis por MODO (em ordem); "diagrama" = esquema correto desenhado/ilustrado e sinalizado
ALTERNATIVAS = {
    'historico_investigativo': ['foto_do_fato', 'documento', 'foto_do_objeto', 'retrato', 'foto_do_lugar', 'mapa', 'ilustracao'],
    'estudo_de_caso': ['foto_do_fato', 'documento', 'foto_do_objeto', 'retrato', 'foto_do_lugar', 'grafico'],
    'mecanismo': ['diagrama', 'foto_cientifica', 'video_do_fato', 'ilustracao', 'grafico'],
    'comparacao': ['grafico', 'foto_do_objeto', 'foto_cientifica', 'diagrama'],
    'descoberta': ['foto_do_fato', 'documento', 'foto_cientifica', 'retrato', 'diagrama'],
    'curiosidade_factual': ['foto_do_fato', 'foto_do_objeto', 'video_do_fato', 'grafico', 'diagrama'],
    'experimento_mental': ['diagrama', 'ilustracao', 'grafico'],
}
MOVIMENTO = {'retrato': 'aproximar do rosto/assunto', 'foto_do_objeto': 'revelar o detalhe', 'documento': 'dar tempo de ler o trecho',
             'foto_do_lugar': 'percorrer o lugar', 'foto_do_fato': 'mostrar a cena inteira', 'diagrama': 'parado: leitura do esquema',
             'grafico': 'parado: leitura do dado', 'mapa': 'seguir o trajeto', 'linha_tempo': 'parado: leitura das datas'}


def _modo(v: dict) -> str:
    modos = ((v.get('plano') or {}).get('modos') or [])
    return modos[0] if modos and modos[0] in ALTERNATIVAS else 'curiosidade_factual'


def _funcao(c: dict) -> str:
    b = c.get('bloco') if isinstance(c.get('bloco'), dict) else {}
    return str(b.get('funcao') or '').strip().lower()


def _requisitos(c: dict, funcao: str, modo: str) -> list[str]:
    ac = c.get('acontecimento') or {}
    req = []
    if ac.get('quem'):
        req.append('pessoa')
    if ac.get('onde'):
        req.append('lugar')
    if ac.get('quando'):
        req.append('tempo')
    if ac.get('recurso') in ('objeto', 'documento', 'jornal'):
        req.append('objeto')
    if funcao in ('mecanismo',) or modo in ('mecanismo', 'experimento_mental'):
        req.append('processo')
    if funcao in ('virada', 'evidencia', 'consequencia') and ac.get('quem'):
        req.append('acao')                      # o que a pessoa FEZ: o retrato sozinho não mostra
    return list(dict.fromkeys(req)) or ['assunto']


def _preferida(c: dict, funcao: str, modo: str) -> str:
    if c.get('tipo') in POR_TIPO:
        return POR_TIPO[c['tipo']]
    rec = (c.get('acontecimento') or {}).get('recurso') or ''
    if rec in POR_RECURSO:
        return POR_RECURSO[rec]
    if str(c.get('visual') or '').lower().startswith('clima'):
        return 'video_ambiente'
    if modo in ('mecanismo', 'experimento_mental') and funcao in ('mecanismo', 'evidencia', 'payoff', ''):
        return 'diagrama'
    return ALTERNATIVAS[modo][0]


def construir(v: dict) -> dict:
    """Cria c['sb'] em cada cena (os pedaços de uma ideia compartilham o da ideia)."""
    modo = _modo(v)
    por_grupo = {}
    for k, c in enumerate(v.get('cenas', [])):
        if c.get('tipo') == 'fechamento':
            continue
        if c.get('sub') and c.get('grupo') in por_grupo:
            c['sb'] = por_grupo[c['grupo']]
            continue
        funcao = _funcao(c) or ('abertura' if k == 0 else '')
        pref = _preferida(c, funcao, modo)
        alts = [m for m in ALTERNATIVAS[modo] if m != pref]
        b = c.get('bloco') if isinstance(c.get('bloco'), dict) else {}
        central = funcao in CENTRAIS
        sb = {'versao': VERSAO, 'cena': k, 'evento': c.get('evento'), 'narracao': str(c.get('fala_ideia') or c.get('fala') or '').replace('*', ''),
              'span': None, 'proposito': funcao or 'sem_funcao', 'avanca': str(b.get('avanca') or ''),
              'intencao_visual': str(c.get('mostrar') or c.get('busca') or '').strip(),
              'requisitos': _requisitos(c, funcao, modo), 'midia_preferida': pref, 'alternativas': alts[:4],
              'fallback': alts[0] if alts else None,
              'rejeicao': ('replanejar a cena: nenhuma mídia explica o trecho' if central else
                           'aceita contexto rotulado'),
              'composicao': {'foco': 'dado' if pref in ('grafico', 'linha_tempo', 'mapa', 'diagrama') else 'assunto',
                             'hierarquia': ['visual', 'legenda'] if pref not in ('grafico', 'linha_tempo') else ['dado', 'legenda'],
                             'area_segura': 'legenda na faixa de baixo; rótulos acima dela'},
              'movimento': MOVIMENTO.get(pref, 'leve'), 'transicao': None,
              'midia': None, 'evidencia': 'sem_midia', 'explica': False, 'limitacoes': []}
        c['sb'] = sb
        if c.get('grupo') is not None:
            por_grupo[c['grupo']] = sb
    v['storyboard_versao'] = VERSAO
    return v


def _nivel(c: dict, sb: dict) -> tuple[str, list[str]]:
    lim = []
    if c.get('tipo') in INFOGRAFICOS:
        return 'explicativo', lim
    if c.get('ia') or c.get('midia') == 'ia':
        lim.append('ilustração: não é registro real (sinalizar)')
        return 'ilustrativo', lim
    if not (c.get('foto') or c.get('img') or c.get('midia') in ('video', 'vizinha')):
        return 'sem_midia', ['nenhuma mídia para esta frase']
    if c.get('repetida') or c.get('midia') == 'vizinha':
        return 'contextual', ['mídia emprestada da cena vizinha']
    rel = c.get('relacao')
    if rel in ('fato', 'documento'):
        return 'direto', lim
    if rel == 'pessoa' and 'acao' in sb['requisitos']:
        lim.append('retrato: mostra quem, não o que fez')
    elif rel == 'lugar' and 'acao' in sb['requisitos']:
        lim.append('lugar: mostra onde, não o que aconteceu')
    elif rel in ('tema', 'ambiente', None):
        lim.append('foto do tema/ambiente: contextualiza, não demonstra a frase')
    if rel in ('pessoa', 'lugar', 'objeto') and 'acao' not in sb['requisitos'] and 'processo' not in sb['requisitos']:
        return 'direto', lim                    # a frase é SOBRE a pessoa/lugar/objeto: mostrar é mostrar o fato
    return 'contextual', lim


def atualizar_midia(v: dict) -> dict:
    """Depois do casamento e dos planos sem foto: o que entrou e se explica a frase."""
    for c in v.get('cenas', []):
        sb = c.get('sb')
        if not sb or c.get('sub'):
            continue
        nivel, lim = _nivel(c, sb)
        sb['midia'] = c.get('foto') or c.get('midia') or (c['tipo'] if c.get('tipo') in INFOGRAFICOS else None)
        sb['evidencia'], sb['limitacoes'] = nivel, lim
        sb['explica'] = nivel in ('direto', 'explicativo') or (nivel in ('contextual', 'ilustrativo')
                                                                and sb['proposito'] in CONTEXTUAIS_OK)
    return v


_ANO = re.compile(r'\b(1[0-9]{3}|20[0-9]{2})\b')


def registrar_tempos(cenas: list[dict]):
    """Na montagem: span da narração de cada ideia e o motivo da transição (descritivo)."""
    ant = None
    for c in cenas:
        sb = c.get('sb')
        if not sb:
            continue
        if ant is not None and ant.get('sb') is sb:       # pedaço da mesma ideia (o 'sub' também marca reenquadramento
            sb['span'] = (sb['span'][0], round(float(c['end']), 3))     # de foto emprestada: não serve para isso)
            continue
        sb['span'] = (round(float(c['start']), 3), round(float(c['end']), 3))
        if ant is not None:
            a, b = ant.get('acontecimento') or {}, c.get('acontecimento') or {}
            ya, yb = _ANO.search(str(a.get('quando') or '')), _ANO.search(str(b.get('quando') or ''))
            if c.get('evento') and c.get('evento') == ant.get('evento'):
                sb['transicao'] = 'continuidade'
            elif c.get('lugar') or (ya and yb and ya.group(1) != yb.group(1)):
                sb['transicao'] = 'mudanca_de_lugar_ou_tempo'
            elif sb['proposito'] in ('virada', 'comparacao'):
                sb['transicao'] = 'contraste'
            else:
                sb['transicao'] = 'novo_bloco'
        ant = c


def resumo(cenas: list[dict]) -> dict:
    vistos, por = set(), []
    for c in cenas:
        sb = c.get('sb')
        if sb and id(sb) not in vistos:
            vistos.add(id(sb))
            por.append(sb)
    cont = {n: sum(1 for s in por if s['evidencia'] == n) for n in NIVEIS}
    sem = [s['cena'] for s in por if not s['explica'] and s['proposito'] in CENTRAIS]
    return {'cenas': len(por), 'evidencia': cont, 'centrais_sem_explicacao': sem,
            'sem_funcao': sum(1 for s in por if s['proposito'] == 'sem_funcao')}


def linha_telegram(cenas: list[dict]) -> str:
    r = resumo(cenas)
    if not r['cenas']:
        return ''
    e = r['evidencia']
    txt = (f"🗂 Storyboard (só registro): {r['cenas']} cenas · direto {e['direto']} · explicativo {e['explicativo']} · "
           f"contextual {e['contextual']} · ilustrativo {e['ilustrativo']} · sem mídia {e['sem_midia']}")
    if r['centrais_sem_explicacao']:
        txt += f" · ⚠️ {len(r['centrais_sem_explicacao'])} cena(s) central(is) sem mídia que explique (replanejar)"
    return txt
