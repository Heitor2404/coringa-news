"""E315: optional private visual label derived from an existing motion review.
No extra vision request, no invented causal link, no extra on-screen lane.
"""
import math,re
from . import direcao_eventos as D,revisao_documental as R

def candidato(need,c,window,span):
    if need.get('evidencia_visual')!='movimento' or not need.get('fatos'):return None
    d=c.get('decisao') or {};rid=window.get('revisao_id');sha=(c.get('aquisicao') or {}).get('sha256')
    if not rid or rid!=d.get('revisao_id') or d.get('estado')!='PERTINENTE_PRIVADO':return None
    for row in c.get('janelas',[]):
        p=row.get('pacote') or {};q=p.get('revisao_assistida') or {}
        if (p.get('revisao_id')!=rid or p.get('sha256_origem')!=sha or p.get('fato_id')!=need['fatos'][0] or
            p.get('necessidade')!=need['mostrar'] or p.get('inicio_s')!=window.get('source_in_seconds')):continue
        try:
            if R.decidir(need,c,q,tipo='video')['estado']!='PERTINENTE_PRIVADO':continue
            if D.aceitar_observacao(p,q['resposta_observada'])['veredito']!='pertinente':continue
            raw=q['resposta_bruta'];idx=raw['indices_mudanca'];label=raw.get('rotulo_mudanca')
            if not isinstance(label,str) or not 3<=len(label.strip())<=34 or not label.strip().isprintable():continue
            if q['resposta_observada'].get('rotulo_mudanca')!=label or q['resposta_observada'].get('indices_mudanca')!=idx:continue
            # Use only the second observed sample, not a guessed earlier event.
            a,b=[p['amostras'][i] for i in idx]
            t=b['fonte_s']-p['inicio_s']
            if not math.isfinite(t) or t<0 or t>=span or span-t<.8:continue
            if a['pixels_sha256']==b['pixels_sha256']:continue
            return {'schema':'coringa.observed.label.private.v1','necessidade_id':need['id'],
                'fatos':need['fatos'],'mostrar':need['mostrar'],'sha256':sha,'revisao_id':rid,
                'at':math.ceil(t*30-1e-6)/30,'fonte_s':b['fonte_s'],'label':label.strip(),
                'samples':[a,b],'descricao_mudanca':raw['descricao_mudanca'],
                'publicar':False,'prova_de_acao_continua':False}
        except (KeyError,TypeError,ValueError,IndexError,AttributeError):continue
    return None

def validar(shot,source,sha,need):
    p=shot.get('observacao_temporal_candidata')
    if not isinstance(p,dict) or shot.get('type')!='video' or source.get('expected_sha256')!=sha or p.get('sha256')!=sha:return None
    if (p.get('schema')!='coringa.observed.label.private.v1' or p.get('publicar') is not False or
        p.get('prova_de_acao_continua') is not False or p.get('necessidade_id')!=shot['id'] or
        p.get('fatos')!=need.get('fatos') or p.get('mostrar')!=need.get('mostrar') or need.get('evidencia_visual')!='movimento' or
        not re.fullmatch('[a-f0-9]{64}',str(p.get('revisao_id','')))):return None
    label=p.get('label');samples=p.get('samples');t=p.get('at');orig=p.get('fonte_s');start=shot.get('source_in_seconds')
    span=shot['end']-shot['start']
    if not isinstance(label,str) or not 3<=len(label)<=34 or not label.isprintable() or not isinstance(samples,list) or len(samples)!=2:return None
    if not all(type(v) in (int,float) and math.isfinite(v) for v in (t,orig,start)) or not 0<=t<=span-.8 or not 0<=start+t-orig<1/30+1e-6:return None
    if not isinstance(p.get('descricao_mudanca'),str) or len(p['descricao_mudanca'].strip())<20:return None
    # Re-decode the selected two samples from actual master, only for this opt-in.
    # Failure removes the optional label, not the reviewed source.
    try:
        from scripts.qa_documentario_geografia_e219 import frame
        import hashlib
        a,b=samples
        if not start<=a['fonte_s']<b['fonte_s']==orig or a['pixels_sha256']==b['pixels_sha256']:return None
        for s in samples:
            im=frame(source['local_source'],s['fonte_s'],width=s['px'][0])
            if list(im.size)!=s['px'] or hashlib.sha256(im.tobytes()).hexdigest()!=s['pixels_sha256']:return None
    except Exception:return None
    return {'at':t,'label':label,'sha256':sha,'revisao_id':p['revisao_id'],'status':'PRIVATE_OBSERVATION_PENDING'}
