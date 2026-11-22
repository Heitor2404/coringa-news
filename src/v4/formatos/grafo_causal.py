"""SceneGraph causal v1: atores, relações, precondições, mudanças e foco.

Este módulo usa fichas físicas curadas das capacidades REAIS do catálogo.
Não faz reconhecimento em vídeo, não escolhe física por palavras livres
e não certifica a fidelidade de pixels do renderer. O preflight verifica
ausência ou adulteração do grafo antes de autorizar render de prova privada.
"""
from __future__ import annotations

import json
from pathlib import Path

GRAFOS = json.loads((Path(__file__).with_name('grafo_causal_capacidades.json')).read_text('utf8'))
OPERADORES = frozenset(('emit','reflect','project','expose','translate','open',
                        'close','fill','flow','equalize'))
CAMERAS = frozenset(('show_context','follow_actor','show_connection','show_consequence'))
RELACOES = frozenset(('illuminates','reflects_to','projects_to','rests_on','floats_on',
                      'inside','connected_to','controls','feeds'))
FAMILIAS = frozenset(('optics','semiconductor','hydraulic','vessel'))


class GrafoInvalido(ValueError):
    def __init__(self, codigo: str, motivo: str):
        self.codigo = codigo
        self.motivo = motivo
        super().__init__(codigo + ': ' + motivo)


def _bloquear(code: str, why: str):
    raise GrafoInvalido(code, why)


def _relacao_id(r: dict) -> tuple[str,str,str]:
    return (r['from'],r['type'],r['to'])


def _exigidos_validos(atores, relacoes, ficha):
    roles={x['id'] for x in ficha['atores']}
    exists={_relacao_id(x) for x in ficha['relacoes']}
    if not isinstance(atores,list) or any(not isinstance(a,str) or not a.strip() for a in atores):
        _bloquear('F-GRAFO-REQUISITOS','atores essenciais devem ser uma lista de identificadores')
    if not isinstance(relacoes,list) or any(not isinstance(x,dict)
        or set(x)!={'from','type','to'} or any(not isinstance(v,str) for v in x.values())
        for x in relacoes):
        _bloquear('F-GRAFO-REQUISITOS','relações essenciais devem declarar from,type,to')
    if len(atores)!=len(set(atores)) or len(relacoes)!=len({_relacao_id(x) for x in relacoes}):
        _bloquear('F-GRAFO-REQUISITOS','ator ou relação essencial duplicados')
    missing=sorted(set(atores)-roles)
    if missing:
        _bloquear('F-GRAFO-ATOR-INDISPONIVEL',', '.join(missing))
    missing_rel=sorted({_relacao_id(x) for x in relacoes}-exists)
    if missing_rel:
        _bloquear('F-GRAFO-RELACAO-INDISPONIVEL',str(missing_rel))
    return True


def _validar_ficha(ficha: dict, acoes: tuple[str,...]):
    if not isinstance(ficha,dict):
        _bloquear('F-GRAFO-SEM-FICHA','nenhum modelo físico cadastrado')
    actors=ficha.get('atores')
    relations=ficha.get('relacoes')
    events=ficha.get('eventos')
    initial=ficha.get('estado_inicial')
    if not (isinstance(actors,list) and actors and isinstance(relations,list)
            and relations and isinstance(events,list) and
            isinstance(initial,dict) and initial):
        _bloquear('F-GRAFO-CONTRATO','ficha sem atores, relações, eventos ou estado')
    ids=[]
    for a in actors:
        if not isinstance(a,dict) or set(a)!={'id','tipo','asset_family'} or not all(
            isinstance(v,str) and v.strip() for v in a.values()
        ) or a['asset_family'] not in FAMILIAS:
            _bloquear('F-GRAFO-ATOR','ator não cadastrado')
        ids.append(a['id'])
    if len(ids)!=len(set(ids)):
        _bloquear('F-GRAFO-ATOR','atores duplicados')
    roles=set(ids)
    edge_ids=[]
    for r in relations:
        if not isinstance(r,dict) or set(r)!={'from','type','to'}:
            _bloquear('F-GRAFO-RELACAO','relação malformada')
        edge=_relacao_id(r)
        if edge[0] not in roles or edge[2] not in roles or edge[0]==edge[2] or edge[1] not in RELACOES:
            _bloquear('F-GRAFO-RELACAO','relação com ator inexistente ou operador inválido')
        edge_ids.append(edge)
    if len(set(edge_ids))!=len(edge_ids):
        _bloquear('F-GRAFO-RELACAO','relação duplicada')
    if tuple(e.get('acao') for e in events if isinstance(e,dict)) != acoes or len(events)!=len(acoes):
        _bloquear('F-GRAFO-EVENTO','sequência física divergente do catálogo')
    if not all(isinstance(k,str) and '.' in k and k.split('.',1)[0] in roles
        and isinstance(v,str) and v for k,v in initial.items()):
        _bloquear('F-GRAFO-ESTADO','propriedade inicial inexistente')
    return roles


def montar(capacidade: str, acoes: tuple[str,...], *,
           momentos: tuple[float,...] | None = None,
           atores_essenciais: list | None = None,
           relacoes_essenciais: list | None = None) -> dict:
    """Compila dados estruturados; nunca infere relações a partir de título.

    Saída apresenta CADA mudança real do estado do modelo e seu ator focal.
    Se uma relação/ator essencial não puder ser mostrado, bloqueia imediatamente.
    """
    ficha=GRAFOS.get(capacidade)
    roles=_validar_ficha(ficha,acoes)
    if (atores_essenciais is not None or relacoes_essenciais is not None):
        _exigidos_validos(atores_essenciais or [],relacoes_essenciais or [],ficha)
    if momentos is not None:
        if (not isinstance(momentos,tuple) or len(momentos)!=len(acoes)
                or any(type(v) not in (int,float) or not 0<=v for v in momentos)
                or list(momentos)!=sorted(set(momentos))):
            _bloquear('F-GRAFO-TEMPO','eventos sem sequência temporal estrita')
    state=dict(ficha['estado_inicial'])
    steps=[]
    for i,e in enumerate(ficha['eventos']):
        if (not isinstance(e,dict) or set(e)!={'acao','operador','atores',
               'foco','camera','requer','altera'}
                or e['operador'] not in OPERADORES or e['camera'] not in CAMERAS):
            _bloquear('F-GRAFO-OPERADOR','operador não implementado na gramática')
        subjects=e['atores']; focus=e['foco']
        if (not isinstance(subjects,list) or not subjects or
                not isinstance(focus,list) or not focus or
                any(not isinstance(x,str) or x not in roles for x in subjects+focus)
                or not set(subjects).issubset(focus)):
            _bloquear('F-GRAFO-FOCO','atores essenciais não aparecem no foco da câmera')
        if not any(r['from'] in focus and r['to'] in focus for r in ficha['relacoes']):
            _bloquear('F-GRAFO-FOCO','câmera mostra ator isolado, sem relação causal')
        requires=e['requer']; changes=e['altera']
        if (not isinstance(requires,dict) or not isinstance(changes,dict) or not changes):
            _bloquear('F-GRAFO-ESTADO','etapa sem pré-condição ou consequência')
        for k,v in requires.items():
            if k not in state or state[k]!=v:
                _bloquear('F-GRAFO-PRECONDICAO',
                          f'{capacidade}:{e["acao"]} exige {k}={v}, estado={state.get(k)}')
        before={k:state.get(k) for k in changes}
        for k,v in changes.items():
            if (k not in state or k.split('.',1)[0] not in roles or
                not isinstance(v,str) or not v or state[k]==v):
                _bloquear('F-GRAFO-SEM-MUDANCA',
                          f'{capacidade}:{e["acao"]} não altera propriedade registrada')
        state.update(changes)
        steps.append({
            'acao':e['acao'], 'operador':e['operador'],
            'atores':list(subjects),
            'relacoes_em_foco':[r for r in ficha['relacoes']
                if r['from'] in focus and r['to'] in focus],
            'camera':{'intencao':e['camera'],'alvos':list(focus)},
            'precondicoes':dict(requires),
            'antes':before,'depois':dict(changes),
            'tempo_s':(momentos[i] if momentos is not None else None),
            'prova_por_frames':'PENDENTE',
        })
    return {
        'schema':'coringa-causal-scene-graph-v1',
        'capacidade':capacidade,
        'atores':[dict(x) for x in ficha['atores']],
        'relacoes':[dict(x) for x in ficha['relacoes']],
        'eventos':steps,
        'estado_final':state,
        'origem_geometria':'FICHAS_REVISADAS_MANUALMENTE',
        'integridade_estrutural':'VALIDADA_NAO_COMPROVA_PIXELS',
        'revisao_visual':'PENDENTE',
        'publicar':False,
    }


def verificar_serializado(grafo: object, capacidade: str, acoes: tuple[str,...],
                        momentos: tuple[float,...]) -> None:
    """Não aceitar grafo parcial/forjado: recompila a ficha imutável local."""
    if not isinstance(grafo,dict):
        _bloquear('F-GRAFO-AUSENTE','plano causal obrigatório')
    expected=montar(capacidade,acoes,momentos=momentos)
    if grafo != expected:
        _bloquear('F-GRAFO-DIVERGENTE',
                  'atores, relações, estado ou ordem divergem da capacidade curada')
