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
