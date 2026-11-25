"""Rebuild a missing private discovery manifest from existing immutable V3 packages.
No original source download or AI. Upload only a missing manifest, never replace.
"""
import hashlib,json,re,subprocess,sys
from pathlib import Path
from scripts.recuperar_checkpoints_documentais import REPO,api,listar_releases,verified_download
from src.v3 import pacote_biblioteca as P

def validar_relatorio(r,assets):
    if r.get('publish') is not False or not r.get('modo_progressivo'):raise ValueError('E2647-RELATORIO')
    rows=r.get('checkpoints') or []
    if not 1<=len(rows)<=100:raise ValueError('E2647-PACOTES')
    out={}
    for row in rows:
        if row.get('estado')!='PRIVADO_LOCAL':continue
        mid=row['id'];name=row['arquivo'];digest=row['sha256']
        a=assets.get(name)
        if not re.fullmatch(r'cm-[0-9a-f]{12}',mid) or name!=mid+'.zip' or not re.fullmatch('[0-9a-f]{64}',digest) or not a or a.get('digest')!='sha256:'+digest or not 0<a['size']<=P.MAX_TOTAL+10_000_000 or name in out:raise ValueError('E2647-VINCULO')
        out[name]=a
    if not out or set(out)!={k for k in assets if re.fullmatch(r'cm-[0-9a-f]{12}\.zip',k)}:raise ValueError('E2647-INCOMPLETO')
    if sum(a['size'] for a in out.values())>100_000_000:raise ValueError('E2647-ORCAMENTO')
    return out

def main():
    tag=sys.argv[1];root=Path(sys.argv[2])
    if not re.fullmatch(r'review-[a-z0-9-]+',tag):raise ValueError('E2647-TAG')
    repo=api('')
    if repo.get('private') is not True or repo.get('id')!=1454059520:raise ValueError('E2647-COFRE')
    rel=next(r for r in listar_releases(60) if r['tag_name']==tag and r['draft'] is True)
    assets={a['name']:a for a in rel.get('assets',[])}
    if 'manifesto-revisoes.jsonl' in assets:
        print('E2647 MANIFESTO JA EXISTE',flush=True);return
    root.mkdir(parents=True,exist_ok=False)
    a=assets['revisao.json']
    if not 0<a['size']<=12_000_000 or not re.fullmatch(r'sha256:[0-9a-f]{64}',a.get('digest') or ''):raise ValueError('E2647-RELATORIO')
    subprocess.run(['gh','release','download',tag,'--repo',REPO,'--pattern','revisao.json','--dir',str(root)],check=True,timeout=120)
    raw=(root/'revisao.json').read_bytes()
    if len(raw)!=a['size'] or 'sha256:'+hashlib.sha256(raw).hexdigest()!=a['digest']:raise ValueError('E2647-RELATORIO-SHA')
    packets=validar_relatorio(json.loads(raw),assets)
    restored=0;analyses=0
    for name,a in packets.items():
        p=verified_download(tag,a,root)
        dest=P.extrair_checkpoint(p,root/name[:-4],expected_sha256=a['digest'][7:])
        bib,result=P.restaurar(dest,db=root/'bib.sqlite3',armazem=root/'originais',restaurar_analises_privadas=True)
        try:
            if result['originais_restaurados']!=1 or not bib.obter(name[:-4]):raise ValueError('E2647-PACOTE-ID')
            restored+=result['originais_restaurados'];analyses+=result['analises_restauradas']
            bib.exportar_manifesto(root/'manifesto-revisoes.jsonl')
        finally:bib.fechar()
    manifest=root/'manifesto-revisoes.jsonl'
    if restored!=len(packets) or not 0<manifest.stat().st_size<=8_000_000:raise ValueError('E2647-MANIFESTO')
    # No --clobber: a conflicting upload must stop, not overwrite evidence.
    subprocess.run(['gh','release','upload',tag,str(manifest),'--repo',REPO],check=True,timeout=120)
    print('E2647 MANIFESTO REPARADO',restored,'originais',analyses,'registros de analise',P.sha(manifest),flush=True)
if __name__=='__main__':main()
