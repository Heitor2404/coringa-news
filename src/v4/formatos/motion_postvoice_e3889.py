"""E388.9: post-voice private alternative, never replace the canonical film.
Only a bounded reviewed quantity, actual local artifact, measured phrase and
unprotected contextual scene can enter this route. No source discovery/TTS."""
from __future__ import annotations
import copy,hashlib,math,re,unicodedata
from pathlib import Path
from .motion_direcao_e3884 import fila_plano,relacoes_plano

def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def token(s):
    return unicodedata.normalize('NFC',str(s)).upper().strip('.,;:!?…')

def realnum(v):return type(v) in (float,int) and math.isfinite(v)

def verified_asset(root,asset):
    if not isinstance(asset,str) or not re.fullmatch(r'(?:film_editorial/[a-f0-9]{64}\.(?:jpg|mp4)|e202/[a-f0-9]{64}\.wav)',asset):return None
    p=(root/asset).resolve()
    if not p.is_relative_to(root) or not p.is_file() or digest(p)!=p.stem:return None
    return p

def measured_anchor(shot,review,words,caps):
    phrase=review.get('anchor_phrase')
    idx=review.get('anchor_word_index',0)
    if not isinstance(phrase,list) or not 2<=len(phrase)<=12 or any(not isinstance(t,str) or not token(t) for t in phrase) or type(idx) is not int or not 0<=idx<len(phrase):return None,'MISSING_REVIEWED_PHRASE'
    norm=[token(w.get('w')) for w in words]
    wanted=[token(w) for w in phrase]
    matches=[]
    for i in range(len(norm)-len(wanted)+1):
        if norm[i:i+len(wanted)]!=wanted:continue
        ws=words[i:i+len(wanted)]
        if any(not realnum(w.get('s')) or not realnum(w.get('e')) or w['e']<=w['s'] for w in ws):continue
        if any(v['s']<u['e']-.034 for u,v in zip(ws,ws[1:])):continue
        a=ws[idx]['s']
        if ws[0]['s']>=shot['start']-.034 and ws[-1]['e']<=shot['end']+.034:matches.append((a,ws[idx]['w']))
    if len(matches)!=1:return None,'MISSING_OR_AMBIGUOUS_MEASURED_PHRASE'
    a,w=matches[0];at=a-shot['start']
    if at<.35 or shot['end']-a<1.4:return None,'INSUFFICIENT_CONTEXT_OR_READING_TIME'
    hits=[x['w'] for g in caps if g['start']<=a+.034 and g['end']>a for x in g['words'] if token(x['w'])==token(w)]
    if len(hits)!=1:return None,'CAPTION_BINDING'
    return {'schema':'coringa.motion.anchor.private.v1','publish':False,'at':at,'word':hits[0]},'MEASURED_PHRASE'

def preparar_alternativa(case,plan,props,words,sync,public_root):
    report={'schema':'coringa.motion.postvoice.private.v1','publish':False,'canonical_unchanged':True,'render_authorized':False,'rows':[]}
    if case.get('motion_private_alternatives') is not True or not plan.get('motion_claims'):return None,report
    root=Path(public_root).resolve()
    if plan.get('publicar') is not False or any(props.get(k) is not True for k in ('preview','private_review_only','documentary_media_preview')) or props.get('documentary_caption_origin')!='PALAVRAS_MEDIDAS' or sync.get('ok') is not True or not verified_asset(root,props.get('scene_narration_asset')):
        report['reason']='PRIVATE_AUDIO_OR_SYNC_REQUIRED';return None,report
    original={s['id']:s for s in props['shots']}
    declared={s['id']:s for s in plan['shots']}
    facts={f['id']:f for f in case.get('fatos',[]) if isinstance(f,dict) and 'id' in f}
    needs={n['id']:n for n in plan.get('necessidades_direcao',[])}
    packets={(p['need_id'],p['fact_id']):p for p in plan['motion_claims']}
    caps=props.get('documentary_captions') or []
    if not caps or not words:return None,{**report,'reason':'MEASURED_WORDS_REQUIRED'}
    decisions=fila_plano(plan);replacements={};rows={}
    for d in decisions:
        nid,fid=d['need_id'],d['fact_id']
        row={'need_id':nid,'fact_id':fid,'status':'KEEP_EXISTING','reason':d['reason'],'publish':False};report['rows'].append(row)
        if d['status']!='CHART_CANDIDATE':continue
        s=original.get(nid,{});before=declared.get(nid,{});n=needs.get(nid,{})
        # Reject any existing special factual lane, observed detail, crop or
        # indispensable evidence. This route is deliberately contextual only.
        if n.get('exigir_evidencia_direta') is not False or s.get('evidence')!='representative' or before.get('evidence')!='representative' or s.get('type') not in ('photo','video') or any(k in s for k in ('video_framing','photo_roi_candidate','progressao_visual','motion_graphic')) or any(k.startswith('documentary_') and k not in ('documentary_composition_v2',) for k in s):
            row['reason']='PROTECT_EXISTING_EVIDENCE_OR_LAYOUT';continue
        if not all(realnum(s.get(k)) and s.get(k)==before.get(k) for k in ('start','end')) or s['end']-s['start']<3.5:
            row['reason']='SCENE_TIMING';continue
        r=facts.get(fid,{}).get('quantitative_review') or {}
        p=packets[(nid,fid)];claim=d['claim']
        # The source review is bound to the original reviewed local artifact;
        # only the same hash is accepted here. No arbitrary URL acquisition.
        context=verified_asset(root,s.get('asset'))
        if not context or context.stem!=p['receipt']['source_sha256'] or context.stem!=r.get('source_sha256') or r.get('source_url')!=claim['source']['url'] or r.get('review_id')!=p['receipt'].get('review_id'):
            row['reason']='REVIEWED_SOURCE_ARTIFACT_UNAVAILABLE';continue
        if (s['type']=='photo' and context.suffix!='.jpg') or (s['type']=='video' and context.suffix!='.mp4'):
            row['reason']='UNSUPPORTED_CONTEXT_CONTAINER';continue
        source_in=s.get('source_in_seconds',0)
        credit=s.get('source_display') or s.get('source')
        if not realnum(source_in) or source_in<0 or not isinstance(credit,str) or not 0<len(credit)<=200:
            row['reason']='CONTEXT_CONTRACT';continue
        a,reason=measured_anchor(s,r,words,caps)
        if not a:row['reason']=reason;continue
        chart={'id':nid,'start':s['start'],'end':s['end'],'type':'photo','graphic_original':True,'evidence':'explainer','source':claim['source']['url'],'subject':claim['scope'],'lead':claim['title'],'headline':claim['title'],'documentary_chart_trial':copy.deepcopy(claim),'documentary_chart_anchor':a,'documentary_chart_context':{'schema':'coringa.motion.context.private.v1','publish':False,'asset':s['asset'],'sha256':context.stem,'kind':s['type'],'sourceIn':source_in,'credit':credit}}
        replacements[nid]=chart;rows[nid]=row
        row.update(status='PRIVATE_ALTERNATIVE',reason='MEASURED_PHRASE_AND_REVIEWED_ARTIFACT',anchor=a,source_sha256=context.stem,source_url=claim['source']['url'])
    # An intended pair is atomic: never show half a shared-scale relationship.
    for pair in relacoes_plano(plan,decisions):
        if pair.get('status')!='RELATION_CANDIDATE':continue
        ids=[pair['total_need'],pair['part_need']]
        if all(i in replacements for i in ids):
            for i,rel in zip(ids,pair['relations']):replacements[i]['documentary_chart_relation']=copy.deepcopy(rel)
        else:
            for i in ids:
                if i in replacements:
                    del replacements[i];rows[i].update(status='KEEP_EXISTING',reason='INCOMPLETE_RELATION_PAIR')
    if not replacements:return None,report
    alternative=copy.deepcopy(props)
    alternative['shots']=[replacements.get(s['id'],copy.deepcopy(s)) for s in props['shots']]
    report['alternative_scenes']=list(replacements)
    report['source_bytes_reverified']=True
    report['semantic_review_reperformed']=False
    # Render remains a separate workflow/proof. No automatic replacement of
    # canonical props or approval of rights/publication.
    return alternative,report
