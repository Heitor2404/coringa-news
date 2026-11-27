"""E388.4: private chart decisions by structured claim and editorial need.
Never infer a numeric claim from speech or replace required visual evidence."""
import copy,re
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
