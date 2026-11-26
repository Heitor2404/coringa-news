"""E308: bounded editorial alternative search within the E247 run.
A reviewed photograph remains a valid fallback; no new factual scope or rights.
"""
from copy import deepcopy
from . import revisao_documental as R
from .direcao_short_e306 import tarefas_replanejamento

def tarefas(chosen):
    rows=[{'id':i,'passive_photo':x['kind']=='photo',
           'fatos':x['need']['fatos'],'mostrar':x['need']['mostrar'],
           'preferencia_midia':x['need'].get('preferencia_midia','adequada_ao_fato'),
           'evidencia_visual':x['need'].get('evidencia_visual')}
          for i,x in chosen.items()]
    return tarefas_replanejamento(rows)

def fila_alternativa(need,state,pesquisar,inspecionar,*,pode_buscar,pode_inspecionar,pode_reusar):
    """Resume untried video leads only; do not mutate the historical photo queue."""
    if need.get('preferencia_midia')!='video_preferencial':
        raise ValueError('E308-PREFERENCIA')
    st={'vistos':set(state.get('vistos',set())),
        'buscas_vistas':set(state.get('buscas_vistas',set())),
        'pendentes':deepcopy([c for c in state.get('pendentes',[]) if c.get('tipo')=='video'])}
    def search(n,limit,attempted):
        r=pesquisar(n,limit,attempted)
        return {**r,'candidatos':[c for c in r['candidatos'] if c.get('tipo')=='video']}
    return R.cobertura_progressiva(need,search,inspecionar,
        pode_buscar=pode_buscar,pode_inspecionar=pode_inspecionar,
        pode_reusar=lambda c:c.get('tipo')=='video' and pode_reusar(c),
        max_buscas=4,max_tentativas=4,estado=st)

def replanejar(report,preparar,buscar_alternativa,finalizar):
    """Use the canonical bridge to compare actual coverage, not lexical scores.
    Caller owns shared search/vision/transport and provisional reservations.
    """
    rows=report['cobertura']
    chosen,gate=preparar(report)
    logs=[]
    for task in tarefas(chosen):
        nid=task['necessidade_id']
        if task['acao']!='REVISAR_ALTERNATIVA_REAL_MAIS_EXPLICATIVA':
            logs.append({**task,'estado':'REVISAO_EXPLICATIVA_PENDENTE'});continue
        index=next(i for i,r in enumerate(rows) if r['necessidade_id']==nid)
        old=rows[index]
        need=chosen[nid]['need']
        alternative=buscar_alternativa(need)
        accept=False
        status='SEM_ALTERNATIVA_REVISADA'
        try:
            if alternative and alternative.get('estado')=='CANDIDATO_PRIVADO_REVISADO':
                replacement={**alternative,'necessidade_id':nid,'fatos':need['fatos']}
                trial=rows.copy();trial[index]=replacement
                next_chosen,next_gate=preparar({**report,'cobertura':trial})
                # Never sacrifice existing valid coverage or a feasible >=60s plan.
                accept=(nid in next_chosen and next_chosen[nid]['kind']=='video'
                        and set(chosen)<=set(next_chosen)
                        and (next_gate['capacidade_s']+1e-6>=min(gate['capacidade_s'],60))
                        and (not gate['pronto_para_tts'] or next_gate['pronto_para_tts']))
                status='VIDEO_REVISADO_SUBSTITUI_FOTO' if accept else 'ALTERNATIVA_INCOMPATIVEL_COM_FILME'
                if accept:
                    rows[index]=replacement
                    chosen,gate=next_chosen,next_gate
        finally:
            finalizar(accept)
        logs.append({**task,'estado':status,'reserva_foto':old.get('selecionado'),
                     'alternativa':alternative,'publicar':False,'aprovacao_editorial':False})
    return logs
