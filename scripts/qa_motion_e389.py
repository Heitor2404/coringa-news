"""E389: source-backed stages with original real evidence between them."""
import json,copy,shutil
from pathlib import Path
from PIL import Image
from scripts import qa_abertura_e339 as A
from scripts.recuperar_checkpoints_documentais import api,listar_releases
from src.v3.pacote_biblioteca import sha
ROOT=Path('stage_documental/e389')
def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    meta=api('');A.check(meta['private'] is True and meta['id']==1454059520,'E389-COFRE')
    releases={r['tag_name']:r for r in listar_releases(300)}
    tag='review-e376-45907502601-1'
    movie=A.download(releases,tag,'filme-integral-preto.mp4',ROOT,'e9f961c2d2257aa8946819da44ddc28f1cb52ffa1238eb0e4f77f5ec10ea74bf',30_000_000)
    full=json.loads(A.download(releases,tag,'props-candidate.json',ROOT,'8fbe773cc82a6f0c63ad58c48e90f79deee9d4dfde6d5cec3b9b2dd4b529612e',100_000).read_text())
    seq=json.loads(Path('benchmarks/e389/sequence.json').read_text())
    A.check(full['documentary_caption_origin']=='PALAVRAS_MEDIDAS' and seq['publish'] is False,'E389-ORIGIN')
    start,end=seq['stages'][0]['start'],seq['stages'][-1]['end']
    shots=[copy.deepcopy(s) for s in full['shots'] if s['start']>=start-.0001 and s['end']<=end+.0001]
    A.check([s['id'] for s in shots]==['c5-0','c5-1','c5-2','c5-3'],'E389-SHOTS')
    public=Path('motor4/remotion/public');(public/'e202').mkdir(exist_ok=True)
    for s in shots:
        name=Path(s['asset']).name;h=Path(name).stem
        src=A.download(releases,'review-e323-45864804065-1',name,public/'film_editorial',h,250_000_000)
        if s['type']=='photo':
            with Image.open(src) as im:A.check(list(im.size)==s['source_dimensions'],'E389-PHOTO')
        else:
            w,hh,d=A.probe(src);A.check([w,hh]==s['source_dimensions'] and s['source_in_seconds']+s['end']-s['start']<=d+.05,'E389-VIDEO')
        s['start']-=start;s['end']-=start
    caps=[{**g,'start':max(g['start'],start)-start,'end':min(g['end'],end)-start} for g in full['documentary_captions'] if g['end']>start and g['start']<end]
    wav=ROOT/'same-mix.wav';A.ff('-ss',start,'-i',movie,'-vn','-t',end-start,'-ar',48000,'-c:a','pcm_s16le',wav)
    audio='e202/'+sha(wav)+'.wav';shutil.copyfile(wav,public/audio)
    baseline={**full,'shots':shots,'duracao':end-start,'scene_narration_asset':audio,'documentary_captions':caps}
    variant=copy.deepcopy(baseline)
    for index,stage,regions in [(0,seq['stages'][0],[(56.014,[.21,.49,.60,.99],'Reservatório de magma','RESERVATÓRIO')]),(3,seq['stages'][2],[(64.603,[.14,.30,.53,.76],'Blocos rebaixados','COLAPSO'),(66.328,[.31,.49,.48,.75],'Espaço vazio no esquema','PROCESSO')])]:
        s=variant['shots'][index];r=s.pop('documentary_static_reveal')
        A.check(r['bbox']==stage['bbox'] and r['sha256']==seq['source']['sha256'] and r['revisao_id']==seq['source']['review'],'E389-REVIEW-BIND')
        s.pop('documentary_composition_v2',None)
        s['documentary_causal_stage']={'schema':'coringa.causal.stage.private.v1','publish':False,'group':'E323-reviewed-states','stage':0 if index==0 else 1,'count':2,'sourceSha':r['sha256'],'review':r['revisao_id'],'panel':r['bbox'],'title':stage['label'],'credit':'USGS · Hawaiian Volcano Observatory','scale':'illustrative_not_to_scale','highlights':[{'at':t-start-s['start'],'box':box,'label':label,'anchorWord':word} for t,box,label,word in regions]}
    A.check(variant['shots'][1:3]==baseline['shots'][1:3],'E389-PRESERVE-RECORD')
    for name,p in [('baseline',baseline),('variant',variant)]:
        (ROOT/(name+'.json')).write_text(json.dumps(p,ensure_ascii=False))
    A.ff('-ss',start,'-i',movie,'-t',end-start,'-map','0:v:0','-map','0:a:0','-c:v','libx264','-crf',20,'-c:a','aac',ROOT/'motion-baseline.mp4')
    (ROOT/'motion-attribution.json').write_text(json.dumps({'publish':False,'audio_sha256':sha(wav),'source':seq['source'],'preserved_real_shots':['c5-1','c5-2'],'original_film_sha256':sha(movie),'timing_origin':'existing measured caption groups, not new word measurements','illustrative_not_to_scale':True,'physical_simulation':False,'rights_status':'REVIEW_PENDING'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
