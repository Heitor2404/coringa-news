"""E387: private clean layout, complete source credits stay in props and sidecar."""
import json
from pathlib import Path
from scripts import qa_tipografia_e386 as E
from scripts.qa_fala_visual_e338 import read as archived
ROOT=Path('stage_documental/e387')
def main():
    E.ROOT=ROOT;E.main()
    receipts=json.loads(Path('stage_documental/e286/prova.json').read_text())['source_receipts']
    plan=archived('plano.json')
    labels=['NAVIO EM TRÂNSITO PELO CANAL','A QUEDA D ÁGUA DESCE PELA ROCHA','O RELEVO SE DESTACA NO HORIZONTE','INSTRUMENTO DO TELESCÓPIO HUBBLE']
    output=[]
    for name in ('fixtures','narrated'):
        f=ROOT/(name+'.json');p=json.loads(f.read_text())
        for i,s in enumerate(p['shots']):
            h=Path(s['asset']).stem
            if name=='fixtures':
                meta=next(r for r in receipts if r['sha256']==h)['source']
                g=p['documentary_captions'][i]
                g['words']=[{'w':w,'hl':j==1} for j,w in enumerate(labels[i].split())]
            else:
                meta=next(r for r in plan['media'].values() if r.get('expected_sha256')==h)
            credit=s.get('source_display') or s['source']
            if not credit or not meta:raise ValueError('E387-ATTRIBUTION')
            d=dict(placement='POST_DESCRIPTION',private_only=True,credit=credit)
            if s['evidence']=='representative':d['context_label']='CONTEXTO'
            s['documentary_clean_credit']=d
            output.append(dict(case=name,shot=s['id'],asset_sha256=h,credit=credit,source_record=meta,
                placement='POST_DESCRIPTION',rights_approval=False,publication_blocked=True))
        f.write_text(json.dumps(p,ensure_ascii=False))
    (ROOT/'attribution-manifest.json').write_text(json.dumps(dict(publish=False,rights_approved=False,
        note='Private layout review only. Before publication audit license-specific placement, retain embedded marks and context qualifiers, and include full attribution in post.',items=output),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
