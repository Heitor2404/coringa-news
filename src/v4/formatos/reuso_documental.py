"""E251: opt-in rehydrated originals for private documentary inspection.
A catalogue hit is not a semantic verdict. No network fallback inside this adapter.
"""
import hashlib,json,re,unicodedata
from pathlib import Path
from PIL import Image
from src.v3.pacote_biblioteca import sha

def escopo(n):
    return {k:n.get(k) for k in ('id','sujeito','mostrar','fatos','necessidade','evidencia_visual')}

def historicos(n):
    """Explicit historical leads, never semantic approvals or a cache."""
    out=[]
    for h in n.get('candidatos_historicos') or []:
        if not isinstance(h,dict) or h.get('escopo')!=escopo(n) or h.get('publicar') is not False or h.get('direitos_aprovados') is not False or h.get('estado')!='PISTA_HISTORICA_PENDENTE':continue
        if not re.fullmatch('[0-9a-f]{64}',str(h.get('sha256',''))) or not h.get('pagina') or not h.get('relatorio') or not h.get('necessidade_anterior'):continue
        if h.get('tipo') not in ('foto','video') or (n.get('evidencia_visual')=='movimento' and h['tipo']!='video'):continue
        if n.get('necessidade') not in ('registro','lacuna_explicativa'):continue
        out.append(h)
    return out

def vinculo_historico(n,row):
    return next((h for h in historicos(n) if h['sha256']==row.get('sha256') and h['pagina']==row.get('url_pagina') and h['tipo']==row.get('tipo')),None)

def _tokens(text):
    text=unicodedata.normalize('NFKD',str(text or '').lower())
    text=''.join(c for c in text if not unicodedata.combining(c))
    return set(re.findall(r'[a-z0-9]{3,}',text))-{'the','and','with','from','this','that','real','video','photo','photograph','uma','para','com','que','por'}

def _consultas(n):
    return (n.get('pesquisa') or n).get('consultas_en') or []

def prioridade_memoria(n,row):
    """Previously observed positives are retrieval hints only. No cache migration."""
    if row.get('tipo')!='foto' or n.get('evidencia_visual')=='movimento':return 0
    if n.get('necessidade') not in ('registro','lacuna_explicativa'):return 0
    scores=[]
    for rec in (row.get('analises') or {}).values():
        if not isinstance(rec,dict) or rec.get('publicar') is not False or rec.get('direitos_aprovados') is not False:continue
        q=rec.get('revisao') or {};d=rec.get('decisao') or {};scope=rec.get('escopo_pesquisa') or {}
        if not isinstance(scope,dict) or q.get('sha256_origem')!=row.get('sha256') or q.get('publicar') is not False or d.get('estado')!='PERTINENTE_PRIVADO' or d.get('direitos_aprovados') is not False or d.get('publicar') is not False:continue
        if not q.get('revisao_id') or q.get('revisao_id')!=d.get('revisao_id') or not re.fullmatch('[0-9a-f]{64}',str(q.get('pixels_sha256',''))):continue
        if q.get('necessidade_id')!=scope.get('id') or q.get('mostrar')!=scope.get('mostrar') or scope.get('evidencia_visual')=='movimento':continue
        if _tokens(n.get('mostrar')) and _tokens(n.get('mostrar'))==_tokens(scope.get('mostrar')) and _tokens(n.get('sujeito'))==_tokens(scope.get('sujeito')):
            scores.append(1.8);continue
        for a in _consultas(n):
            aa=_tokens(a)
            for b in scope.get('consultas_en') or []:
                bb=_tokens(b)
                if len(aa&bb)>=2 and len(aa&bb)/max(len(aa),len(bb),1)>=.67:scores.append(1.1)
    return max(scores,default=0)

def negativa_observada(n,c,im):
    """A scoped external inspection can defer an incompatible exact sample,
    not declare the original useless or certify a different obligation."""
    h=c.get('pista_historica') or {};o=h.get('observacao_visual') or {}
    if h not in historicos(n) or c.get('tipo')!='foto' or h.get('sha256')!=c.get('sha_catalogo') or h.get('pagina')!=c.get('pagina'):return None
    if o.get('estado')!='INCOMPATIVEL_NA_AMOSTRA' or o.get('publicar') is not False or not o.get('relatorio_amostra') or not o.get('motivo'):return None
    if o.get('px')!=list(im.size) or o.get('pixels_sha256')!=hashlib.sha256(im.convert('RGB').tobytes()).hexdigest():return None
    return o

def candidatos(bib,necessidade,limite=4):
    if necessidade.get('necessidade') not in ('registro','lacuna_explicativa'):return []
    ev=necessidade.get('evidencia_visual')
    tipos=('video',) if ev=='movimento' else ('foto','video')
    search=necessidade.get('pesquisa') or {}
    queries=(search.get('consultas_en') or [])+(search.get('consultas') or [])
    out=[];seen=set();ranked={}
    for h in historicos(necessidade):
        d=bib.obter('cm-'+h['sha256'][:12])
        if d and not d.get('ia') and vinculo_historico(necessidade,d):
            ranked[h['sha256']]=(2,d['tipo'],d)
    # Existing SQLite analyses are also a search surface, independent of metadata hits.
    if hasattr(bib,'con'):
        for row in bib.con.execute("SELECT sha256,conteudo FROM analises WHERE tipo LIKE 'documental:%' AND tipo NOT LIKE 'documental:recibo:%'"):
            rec=json.loads(row[1]);d=bib.por_sha(row[0])
            if not d or d.get('ia'):continue
            score=prioridade_memoria(necessidade,{**d,'analises':{'r':rec}})
            if score and (row[0] not in ranked or score>ranked[row[0]][0]):ranked[row[0]]=(score,d['tipo'],d)
    for q in queries:
        for tipo in tipos:
            # Rank metadata first, but only count verified local files against the review quota.
            for d in bib.buscar(q,tipo=tipo,so_comercial=False,limite=None):
                h=d['sha256'];score=d.get('pontos',0)
                if h not in ranked or score>ranked[h][0]:ranked[h]=(score,tipo,d)
    for score,tipo,d in sorted(ranked.values(),key=lambda x:-x[0]):
        h=d['sha256']
        if h in seen or d['uso_comercial']=='nao':continue
        if tipo=='video' and d['ext'] not in ('.mp4','.webm','.mov'):continue
        if tipo=='foto' and d['ext'] not in ('.jpg','.jpeg','.png','.webp'):continue
        p=bib.caminho(h,d['ext'])
        if not p.is_file() or sha(p)!=h:continue
        seen.add(h)
        out.append({'fonte':'biblioteca_v3','source_id':d['id'],'tipo':tipo,
            'titulo':d['titulo'],'descricao':d['descricao'],'url':d['url_original'],
            'pagina':d['url_pagina'],'credito':d['atribuicao'],'licenca':d['licenca'],
            'direitos':'QUARENTENA_REVISAO_PRIVADA','sha_catalogo':h,
            'natureza_preliminar':'NATUREZA_PENDENTE_INSPECAO','publicar':False,
            'pista_memoria_semantica':1<score<2,
            **({'pista_historica':vinculo_historico(necessidade,d)} if vinculo_historico(necessidade,d) else {})})
        if len(out)>=limite:return out
    return out

def amostra(bib,c,*,probe=None,frame=None):
    if c.get('fonte')!='biblioteca_v3' or c.get('publicar') is not False:raise ValueError('E251-PRIVADO')
    d=bib.obter(c['source_id'])
    if not d or d['sha256']!=c['sha_catalogo'] or d['tipo']!=c['tipo'] or d['uso_comercial']=='nao':raise ValueError('E251-VINCULO')
    p=bib.caminho(d['sha256'],d['ext'])
    if not p.is_file() or sha(p)!=d['sha256']:raise ValueError('E251-BYTES')
    if c['tipo']=='foto':
        if d['ext'] not in ('.jpg','.jpeg','.png','.webp'):raise ValueError('E251-TIPO')
        with Image.open(p) as im:
            if im.format not in ('JPEG','PNG','WEBP') or min(im.size)<600:raise ValueError('E251-PIXELS')
            w,h=im.size;visual=im.convert('RGB')
        dur=None
    elif c['tipo']=='video':
        if d['ext'] not in ('.mp4','.webm','.mov') or probe is None or frame is None:raise ValueError('E251-TIPO')
        w,h,dur=probe(p)
        if min(w,h)<360 or dur<3:raise ValueError('E251-VIDEO')
        visual=frame(p,min(2,dur*.3),width=640)
    else:raise ValueError('E251-TIPO')
    return {'width':w,'height':h,'duration_s':dur,'sha256':d['sha256'],'bytes':p.stat().st_size,
        'url_adquirida':d['url_original'],'status':'BYTES_VERIFIED_SEMANTICS_PENDING',
        'reuso_biblioteca':True,'direitos_aprovados':False},visual,p
