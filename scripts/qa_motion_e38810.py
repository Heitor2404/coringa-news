"""E388.10: actual automatic postvoice output in a full archived film.
No manual chart props, no new TTS, no replacement of protected canonical scene.
One independently declared contextual alternative; exact same reviewed map."""
import copy,json,shutil,subprocess
from pathlib import Path
from PIL import Image
from scripts import qa_abertura_e339 as A,qa_integracao_e345 as Q
from scripts.recuperar_checkpoints_documentais import api,listar_releases
from src.v3.pacote_biblioteca import sha
from src.v4.formatos import legenda_sync as LS
from src.v4.formatos.motion_intake_e3888 import integrar
from src.v4.formatos.motion_postvoice_e3889 import preparar_alternativa
ROOT=Path('stage_documental/e38810')
PUBLIC=Path('motor4/remotion/public')
def write(n,v):(ROOT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2))
def read(n):return json.loads((ROOT/n).read_text())
def prepare():
    ROOT.mkdir(parents=True,exist_ok=True)
    meta=api('');A.check(meta['private'] is True and meta['id']==1454059520,'E38810-COFRE')
    rel={r['tag_name']:r for r in listar_releases(300)}
    tag='review-e376-45907502601-1';voice_tag='review-e326-45870900796-1'
    movie=A.download(rel,tag,'filme-integral-preto.mp4',ROOT,'e9f961c2d2257aa8946819da44ddc28f1cb52ffa1238eb0e4f77f5ec10ea74bf',30_000_000)
    full=json.loads(A.download(rel,tag,'props-candidate.json',ROOT,'8fbe773cc82a6f0c63ad58c48e90f79deee9d4dfde6d5cec3b9b2dd4b529612e',100_000).read_text())
    narr=A.download(rel,voice_tag,'narracao.json',ROOT,'19ed0d467b16de361c2c9e378ac162729f8ff79fad9fdc3ac1c51fa46b766a0d',100_000)
    voice=A.download(rel,voice_tag,'narracao48k.wav',ROOT,'d7a6e9e05a8b16904a76f874c38b908a1b5955353943f127e1b29ae767818ad6',20_000_000)
    historical=json.loads(A.download(rel,voice_tag,'sincronia-medida.json',ROOT,'5ebd081bd2efa984d13494b3cb89410cfbff954821bdf64f39bf72e8dd5a3ffa',10000).read_text())
    n=json.loads(narr.read_text());A.check(n['voice_sha256']==sha(voice) and historical['ok'] is True and full['documentary_caption_origin']=='PALAVRAS_MEDIDAS','E38810-VOICE-BIND')
    sync=LS.conferir(narr,voice,maximo=3);write('sync-reverified.json',sync);A.check(sync['ok'] is True,'E38810-SYNC')
    (PUBLIC/'e202').mkdir(exist_ok=True)
    audio='e202/'+sha(voice)+'.wav';shutil.copyfile(voice,PUBLIC/audio)
    i=next(i for i,s in enumerate(full['shots']) if s['id']=='c6-0');original=full['shots'][i];h=Path(original['asset']).stem
    r=original['documentary_static_reveal']
    A.check(h==r['sha256']=='b6ebc2d171849a048e5b514b56364ac725f7d57860e8b85fc59791519de961ff' and r['label']=='35,5 KM² · QUADRO DO MAPA' and r['revisao_id']=='revisoes/e320-45860199613-1/evidencia-00.jpg','E38810-MAP-REVIEW')
    source=A.download(rel,A.PHOTO,Path(original['asset']).name,PUBLIC/'film_editorial',h,10_000_000)
    with Image.open(source) as im:A.check(list(im.size)==original['source_dimensions'],'E38810-MAP-DIM')
    url='https://www.usgs.gov/media/images/map-kilauea-volcanos-lower-east-rift-zone'
    # Source-reviewed facts, NOT renderer props. Independent contextual
    # storyboard deliberately has no existing static-reveal lane. Original
    # protected storyboard is first tested for refusal and remains untouched.
    fact={'id':'area-total','fonte':url,'quantitative_review':{'schema':'coringa.fact.quantity.review.private.v1','publish':False,'reviewed':True,'fact_id':'area-total','relevance':'central','source_url':url,'source_sha256':h,'source_date':'2018-08','statement':'USGS map: total flow area 35.5 square kilometers, includes lava delta.','review_id':r['revisao_id'],'anchor_phrase':['TRINTA','E','CINCO'],'anchor_word_index':0,'measurement':{'kind':'measurement','title':'ÁREA COBERTA PELA LAVA','scope':'Maio–agosto de 2018 · inclui o delta de lava','unit':'km²','qualifier':'approx','values':[{'label':'Área total coberta','value':35.5}]}}}
    need={'id':original['id'],'fatos':['area-total'],'necessidade':'explicacao_quantitativa','papel_visual':'quantificacao','exigir_evidencia_direta':False,'evidencia_visual':'estatica','mostrar':'Explicar magnitude da área total documentada'}
    case={'motion_private_alternatives':True,'fatos':[fact],'necessidades':[need]}
    base={**full,'scene_narration_asset':audio}
    raw={'publicar':False,'shots':copy.deepcopy(full['shots']),'necessidades_direcao':[need.copy()]}
    protected=integrar(case,raw)
    denied,denial=preparar_alternativa(case,protected,base,n['words'],sync,PUBLIC)
    A.check(denied is None and denial['rows'][0]['status']=='KEEP_EXISTING','E38810-PROTECTED')
    # Independent contextual plan: do not strip protection from original;
    # construct a new photo obligation using exact source, timing and credit.
    s={k:original[k] for k in ('id','type','start','end','asset','source','source_display','source_dimensions','photo_framing','subject','headline','lead','evidence')}
    draft=copy.deepcopy(base);draft['shots'][i]=s
    plan=integrar(case,{'publicar':False,'shots':copy.deepcopy(draft['shots']),'necessidades_direcao':[need.copy()]})
    before=copy.deepcopy(draft)
    alternative,report=preparar_alternativa(case,plan,draft,n['words'],sync,PUBLIC)
    write('motion-attribution.json',{'publish':False,'source_review':fact,'protected_original_refusal':denial,'intake':plan['motion_intake'],'postvoice':report,'original_film_sha256':sha(movie),'voice_sha256':sha(voice),'scope':'assisted contextual storyboard; automatic chart selection and postvoice construction; full film patch replay, not a fresh full compositor render'})
    A.check(alternative is not None and report['alternative_scenes']==[s['id']] and draft==before and alternative['shots'][:i]==base['shots'][:i] and alternative['shots'][i+1:]==base['shots'][i+1:] and alternative['documentary_captions']==base['documentary_captions'],'E38810-AUTOMATIC')
    write('automatic-full-props.json',alternative)
    # Re-render only the automatically generated shot: archived map binary
    # absent, preserve all other decoded film frames instead of inventing it.
    a,b=s['start'],s['end'];chart=copy.deepcopy(alternative['shots'][i]);chart['start']=0;chart['end']=b-a
    caps=[{**g,'start':max(g['start'],a)-a,'end':min(g['end'],b)-a} for g in base['documentary_captions'] if g['end']>a and g['start']<b]
    wav=ROOT/'same-mix.wav';A.ff('-ss',a,'-i',movie,'-vn','-t',b-a,'-ar',48000,'-c:a','pcm_s16le',wav)
    clipaudio='e202/'+sha(wav)+'.wav';shutil.copyfile(wav,PUBLIC/clipaudio)
    write('c6-0.json',{**alternative,'shots':[chart],'duracao':b-a,'documentary_captions':caps,'scene_narration_asset':clipaudio})
    write('patch.json',{'start_frame':round(a*30),'end_frame':round(b*30),'total_frames':2492,'publish':False})
def frame_hashes(path):
    r=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-map','0:v:0','-pix_fmt','yuv420p','-f','framemd5','-'],capture_output=True,text=True,check=True,timeout=180)
    return [l.split(',')[-1].strip() for l in r.stdout.splitlines() if l and not l.startswith('#')]
def finish():
    p=read('patch.json');a,b=p['start_frame'],p['end_frame'];movie=ROOT/'filme-integral-preto.mp4';clip=ROOT/'motion-c6-0.mp4'
    A.check(Q.video_frames(clip)==b-a and Q.video_frames(movie)==p['total_frames'],'E38810-CLIP-FRAMES')
    vf=f'[0:v]trim=end_frame={a},setpts=PTS-STARTPTS[x];[1:v]setpts=PTS-STARTPTS[y];[0:v]trim=start_frame={b},setpts=PTS-STARTPTS[z];[x][y][z]concat=n=3:v=1:a=0[v]'
    out=ROOT/'motion-integral.mp4'
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(movie),'-i',str(clip),'-filter_complex',vf,'-map','[v]','-map','0:a:0','-c:v','libx264','-preset','ultrafast','-crf','0','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',str(out)],check=True,timeout=300)
    x,y=frame_hashes(movie),frame_hashes(out);z=frame_hashes(clip)
    A.check(len(x)==len(y)==p['total_frames'] and x[:a]==y[:a] and x[b:]==y[b:] and y[a:b]==z and x[a:b]!=y[a:b],'E38810-PIXELS')
    A.check(Q.audio_packets(movie)==Q.audio_packets(out),'E38810-AUDIO-PACKETS')
    result=read('comparison.json');result.update(full_film_replay=True,fresh_full_render=False,original_outside_patch_frames_identical=True,patched_frames_identical_to_generated_clip=True,audio_packets_identical=True,total_frames=len(y),duration_s=len(y)/30,full_sha256=sha(out),patch_frames=b-a)
    write('comparison.json',result)
if __name__=='__main__':
    import sys
    (finish if '--finish' in sys.argv else prepare)()
