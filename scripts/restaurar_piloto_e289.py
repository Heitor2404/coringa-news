"""Restore a previously acquired, hash-bound USGS pilot from the private vault.
No origin video downloads, no vision, no publication.
"""
import json,re,subprocess,sys
from pathlib import Path
from urllib.parse import urlsplit
from scripts.recuperar_checkpoints_documentais import api,listar_releases,REPO
from src.v3.pacote_biblioteca import sha

def validar_acervo(data,rows,root):
    from scripts.qa_documentario_geografia_e219 import probe,HOSTS
    if data.get('publish') is not False:raise ValueError('E289-PRIVADO')
    labels=dict(rows);out={}
    for slug,m in data['acquired'].items():
        if slug not in labels or m.get('id')!=slug or m.get('label')!=labels[slug]:raise ValueError('E289-ESCOPO')
        h=m.get('expected_sha256','')
        if not re.fullmatch(r'[0-9a-f]{64}',h) or m.get('license')!='Public domain' or m.get('page')!='https://www.usgs.gov/media/videos/'+slug or not re.fullmatch(r'[0-9a-f]{64}',m.get('page_sha256','')):raise ValueError('E289-RECIBO')
        u=urlsplit(m.get('url_original',''))
        if u.scheme!='https' or u.hostname not in HOSTS:raise ValueError('E289-ORIGEM')
        p=Path(root)/(h+'.mp4')
        if not p.is_file() or sha(p)!=h:raise ValueError('E289-SHA')
        w,height,d=probe(p)
        if (w,height)!=(m['width'],m['height']) or abs(d-m['duration_s'])>.02:raise ValueError('E289-DIMENSOES')
        out[slug]={**m,'local_source':str(p)}
    return out,data.get('errors',[])

def restore(tag,out,root):
    if not re.fullmatch(r'review-e287-\d+-\d+',tag):raise ValueError('E289-TAG')
    meta=api('')
    if meta.get('private') is not True or meta.get('id')!=1454059520:raise ValueError('E289-COFRE')
    rel=next(r for r in listar_releases(100) if r['tag_name']==tag and r['draft'] is True)
    assets={a['name']:a for a in rel['assets']}
    out=Path(out);root=Path(root);out.mkdir(parents=True,exist_ok=True);root.mkdir(parents=True,exist_ok=True)
    def check(name,p):
        a=assets[name]
        if a.get('digest')!='sha256:'+sha(p) or p.stat().st_size!=a['size']:raise ValueError('E289-ASSET-SHA')
    def download(name,folder):
        subprocess.run(['gh','release','download',tag,'--repo',REPO,'--pattern',name,'--dir',str(folder)],check=True,timeout=300)
        check(name,folder/name)
    download('acervo.json',out);download('preflight-piloto.json',out)
    data=json.loads((out/'acervo.json').read_text());pre=json.loads((out/'preflight-piloto.json').read_text())
    if data.get('publish') is not False or pre.get('publish') is not False or any(x.get('type')=='video' and not x.get('windows') for x in pre['chapters']):raise ValueError('E289-PREFLIGHT')
    names={m['expected_sha256']+'.mp4' for m in data['acquired'].values()}
    if any(not re.fullmatch(r'[0-9a-f]{64}\.mp4',n) or assets[n]['digest']!='sha256:'+n[:-4] or not 0<assets[n]['size']<=250_000_000 for n in names) or sum(assets[n]['size'] for n in names)>1_500_000_000:raise ValueError('E289-LIMITE')
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(lambda n:download(n,root),sorted(names)))
    (out/'acervo-restaurado.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
    print('E289 ORIGINAIS RESTAURADOS',len(names),'bytes',sum(assets[n]['size'] for n in names),flush=True)
if __name__=='__main__':restore(sys.argv[1],sys.argv[2],sys.argv[3])
