"""E347/E348: restore E345 checkpoint, rerender only reviewed panel passages."""
import json,shutil
from pathlib import Path
from PIL import Image
from scripts import qa_integracao_e345 as Q,qa_abertura_e339 as A
from scripts.qa_fala_visual_e338 import read as archived
from scripts.recuperar_checkpoints_documentais import api,listar_releases
from src.v4.formatos.auditoria_fala_visual_e338 import organizar
from src.v4.formatos.paineis_fonte_e346 import aplicar
from src.v3.pacote_biblioteca import sha
Q.ROOT=Path('stage_documental/e348');ROOT=Q.ROOT
PREV='review-e345-45894220012-1'
def prepare():
    ROOT.mkdir(parents=True,exist_ok=False);m=api('');Q.check(m['private'] is True and m['id']==1454059520,'E348-COFRE')
    rel={r['tag_name']:r for r in listar_releases(100)}
    base=A.download(rel,PREV,'filme-integrado.mp4',ROOT,'c4617f59737ad2a773812d3df049a56afcf68bd07a23c0e4c8cbe98d8886c936',30_000_000)
    base.rename(ROOT/'filme.mp4');base=ROOT/'filme.mp4'
    p=json.loads(A.download(rel,PREV,'props-candidate.json',ROOT,'af8856ba0a50b030f520c2a113e4e5a519e4b6d8ffabb14fe7fd6b623976895e',100_000).read_text())
    prior=json.loads(A.download(rel,PREV,'proof.json',ROOT,'bcb5da790dc63c4de0e65012e55f9731df3a08e32123ba36e600a31dce6b88b1',100_000).read_text())
    Q.check(prior['final_sha256']==sha(base) and prior['audio_packet_fingerprint']==Q.audio_packets(base)[0],'E348-BASE')
    n=json.loads(A.download(rel,A.FILM,'narracao.json',ROOT,'19ed0d467b16de361c2c9e378ac162729f8ff79fad9fdc3ac1c51fa46b766a0d',100_000).read_text())
    plan=archived('plano.json');queue=organizar(plan,archived('obrigacoes-visuais.json'));config=json.loads(Path('benchmarks/e348/paineis.json').read_text());Q.check(config['publish'] is False,'E348-CONFIG')
    out,proof=aplicar(p,queue,n['words'],prior,config['entries'])
    Q.check(Q.video_frames(base)==proof['total_frames'],'E348-FRAMES')
    public=Path('motor4/remotion/public')
    for s in out['shots']:
        if s['id'] not in proof['changed_shots']:continue
        name=Path(s['asset']).name;h=name.split('.')[0];med=next(x for x in plan['media'].values() if x.get('expected_sha256')==h)
        Q.check(med['license']=='Public domain' and med['page'].startswith('https://www.usgs.gov/media/'),'E348-RECEIPT')
        tag=next(t for t in (A.PHOTO,'review-e323-45864804065-1') if any(x['name']==name for x in rel[t]['assets']))
        f=A.download(rel,tag,name,public/'film_editorial',h,30_000_000)
        with Image.open(f) as im:Q.check(list(im.size)==s['source_dimensions'],'E348-DIM')
    mix=ROOT/'original-mix.wav';A.ff('-i',base,'-vn','-ar',48000,'-c:a','pcm_s16le',mix)
    name=sha(mix)+'.wav';(public/'e202').mkdir(exist_ok=True);shutil.copyfile(mix,public/'e202'/name)
    out['scene_narration_asset']='e202/'+name
    out['documentary_text_probe']=False
    proof.update(status='PREPARED_PRIVATE',new_ai=0,new_tts=0,original_film_sha256=sha(base),audio_packet_fingerprint=Q.audio_packets(base)[0],comparison_times=[54.5,56.7,65,66.7,68.7,70.5],prior_release=PREV)
    Q.write('props-candidate.json',out);Q.write('proof.json',proof)
if __name__=='__main__':
    import sys
    (Q.finish if '--finish' in sys.argv else prepare)()
