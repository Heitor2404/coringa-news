"""E386 private typography A/B: versioned four-source fixture plus actual Kilauea speech."""
import json,shutil
from pathlib import Path
from scripts import qa_abertura_e339 as A
from scripts.qa_visual_e286 import main as fixtures
from scripts.recuperar_checkpoints_documentais import api,listar_releases
from src.v3.pacote_biblioteca import sha
ROOT=Path('stage_documental/e386')
TAG='review-e376-45907502601-1'
def main():
    ROOT.mkdir(parents=True,exist_ok=False)
    fixtures()
    p=json.loads(Path('stage_documental/e286/props.json').read_text())
    for s in p['shots']:s['documentary_composition_v2']=True
    for g in p['documentary_captions']:
        g['words']=[{'w':w,'hl':i==2} for i,w in enumerate('A MICROFABRICAÇÃO EXIGE CONTROLE PRECISO'.split())]
    (ROOT/'fixtures.json').write_text(json.dumps(p))
    meta=api('');A.check(meta['private'] is True and meta['id']==1454059520,'E386-COFRE')
    rel={r['tag_name']:r for r in listar_releases(300)}
    base=A.download(rel,TAG,'filme-integral-preto.mp4',ROOT,'e9f961c2d2257aa8946819da44ddc28f1cb52ffa1238eb0e4f77f5ec10ea74bf',30_000_000)
    p=json.loads(A.download(rel,TAG,'props-candidate.json',ROOT,'8fbe773cc82a6f0c63ad58c48e90f79deee9d4dfde6d5cec3b9b2dd4b529612e',100_000).read_text())
    s=next(x for x in p['shots'] if x['id']=='c3-1')
    start,end=s['start'],s['end'];duration=end-start
    name=Path(s['asset']).name;h=Path(name).stem
    public=Path('motor4/remotion/public')
    tag=next(t for t in (A.BASE,A.FILM,'review-e320-45860199613-1','review-e323-45864804065-1') if t in rel and any(x['name']==name for x in rel[t]['assets']))
    f=A.download(rel,tag,name,public/'film_editorial',h,250_000_000)
    w,hh,d=A.probe(f);A.check([w,hh]==s['source_dimensions'] and s['source_in_seconds']+duration<=d+.05,'E386-SOURCE')
    mix=ROOT/'same-mix.wav';A.ff('-ss',start,'-i',base,'-vn','-t',duration,'-ar',48000,'-c:a','pcm_s16le',mix)
    audio='e202/'+sha(mix)+'.wav';(public/'e202').mkdir(exist_ok=True);shutil.copyfile(mix,public/audio)
    captions=[{**g,'start':max(g['start'],start)-start,'end':min(g['end'],end)-start} for g in p['documentary_captions'] if g['end']>start and g['start']<end]
    p.update(shots=[{**s,'start':0,'end':duration}],duracao=duration,scene_narration_asset=audio,documentary_captions=captions,documentary_text_probe=True)
    A.check(captions and p['private_review_only'] and p['preview'],'E386-CAPTIONS')
    (ROOT/'narrated.json').write_text(json.dumps(p))
    (ROOT/'input-proof.json').write_text(json.dumps(dict(publish=False,semantic_approval=False,new_ai=0,new_tts=0,source_sha256=h,audio_sha256=sha(mix),original_time=[start,end],duration=duration,fixture_captions='synthetic layout only',narrated_captions='original measured words'),indent=2))
if __name__=='__main__':main()
