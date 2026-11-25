"""Bounded portable original-media packages for the existing V3 library.
Private work only. No license approval, no automatic reuse of semantic opinions.
The package is flat and immutable; binary transport belongs to the private vault.
"""
import hashlib,json,re,shutil
from pathlib import Path
from src.v3.biblioteca import restaurar_catalogo

MAX_TOTAL=40_000_000
MAX_FILES=8
EXTS={'.jpg','.jpeg','.png','.webp','.mp4','.webm','.mov'}
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def exportar(bib,ids,destino):
    dest=Path(destino);dest.mkdir(parents=True,exist_ok=False)
    if not 1<=len(ids)<=MAX_FILES or len(set(ids))!=len(ids):raise ValueError('E250-IDS')
    rows=[];total=0
    for mid in ids:
        d=bib.obter(mid)
        if not d or d['ext'] not in EXTS:raise ValueError('E250-REGISTRO')
        p=bib.caminho(d['sha256'],d['ext'])
        if not p.is_file() or sha(p)!=d['sha256']:raise ValueError('E250-SHA')
        total+=p.stat().st_size
        if total>MAX_TOTAL:raise ValueError('E250-LIMITE')
        name=d['sha256']+d['ext']
        shutil.copyfile(p,dest/name)
        # Pending rights are deliberately excluded from normal commercial search.
        d={**d,'uso_comercial':'indefinido','verificacao':'nao_verificada',
           'regioes':{},'temas':[],'usos':[],'analises':{}}
        rows.append((d,{'id':d['id'],'sha256':d['sha256'],'arquivo':name,'bytes':p.stat().st_size}))
    m=dest/'manifesto.jsonl'
    m.write_text('\n'.join(json.dumps(x,ensure_ascii=False,sort_keys=True) for x in
        [{'_manifesto':'biblioteca-coringa','versao_esquema':bib.versao()}]+[d for d,e in rows])+'\n',encoding='utf8')
    idx={'schema':'coringa.v3.originals.private.v1','publicar':False,'direitos_aprovados':False,
         'manifesto_sha256':sha(m),'arquivos':[e for d,e in rows]}
    (dest/'index.json').write_text(json.dumps(idx,ensure_ascii=False,indent=2),encoding='utf8')
    return idx

def restaurar(pacote,*,db,armazem):
    root=Path(pacote);idx=json.loads((root/'index.json').read_text(encoding='utf8'))
    if idx.get('schema')!='coringa.v3.originals.private.v1' or idx.get('publicar') is not False or idx.get('direitos_aprovados') is not False:raise ValueError('E250-PRIVADO')
    entries=idx['arquivos'];m=root/'manifesto.jsonl'
    if not 1<=len(entries)<=MAX_FILES or sha(m)!=idx['manifesto_sha256']:raise ValueError('E250-MANIFESTO')
    records=[json.loads(l) for l in m.read_text(encoding='utf8').splitlines()][1:]
    if len(records)!=len(entries):raise ValueError('E250-REGISTROS')
    byid={d['id']:d for d in records};seen=set();total=0
    for e in entries:
        h=e['sha256'];d=byid.get(e['id']);name=e['arquivo']
        if not isinstance(h,str) or not re.fullmatch('[0-9a-f]{64}',h) or not d or d.get('sha256')!=h or e['id']!='cm-'+h[:12] or d['ext'] not in EXTS or name!=h+d['ext'] or name in seen or d.get('uso_comercial')!='indefinido' or d.get('verificacao')!='nao_verificada' or any(d.get(k) for k in ('regioes','usos','analises','temas')):
            raise ValueError('E250-VINCULO')
        seen.add(name);p=root/name
        if not p.is_file() or p.is_symlink() or p.stat().st_size!=e['bytes'] or sha(p)!=h:raise ValueError('E250-BYTES')
        total+=e['bytes']
        if total>MAX_TOTAL:raise ValueError('E250-LIMITE')
    bib,report=restaurar_catalogo(m,db=db,armazem=armazem)
    try:
        for e in entries:
            d=bib.obter(e['id'])
            if d['ext']!=byid[e['id']]['ext']:raise ValueError('E250-EXT-CONFLITO')
            p=bib.caminho(d['sha256'],d['ext']);p.parent.mkdir(parents=True,exist_ok=True)
            tmp=p.with_suffix(p.suffix+'.parcial')
            shutil.copyfile(root/e['arquivo'],tmp)
            if sha(tmp)!=e['sha256']:tmp.unlink(missing_ok=True);raise ValueError('E250-COPIA')
            tmp.replace(p)
        return bib,{**report,'originais_restaurados':len(entries),'bytes_restaurados':total,'direitos_aprovados':False}
    except Exception:
        bib.fechar()
        raise
