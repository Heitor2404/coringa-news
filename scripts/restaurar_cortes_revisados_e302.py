"""Restore explicitly reviewed source windows from authenticated private release.
No public downloads, new AI, or semantic inference from metadata alone.
"""
import json,re,subprocess,sys
from pathlib import Path
from scripts.recuperar_checkpoints_documentais import api,listar_releases,REPO
from src.v3.pacote_biblioteca import sha
from scripts.restaurar_piloto_e289 import validar_acervo

def restore(config,out,root):
    if config.get('publish') is not False or config.get('schema')!='coringa.reviewed-cut.private.v1':
        raise ValueError('E302-SCHEMA')
    tag=config['release']
    if not re.fullmatch(r'review-e300-\d+-\d+',tag):raise ValueError('E302-TAG')
    meta=api('')
    if meta.get('private') is not True or meta.get('id')!=1454059520:raise ValueError('E302-COFRE')
    rel=next(r for r in listar_releases(100) if r['tag_name']==tag and r['draft'] is True)
    assets={a['name']:a for a in rel['assets']}
    out=Path(out);root=Path(root)
    def download(name,folder,limit):
        a=assets[name];p=folder/name
        if not 0<a['size']<=limit:raise ValueError('E302-LIMITE')
        if not p.exists():
            subprocess.run(['gh','release','download',tag,'--repo',REPO,'--pattern',name,'--dir',str(folder)],check=True,timeout=300)
        if p.stat().st_size!=a['size'] or a.get('digest')!='sha256:'+sha(p):raise ValueError('E302-SHA')
        return p
    receipt=json.loads(download('coverage.json',out,2_000_000).read_text())
    if receipt.get('publish') is not False:raise ValueError('E302-PRIVADO')
    extra={}
    base=json.loads((out/'acervo-restaurado.json').read_text())
    if base.get('publish') is not False:raise ValueError('E321-PRIVADO')
    for cut in config['cuts']:
        if cut.get('acervo_existente') is True:
            m=base['acquired'].get(cut['source'])
            if not m or m.get('expected_sha256')!=cut['sha256'] or m.get('label')!=cut['label'] or not cut.get('samples'):
                raise ValueError('E321-ACERVO-OU-AMOSTRAS')
            continue
        row=next(r for r in receipt['records'] if r['status']=='BYTES_AND_WINDOWS_VERIFIED' and r['media']['id']==cut['source'])
        m=row['media'];h=cut['sha256']
        if m['expected_sha256']!=h or m['label']!=cut['label'] or not re.fullmatch('[a-f0-9]{64}',h):
            raise ValueError('E302-ORIGEM')
        if not any(w['start']==cut['window_start'] and w['duration']==cut['window_duration'] for w in row['windows']):
            raise ValueError('E302-JANELA')
        download(h+'.mp4',root,250_000_000)
        extra[m['id']]=m
    verified,_=validar_acervo({'publish':False,'acquired':extra},[(c['source'],c['label']) for c in config['cuts']],root)
    data=json.loads((out/'acervo-restaurado.json').read_text())
    if data.get('publish') is not False or set(data['acquired'])&set(verified):raise ValueError('E302-ACERVO')
    data['acquired'].update(verified)
    (out/'acervo-restaurado.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
    print('E302 ORIGINAIS RESTAURADOS',list(verified),flush=True)

if __name__=='__main__':
    restore(json.loads(Path(sys.argv[1]).read_text()),sys.argv[2],sys.argv[3])
