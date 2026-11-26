"""E381: opt-in ephemeral Pixabay context in the existing private compositor.
Never upgrades factual coverage, never caches media, never approves rights."""
import hashlib,math,re,tempfile
from pathlib import Path
from contextlib import contextmanager
from urllib.parse import urlsplit
from src.v4.fontes_publicas_e354 import safe
from src.v4.fontes_contextuais_e359 import stock_declarado_sintetico
from src.v3.pacote_biblioteca import sha

LICENSE='https://pixabay.com/service/license-summary/'
HOSTS={'cdn.pixabay.com'}
LABEL='IMAGEM DE CONTEXTO'
def escopo(n):
    return n.get('necessidade')=='registro' and n.get('evidencia_visual')=='contexto' and n.get('exigir_evidencia_direta') is False and bool(n.get('id'))

def receipt_valid(asset):
    d=asset.get('documentary_receipt') or {};r=d.get('recibo') or {}
    ident=r.get('id');page=asset.get('page');author=r.get('author')
    if not isinstance(ident,str) or not re.fullmatch(r'[0-9]+',ident):return False
    return (d.get('provedor')=='pixabay_contextual' and r.get('direitos')=='PENDENTE_AUDITORIA_INDIVIDUAL'
        and d.get('publicar') is False and d.get('direitos_aprovados') is False
        and d.get('sha256_origem')==asset.get('expected_sha256') and type(d.get('bytes')) is int and 0<d['bytes']<=18_000_000
        and r.get('page')==page and safe(page,{'pixabay.com','www.pixabay.com'}) and re.search(r'(?:-|/)'+ident+r'/?$',urlsplit(page).path) is not None
        and isinstance(author,str) and bool(author.strip()) and asset.get('credit')==author+' · Pixabay'
        and r.get('license_url')==LICENSE and asset.get('license')=='REVIEW_PENDING' and asset.get('rights_status')=='REVIEW_PENDING'
        and asset.get('media_type')=='video' and r.get('scope')=='CONTEXTO_APENAS' and r.get('permanent_cache') is False
        and r.get('proof_factual') is False and isinstance(r.get('title'),str) and not stock_declarado_sintetico(r['title'])
        and safe(d.get('url_adquirida'),HOSTS) and r.get('variant_url')==d['url_adquirida'])

def candidate_for(n,report,ident):
    if not escopo(n) or report.get('id')!=n['id']:raise ValueError('E381-SCOPE')
    lane=report.get('stock_contextual') or {}
    if lane.get('prova_factual') is not False or lane.get('publicar') is not False or lane.get('estado')!='LEADS':raise ValueError('E381-LANE')
    rows=[c for c in lane.get('candidatos',[]) if c.get('id')==ident]
    if len(rows)!=1:raise ValueError('E381-ID')
    c=rows[0]
    if c.get('provider')!='pixabay' or c.get('editorial_scope')!='CONTEXTO_APENAS' or c.get('permanent_cache') is not False or c.get('publish') is not False or c.get('semantic_approval') is not False or stock_declarado_sintetico(c.get('title')):raise ValueError('E381-CANDIDATE')
    return c

@contextmanager
def materializar(n,report,ident,transport,public,*,probe=None):
    from src.v4.formatos.filme_editorial import MIN_VIDEO_COMPOSITION_PX
    c=candidate_for(n,report,ident)
    vs=[v for v in c.get('variants',[]) if safe(v.get('url'),HOSTS) and type(v.get('size')) is int and 0<v['size']<=18_000_000 and all(type(v.get(k)) is int and v[k]>=MIN_VIDEO_COMPOSITION_PX for k in ('w','h'))]
    if not vs:raise ValueError('E381-NO-VARIANT')
    v=min(vs,key=lambda x:(n.get('preferir_imersao_vertical') is True and x['h']<=x['w'],x['size']))
    raw=transport.get(v['url'],HOSTS,18_000_000)
    h=hashlib.sha256(raw).hexdigest()
    if len(raw)!=v['size']:raise ValueError('E381-BYTES')
    public=Path(public);copy_path=public/'film_editorial'/(h+'.mp4')
    if copy_path.exists():raise ValueError('E381-PREEXISTING-STOCK-COPY')
    stage=Path('stage_documental');stage.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='stock-ephemeral-',dir=stage) as td:
        p=Path(td)/(h+'.mp4');p.write_bytes(raw)
        if probe is None:
            from scripts.qa_documentario_geografia_e219 import probe
        w,hh,dur=probe(p)
        if (w,hh)!=(v['w'],v['h']) or not math.isfinite(dur) or dur<3:raise ValueError('E381-DECODE')
        r=dict(id=c['id'],page=c['page'],author=c['author'],license_url=c['license_url'],title=c['title'],variant_url=v['url'],scope='CONTEXTO_APENAS',permanent_cache=False,proof_factual=False,direitos='PENDENTE_AUDITORIA_INDIVIDUAL')
        a=dict(local_source=str(p),expected_sha256=h,media_type='video',width=w,height=hh,duration_s=dur,page=c['page'],credit=c['author']+' · Pixabay',license='REVIEW_PENDING',rights_status='REVIEW_PENDING',documentary_receipt=dict(provedor='pixabay_contextual',sha256_origem=h,bytes=len(raw),url_adquirida=v['url'],recibo=r,publicar=False,direitos_aprovados=False))
        if not receipt_valid(a):raise ValueError('E381-RECEIPT')
        try:yield a
        finally:
            # Only this session's copy may be removed; no shared cache changes.
            if copy_path.is_file() and sha(copy_path)==h:copy_path.unlink()

def previa(n,asset,*,start=1.0,span=3.2):
    if not escopo(n) or not receipt_valid(asset):raise ValueError('E381-PREVIEW-SCOPE')
    if not (1.4<=span<=3.8 and 0<=start and start+span<=asset['duration_s']):raise ValueError('E381-WINDOW')
    subject=n.get('sujeito')
    if not isinstance(subject,str) or not subject.strip():raise ValueError('E381-SUBJECT')
    return dict(formato='filme_editorial',tipo='PROVA_VISUAL_PRIVADA',publicar=False,titulo=subject,duracao=span,documentary_framing='ADAPTIVE_REVIEW_V1',
        media={'context':asset},necessidades_direcao=[n],
        shots=[dict(id=n['id'],type='video',asset='context',start=0,end=span,source_in_seconds=start,headline=subject,subject=subject,evidence='representative',source_display=LABEL+' · Pixabay',video_zoom=1,focus=[.5,.5],video_context_layout='cena_integral',cues=[{'at':.2,'label':subject}])])
