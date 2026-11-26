"""Restore E323 reviewed candidate videos from one authenticated private archive.
No new acquisition or AI; check both report window and exact pixel samples.
"""
import json,re,subprocess,sys
from pathlib import Path
from scripts.recuperar_checkpoints_documentais import api,listar_releases,REPO
from scripts.restaurar_piloto_e289 import validar_acervo
from src.v3.pacote_biblioteca import sha

def restore(config,out,root,tag):
    if config.get('publish') is not False or not re.fullmatch(r'review-e323-\d+-\d+',tag):raise ValueError('E324-ESCOPO')
    meta=api('')
    if meta.get('private') is not True or meta.get('id')!=1454059520:raise ValueError('E324-COFRE')
    rel=next(r for r in listar_releases(100) if r['tag_name']==tag and r.get('draft') is True)
    assets={a['name']:a for a in rel['assets']}
    out=Path(out);root=Path(root);root.mkdir(parents=True,exist_ok=True)
    def download(name,folder,limit):
        a=assets[name];p=folder/name
        if not 0<a['size']<=limit:raise ValueError('E324-LIMITE')
        if not p.exists():
            subprocess.run(['gh','release','download',tag,'--repo',REPO,'--pattern',name,'--dir',str(folder)],check=True,timeout=300)
        if p.stat().st_size!=a['size'] or a.get('digest')!='sha256:'+sha(p):raise ValueError('E324-SHA')
        return p
    data=json.loads((out/'acervo-restaurado.json').read_text())
    receipt=json.loads(download('evidencias.json',root,2_000_000).read_text())
    if data.get('publish') is not False or receipt.get('publish') is not False:raise ValueError('E324-PRIVADO')
    extra={};labels=[]
    for cut in config['cuts']:
        if not cut.get('review_ref','').startswith('revisoes/e323-'):continue
        r=next(r for r in receipt['records'] if r['status']=='BYTES_VERIFIED' and r['media']['id']==cut['source'])
        m=r['media'];h=cut['sha256']
        if m['media_type']!='video' or m['expected_sha256']!=h or m['label']!=cut['label'] or not re.fullmatch('[a-f0-9]{64}',h):raise ValueError('E324-ORIGEM')
        if not any(w['window_start']==cut['window_start'] and w['window_duration']==cut['window_duration'] and w['samples']==cut['samples'] for w in r['windows']):raise ValueError('E324-JANELA')
        download(h+'.mp4',root,250_000_000)
        # The rescue source's own credit explicitly names the USGS and DOI OAS.
        if m['id']=='kilauea-volcano-uas-mission-aid-rescue':
            m={**m,'credit':'USGS · DOI Office of Aviation Services · apoio HVO'}
        extra[m['id']]=m;labels.append((m['id'],m['label']))
    if not extra or set(extra)&set(data['acquired']):raise ValueError('E324-ACERVO')
    verified,_=validar_acervo({'publish':False,'acquired':extra},labels,root)
    data['acquired'].update(verified)
    (out/'acervo-restaurado.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
if __name__=='__main__':restore(json.loads(Path(sys.argv[1]).read_text()),sys.argv[2],sys.argv[3],sys.argv[4])
