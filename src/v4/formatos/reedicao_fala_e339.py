"""E339: bounded private re-edit of an already measured passage.
Donor geometry belongs to its bytes; donor semantic review never transfers.
"""
import copy,math,re
def edit(props,queue,changes,end):
    if props.get('private_review_only') is not True or props.get('preview') is not True or queue.get('publish') is not False:
        raise ValueError('E339-PRIVATE')
    if props.get('documentary_caption_origin')!='PALAVRAS_MEDIDAS' or not props.get('documentary_captions'):
        raise ValueError('E339-CAPTIONS')
    if not isinstance(end,(int,float)) or not 0<end<=20:raise ValueError('E339-DURATION')
    source={s['id']:s for s in props['shots']};tasks={s['shot']:s for s in queue['tasks']}
    if len(source)!=len(props['shots']) or len(tasks)!=len(queue['tasks']):raise ValueError('E339-DUPLICATE')
    selected=[s for s in props['shots'] if s['start']<end]
    if not selected or abs(selected[0]['start'])>1e-6 or abs(selected[-1]['end']-end)>1e-6 or any(abs(a['end']-b['start'])>1e-6 for a,b in zip(selected,selected[1:])):
        raise ValueError('E339-PASSAGE')
    if not set(changes)<=set(s['id'] for s in selected):raise ValueError('E339-TARGET')
    out=[];report=[]
    for old in selected:
        target=tasks[old['id']]
        if abs(target['start']-old['start'])>1e-6 or abs(target['end']-old['end'])>1e-6 or not target['speech']:raise ValueError('E339-SPEECH')
        change=changes.get(old['id'])
        if not change:
            s=copy.deepcopy(old);donor=target
        else:
            donor=tasks[change['donor']];d=source[change['donor']]
            if not donor.get('review_ref') or not donor.get('observed') or donor['status']!='AMOSTRAS_REVISADAS_PERTINENTES':raise ValueError('E339-DONOR')
            if d['type'] not in ('video','photo') or abs(d['start']-donor['start'])>1e-6 or abs(d['end']-donor['end'])>1e-6:raise ValueError('E339-DONOR-SCOPE')
            # Only copy source presentation, never donor claim/reveal/label or action approval.
            fields=('type','asset','source','source_display','source_dimensions','source_in_seconds','video_zoom','video_context_layout','video_framing','framing_positions','documentary_integral_required','photo_framing','subject','headline')
            s={k:copy.deepcopy(d[k]) for k in fields if k in d}
            if d['type']=='video':
                if not d.get('documentary_integral_required') or d.get('framing_positions') or (d.get('video_framing') or {}).get('modo')!='fonte_integral':raise ValueError('E339-VIDEO-CONTEXT')
                span=old['end']-old['start']
                if span>donor['end']-donor['start']+1e-6 or abs(d['source_in_seconds']-donor['source_in'])>1e-6 or d['source_in_seconds']+span>donor['source_out']+1e-6:raise ValueError('E339-WINDOW')
            else:
                s['photo_framing']='integral'
            s.update(id=old['id'],start=old['start'],end=old['end'],lead=change['lead'],evidence='representative',cues=[],documentary_composition_v2=True)
        if not re.fullmatch(r'film_editorial/[a-f0-9]{64}[.](mp4|jpg|jpeg|png|webp)',s['asset']) or s['asset'].split('/')[-1].split('.')[0]!=donor['sha256']:
            raise ValueError('E339-ASSET')
        out.append(s)
        report.append({'shot':old['id'],'speech':target['speech'],'start':old['start'],'end':old['end'],
            'old_sha256':target['sha256'],'source_sha256':donor['sha256'],'source_asset':s['asset'],'source_in':s.get('source_in_seconds'),
            'source_out':s['source_in_seconds']+s['end']-s['start'] if s['type']=='video' else None,
            'donor':change['donor'] if change else None,'prior_observation':donor.get('observed'),'prior_review_ref':donor.get('review_ref'),
            'status':'NOVO_ESCOPO_PENDENTE' if change else 'BASELINE_PRESERVADA','direct_evidence_verified':False,'publicar':False})
    caps=[{**c,'end':min(c['end'],end)} for c in props['documentary_captions'] if c['start']<end]
    return {**props,'duracao':end,'shots':out,'documentary_captions':caps,'documentary_text_probe':False},report
