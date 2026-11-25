"""Public Figshare discovery: per-item/file receipts, no blanket OA assumption."""
import hashlib,json,re
from urllib.parse import urlsplit
import requests
from src.v4.aquisicao_documental import UA

API='https://api.figshare.com/v2/articles'
HOSTS={'figshare.com','ndownloader.figshare.com','ndownloader.figsh.com','api.figshare.com'}
EXT={'video':('.mp4','.webm','.mov'), 'foto':('.jpg','.jpeg','.png','.webp')}
LICENSES={
    'https://creativecommons.org/licenses/by/4.0':'CC BY 4.0',
    'https://creativecommons.org/publicdomain/zero/1.0':'CC0 1.0',
}
def safe_url(u,hosts):
    if not isinstance(u,str):return False
    try:
        p=urlsplit(u)
        return p.scheme=='https' and p.hostname in hosts and not p.username and not p.password and p.port in (None,443)
    except ValueError:return False

def _json(session,method,url,**kwargs):
    with session.request(method,url,headers=UA,timeout=(10,25),stream=True,allow_redirects=False,**kwargs) as r:
        if r.status_code!=200:raise ValueError('FIGSHARE_HTTP_'+str(r.status_code))
        data=bytearray()
        for b in r.iter_content(65536):
            data.extend(b)
            if len(data)>2_000_000:raise ValueError('FIGSHARE_METADATA_LIMIT')
    return json.loads(data),hashlib.sha256(data).hexdigest()

def candidatos(consulta,tipo,*,session=None):
    if tipo not in EXT or not isinstance(consulta,str) or not 2<=len(consulta.strip())<=180:raise ValueError('FIGSHARE_QUERY')
    s=session or requests.Session()
    rows,_=_json(s,'POST',API+'/search',json={'search_for':consulta,'limit':5})
    out=[]
    for row in rows[:5]:
        aid=row.get('id')
        if type(aid) is not int or aid<=0:continue
        d,receipt=_json(s,'GET',API+'/'+str(aid))
        if d.get('id')!=aid or d.get('is_embargoed') or d.get('is_confidential') or d.get('is_metadata_record'):continue
        lic=(d.get('license') or {}).get('url','').rstrip('/')
        # The license URI is explicit, not inferred from the repository name.
        if lic.startswith('http://creativecommons.org/'):lic='https://'+lic[7:]
        if lic not in LICENSES:continue
        authors=[a.get('full_name') for a in d.get('authors',[]) if isinstance(a,dict) and a.get('full_name')]
        doi=d.get('doi')
        if not authors or not isinstance(doi,str) or not re.fullmatch(r'10\.\d{4,9}/[^\s]+',doi):continue
        page=d.get('url_public_html')
        if not isinstance(page,str) or urlsplit(page).scheme!='https':continue
        for f in d.get('files',[])[:15]:
            if not isinstance(f,dict):continue
            name=f.get('name','');fid=f.get('id');url=f.get('download_url');size=f.get('size')
            if not isinstance(name,str) or not name.lower().endswith(EXT[tipo]) or type(fid) is not int or fid<=0 or f.get('is_link_only') or type(size) is not int or not 0<size<=(80_000_000 if tipo=='video' else 26_000_000) or not safe_url(url,HOSTS):continue
            md5=f.get('computed_md5') or f.get('supplied_md5')
            if not isinstance(md5,str) or not re.fullmatch('[0-9a-fA-F]{32}',md5):continue
            out.append({'titulo':str(d.get('title') or name),'descricao':str(d.get('description') or '')[:8000],
                'url':url,'pagina':page,'licenca':LICENSES[lic],'licenca_url':lic,
                'credito':', '.join(authors)+' ('+LICENSES[lic]+')','source_id':f'{aid}:{fid}',
                'tamanho_original':size,'recibo_cientifico':{'provedor':'figshare','article_id':aid,
                'file_id':fid,'doi':doi,'file_name':name,'authors':authors,'licenca_url':lic,
                'metadata_sha256':receipt,'md5_declarado':md5.lower(),'bytes':size,
                'direitos':'PENDENTE_AUDITORIA_INDIVIDUAL'}})
            if len(out)>=4:return out
    return out
