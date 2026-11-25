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

def exportar(bib,ids,destino,*,incluir_analises_privadas=False):
    dest=Path(destino);dest.mkdir(parents=True,exist_ok=False)
    if not 1<=len(ids)<=MAX_FILES or len(set(ids))!=len(ids):raise ValueError('E250-IDS')
    rows=[];total=0;analises={}
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
        if incluir_analises_privadas:
            stored={r['tipo']:json.loads(r['conteudo']) for r in bib.con.execute('SELECT tipo,conteudo FROM analises WHERE sha256=?',(d['sha256'],)) if r['tipo'].startswith('documental:')}
            analises[d['sha256']]={k:v for k,v in stored.items() if isinstance(v,dict) and v.get('publicar') is False and v.get('direitos_aprovados') is False}
        rows.append((d,{'id':d['id'],'sha256':d['sha256'],'arquivo':name,'bytes':p.stat().st_size}))
    m=dest/'manifesto.jsonl'
    m.write_text('\n'.join(json.dumps(x,ensure_ascii=False,sort_keys=True) for x in
        [{'_manifesto':'biblioteca-coringa','versao_esquema':bib.versao()}]+[d for d,e in rows])+'\n',encoding='utf8')
    idx={'schema':'coringa.v3.originals.private.v1','publicar':False,'direitos_aprovados':False,
         'manifesto_sha256':sha(m),'arquivos':[e for d,e in rows]}
    if incluir_analises_privadas:
        side=dest/'analises-privadas.json'
        side.write_text(json.dumps({'schema':'coringa.documental.analises.v1','publicar':False,'direitos_aprovados':False,'por_sha':analises},ensure_ascii=False,sort_keys=True),encoding='utf8')
        if side.stat().st_size>8_000_000:raise ValueError('E258-LIMITE-ANALISES')
        idx['analises_sha256']=sha(side)
    (dest/'index.json').write_text(json.dumps(idx,ensure_ascii=False,indent=2),encoding='utf8')
    return idx

def restaurar(pacote,*,db,armazem,restaurar_analises_privadas=False):
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
    side_data={}
    if restaurar_analises_privadas and 'analises_sha256' in idx:
        side=root/'analises-privadas.json'
        if not side.is_file() or side.is_symlink() or side.stat().st_size>8_000_000 or sha(side)!=idx['analises_sha256']:raise ValueError('E258-SHA-ANALISES')
        packet=json.loads(side.read_text(encoding='utf8'))
        if packet.get('schema')!='coringa.documental.analises.v1' or packet.get('publicar') is not False or packet.get('direitos_aprovados') is not False:raise ValueError('E258-ANALISE-PRIVADA')
        side_data=packet['por_sha']
        if not isinstance(side_data,dict) or set(side_data)-{e['sha256'] for e in entries}:raise ValueError('E258-VINCULO-ANALISES')
        for h,records in side_data.items():
            if not isinstance(records,dict) or any(not isinstance(k,str) or not re.fullmatch(r'documental:(?:recibo:)?[0-9a-f]{64}',k) or not isinstance(v,dict) or v.get('publicar') is not False or v.get('direitos_aprovados') is not False for k,v in records.items()):
                raise ValueError('E258-ANALISE-PRIVADA')
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
        for h,records in side_data.items():
            for k,v in records.items():
                if bib.analise(h,k) is None:bib.gravar_analise(h,k,v,origem='checkpoint privado E258')
        return bib,{**report,'originais_restaurados':len(entries),'bytes_restaurados':total,'analises_restauradas':sum(len(v) for v in side_data.values()),'direitos_aprovados':False}
    except Exception:
        bib.fechar()
        raise
