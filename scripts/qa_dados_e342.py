"""Restore only two original videos and the archived measured voice. No full film render."""
import json,shutil
from pathlib import Path
from scripts import qa_abertura_e339 as A
from scripts.qa_fala_visual_e338 import read as archived
from scripts.recuperar_checkpoints_documentais import api,listar_releases
from src.v4.formatos.auditoria_fala_visual_e338 import organizar
from src.v4.formatos.dados_atribuidos_e342 import vincular
from src.v3.pacote_biblioteca import sha
ROOT=Path('stage_documental/e342')
def write(n,v):(ROOT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2))
def main():
    ROOT.mkdir(parents=True,exist_ok=False)
    m=api('');A.check(m['private'] is True and m['id']==1454059520,'E342-COFRE')
    releases={r['tag_name']:r for r in listar_releases(100)}
    p=A.download(releases,A.FILM,'props.json',ROOT,'db2c33f187531841197128775668fb3c3843d9e19fe84422a302a23157ee9c55',100_000)
    p=json.loads(p.read_text());plan=archived('plano.json');queue=organizar(plan,archived('obrigacoes-visuais.json'))
    n=A.download(releases,A.FILM,'narracao.json',ROOT,'19ed0d467b16de361c2c9e378ac162729f8ff79fad9fdc3ac1c51fa46b766a0d',100_000)
    n=json.loads(n.read_text());cfg=json.loads(Path('benchmarks/e342/dados.json').read_text());A.check(cfg['publish'] is False,'E342-PRIVATE')
    out,proof=vincular(p,queue,n['words'],cfg['entries'])
    public=Path('motor4/remotion/public');ids={r['shot'] for r in proof}
    voice=A.download(releases,A.FILM,'narracao48k.wav',ROOT,n['voice_sha256'],50_000_000)
    (public/'e202').mkdir(exist_ok=True);name=sha(voice)+'.wav';shutil.copyfile(voice,public/'e202'/name)
    for props in (p,out):
        props['scene_narration_asset']='e202/'+name
        props['shots']=[s for s in props['shots'] if s['id'] in ids]
        props['documentary_text_probe']=True
    for r in proof:
        s=next(s for s in out['shots'] if s['id']==r['shot']);med=next(x for x in plan['media'].values() if x['expected_sha256']==r['sha256'])
        A.check(med['license']=='Public domain' and med['page'].startswith('https://www.usgs.gov/media/'),'E342-RECEIPT')
        file=A.download(releases,A.BASE,Path(s['asset']).name,public/'film_editorial',r['sha256'],250_000_000)
        w,h,d=A.probe(file);A.check([w,h]==s['source_dimensions'] and s['source_in_seconds']+s['end']-s['start']<=d,'E342-PROBE')
    write('baseline.json',p);write('candidate.json',out);write('proof.json',{'publish':False,'semantic_approval':False,'new_ai':0,'new_tts':0,'full_documentary':False,'records':proof})
if __name__=='__main__':main()
