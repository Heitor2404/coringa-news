"""Recover useful private V3 packages from the existing vault, not a new database."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
from src.v3 import pacote_biblioteca as P
from src.v4.formatos import reuso_documental as RE

REPO='Heitor2404/coringa-cofre'
def api(path):
    return json.loads(subprocess.check_output(['gh','api','repos/'+REPO+path],timeout=60))
def tokens(s):
    return set(re.findall(r'[a-z0-9]{3,}',str(s).lower()))-{'the','and','with','from','this','that','video','footage','real'}
def relevances(row,needs):
    typ=row.get('tipo')
    words=tokens(' '.join(str(row.get(k) or '') for k in ('titulo','descricao','mostra')))
    scores={}
    for n in needs:
        if n.get('necessidade') not in ('registro','lacuna_explicativa') or (n.get('evidencia_visual')=='movimento' and typ!='video'):continue
        if RE.vinculo_historico(n,row):scores[n['id']]=2
        for q in n.get('consultas_en') or []:
            qs=tokens(q)
            if qs:
                nid=n.get('id')
                scores[nid]=max(scores.get(nid,0),len(qs&words)/len(qs))
    return {k:v for k,v in scores.items() if v>0}

def relevance(row,needs):
    return max(relevances(row,needs).values(),default=0)

def priorizar(ranked):
    # Offer each obligation its best lexical candidate before alternatives.
    # This is ordering, never evidence or approval. Keep all alternatives.
    ranked=sorted(ranked,key=lambda x:-max(x[0].values()))
    best={}
    for scores,tag,a in ranked:
        for nid,score in scores.items():
            if nid not in best or score>best[nid][0]:best[nid]=(score,tag,a)
    preferred={(tag,a['name']) for _,tag,a in best.values()}
    return sorted(ranked,key=lambda x:( (x[1],x[2]['name']) not in preferred, -max(x[0].values())))
def verified_download(tag,a,root):
    name=a['name'];digest=a.get('digest') or ''
    if not re.fullmatch(r'sha256:[0-9a-f]{64}',digest):raise ValueError('E259-DIGEST')
    if not re.fullmatch(r'(?:cm-[0-9a-f]{12}\.zip|manifesto-revisoes\.jsonl)',name):raise ValueError('E259-NOME')
    root.mkdir(parents=True,exist_ok=True)
    subprocess.run(['gh','release','download',tag,'--repo',REPO,'--pattern',name,'--dir',str(root)],check=True,timeout=120)
    p=root/name
    if p.stat().st_size!=a['size'] or P.sha(p)!=digest[7:]:raise ValueError('E259-DOWNLOAD-SHA')
    return p
def listar_releases(max_releases):
    # Bounded catalogue pagination; count manifests separately from release rows.
    if type(max_releases) is not int or not 1<=max_releases<=100:raise ValueError('E259-LIMITE-RELEASES')
    size=min(20,max_releases);rows=[]
    for page in range(1,(max_releases+size-1)//size+1):
        batch=api('/releases?per_page='+str(size)+'&page='+str(page))
        if not isinstance(batch,list):raise ValueError('E259-LISTA')
        rows.extend(batch)
        if len(batch)<size:break
    return rows[:max_releases]


def discover(needs,root,*,max_releases=60,max_bytes=100_000_000,max_packages=None):
    # Scale the package count with the actual obligations, within the same byte budget.
    if max_packages is None:max_packages=max(6,min(36,2*len(needs)))
    if type(max_packages) is not int or not 1<=max_packages<=100:raise ValueError('E259-LIMITE-PACOTES')
    root=Path(root);meta=api('')
    if meta.get('private') is not True or meta.get('id')!=1454059520:raise ValueError('E259-COFRE')
    releases=listar_releases(max_releases);ranked=[];events=[];spent=0;manifests=0
    for rel in releases:
        tag=rel.get('tag_name','')
        if rel.get('draft') is not True or not re.fullmatch(r'review-[a-z0-9-]+',tag):continue
        assets={a['name']:a for a in rel.get('assets',[])}
        manifest=assets.get('manifesto-revisoes.jsonl')
        if not manifest or not 0<manifest['size']<=8_000_000 or spent+manifest['size']>max_bytes:continue
        if not any(re.fullmatch(r'cm-[0-9a-f]{12}\.zip',k) for k in assets):continue
        folder=root/tag
        try:
            spent+=manifest['size']
            p=verified_download(tag,manifest,folder);manifests+=1
            for line in p.read_text(encoding='utf8').splitlines():
                row=json.loads(line);mid=row.get('id','');asset=assets.get(mid+'.zip')
                if not asset or not re.fullmatch(r'cm-[0-9a-f]{12}',mid) or not 0<asset['size']<=P.MAX_TOTAL+10_000_000:continue
                scores=relevances(row,needs)
                if scores:ranked.append((scores,tag,asset))
        except (OSError,ValueError,subprocess.SubprocessError,KeyError) as e:events.append({'tag':tag,'motivo':type(e).__name__})
    dirs=[];seen=set()
    skipped={'duplicado':0,'limite_pacotes':0,'limite_bytes':0}
    for scores,tag,a in priorizar(ranked):
        mid=a['name'][:-4]
        if mid in seen:skipped['duplicado']+=1;continue
        if len(dirs)>=max_packages:skipped['limite_pacotes']+=1;continue
        if spent+a['size']>max_bytes:skipped['limite_bytes']+=1;continue
        try:
            spent+=a['size']
            p=verified_download(tag,a,root/tag)
            dest=P.extrair_checkpoint(p,root/tag/mid,expected_sha256=a['digest'][7:])
            dirs.append(str(dest));seen.add(mid)
            events.append({'id':mid,'tag':tag,'score':max(scores.values()),'prioridades_por_necessidade':scores, 'pista_historica':any(v==2 for v in scores.values()),'estado':'PACOTE_LOCAL_VERIFICADO'})
        except (OSError,ValueError,subprocess.SubprocessError,KeyError) as e:events.append({'id':mid,'motivo':type(e).__name__})
    return {'pacotes':dirs,'releases_examinadas':len(releases),'limite_releases':max_releases,'manifestos_lidos':manifests,'candidatos_ranqueados':len(ranked),'limite_pacotes':max_packages,'nao_restaurados':skipped,'bytes_reservados':spent,'eventos':events,'publicar':False,'direitos_aprovados':False}
def main():
    spec=json.loads(Path(sys.argv[1]).read_text());case=next(c for c in spec['cases'] if c['id']==sys.argv[2])
    if spec.get('publish') is not False:raise ValueError('E259-PRIVADO')
    root=Path(sys.argv[3]);root.mkdir(parents=True,exist_ok=True)
    report=discover(case['necessidades'],root)
    (root/'descoberta.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print('E259 PACOTES',len(report['pacotes']))
if __name__=='__main__':main()
