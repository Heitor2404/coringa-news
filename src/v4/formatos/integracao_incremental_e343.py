"""E343-E345: integrate private local edits without rebuilding unaffected shots."""
import copy,math
from .reedicao_fala_e339 import edit
from .dados_atribuidos_e342 import vincular

def frame(t):
    if type(t) not in (int,float) or not math.isfinite(t) or abs(t*30-round(t*30))>1e-5:raise ValueError('E343-FRAME')
    return round(t*30)

def intervalos(shots,duration,changed):
    total=frame(duration);cursor=0;parts=[];seen=set()
    for s in shots:
        a,b=frame(s['start']),frame(s['end'])
        if a!=cursor or b<=a or s['id'] in seen:raise ValueError('E343-TIMELINE')
        seen.add(s['id']);cursor=b;mode=s['id'] in changed
        if parts and parts[-1]['changed']==mode:
            parts[-1]['end']=b;parts[-1]['shots'].append(s['id'])
        else:parts.append({'start':a,'end':b,'changed':mode,'shots':[s['id']]})
    if cursor!=total or not set(changed)<=seen or not changed:raise ValueError('E343-COVERAGE')
    return parts

def integrar(props,queue,words,config,data):
    if config.get('publish') is not False or props.get('private_review_only') is not True or props.get('preview') is not True:raise ValueError('E343-PRIVATE')
    out=copy.deepcopy(props);replacements={};notes=[];tasks={t['shot']:t for t in queue['tasks']}
    for passage in config['passages']:
        frag,rows=edit(props,queue,passage['changes'],passage['end'],start=passage['start'])
        for s,r in zip(frag['shots'],rows,strict=True):
            if r['status']=='BASELINE_PRESERVADA':continue
            if s['id'] in replacements:raise ValueError('E343-DUPLICATE')
            replacements[s['id']]=s;notes.append(r)
    # Bind a new label to an already visible, explicitly reviewed source panel,
    # with measured word timing. Never transfer the donor's semantic approval.
    for r in config['static_reveals']:
        s=replacements[r['shot']];t=tasks[r['shot']];donor=tasks[r['donor']]
        if s['type']!='photo' or r['speech']!=t['speech'] or r['sha256']!=donor['sha256'] or r['review_ref']!=donor['review_ref'] or s['asset']!='film_editorial/'+r['sha256']+'.png':
            raise ValueError('E344-SCOPE')
        box=r['bbox']
        if len(box)!=4 or not all(type(x) in (int,float) and math.isfinite(x) for x in box) or not (0<=box[0]<box[2]<=1 and 0<=box[1]<box[3]<=1):raise ValueError('E344-BOX')
        w=[w for w in words if w['w']==r['anchor'] and s['start']<=w['s']<s['end']]
        if len(w)!=1 or s['end']-w[0]['s']<.8 or not r.get('observation') or len(r['label'])>34:raise ValueError('E344-ANCHOR')
        s['documentary_static_reveal']={'at':w[0]['s']-s['start'],'label':r['label'],'bbox':box,'sha256':r['sha256'],'revisao_id':r['review_ref'],'status':'PRIVATE_STATIC_REVEAL_PENDING'}
        notes.append({**r,'status':'PRIVATE_CAUSAL_PANEL_PENDING','direct_evidence_verified':False,'publicar':False})
    out['shots']=[replacements.get(s['id'],s) for s in out['shots']]
    if set(replacements)&{r['shot'] for r in data}:raise ValueError('E343-OVERLAP')
    out,reported=vincular(out,queue,words,data)
    changed=set(replacements)|{r['shot'] for r in reported}
    if out['documentary_captions']!=props['documentary_captions'] or out['duracao']!=props['duracao']:raise ValueError('E343-VOICE')
    parts=intervalos(out['shots'],out['duracao'],changed)
    repeats=[]
    for s in out['shots']:
        if s['id'] not in changed or s['type'] not in ('photo','video'):continue
        for other in out['shots']:
            if s['id']==other['id'] or s.get('asset')!=other.get('asset'):continue
            overlap=s['type']=='photo' or max(s['source_in_seconds'],other['source_in_seconds'])<min(s['source_in_seconds']+s['end']-s['start'],other['source_in_seconds']+other['end']-other['start'])
            if overlap:repeats.append({'shot':s['id'],'other':other['id'],'reason':'REUSO_EDITORIAL_PENDENTE'})
    return out,{'publish':False,'semantic_approval':False,'editorial_review':'PENDING','changes':notes,'reported_facts':reported,'repeated_sources':repeats,'parts':parts,'changed_shots':sorted(changed),'total_frames':frame(out['duracao'])}
