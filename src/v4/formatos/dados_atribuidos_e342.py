"""E342: exact speech-bound, attributed reported data, not visual measurement.
Private candidate only; no modification of narration or evidence approval.
"""
import copy,re,math
def vincular(props,queue,words,entries):
    if props.get('preview') is not True or props.get('private_review_only') is not True or queue.get('publish') is not False or props.get('documentary_caption_origin')!='PALAVRAS_MEDIDAS':
        raise ValueError('E342-PRIVATE')
    out=copy.deepcopy(props);shots={s['id']:s for s in out['shots']};tasks={t['shot']:t for t in queue['tasks']}
    if len(shots)!=len(out['shots']) or len(tasks)!=len(queue['tasks']) or len({r['shot'] for r in entries})!=len(entries):raise ValueError('E342-DUPLICATE')
    report=[]
    for r in entries:
        shot=shots[r['shot']];t=tasks[r['shot']];h=r['sha256']
        if r.get('publish') is not False or r['speech']!=t['speech'] or t['sha256']!=h or not re.fullmatch('[a-f0-9]{64}',h) or shot['asset']!='film_editorial/'+h+'.mp4' or shot['type']!='video':
            raise ValueError('E342-SCOPE')
        if any(abs(shot[k]-t[k])>1e-6 for k in ('start','end')) or abs(shot['source_in_seconds']-t['source_in'])>1e-6 or not shot.get('documentary_integral_required') and shot.get('video_context_layout')!='cena_integral':
            raise ValueError('E342-WINDOW')
        if not r['source_url'].startswith('https://') or not r['authority'] or len(r['authority'])>60 or not r.get('source_statement') or not r.get('source_date') or not 1<=len(r['value'])<=24 or not 1<=len(r['scope'])<=72:
            raise ValueError('E342-SOURCE')
        matches=[w for w in words if w['w']==r['anchor'] and shot['start']<=w['s']<shot['end']]
        if len(matches)!=1 or not math.isfinite(matches[0]['s']) or shot['end']-matches[0]['s']<1.4:raise ValueError('E342-ANCHOR')
        # Explicit integral is a protective choice; no inherited crop geometry.
        for k in ('documentary_viewport','framing_positions','focus','documentary_roi_points','documentary_observed_viewport_trial','documentary_balance_trial'):
            shot.pop(k,None)
        shot.update(documentary_integral_required=True,video_context_layout='cena_integral',video_zoom=1,documentary_composition_v2=True)
        fact={'schema':'coringa.reported.fact.private.v1','publish':False,'at':matches[0]['s']-shot['start'],'value':r['value'],'scope':r['scope'],'authority':r['authority'],'url':r['source_url'],'sha256':h}
        shot['documentary_reported_fact']=fact
        report.append({**r,'at_s':matches[0]['s'],'status':'DADO_ATRIBUIDO_REVISAO_PRIVADA','measurement_from_pixels':False,'direct_evidence_verified':False})
    return out,report
