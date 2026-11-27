"""E388.1: focused Taiwan motion proof, no repeated ordinary fixtures."""
import json,shutil
from pathlib import Path
from scripts import qa_abertura_e339 as A
from scripts.recuperar_checkpoints_documentais import api,listar_releases
from scripts.qa_fala_visual_e338 import read as archived
from src.v3.pacote_biblioteca import sha
ROOT=Path('stage_documental/e3881')
def main():
    ROOT.mkdir(parents=True,exist_ok=False)
    meta=api('');A.check(meta['private'] is True and meta['id']==1454059520,'E3881-COFRE')
    rel={r['tag_name']:r for r in listar_releases(300)}
    tag='review-e376-45907502601-1'
    A.download(rel,tag,'filme-integral-preto.mp4',ROOT,'e9f961c2d2257aa8946819da44ddc28f1cb52ffa1238eb0e4f77f5ec10ea74bf',30_000_000)
    full=json.loads(A.download(rel,tag,'props-candidate.json',ROOT,'8fbe773cc82a6f0c63ad58c48e90f79deee9d4dfde6d5cec3b9b2dd4b529612e',100_000).read_text())
    data=json.loads(Path('benchmarks/e342/dados.json').read_text())
    plan=archived('plano.json');public=Path('motor4/remotion/public')
    facts=[]
    for r in data['entries']:
        s=next(x for x in full['shots'] if x['id']==r['shot'])
        f=s['documentary_reported_fact']
        A.check(data['publish'] is False and f['publish'] is False and f['value']==r['value'] and f['scope']==r['scope'] and f['sha256']==r['sha256'] and f['url']==r['source_url'] and f['authority']==r['authority'],'E388-RECEIPT')
        a,b=s['start'],s['end'];duration=b-a
        A.check(duration-f['at']>=1.4,'E388-HOLD')
        h=r['sha256'];name=Path(s['asset']).name
        A.check(name==h+'.mp4','E388-SOURCE')
        med=next(x for x in plan['media'].values() if x.get('expected_sha256')==h)
        A.check(med['license']=='Public domain','E388-RIGHTS')
        tag=next(t for t in (A.BASE,A.FILM,A.PHOTO,'review-e323-45864804065-1') if t in rel and any(x['name']==name for x in rel[t]['assets']))
        src=A.download(rel,tag,name,public/'film_editorial',h,250_000_000)
        w,hh,d=A.probe(src);A.check([w,hh]==s['source_dimensions'] and s['source_in_seconds']+duration<=d+.05,'E388-SOURCE-WINDOW')
        mix=ROOT/(s['id']+'.wav');A.ff('-ss',a,'-i',ROOT/'filme-integral-preto.mp4','-vn','-t',duration,'-ar',48000,'-c:a','pcm_s16le',mix)
        audio='e202/'+sha(mix)+'.wav';(public/'e202').mkdir(exist_ok=True);shutil.copyfile(mix,public/audio)
        captions=[{**g,'start':max(g['start'],a)-a,'end':min(g['end'],b)-a} for g in full['documentary_captions'] if g['end']>a and g['start']<b]
        p={**full,'shots':[{**s,'start':0,'end':duration,'documentary_fact_motion_trial':True,'documentary_taiwan_typography_trial':True,'documentary_overlay_trial':60,'documentary_clean_credit':dict(placement='POST_DESCRIPTION',private_only=True,credit=s.get('source_display') or s['source'])}],'duracao':duration,'scene_narration_asset':audio,'documentary_captions':captions,'documentary_text_probe':False}
        (ROOT/(s['id']+'.json')).write_text(json.dumps(p,ensure_ascii=False))
        facts.append(dict(shot=s['id'],source_record=med,receipt=r,at=f['at'],hold=duration-f['at'],audio_sha256=sha(mix),measurement_from_pixels=False,publish=False,credit=s.get('source_display') or s['source'],placement='POST_DESCRIPTION'))
    (ROOT/'motion-attribution.json').write_text(json.dumps(dict(publish=False,rights_approved=False,items=facts),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
