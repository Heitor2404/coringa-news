"""E388.8: reviewed factual quantities -> editorial proposals in E254/E306.
No raw-speech extraction, no source verification by declaration, no renderer
authorization. Keep direct evidence and historical cases untouched."""
from __future__ import annotations
import copy,math,re,datetime

PURPOSE={'scalar':'magnitude','interval':'magnitude','area':'magnitude','part':'proportion','comparison':'comparison','timeline':'chronology'}
KINDS={'measurement':'scalar','range':'interval','subset':'part','comparable':'comparison','events':'timeline'}
QUANT_ROLES={'quantificacao','comparacao','cronologia'}

def text_ok(s,limit):return isinstance(s,str) and bool(s.strip()) and len(s)<=limit
def number(v):return type(v) in (int,float) and math.isfinite(v) and 0<=v<=1e12
def date_ok(v):
    try:return isinstance(v,str) and datetime.date.fromisoformat(v).isoformat()==v
    except ValueError:return False

def claim_from_fact(fact):
    """A reviewer supplies factual measurement, not a renderer or chart family.
    The digest refers to the reviewed source artifact, not to this declaration.
    This adapter checks binding; actual bytes/semantic review are upstream."""
    r=fact.get('quantitative_review')
    if not isinstance(r,dict) or r.get('schema')!='coringa.fact.quantity.review.private.v1' or r.get('publish') is not False or r.get('reviewed') is not True or r.get('fact_id')!=fact.get('id'):
        return None,'REVIEW_REQUIRED'
    if r.get('relevance')!='central':return None,'INCIDENTAL_QUANTITY'
    url=fact.get('fonte')
    if not isinstance(url,str) or not re.fullmatch(r'https://[^\s]+',url) or r.get('source_url')!=url or not re.fullmatch(r'[a-f0-9]{64}',str(r.get('source_sha256',''))) or not text_ok(r.get('source_date'),32) or not text_ok(r.get('statement'),500) or not text_ok(r.get('review_id'),200):
        return None,'UNBOUND_SOURCE_REVIEW'
    m=r.get('measurement')
    if not isinstance(m,dict) or not text_ok(m.get('title'),48) or not text_ok(m.get('scope'),100):return None,'MALFORMED_MEASUREMENT'
    k=KINDS.get(m.get('kind'));unit=m.get('unit')
    if k is None or not isinstance(unit,str) or len(unit)>12:return None,'UNSUPPORTED_MEASUREMENT'
    # Currency, conversion and exceptional price context remain in V2 factual
    # contract; this new route does not bypass those specialized obligations.
    if re.search(r'[$€£¥]|\b(?:USD|BRL|EUR|GBP|JPY|CNY|reais|d[oó]lar(?:es)?|euros?)\b',unit,re.I) or m.get('currency') or m.get('conversion'):return None,'SPECIALIZED_MONEY_REVIEW'
    values=m.get('values');relation=m.get('qualifier','exact')
    if not isinstance(values,list) or any(not isinstance(v,dict) or not text_ok(v.get('label'),32) or not number(v.get('value')) for v in values):return None,'MALFORMED_VALUES'
    if relation not in ('exact','approx','lower','upper'):return None,'MALFORMED_QUALIFIER'
    if k=='scalar' and unit=='km²':k='area'
    n=len(values)
    extra={}
    if k=='timeline':
        ev=m.get('events')
        if n or unit or not isinstance(ev,list) or not 2<=len(ev)<=3 or any(not isinstance(e,dict) or not text_ok(e.get('label'),40) or not date_ok(e.get('date')) for e in ev) or any(x['date']>=y['date'] for x,y in zip(ev,ev[1:])):return None,'INVALID_TIMELINE'
        extra['events']=copy.deepcopy(ev)
    elif k=='area':
        if n!=1 or not 0<values[0]['value']<=10000 or relation not in ('exact','approx'):return None,'INVALID_AREA'
    elif k=='scalar':
        if n!=1 or not unit:return None,'INVALID_SCALAR'
    elif k=='range':
        # not used; interval is normalized above
        return None,'INVALID_SHAPE'
    elif k=='interval':
        if n!=2 or not unit or values[0]['value']>=values[1]['value'] or relation not in ('exact','approx'):return None,'INVALID_INTERVAL'
    elif k=='part':
        d=m.get('denominator')
        if n!=1 or unit!='%' or not number(d) or not d or values[0]['value']>d:return None,'INVALID_DENOMINATOR'
        extra['denominator']=d
    elif k=='comparison':
        if not 2<=n<=3 or not unit or m.get('same_basis') is not True or not any(v['value']>0 for v in values) or relation not in ('exact','approx'):return None,'INCOMPARABLE_VALUES'
        extra['comparable']=True
    if k!='timeline':extra['relation']=relation
    c={'schema':'coringa.motion.claim.private.v1','publish':False,'fixture':False,'shape':k,'title':m['title'],'scope':m['scope'],'unit':unit,'values':copy.deepcopy(values),'source':{'url':url,'date':r['source_date'],'statement':r['statement']},**extra}
    return c,'BOUND_DECLARATION_PENDING_BYTE_REVIEW'

def integrar(case,plan):
    """Add only proposal metadata. Do not mutate inputs, media, timing or gates."""
    facts=case.get('fatos') or []
    if not any(isinstance(f,dict) and 'quantitative_review' in f for f in facts) and not case.get('quantitative_relations'):return plan
    if plan.get('publicar') is not False:raise ValueError('E3888-PRIVATE')
    p=copy.deepcopy(plan)
    source_needs={n['id']:n for n in case.get('necessidades',[]) if isinstance(n,dict) and 'id' in n}
    indexed={};dups=set()
    for f in facts:
        if not isinstance(f,dict) or not text_ok(f.get('id'),100):continue
        if f['id'] in indexed:dups.add(f['id'])
        indexed[f['id']]=f
    packets=[];audit=[];eligible={}
    for n in p.get('necessidades_direcao',[]):
        original=source_needs.get(n['id'],{})
        role=original.get('papel_visual')
        quantitative=original.get('necessidade')=='explicacao_quantitativa' or role in QUANT_ROLES
        # Explicit false only. A missing field never authorizes replacement.
        protected=original.get('exigir_evidencia_direta') is not False or original.get('evidencia_visual')=='movimento'
        for fid in n.get('fatos',[]):
            f=indexed.get(fid,{})
            if 'quantitative_review' not in f:continue
            c,reason=claim_from_fact(f)
            if fid in dups:c=None;reason='DUPLICATE_FACT'
            if c and not quantitative:c=None;reason='NO_QUANTITATIVE_OBLIGATION'
            row={'need_id':n['id'],'fact_id':fid,'status':'KEEP_EXISTING','reason':reason,'publish':False,'render_authorized':False}
            if c:
                r=f['quantitative_review']
                packet={'need_id':n['id'],'fact_id':fid,'claim':c,'receipt':{'fact_id':fid,'verified_claim':copy.deepcopy(c),'source_sha256':r['source_sha256'],'publish':False,'review_id':r['review_id']}}
                if protected:
                    row.update(status='SUPPLEMENT_ONLY',reason='PROTECT_DIRECT_EVIDENCE',claim=c)
                else:
                    row.update(status='CANDIDATE_INPUT',reason='REVIEWED_QUANTITY')
                    eligible.setdefault(n['id'],[]).append(packet)
            audit.append(row)
        if len(eligible.get(n['id'],[]))==1:
            packet=eligible[n['id']][0]
            n.update(motion_role='quantitative_explainer',motion_purpose=PURPOSE[packet['claim']['shape']],exigir_evidencia_direta=False)
            packets.append(packet)
        elif len(eligible.get(n['id'],[]))>1:
            for row in audit:
                if row['need_id']==n['id'] and row['status']=='CANDIDATE_INPUT':row.update(status='KEEP_EXISTING',reason='AMBIGUOUS_MULTIPLE_QUANTITIES')
    p['motion_claims']=packets
    # Fact-level inclusion receipts can be paired without specifying a renderer
    # or shot IDs, but only if each fact has exactly one eligible obligation.
    byfact={}
    for x in packets:byfact.setdefault(x['fact_id'],[]).append(x)
    relations=[]
    for r in case.get('quantitative_relations') or []:
        if not isinstance(r,dict) or r.get('schema')!='coringa.fact.inclusion.review.private.v1' or r.get('reviewed') is not True or r.get('publish') is not False:
            audit.append({'status':'KEEP_EXISTING','reason':'NO_REVIEWED_INCLUSION','publish':False});continue
        a,z=[byfact.get(r.get(k+'_fact'),[]) for k in ('total','part')]
        if len(a)!=1 or len(z)!=1:
            audit.append({'status':'KEEP_EXISTING','reason':'AMBIGUOUS_OR_PROTECTED_RELATION','publish':False});continue
        a,z=a[0],z[0]
        if r.get('source_url')!=a['claim']['source']['url'] or r.get('source_url')!=z['claim']['source']['url'] or r.get('source_date')!=a['claim']['source']['date'] or r.get('source_date')!=z['claim']['source']['date'] or not text_ok(r.get('statement'),500) or r.get('total_measurement')!=indexed[a['fact_id']]['quantitative_review']['measurement'] or r.get('part_measurement')!=indexed[z['fact_id']]['quantitative_review']['measurement']:
            audit.append({'status':'KEEP_EXISTING','reason':'UNBOUND_INCLUSION_REVIEW','publish':False});continue
        relations.append({'schema':'coringa.motion.inclusion.receipt.private.v1','publish':False,'reviewed':True,'relation':'included_area','total_need':a['need_id'],'total_fact':a['fact_id'],'part_need':z['need_id'],'part_fact':z['fact_id'],'source_url':r['source_url'],'source_date':r['source_date'],'statement':r['statement'],'total_claim':copy.deepcopy(a['claim']),'part_claim':copy.deepcopy(z['claim'])})
    p['motion_relation_receipts']=relations
    p['motion_intake']={'schema':'coringa.motion.intake.private.v1','audit':audit,'publish':False,'render_authorized':False,'source_bytes_reverified':False}
    return p
