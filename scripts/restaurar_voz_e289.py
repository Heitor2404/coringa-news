"""Explicit recovery of a raw Gemini voice from a private draft release.
No AI calls. Request/voice binding is checked again by src.voz before use.
"""
import re,sys,subprocess
from pathlib import Path
from scripts.recuperar_checkpoints_documentais import api,listar_releases,REPO
from src.v3.pacote_biblioteca import sha

def restaurar(tag,pasta,nome='gemini0'):
    if not re.fullmatch(r'review-e289-\d+-\d+',tag) or nome not in ('gemini0','gemini1'):
        raise ValueError('E289-VOZ-TAG')
    meta=api('')
    if meta.get('private') is not True or meta.get('id')!=1454059520:raise ValueError('E289-VOZ-COFRE')
    rel=next(r for r in listar_releases(100) if r['tag_name']==tag and r['draft'] is True)
    assets={a['name']:a for a in rel['assets']}
    pasta=Path(pasta);pasta.mkdir(parents=True,exist_ok=True)
    for ext,limit in (('.json',100_000),('.wav',50_000_000)):
        n=nome+ext;a=assets[n]
        if not 0<a['size']<=limit or not re.fullmatch(r'sha256:[0-9a-f]{64}',a.get('digest') or ''):
            raise ValueError('E289-VOZ-METADADOS')
        subprocess.run(['gh','release','download',tag,'--repo',REPO,'--pattern',n,'--dir',str(pasta)],check=True,timeout=180)
        f=pasta/n
        if f.stat().st_size!=a['size'] or 'sha256:'+sha(f)!=a['digest']:raise ValueError('E289-VOZ-SHA')
    return pasta/(nome+'.wav')

if __name__=='__main__':
    print(restaurar(sys.argv[1],sys.argv[2],sys.argv[3] if len(sys.argv)>3 else 'gemini0'))
