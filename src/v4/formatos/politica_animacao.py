"""E211 — policy shared with the final compositor. A technical pass is not visual approval."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
POLICY=json.loads((ROOT/'motor4/remotion/src/formatos/animation-policy.json').read_text(encoding='utf8'))
LEGACY=POLICY['legacy_mode']

def chave(shot):
    tipo=shot.get('type')
    if tipo=='mechanism':
        return 'mechanism:'+str(shot.get('mechanism') or '')
    if tipo=='scene_graph':
        return 'scene_graph:'+str((shot.get('scene_graph') or {}).get('schema') or '')
    if tipo=='cad_preview':
        return 'cad_preview'
    return None

def avaliar(shots, *, modo=None, privado=False, preview=True):
    """Reject legacy/unknown renderer by default, including manual/cached plans.
    A legacy QA exception is explicit, private and never an editorial candidate.
    """
    rotas=[]; bloqueios=[]
    if modo not in (None, 'EDITORIAL', LEGACY):
        bloqueios.append({'codigo':'A-MODO-INVALIDO','cena':'-','motivo':'modo visual desconhecido'})
    if modo==LEGACY and not (privado and preview):
        bloqueios.append({'codigo':'A-QA-PRIVADO','cena':'-','motivo':'regressão histórica somente privada'})
    for s in shots:
        k=chave(s)
        if k is None:
            continue
        status=POLICY['renderers'].get(k,{}).get('status','DESCONHECIDO')
        rotas.append({'cena':s.get('id'),'renderer':k,'status':status})
        motivo=None
        if status=='DESCONHECIDO':
            motivo='renderer sem registro'
        elif status=='REPROVADO' and not (modo==LEGACY and privado and preview):
            motivo='renderer reprovado; replanejar com mídia real ou nova representação validável'
        elif status in ('LABORATORIO','CANDIDATO') and not (privado and preview):
            motivo='animação não homologada, somente avaliação privada'
        if motivo:
            bloqueios.append({'codigo':'A-ROTA-BLOQUEADA','cena':s.get('id'),'motivo':motivo})
    return {'permitido':not bloqueios,'rotas':rotas,'bloqueios':bloqueios,
            'editorial_homologado':not bloqueios and modo!=LEGACY and all(x['status']=='APROVADO' for x in rotas),
            'aprovacao_humana':'PENDENTE'}

def exigir(shots, **kwargs):
    r=avaliar(shots,**kwargs)
    if not r['permitido']:
        raise ValueError('E211-POLITICA-VISUAL: '+json.dumps(r['bloqueios'],ensure_ascii=False))
    return r

def decidir_complemento(*, midia_adequada: bool, acao: str, lacuna: str,
                         motivo_lacuna: str, renderer: str | None=None):
    """Routing only: caller must inspect media and establish the facts.
    No guessed geometry and no automatic substitution of rejected animation.
    """
    if not isinstance(midia_adequada,bool):
        raise ValueError('E211-MIDIA-NAO-AVALIADA')
    if midia_adequada:
        return 'USAR_MIDIA_REAL'
    if (not isinstance(acao,str) or not acao.strip() or not isinstance(lacuna,str)
            or not lacuna.strip() or motivo_lacuna not in ('BUSCA_SEM_REGISTRO_ADEQUADO','IMPOSSIVEL_FILMAR')):
        return 'PESQUISAR_OU_REPLANEJAR_MIDIA_REAL'
    status=POLICY['renderers'].get(renderer,{}).get('status')
    if status=='APROVADO':
        return 'ANIMACAO_COMPLEMENTAR'
    if status=='CANDIDATO':
        return 'ANIMACAO_COMPLEMENTAR_EM_QA_PRIVADA'
    return 'REPLANEJAR_MIDIA_REAL_OU_DECLARAR_LACUNA'
