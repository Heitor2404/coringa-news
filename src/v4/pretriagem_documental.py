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
        variants=[v for v in c.get('variantes') or [] if v.get('url') and v['url']!=c.get('url') and all(type(v.get(k)) is int and 240<=v[k]<=2400 for k in ('width','height'))]
        if variants:
            # Prefer a declared preview near the already validated 640px
            # request, not a guessed URL or a low-resolution master.
            v=min(variants,key=lambda x:(abs(max(x['width'],x['height'])-640),x['width']*x['height']))
            out.append((c,v))
    # Keep the most relevant choice first, then prefer another actual query
    # before spending a small preview quota on a single result series.
    # Unknown origin is a single group; no candidate is removed.
    # Diversity only within contiguous relevance bands. A new query
    # is not an editorial reason to promote an ambiguous result.
    from itertools import groupby
    result=[]
    def band(item):
        c=item[0]
        return (R.contexto_de_busca(n,c),R.cobertura_componentes(n,c),R.forca_contextual(n,c))
    for _,items in groupby(out,key=band):
        first=[];later=[];queries=set()
        for item in items:
            key=str(item[0].get('consulta_origem') or '').strip().casefold()
            if key in queries:later.append(item)
            else:queries.add(key);first.append(item)
        result.extend(first+later)
    return result

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


def escolhas_observadas(spec,report,observations,folder):
    """Select only scoped observed preview leads, not semantic coverage.
    The observer is explicitly named by origin; no model or rights approval
    is inferred. Verify the exact saved review sheet, not the raw preview
    hash (which belongs to the provider bytes before recompression)."""
    from pathlib import Path
    import re
    from src.v4.formatos import diretor_visual_e202 as D,reuso_documental as RE
    if any(x.get('publicar',x.get('publish')) is not False for x in (spec,report,observations)) or observations.get('direitos_aprovados') is not False:raise ValueError('E278-PRIVADO')
    case=next(c for c in spec['cases'] if c['id']==observations['case'])
    needs={n['id']:n for n in D.triagem_documental(case['necessidades'],case['fatos'],progressivo=True)}
    rows={(g['id'],a.get('pagina'),a.get('preview_sha256')):a for g in report['necessidades'] for a in g['amostras']}
    seen=set();choices={}
    for o in observations['observacoes']:
        n=needs[o['id']]
        k=(o['id'],o['pagina'],o['preview_sha256'])
        a=rows.get(k)
        if k in seen or not a or o.get('escopo')!=RE.escopo(n) or n['necessidade']!='registro' or n['evidencia_visual']=='movimento':raise ValueError('E278-ESCOPO')
        seen.add(k)
        if a.get('estado')!='PRETRIAGEM_PENDENTE' or a.get('publicar') is not False or o.get('source_id')!=a.get('source_id') or o.get('folha')!=a.get('folha'):raise ValueError('E278-VINCULO')
        name=o['folha']
        if Path(name).name!=name or not re.fullmatch(r'[0-9a-f]{64}',str(o.get('folha_sha256',''))) or hashlib.sha256((Path(folder)/name).read_bytes()).hexdigest()!=o['folha_sha256']:raise ValueError('E278-FOLHA')
        verdict=o.get('decisao')
        if verdict not in ('PRIORIZAR_AQUISICAO','ALTERNATIVA','NAO_PRIORIZAR','CONTEXTO_CONDICIONAL') or o.get('origem') not in ('INSPECAO_ASSISTIDA','CURADORIA_HUMANA') or not isinstance(o.get('observacao'),str) or not o['observacao'].strip() or o.get('publicar') is not False:raise ValueError('E278-PARECER')
        if verdict=='PRIORIZAR_AQUISICAO':
            if n['id'] in choices:raise ValueError('E278-ESCOLHA-DUPLICADA')
            choices[n['id']]={'id':n['id'],'mostrar':n['mostrar'],'pagina':a['pagina'],'preview_sha256':a['preview_sha256'],'observacao_previa':o}
    return {'case':case['id'],'publicar':False,'direitos_aprovados':False,'selecao':list(choices.values())}
