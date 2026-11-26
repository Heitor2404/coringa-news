"""E331: exact-action specificity and scoped negative feedback.
No inferred absence, no global ban by source, no new vision request.
"""
import json,math,re
from pathlib import Path
from functools import lru_cache

@lru_cache(maxsize=1)
def registros():
    p=Path(__file__).resolve().parents[3]/'benchmarks/e331/feedback_movimento.json'
    j=json.loads(p.read_text(encoding='utf8'))
    if j.get('schema')!='coringa.motion.feedback.private.v1' or j.get('publish') is not False:
        raise ValueError('E331-REGISTRO')
    for r in j['records']:
        if (r.get('publicar') is not False or r.get('estado')!='REVISAR_ACAO_ESPECIFICA'
            or not all(re.fullmatch('[a-f0-9]{64}',str(r.get(k,''))) for k in ('sha256','review_id'))
            or not isinstance(r.get('mostrar'),str) or not isinstance(r.get('fatos'),list)
            or not r.get('evidencias') or not r.get('observacao')):
            raise ValueError('E331-REGISTRO-ITEM')
    return tuple(j['records'])

def feedback(need,sha,rid,start=None):
    if need.get('evidencia_visual')!='movimento':return None
    for r in registros():
        if (r['sha256']==sha and r['review_id']==rid and r['necessidade_id']==need.get('id')
            and r['mostrar']==need.get('mostrar') and r['fatos']==need.get('fatos')):
            if start is not None and (type(start) not in (int,float) or not math.isfinite(start)
                or abs(start-r['source_in_seconds'])>1e-6):continue
            return {'estado':r['estado'],'observacao':r['observacao'],'evidencias':list(r['evidencias']),'publicar':False}
    return None

def avaliar(resposta):
    """Legacy observations remain usable as private candidates. New explicit
    partial/uncertain answers cannot be promoted by a generic positive verdict."""
    if 'correspondencia_acao' not in resposta:return {'estado':'LEGADO_REVISAR','especificidade_verificada':False}
    x=resposta['correspondencia_acao']
    if not isinstance(x,dict) or x.get('estado') not in ('direta','parcial','incerta','nao_corresponde'):
        return {'estado':'FORMATO_INVALIDO','especificidade_verificada':False}
    if x['estado']!='direta':
        return {'estado':'REVISAR_ACAO_ESPECIFICA','especificidade_verificada':False}
    if any(not isinstance(x.get(k),str) or len(x[k].strip())<16 for k in ('referente','mudanca','referencia_estavel')):
        return {'estado':'FORMATO_INVALIDO','especificidade_verificada':False}
    return {'estado':'DIRETA_DECLARADA','especificidade_verificada':False}

def fila(needs,issues):
    by={n['id']:n for n in needs};out=[]
    for issue in issues:
        n=by.get(issue['id'])
        if not n:continue
        motion=n.get('evidencia_visual')=='movimento'
        out.append({'necessidade_id':n['id'],'fatos':n.get('fatos',[]),'mostrar':n.get('mostrar'),
            'evidencia_visual':n.get('evidencia_visual'),'motivo':issue['motivo'],
            'acao':'BUSCAR_OUTRA_JANELA_OU_FONTE_DA_ACAO_EXATA' if motion else 'REAVALIAR_COBERTURA_DO_FATO',
            'prioridade':0 if motion else 1,'publicar':False,'autoriza_animacao':False,
            'feedback':issue.get('feedback')})
    return sorted(out,key=lambda x:x['prioridade'])
