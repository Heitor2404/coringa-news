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
        if verdict not in ('PRIORIZAR_AQUISICAO','ALTERNATIVA','NAO_PRIORIZAR','CONTEXTO_CONDICIONAL') or o.get('origem') not in ('INSPECAO_ASSISTIDA','CURADORIA_HUMANA','VISAO_MOTOR') or not isinstance(o.get('observacao'),str) or not o['observacao'].strip() or o.get('publicar') is not False:raise ValueError('E278-PARECER')
        if verdict=='PRIORIZAR_AQUISICAO':
            if n['id'] in choices:raise ValueError('E278-ESCOLHA-DUPLICADA')
            choices[n['id']]={'id':n['id'],'mostrar':n['mostrar'],'pagina':a['pagina'],'preview_sha256':a['preview_sha256'],'observacao_previa':o}
    return {'case':case['id'],'publicar':False,'direitos_aprovados':False,'selecao':list(choices.values())}


def revisar_folhas_lote(n,amostras,folder,ask):
    """One logical vision call per need, through the caller's budget.
    No call for an empty batch; no decisions on malformed output."""
    from pathlib import Path
    import json
    from src.v4.formatos import reuso_documental as RE
    if not amostras:return []
    if n['necessidade']!='registro' or n['evidencia_visual']=='movimento' or len(amostras)>6:raise ValueError('E278.1-ESCOPO')
    images=[];bound=[]
    for i,a in enumerate(amostras):
        name=a['folha']
        if Path(name).name!=name or a.get('estado')!='PRETRIAGEM_PENDENTE' or a.get('publicar') is not False or a.get('necessidade_id')!=n['id'] or a.get('mostrar')!=n['mostrar']:raise ValueError('E278.1-VINCULO')
        raw=(Path(folder)/name).read_bytes()
        with Image.open(io.BytesIO(raw)) as im:
            if im.format!='JPEG':raise ValueError('E281-FOLHA-JPEG')
            im.load()
        # Send the very same JPEG bytes whose hash is recorded in the
        # observation. Gemini.json_visao expects bytes, not PIL objects.
        images.append(raw)
        bound.append({'indice':i,'id':n['id'],'escopo':RE.escopo(n),'pagina':a['pagina'],'source_id':a['source_id'],'preview_sha256':a['preview_sha256'],'folha':name,'folha_sha256':hashlib.sha256(raw).hexdigest(),'origem':'VISAO_MOTOR','publicar':False})
    prompt=("Avalie apenas as miniaturas anexadas, na ordem. Objetivo visual: "+json.dumps(RE.escopo(n),ensure_ascii=False)+
            ". Observe o referente e os componentes visiveis; nao deduza identidade, licenca, movimento ou fatos ausentes. "
            "Nao trate ilustracao como registro. Se cor artificial, contexto condicional. "
            "Responda JSON {observacoes:[{indice:0,decisao:...,observacao:...}]} com todos indices exatamente uma vez. "
            "Decisoes: PRIORIZAR_AQUISICAO, ALTERNATIVA, NAO_PRIORIZAR, CONTEXTO_CONDICIONAL. "
            "No maximo uma prioridade, ou nenhuma. Isso apenas escolhe qual arquivo adquirir para revisao posterior.")
    response=ask(prompt,images)
    rows=response.get('observacoes') if isinstance(response,dict) else None
    if not isinstance(rows,list) or len(rows)!=len(bound):raise ValueError('E278.1-RESPOSTA')
    decisions=('PRIORIZAR_AQUISICAO','ALTERNATIVA','NAO_PRIORIZAR','CONTEXTO_CONDICIONAL')
    seen=set();out=[];positive=0
    for row in rows:
        i=row.get('indice') if isinstance(row,dict) else None
        if type(i) is not int or not 0<=i<len(bound) or i in seen or row.get('decisao') not in decisions or not isinstance(row.get('observacao'),str) or not row['observacao'].strip():raise ValueError('E278.1-RESPOSTA')
        seen.add(i);positive+=row['decisao']=='PRIORIZAR_AQUISICAO'
        out.append({**bound[i],'decisao':row['decisao'],'observacao':row['observacao'][:1000]})
    if positive>1:raise ValueError('E278.1-PRIORIDADE')
    return sorted(out,key=lambda x:x['indice'])


def reservar_encadeamento(necessidades,budget):
    """Two existing calls per selected static need; reserve one per other
    reviewable need first. Never expand the caller's budget."""
    reviewable=[n for n in necessidades if n['necessidade']!='territorio']
    extra=max(0,budget-len(reviewable))
    return {n['id'] for n in [x for x in reviewable if x['necessidade']=='registro' and x['evidencia_visual']=='estatica'][:extra]}


def candidato_priorizado(n,choice,amostras,pending):
    """Bind the observed lead to the already discovered original candidate.
    The preview URL stays distinct from the asset acquired by the inspector."""
    from src.v4.formatos import reuso_documental as RE
    o=choice['observacao_previa']
    if choice['id']!=n['id'] or o.get('escopo')!=RE.escopo(n) or o.get('decisao')!='PRIORIZAR_AQUISICAO' or o.get('publicar') is not False:raise ValueError('E279-ESCOPO')
    samples=[a for a in amostras if a['pagina']==choice['pagina'] and a['preview_sha256']==choice['preview_sha256'] and a['source_id']==o['source_id']]
    if len(samples)!=1:raise ValueError('E279-AMOSTRA')
    a=samples[0]
    rows=[c for c in pending if c.get('fonte')=='commons' and c.get('tipo')=='foto' and c.get('pagina')==a['pagina'] and c.get('source_id')==a['source_id'] and c.get('url')!=a['preview_url'] and any(v.get('url')==a['preview_url'] for v in c.get('variantes',[]))]
    if len(rows)!=1:raise ValueError('E279-CANDIDATO')
    c=rows[0]
    c['observacao_previa']=o
    return c


def revisar_prioridade(n,row,c,inspect,can_inspect):
    """Use the SAME formal review and round contract consumed by the film.
    A preview alone can never advance coverage."""
    if row['estado']!='LACUNA_PENDENTE' or not can_inspect():return row
    result=R.fila_cobertura(n,[c],inspect,max_candidatos=1,pode_inspecionar=can_inspect)
    rounds=[*row['rodadas'],{'rodada':len(row['rodadas'])+1,
        'pesquisa':{'id':n['id'],'buscas':[],'candidatos':[c],'origem':'PREVIA_OBSERVADA'},
        'cobertura':result}]
    return {**row,**result,'rodadas':rounds,'tentativas':row['tentativas']+result['tentativas'],
        'diagnostico':R.diagnostico_cobertura(rounds,'EVIDENCIA_REVISADA' if result['estado']=='CANDIDATO_PRIVADO_REVISADO' else 'PRIORIDADE_REVISAO_PENDENTE')}


def reserva_rede_encadeamento(http,bytes_,reservadas):
    """Leave transfer capacity for preview AND final file without increasing
    global limits. Other modalities keep at least half the shared capacity.
    Reservation is an allocation, not a new eligibility or quality rule."""
    if not reservadas:return (0,0)
    return min(http//2,4*reservadas),min(bytes_//2,29_000_000*reservadas)
