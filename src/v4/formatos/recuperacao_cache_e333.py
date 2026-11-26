"""E333: re-use alternative historical windows of the exact same obligation.
The caller authenticates pixels; no lexical guessing or extra vision.
"""
from copy import deepcopy
from . import direcao_eventos as DE,revisao_documental as R,especificidade_movimento_e331 as M

def alternativa(need,candidate,validate,*,estrita=False):
    if need.get('evidencia_visual')!='movimento' or candidate.get('tipo')!='video':return None
    a=candidate['aquisicao'];h=a['sha256'];old=candidate['decisao']['revisao_id']
    media={'id':candidate.get('source_id'),'expected_sha256':h,'duration_s':a['duration_s'],'width':a['width'],'height':a['height']}
    eligible=[]
    for row in candidate.get('janelas',[]):
        p=row.get('pacote') or {};q=p.get('revisao_assistida') or {}
        if (p.get('revisao_id')==old or p.get('publicar') is not False or p.get('sha256_origem')!=h
            or p.get('fato_id')!=need['fatos'][0] or p.get('necessidade')!=need['mostrar']
            or q.get('revisao_id')!=p.get('revisao_id') or not p.get('amostras')):continue
        try:
            d=R.decidir(need,candidate,q,tipo='video')
            if d['estado']!='PERTINENTE_PRIVADO':continue
            if estrita and not correspondencia_explicita(q):continue
            s=DE.candidato_revisado(p,media,fato_id=need['fatos'][0])
            if s['estado']!='CANDIDATO_PERTINENTE':continue
            eligible.append({'pacote':p,'midia':media,'decisao':d,'selection':s})
        except (ValueError,KeyError,TypeError,AttributeError):continue
    for ranked in DE.selecionar_revisados(eligible,fato_id=need['fatos'][0],preferir_legibilidade=bool(need.get('exigir_legibilidade'))):
        x=eligible[ranked['ordem']]
        c={**deepcopy(candidate),'decisao':x['decisao'],'selecao_janela':x['selection']}
        if not validate(need,c):continue
        return {'estado':'CANDIDATO_PRIVADO_REVISADO','selecionado':[c.get('fonte'),c.get('source_id') or c.get('url')],
            'rodadas':[{'pesquisa':{'candidatos':[c]}}],'publicar':False,'origem':'JANELA_HISTORICA_REVALIDADA'}
    return None


def correspondencia_explicita(q):
    """Legacy stays available for private review, not automatic exact-action recovery."""
    raw=q.get('resposta_bruta') or {}
    observed=q.get('resposta_observada') or {}
    return (M.avaliar(raw)['estado']=='DIRETA_DECLARADA'
            and M.avaliar(observed)['estado']=='DIRETA_DECLARADA'
            and raw.get('correspondencia_acao')==observed.get('correspondencia_acao'))

def selecionado(row):
    selected=row.get('selecionado')
    if not selected:return None
    return next((c for r in reversed(row.get('rodadas',[]))
        for c in reversed(r.get('pesquisa',{}).get('candidatos',[]))
        if [c.get('fonte'),c.get('source_id') or c.get('url')]==list(selected)
        and c.get('tipo')=='video' and (c.get('decisao') or {}).get('estado')=='PERTINENTE_PRIVADO'),None)

def revalidar(need,candidate,extrair):
    """Authenticate exact original and three original decoded samples; diagnostic
    motion is not a semantic verdict. No provider request, no new review."""
    import hashlib,json,math
    from pathlib import Path
    from . import diagnostico_movimento_e334 as DM
    a=candidate['aquisicao'];d=candidate['decisao'];w=candidate['selecao_janela']
    h=a['sha256'];rid=d['revisao_id'];src=Path(candidate['local_source'])
    if not src.is_file() or (a.get('bytes') is not None and src.stat().st_size!=a['bytes']):
        raise ValueError('E334-ORIGINAL')
    digest=hashlib.sha256()
    with src.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):digest.update(chunk)
    if digest.hexdigest()!=h:raise ValueError('E334-SHA')
    p=next((r.get('pacote') for r in candidate.get('janelas',[]) if (r.get('pacote') or {}).get('revisao_id')==rid),None)
    if not p:raise ValueError('E334-JANELA')
    q=p.get('revisao_assistida') or {}
    if (p.get('publicar') is not False or q.get('publicar') is not False
        or p.get('sha256_origem')!=h or q.get('sha256_origem')!=h
        or q.get('necessidade_id')!=need['id'] or q.get('revisao_id')!=rid
        or p.get('fato_id')!=need['fatos'][0] or p.get('necessidade')!=need['mostrar']
        or p.get('inicio_s')!=w.get('source_in_seconds') or w.get('revisao_id')!=rid
        or p.get('duracao_s')!=w.get('duracao_s')):raise ValueError('E334-ESCOPO')
    base={k:p[k] for k in ('sha256_origem','inicio_s','duracao_s','fato_id','necessidade','amostras')}
    if hashlib.sha256(json.dumps(base,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()!=rid:
        raise ValueError('E334-ID')
    samples=p['amostras'];frames=[]
    if len(samples)!=3:raise ValueError('E334-AMOSTRAS')
    times=[s['fonte_s'] for s in samples]
    if not all(type(t) in (int,float) and math.isfinite(t) and p['inicio_s']<=t<p['inicio_s']+p['duracao_s'] for t in times) or not times[0]<times[1]<times[2]:
        raise ValueError('E334-TEMPOS')
    for s in samples:
        im=extrair(src,s['fonte_s'],width=s['px'][0]).convert('RGB')
        if list(im.size)!=s['px'] or hashlib.sha256(im.tobytes()).hexdigest()!=s['pixels_sha256']:
            raise ValueError('E334-PIXELS')
        frames.append(im)
    v=DE.aceitar_observacao(p,q['resposta_observada'])
    if v['veredito']!='pertinente' or v['video_framing']!=w.get('video_framing'):
        raise ValueError('E334-ENQUADRAMENTO')
    fresh=R.decidir(need,candidate,q,tipo='video')
    diagnostic=DM.diagnosticar(frames,times,v['video_framing'])
    return {'status':'PIXELS_REVALIDATED','sha256':h,'review_id':rid,
            'samples':[s['pixels_sha256'] for s in samples],
            'correspondencia_explicita':correspondencia_explicita(q),
            'decisao_atual':fresh['estado'],'diagnostico_movimento':diagnostic,
            'aprovacao_semantica':False,'publicar':False}

def recuperar_reservada(need,row,extrair,reservar,*,historicas=(),diagnosticos=None):
    """Try already acquired bytes before paid search. A reservation must be
    accepted by the caller's existing transaction, never invented here."""
    c=selecionado(row)
    if not c:return None
    from . import amostragem_documental as AD
    c={**c,'janelas':AD.consolidar_janelas(historicas,c.get('janelas',[]))}
    def validar(n,x):
        try:
            proof=revalidar(n,x,extrair)
            if diagnosticos is not None:diagnosticos.append(proof)
            if proof['decisao_atual']!='PERTINENTE_PRIVADO' or not proof['correspondencia_explicita']:return False
            x['recuperacao_amostras']=proof
            return reservar(n,x)
        except (ValueError,KeyError,TypeError,AttributeError,OSError,RuntimeError) as exc:
            if diagnosticos is not None:diagnosticos.append({'status':'REVALIDACAO_PENDENTE','reason':str(exc)[:180],'publicar':False})
            return False
    return alternativa(need,c,validar,estrita=True)
