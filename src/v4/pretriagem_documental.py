"""Bounded provider-declared preview acquisition for private documentary research.
Preview bytes and metadata are leads only, never master identity or coverage.
"""
import hashlib,io
from PIL import Image
from src.v4.formatos import revisao_documental as R

def candidatos(n,rows,previous_pages=()):
    if n.get('evidencia_visual')=='movimento' or n.get('necessidade') not in ('registro','lacuna_explicativa'):return []
    seen=set(previous_pages);out=[]
    for c in R.ordenar_candidatos(n,rows):
        page=c.get('pagina')
        if not page or page in seen or c.get('tipo')!='foto' or c.get('fonte')!='commons' or c.get('direitos')!='DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA' or c.get('natureza_preliminar')=='REPRESENTACAO_DECLARADA':continue
        seen.add(page)
        if R.incompatibilidade_metadados(n,c):continue
        v=next((v for v in c.get('variantes') or [] if v.get('url') and v['url']!=c.get('url') and all(type(v.get(k)) is int and 240<=v[k]<=2400 for k in ('width','height'))),None)
        if v:out.append((c,v))
    # Keep the most relevant choice first, then prefer another actual query
    # before spending a small preview quota on a single result series.
    # Unknown origin is a single group; no candidate is removed.
    first=[];later=[];queries=set()
    for item in out:
        key=str(item[0].get('consulta_origem') or '').strip().casefold()
        if key in queries:later.append(item)
        else:queries.add(key);first.append(item)
    return first+later

def coletar_fila(queues,transport,on_sample,*,max_samples=3,max_preview_bytes=1_000_000):
    """Round-robin attempts. No obligation monopolizes the shared budget.
    Failures count in the same transport. Callback receives exact preview digest.
    """
    if not 1<=max_samples<=6 or not 1<=max_preview_bytes<=2_000_000:raise ValueError('PRETRIAGEM-LIMITE')
    states=[{'n':n,'pending':iter(rows),'samples':[],'errors':[]} for n,rows in queues]
    active=list(states)
    while active and transport.http<transport.max_http and transport.bytes<transport.max_bytes:
        next_round=[]
        for st in active:
            if transport.http>=transport.max_http or transport.bytes>=transport.max_bytes:break
            n=st['n']
            if len(st['samples'])>=max_samples:continue
            item=next(st['pending'],None)
            if item is None:continue
            c,v=item
            try:
                raw=transport.get(v['url'],{'upload.wikimedia.org','thumb.wikimedia.org'},max_preview_bytes)
                with Image.open(io.BytesIO(raw)) as img:
                    if img.format not in ('JPEG','PNG','WEBP') or min(img.size)<240 or max(img.size)>2400:raise ValueError('PREVIEW_PIXELS')
                    im=img.convert('RGB')
                digest=hashlib.sha256(raw).hexdigest()
                result=on_sample(n,c,v,im,digest,len(st['samples'])+1)
                st['samples'].append(result)
            except Exception as e:st['errors'].append({'pagina':c['pagina'],'motivo':str(e)[:180]})
            if len(st['samples'])<max_samples:next_round.append(st)
        active=next_round
    return [{'id':s['n']['id'],'amostras':s['samples'],'erros':s['errors']} for s in states]


def pendencias_do_fluxo(necessidades,resultados,estados):
    """Use only the existing progressive queue; no new discovery or approval."""
    rows={r['necessidade_id']:r for r in resultados}
    queues=[]
    for n in necessidades:
        if rows.get(n['id'],{}).get('estado')!='LACUNA_PENDENTE':continue
        pending=estados.get(n['id'],{}).get('pendentes',[])
        choices=candidatos(n,pending)
        if choices:queues.append((n,choices))
    return queues
