"""E388.4: private chart decisions by structured claim and editorial need.
Never infer a numeric claim from speech or replace required visual evidence."""
import copy,re,math
KINDS={'scalar':'number','interval':'range','part':'proportion','area':'area','comparison':'bars','timeline':'timeline'}
INTENTS={'magnitude':{'scalar','area','interval'},'proportion':{'part'},'comparison':{'comparison','interval','area'},'chronology':{'timeline'}}
def decidir(need, claim, receipt):
    def no(reason):return {'status':'KEEP_EXISTING','reason':reason,'publish':False}
    if not all(isinstance(v,dict) for v in (need,claim,receipt)):return no('MISSING_STRUCTURED_INPUT')
    if need.get('requires_direct_evidence') is not False or need.get('role')!='quantitative_explainer':return no('PROTECT_EVIDENCE_OR_NONQUANTITATIVE')
    if need.get('purpose') not in INTENTS or claim.get('shape') not in INTENTS[need['purpose']]:return no('NO_EDITORIAL_BENEFIT')
    if claim.get('schema')!='coringa.motion.claim.private.v1' or claim.get('publish') is not False or claim.get('fixture') is not False:return no('PRIVATE_REAL_CLAIM_REQUIRED')
    source=claim.get('source') or {}
    if receipt.get('publish') is not False or receipt.get('verified_claim')!=claim or not need.get('fact_id') or need['fact_id']!=receipt.get('fact_id') or not re.fullmatch(r'[a-f0-9]{64}',str(receipt.get('source_sha256',''))) or not str(source.get('url','')).startswith('https://') or not source.get('statement') or not source.get('date'):return no('UNBOUND_SOURCE')
    return {'status':'CHART_CANDIDATE','kind':KINDS[claim['shape']],'claim':copy.deepcopy(claim),'fact_id':need['fact_id'],'publish':False,'reason':'STRUCTURED_QUANTITATIVE_NEED'}

def ancorar(decision, shot, fact, receipt, captions):
    if decision.get('status')!='CHART_CANDIDATE' or fact.get('publish') is not False or receipt.get('publish') is not False:raise ValueError('E3885-DECISION')
    if shot.get('id')!=receipt.get('shot') or decision.get('fact_id')!=receipt.get('shot') or fact.get('sha256')!=receipt.get('sha256') or fact.get('url')!=receipt.get('source_url') or fact.get('value')!=receipt.get('value') or fact.get('scope')!=receipt.get('scope'):raise ValueError('E3885-RECEIPT')
    a=fact.get('at');duration=shot['end']-shot['start'];word=receipt.get('anchor')
    if type(a) not in (int,float) or not math.isfinite(a) or a<0 or duration-a<1.4 or not word:raise ValueError('E3885-TIME')
    if not any(g['start']<=a+.034 and g['end']>a and any(w['w']==word for w in g['words']) for g in captions):raise ValueError('E3885-CAPTION')
    return {'schema':'coringa.motion.anchor.private.v1','at':a,'word':word,'publish':False}

def fila_plano(plan):
    """Opt-in handoff in the existing short director. Never mutates shots.
    The claim must be linked to an existing factual obligation, not just a
    numeric token. Direct or unspecified evidence is preserved by default."""
    packets=plan.get('motion_claims') or []
    if not packets:return []
    if plan.get('publicar') is not False:raise ValueError('E3884-PRIVATE-PLAN')
    needs={n['id']:n for n in plan.get('necessidades_direcao',[])}
    shots={s['id']:s for s in plan.get('shots',[])}
    seen=set();out=[]
    for p in packets:
        i=p.get('need_id');fact=p.get('fact_id');n=needs.get(i);shot=shots.get(i)
        if not n or not shot or not fact or fact not in n.get('fatos',[]) or (i,fact) in seen:
            out.append({'need_id':i,'fact_id':fact,'status':'KEEP_EXISTING','reason':'UNBOUND_OR_DUPLICATE_OBLIGATION','publish':False});continue
        seen.add((i,fact))
        need={'fact_id':fact,'role':n.get('motion_role'),'purpose':n.get('motion_purpose'),'requires_direct_evidence':n.get('exigir_evidencia_direta') is not False or n.get('evidencia_visual')=='movimento' or shot.get('type') not in ('photo','video') or bool(shot.get('documentary_static_reveal'))}
        d=decidir(need,p.get('claim'),p.get('receipt'))
        out.append({**d,'need_id':i,'fact_id':fact,'original_shot_preserved':True,'render_authorized':False})
    return out

def relacoes_plano(plan, candidates=None):
    """Auto-pair adjacent eligible quantitative obligations using explicit
    source-reviewed inclusion receipts. Never infer inclusion from same unit,
    page, smaller value or topic. Returns proposals only; no scene mutation."""
    cs=fila_plano(plan) if candidates is None else candidates
    allowed={(x['need_id'],x['fact_id']):x for x in cs if x.get('status')=='CHART_CANDIDATE'}
    shots={s['id']:s for s in plan.get('shots',[])}
    packets=plan.get('motion_relation_receipts') or []
    if packets and plan.get('publicar') is not False:raise ValueError('E3887-PRIVATE')
    out=[];seen=set()
    for r in packets:
        def reject(reason):return {'status':'KEEP_EXISTING','reason':reason,'publish':False}
        if not isinstance(r,dict) or r.get('schema')!='coringa.motion.inclusion.receipt.private.v1' or r.get('publish') is not False or r.get('relation')!='included_area' or r.get('reviewed') is not True:
            out.append(reject('NO_REVIEWED_INCLUSION'));continue
        keys=[(r.get(k+'_need'),r.get(k+'_fact')) for k in ('total','part')]
        if any(k not in allowed for k in keys) or keys[0]==keys[1] or any(k in seen for k in keys):
            out.append(reject('UNBOUND_OR_PROTECTED_OBLIGATION'));continue
        a,z=[allowed[k]['claim'] for k in keys]
        s,t=[shots[k[0]] for k in keys]
        source=a.get('source') or {};other=z.get('source') or {}
        if any(c.get('shape')!='area' or c.get('unit')!='km²' or c.get('fixture') is not False or c.get('relation') not in (None,'approx','exact') or len(c.get('values') or [])!=1 for c in (a,z)):
            out.append(reject('INCOMPATIBLE_QUANTITIES'));continue
        if r.get('source_url')!=source.get('url') or r.get('source_url')!=other.get('url') or r.get('source_date')!=source.get('date') or r.get('source_date')!=other.get('date') or not isinstance(r.get('statement'),str) or not 0<len(r['statement'])<=500 or r.get('total_claim')!=a or r.get('part_claim')!=z:
            out.append(reject('UNBOUND_INCLUSION_SOURCE'));continue
        av,zv=a['values'][0].get('value'),z['values'][0].get('value')
        if not all(type(v) in (int,float) and math.isfinite(v) and 0<v<=10000 for v in (av,zv)) or zv>=av:
            out.append(reject('INVALID_INCLUSION_MAGNITUDE'));continue
        if not all(type(v) in (int,float) and math.isfinite(v) for v in (s.get('start'),s.get('end'),t.get('start'),t.get('end'))) or abs(s['end']-t['start'])>1e-6 or min(s['end']-s['start'],t['end']-t['start'])<2.4:
            out.append(reject('NONCONTIGUOUS_OR_INSUFFICIENT_TIME'));continue
        group='area-'+keys[0][0]+'-'+keys[1][0]
        if len(group)>80:out.append(reject('INVALID_GROUP'));continue
        base={'schema':'coringa.motion.area_relation.private.v1','publish':False,'kind':'included_area','group':group,'total':copy.deepcopy(a),'part':copy.deepcopy(z),'inclusion_statement':r['statement']}
        seen.update(keys)
        out.append({'status':'RELATION_CANDIDATE','total_need':keys[0][0],'part_need':keys[1][0],'ratio':zv/av,'relations':[dict(base,role='total'),dict(base,role='part')],'render_authorized':False,'publish':False})
    return out
