"""E346: enlarge an explicitly inspected panel from an exact static source.
This is a private re-edit, not an inferred observation or semantic approval.
"""
import copy,math,re
from .integracao_incremental_e343 import intervalos

def aplicar(props,queue,words,prior,entries):
    if props.get('preview') is not True or props.get('private_review_only') is not True or props.get('documentary_caption_origin')!='PALAVRAS_MEDIDAS' or queue.get('publish') is not False or prior.get('publish') is not False or prior.get('status')!='RENDERED_PRIVATE_INTEGRAL':
        raise ValueError('E346-PRIVATE')
    out=copy.deepcopy(props);shots={s['id']:s for s in out['shots']};tasks={t['shot']:t for t in queue['tasks']}
    if len(shots)!=len(out['shots']) or len(tasks)!=len(queue['tasks']) or len({r['shot'] for r in entries})!=len(entries):raise ValueError('E346-DUPLICATE')
    changes=[]
    for r in entries:
        s=shots[r['shot']];t=tasks[r['shot']];h=r['sha256'];donor=tasks[r['donor']]
        if r.get('publish') is not False or s['type']!='photo' or s.get('photo_framing')!='integral' or s.get('photo_crop_preview') or r['speech']!=t['speech'] or s['asset'] not in ('film_editorial/'+h+'.png','film_editorial/'+h+'.jpg','film_editorial/'+h+'.webp') or not re.fullmatch('[a-f0-9]{64}',h):
            raise ValueError('E346-SCOPE')
        if h!=donor['sha256'] or r['review_ref']!=donor['review_ref'] or donor['status']!='AMOSTRAS_REVISADAS_PERTINENTES' or not donor['observed'] or any(abs(s[k]-t[k])>1e-6 for k in ('start','end')):
            raise ValueError('E346-RECEIPT')
        if r['shot']!=r['donor'] and not any(c.get('shot')==r['shot'] and c.get('donor')==r['donor'] and c.get('source_sha256')==h and c.get('prior_review_ref')==r['review_ref'] and c.get('speech')==r['speech'] and c.get('status')=='NOVO_ESCOPO_PENDENTE' for c in prior['changes']):
            raise ValueError('E346-PRIOR')
        b=r['bbox'];dims=s['source_dimensions']
        if len(b)!=4 or not all(type(x) in (int,float) and math.isfinite(x) for x in b) or not (0<=b[0]<b[2]<=1 and 0<=b[1]<b[3]<=1) or (b[2]-b[0])*(b[3]-b[1])>.45 or len(dims)!=2 or not all(type(x) is int and x>=600 for x in dims):
            raise ValueError('E346-BOX')
        if r['kind'] not in ('SCHEME','MAP') or not 3<=len(r['label'])<=34 or not r.get('observation') or len(r['observation'])<35:raise ValueError('E346-LABEL')
        w,hp=dims;dw=(b[2]-b[0])*w;dh=(b[3]-b[1])*hp
        scale=min(1080/dw,666/dh);gain=scale/min(1080/w,900/hp)
        if gain<1.4 or min(dw*scale,dh*scale)<300:raise ValueError('E346-GAIN')
        matches=[word for word in words if word['w']==r['anchor'] and s['start']<=word['s']<s['end']]
        if len(matches)!=1:raise ValueError('E346-ANCHOR')
        at=matches[0]['s']-s['start']
        if not .8<=at<=s['end']-s['start']-.8:raise ValueError('E346-ANCHOR')
        s['documentary_static_reveal']={'at':at,'label':r['label'],'bbox':b,'sha256':h,'revisao_id':r['review_ref'],'status':'PRIVATE_STATIC_REVEAL_PENDING','detail_zoom':True,'panel_focus':True,'panel_kind':r['kind'],'detail_gain':round(gain,3)}
        changes.append({**r,'at_s':matches[0]['s'],'detail_gain':round(gain,3),'panel_px':[round(dw*scale),round(dh*scale)],'status':'SOURCE_PANEL_PRIVATE_PENDING','direct_evidence_verified':False})
    changed={r['shot'] for r in changes}
    if out['documentary_captions']!=props['documentary_captions'] or out['duracao']!=props['duracao']:raise ValueError('E346-VOICE')
    return out,{'publish':False,'semantic_approval':False,'editorial_review':'PENDING','changes':changes,'parts':intervalos(out['shots'],out['duracao'],changed),'changed_shots':sorted(changed),'total_frames':round(out['duracao']*30)}
