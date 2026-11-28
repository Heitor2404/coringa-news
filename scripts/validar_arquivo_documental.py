"""Verify the private discovery index against checkpoint contents before archive.
No network or AI. Review-only archives retain their existing contract.
"""
import hashlib,json,re,sys,zipfile
from pathlib import Path

def validar(paths):
    files=[Path(p) for p in paths]
    zips=[p for p in files if re.fullmatch(r'cm-[0-9a-f]{12}\.zip',p.name)]
    if not zips:return 0
    manifests=[p for p in files if p.name=='manifesto-revisoes.jsonl']
    if len(manifests)!=1 or not 0<manifests[0].stat().st_size<=8_000_000:raise ValueError('COFRE_MANIFESTO_AUSENTE_OU_INVALIDO')
    rows=[json.loads(l) for l in manifests[0].read_text(encoding='utf8').splitlines() if l.strip()]
    if not rows or rows[0].get('_manifesto')!='biblioteca-coringa':raise ValueError('COFRE_MANIFESTO_ESQUEMA')
    byid={r.get('id'):r for r in rows[1:]}
    if len(byid)!=len(rows)-1:raise ValueError('COFRE_MANIFESTO_DUPLICADO')
    seen=set()
    for p in zips:
        mid=p.stem
        if mid in seen or mid not in byid:raise ValueError('COFRE_PACOTE_SEM_INDICE')
        seen.add(mid);row=byid[mid];h=row.get('sha256','')
        if not re.fullmatch('[0-9a-f]{64}',h) or mid!='cm-'+h[:12]:raise ValueError('COFRE_IDENTIDADE')
        with zipfile.ZipFile(p) as z:
            info=z.getinfo('index.json')
            if info.file_size>1_000_000:raise ValueError('COFRE_INDICE_LIMITE')
            idx=json.loads(z.read(info))
            entries=idx.get('arquivos') or []
            if idx.get('schema')!='coringa.v3.originals.private.v1' or idx.get('publicar') is not False or idx.get('direitos_aprovados') is not False or len(entries)!=1 or entries[0].get('id')!=mid or entries[0].get('sha256')!=h:raise ValueError('COFRE_PACOTE_INCOMPATIVEL')
            manifest=z.getinfo('manifesto.jsonl')
            if manifest.file_size>8_000_000 or hashlib.sha256(z.read(manifest)).hexdigest()!=idx.get('manifesto_sha256'):raise ValueError('COFRE_MANIFESTO_PACOTE_SHA')
            if 'analises_sha256' in idx:
                side=z.getinfo('analises-privadas.json')
                if side.file_size>8_000_000:raise ValueError('COFRE_ANALISE_LIMITE')
                raw=z.read(side)
                if hashlib.sha256(raw).hexdigest()!=idx['analises_sha256']:raise ValueError('COFRE_ANALISE_SHA')
                data=json.loads(raw)
                if data.get('publicar') is not False or data.get('direitos_aprovados') is not False or data.get('schema')!='coringa.documental.analises.v1':raise ValueError('COFRE_ANALISE_PRIVADA')
                records=data.get('por_sha') or {}
                if set(records)-{h}:raise ValueError('COFRE_ANALISE_VINCULO')
                indexed=row.get('analises') or {}
                if any(indexed.get(k)!=v for k,v in records.get(h,{}).items()):raise ValueError('COFRE_ANALISE_NAO_INDEXADA')
    return len(seen)

if __name__=='__main__':
    print('COFRE CHECKPOINTS INDEXADOS',validar(sys.argv[1:]),flush=True)
