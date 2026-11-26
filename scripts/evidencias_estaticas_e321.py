"""Private, exact-speech static explanatory evidence for the assisted pilot.
The general E254 already has static media support; this is only its curatorial replay.
"""
import json, re, sys, subprocess
from pathlib import Path
from PIL import Image
from scripts.recuperar_checkpoints_documentais import api,listar_releases,REPO
from src.v3.pacote_biblioteca import sha

def read(p):return json.loads(Path(p).read_text())

def validate_config(cfg):
    if cfg.get('schema')!='coringa.reviewed-static.private.v1' or cfg.get('publish') is not False or not isinstance(cfg.get('cuts'),list):
        raise ValueError('E321-ESTATICO-ESCOPO')
    cuts={c['shot']:c for c in cfg['cuts']}
    if len(cuts)!=len(cfg['cuts']) or len({c['sha256'] for c in cuts.values()})!=len(cuts):
        raise ValueError('E321-ESTATICO-REPETICAO')
    return cuts

def validate_media(m,cut):
    p=Path(m['local_source'])
    if (m.get('media_type')!='photo' or m.get('evidence_scope')!='STATIC_ONLY' or m.get('rights_status')!='REVIEW_PENDING'
        or m.get('id')!=cut['source'] or m.get('label')!=cut['label'] or m.get('expected_sha256')!=cut['sha256']
        or not re.fullmatch('[a-f0-9]{64}',cut['sha256']) or m.get('license')!='Public domain'
        or not m.get('page','').startswith('https://www.usgs.gov/media/images/') or not m.get('credit')
        or p.parts[:1]!=('stage_documental',) or '..' in p.parts or p.is_absolute() or not p.is_file() or sha(p)!=cut['sha256']):
        raise ValueError('E321-ESTATICO-FONTE')
    with Image.open(p) as im:
        if list(im.size)!=[m['width'],m['height']] or min(im.size)<600:raise ValueError('E321-ESTATICO-DIMENSOES')
        im.verify()
    return m

def shot_for(cut,m,words,chapter,start,end):
    speech=' '.join(w['w'] for w in words if w['s']<end and w['e']>start)
    if (cut.get('chapter')!=chapter or cut.get('speech')!=speech or cut.get('kind')!='photo'
        or not cut.get('review_ref') or not cut.get('observed') or not cut.get('lead') or not 1.4-1e-6<=end-start<=3.8+1e-6):
        raise ValueError('E321-ESTATICO-FALA')
    validate_media(m,cut)
    shot={'id':cut['shot'],'type':'photo','asset':m['id'],'start':start,'end':end,
            'photo_framing':'integral','lead':cut['lead'],'headline':m['label'],'subject':m['subject'],
            'source_display':m['credit'],'evidence':'representative','cues':[{'at':.2,'label':cut['lead']}]}
    if cut.get('reveal') is not None:
        import math
        from src.v4.formatos import progressao_estatica_e322 as R
        reveal=cut['reveal']
        anchors=[w for w in words if start<=w['s']<end and w['w']==reveal['anchor_word']]
        if len(anchors)!=1:raise ValueError('E322-ANCORA-FALA')
        at=math.ceil((anchors[0]['s']-start)*30-1e-6)/30
        shot['static_fact_reveal']={'schema':'coringa.static.reveal.private.v1','publicar':False,
            'shot':cut['shot'],'sha256':cut['sha256'],'review_ref':cut['review_ref'],
            'at':at,'label':reveal['label'],'bbox':reveal['bbox'],'observation':reveal['observation']}
        shot['cues'].append({'at':at,'label':reveal['label']})
        R.validar(shot,m,m['expected_sha256'],private=True)
    return shot

def restore(cfg,out,root):
    cuts=validate_config(cfg);tag=cfg['release']
    if not re.fullmatch(r'review-e320-\d+-\d+',tag):raise ValueError('E321-ESTATICO-RELEASE')
    meta=api('')
    if meta.get('private') is not True or meta.get('id')!=1454059520:raise ValueError('E321-ESTATICO-COFRE')
    rel=next(r for r in listar_releases(100) if r['tag_name']==tag and r.get('draft') is True)
    assets={a['name']:a for a in rel['assets']}
    root=Path(root);root.mkdir(parents=True,exist_ok=True);out=Path(out)
    def download(name,limit):
        a=assets[name];p=root/name
        if not 0<a['size']<=limit:raise ValueError('E321-ESTATICO-LIMITE')
        if not p.exists():
            subprocess.run(['gh','release','download',tag,'--repo',REPO,'--pattern',name,'--dir',str(root)],check=True,timeout=120)
        if p.stat().st_size!=a['size'] or a.get('digest')!='sha256:'+sha(p):raise ValueError('E321-ESTATICO-SHA')
        return p
    receipt=read(download('evidencias.json',2_000_000))
    if receipt.get('publish') is not False:raise ValueError('E321-ESTATICO-PRIVADO')
    result={}
    for c in cuts.values():
        m=next(r['media'] for r in receipt['records'] if r['status']=='BYTES_VERIFIED' and r['media']['id']==c['source'])
        filename=Path(m['local_source']).name
        if not re.fullmatch(c['sha256']+r'\.(jpg|png|webp)',filename):raise ValueError('E321-ESTATICO-NOME')
        m={**m,'local_source':str(download(filename,26_000_000))}
        result[m['id']]=validate_media(m,c)
    (out/'static-restaurado.json').write_text(json.dumps({'publish':False,'acquired':result},ensure_ascii=False,indent=2))
if __name__=='__main__':restore(read(sys.argv[1]),sys.argv[2],sys.argv[3])
