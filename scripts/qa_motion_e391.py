"""E391: isolated narrated vector alternative; E390 remains canonical."""
import json,shutil
from pathlib import Path
from PIL import Image
from scripts import qa_abertura_e339 as A
from scripts.recuperar_checkpoints_documentais import api,listar_releases
from src.v3.pacote_biblioteca import sha
ROOT=Path('stage_documental/e391')
def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    meta=api('');A.check(meta['private'] is True and meta['id']==1454059520,'E391-COFRE')
    rel={r['tag_name']:r for r in listar_releases(300)}
    tag='review-e390-45935832558-1'
    movie=A.download(rel,tag,'CORINGA-EXPLICA-KILAUEA-ATUAL-E390.mp4',ROOT,'93e47c6a2f716956a85ac00a6674cf11e7357d8b17a49cb143d84fb956a68ede',30_000_000)
    info=next(a for a in rel[tag]['assets'] if a['name']=='props-current.json')
    full=json.loads(A.download(rel,tag,'props-current.json',ROOT,info['digest'].removeprefix('sha256:'),100_000).read_text())
    seq=json.loads(Path('benchmarks/e391/sequence.json').read_text())
    original=json.loads(Path('benchmarks/e389/sequence.json').read_text())
    narr=json.loads(A.download(rel,'review-e326-45870900796-1','narracao.json',ROOT,'19ed0d467b16de361c2c9e378ac162729f8ff79fad9fdc3ac1c51fa46b766a0d',100_000).read_text())
    source=A.download(rel,'review-e323-45864804065-1',seq['sourceSha']+'.png',ROOT,seq['sourceSha'],10_000_000)
    with Image.open(source) as im:A.check(im.width>1000 and im.height>1000,'E391-SOURCE')
    A.check(seq['sourceSha']==original['source']['sha256'] and seq['review']==original['source']['review'] and seq['publish'] is False,'E391-REVIEW')
    start,end=original['stages'][0]['start'],original['stages'][-1]['end']
    shots=[s for s in full['shots'] if s['start']>=start-.0001 and s['end']<=end+.0001]
    A.check([s['id'] for s in shots]==['c5-0','c5-1','c5-2','c5-3'] and full['documentary_caption_origin']=='PALAVRAS_MEDIDAS','E391-SHOTS')
    caps=[{**g,'start':max(g['start'],start)-start,'end':min(g['end'],end)-start} for g in full['documentary_captions'] if g['end']>start and g['start']<end]
    for state in seq['states'][1:]:
        hits=[w for w in narr['words'] if w['w']==state['anchorWord'] and abs(w['s']-start-state['at'])<.001]
        A.check(len(hits)==1 and any(g['start']<=state['at']<g['end'] and any(w['w']==state['anchorWord'] for w in g['words']) for g in caps),'E391-MEASURED-WORD '+state['id'])
    wav=ROOT/'same-mix.wav';A.ff('-ss',start,'-i',movie,'-vn','-t',end-start,'-ar',48000,'-c:a','pcm_s16le',wav)
    public=Path('motor4/remotion/public');(public/'e202').mkdir(exist_ok=True);audio='e202/'+sha(wav)+'.wav';shutil.copyfile(wav,public/audio)
    p={'sequence':seq,'duracao':end-start,'private_review_only':True,'audio':audio,'captions':caps,'probe':False}
    (ROOT/'variant.json').write_text(json.dumps(p,ensure_ascii=False))
    (ROOT/'motion-attribution.json').write_text(json.dumps({'publish':False,'source_sha256':sha(source),'source_review':seq['review'],'original_film_sha256':sha(movie),'audio_sha256':sha(wav),'canonical_preserved':True,'original_shots':shots,'scope':'isolated illustrative alternative; real evidence remains in E390; no measured geometry, duration or volume of physical transitions','rights_status':'REVIEW_PENDING'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
