"""E338: review queue from exact measured-speech obligations of an existing film.
No new facts, no inferred evidence, no permission to publish or render.
"""
import math,re
def near(a,b):
    return all(type(x) in (int,float) and math.isfinite(x) for x in (a,b)) and abs(a-b)<=1e-6

def organizar(plan,obligations):
    if plan.get('publicar') is not False or obligations.get('publish') is not False:
        raise ValueError('E338-PRIVATE')
    if obligations.get('semantic_review')!='PENDING':raise ValueError('E338-REVISAO')
    shots=plan['shots'];media=plan['media'];by={}
    for r in obligations['shots']:
        k=r['shot']
        if k in by:raise ValueError('E338-DUPLICADA')
        by[k]=r
    if len({s['id'] for s in shots})!=len(shots):raise ValueError('E338-CENA-DUPLICADA')
    rows=[];other=[];used=set();last=None
    for s in shots:
        sid=s['id'];a,b=s['start'],s['end']
        if not near(a,a) or not near(b,b) or a<0 or b<=a:raise ValueError('E338-TEMPO')
        if s['type'] not in ('video','photo'):
            other.append({'shot':sid,'kind':s['type'],'status':'REVISAO_ESPECIALIZADA_SEPARADA','publicar':False})
            last=None;continue
        r=by.get(sid);m=media[s['asset']];h=m.get('expected_sha256')
        if not r or r['source']!=s['asset'] or not re.fullmatch('[a-f0-9]{64}',str(h or '')) or r['source_sha256']!=h or not near(a,r['start']) or not near(b,r['end']):
            raise ValueError('E338-VINCULO '+sid)
        if r.get('direct_evidence_verified') is not False:raise ValueError('E338-ESTADO')
        speech=r.get('speech')
        if not isinstance(speech,str) or not speech.strip():raise ValueError('E338-FALA')
        if s['type']=='video':
            start=s.get('source_in_seconds')
            if not near(start,r['source_in']) or not near(start+(b-a),r['source_out']):raise ValueError('E338-JANELA '+sid)
        elif r['source_in'] is not None or r['source_out'] is not None:raise ValueError('E338-FOTO')
        binding=r.get('reviewed_binding');status=r.get('status')
        if binding:
            if status!='AMOSTRAS_REVISADAS_PERTINENTES' or any(binding.get(k)!=r.get(k) for k in ('shot','chapter','speech','source')) or binding.get('sha256')!=h or not binding.get('review_ref') or not binding.get('observed'):
                raise ValueError('E338-REVISAO-VINCULO '+sid)
            if s['type']=='video' and (not near(binding.get('window_start'),r['source_in']) or not near(binding.get('window_duration'),binding.get('window_duration')) or binding['window_duration']+1e-6<b-a):
                raise ValueError('E338-REVISAO-JANELA '+sid)
        elif status!='REVISAR_EVIDENCIA_POR_FALA':raise ValueError('E338-REVISAO-ESTADO')
        used.add(sid);repeat=last==h;last=h
        w,hh=m.get('width'),m.get('height')
        from .imersao_documental_e328 import fracao_integral
        fraction=fracao_integral(w,hh)
        priority=0 if a<3 else 1 if not binding else 2
        rows.append({'shot':sid,'start':a,'end':b,'chapter':r['chapter'],'speech':speech,
            'source':r['source'],'sha256':h,'source_in':r['source_in'],'source_out':r['source_out'],
            'status':status,'priority':priority,'action':'INSPECIONAR_FALA_E_JANELA' if not binding else 'CONFERIR_LIMITE_DA_OBSERVACAO_E_FALA',
            'observed':binding.get('observed') if binding else None,'review_ref':binding.get('review_ref') if binding else None,
            'adjacent_same_source':repeat,'integral_canvas_fraction_estimate':fraction,'direct_evidence_verified':False,'publicar':False})
    if used!=set(by):raise ValueError('E338-OBRIGACAO-SEM-CENA')
    tasks=sorted(rows,key=lambda r:(r['priority'],r['start']))
    groups={}
    for r in tasks:groups.setdefault(r['sha256'],[]).append(r['shot'])
    return {'schema':'coringa.speech.visual.review.queue.v1','publish':False,'semantic_approval':False,'rendered_coverage_verified':False,
        'duration_s':plan['duracao'],'media_shots':len(rows),'unreviewed_shots':sum(r['status']=='REVISAR_EVIDENCIA_POR_FALA' for r in rows),
        'sample_reviewed_shots':sum(r['status']=='AMOSTRAS_REVISADAS_PERTINENTES' for r in rows),'direct_verified_shots':0,
        'specialized_shots':other,'tasks':tasks,'source_batches':[{'sha256':h,'shots':ids} for h,ids in groups.items()]}
