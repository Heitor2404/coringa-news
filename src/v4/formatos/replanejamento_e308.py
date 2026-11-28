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
    if need.get('preferencia_midia')!='video_preferencial' and need.get('evidencia_visual')!='movimento':
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
        alternative=None
        accept=False
        error=None
        status='SEM_ALTERNATIVA_REVISADA'
        try:
            alternative=buscar_alternativa(need)
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
        except Exception as exc:
            # Optional editorial improvement cannot invalidate the existing
            # coverage. Keep the error visible for targeted correction.
            status='FALHA_REPLANEJAMENTO_RESERVA_PRESERVADA'
            error=type(exc).__name__+':'+str(exc)[:160]
        finally:
            finalizar(accept)
        logs.append({**task,'estado':status,'reserva_foto':old.get('selecionado'),
                     'cobertura_reserva':old,'alternativa':alternative,'erro':error,
                     'publicar':False,'aprovacao_editorial':False})
    return logs

def reparar_acoes(report,preparar,buscar_alternativa,finalizar):
    """Recover only a selection refused by the bridge for exact action.
    Existing gaps already use the progressive scheduler. Never repeat all
    searches, exceed shared budgets, or sacrifice compatible coverage."""
    # Acquisition-only static cases have no action to repair and need not
    # declare a film chapter plan. Do not call the film bridge for them.
    if not any(n.get('evidencia_visual')=='movimento' for n in report['triagem']):
        return []
    rows=report['cobertura'];chosen,gate=preparar(report);logs=[]
    needs={n['id']:n for n in report['triagem']}
    for task in gate.get('replanejamento_por_fato',[]):
        nid=task['necessidade_id']
        if task['motivo']!='REVISAR_ACAO_ESPECIFICA' or task['evidencia_visual']!='movimento':continue
        index=next((i for i,row in enumerate(rows) if row['necessidade_id']==nid),None)
        if index is None or rows[index].get('estado')!='CANDIDATO_PRIVADO_REVISADO':continue
        old=rows[index];n=needs[nid];accept=False;alternative=None;error=None
        status='ACAO_EXATA_PENDENTE'
        try:
            alternative=buscar_alternativa(n)
            if alternative and alternative.get('estado')=='CANDIDATO_PRIVADO_REVISADO':
                replacement={**alternative,'necessidade_id':nid,'fatos':n['fatos']}
                trial=rows.copy();trial[index]=replacement
                new,new_gate=preparar({**report,'cobertura':trial})
                accept=(nid in new and new[nid]['kind']=='video' and set(chosen)<=set(new)
                        and new_gate['capacidade_s']+1e-6>=gate['capacidade_s']
                        and (not gate['pronto_para_tts'] or new_gate['pronto_para_tts']))
                status='ACAO_REVISADA_COMPATIVEL' if accept else 'ALTERNATIVA_INCOMPATIVEL_COM_FILME'
                if accept:
                    rows[index]=replacement;chosen,gate=new,new_gate
        except Exception as exc:
            error=type(exc).__name__+':'+str(exc)[:160]
            status='FALHA_RECUPERACAO_ACAO'
        finally:
            finalizar(accept)
        logs.append({**task,'estado':status,'cobertura_recusada':old,'alternativa':alternative,
                     'erro':error,'publicar':False,'aprovacao_editorial':False})
    return logs
