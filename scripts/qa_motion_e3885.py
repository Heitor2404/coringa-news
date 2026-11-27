"""Private narrated chart alternatives, authenticated E379 audio; original film unchanged."""
import json,shutil
from pathlib import Path
from scripts import qa_abertura_e339 as A
from scripts.recuperar_checkpoints_documentais import api,listar_releases
from src.v3.pacote_biblioteca import sha
from src.v4.formatos.motion_direcao_e3884 import decidir,ancorar
ROOT=Path('stage_documental/e3885')
def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    meta=api('');A.check(meta['private'] is True and meta['id']==1454059520,'E3885-COFRE')
    rel={r['tag_name']:r for r in listar_releases(300)}
    tag='review-e376-45907502601-1'
    movie=A.download(rel,tag,'filme-integral-preto.mp4',ROOT,'e9f961c2d2257aa8946819da44ddc28f1cb52ffa1238eb0e4f77f5ec10ea74bf',30_000_000)
    full=json.loads(A.download(rel,tag,'props-candidate.json',ROOT,'8fbe773cc82a6f0c63ad58c48e90f79deee9d4dfde6d5cec3b9b2dd4b529612e',100_000).read_text())
    A.check(full['documentary_caption_origin']=='PALAVRAS_MEDIDAS','E3885-CAPTIONS')
    entries=json.loads(Path('benchmarks/e342/dados.json').read_text())['entries']
    library=json.loads(Path('benchmarks/e3883/props.json').read_text())
    public=Path('motor4/remotion/public');(public/'e202').mkdir(exist_ok=True)
    report=[]
    for i,r in enumerate(entries):
        s=next(x for x in full['shots'] if x['id']==r['shot']);f=s['documentary_reported_fact'];a,b=s['start'],s['end'];duration=b-a
        A.check(f['publish'] is False and f['value']==r['value'] and f['scope']==r['scope'] and f['sha256']==r['sha256'] and f['url']==r['source_url'] and f['authority']==r['authority'],'E3885-RECEIPT')
        claim=library['shots'][i]['documentary_chart_trial']
        A.check(claim['source']['url']==r['source_url'] and claim['source']['date']==r['source_date'] and ((i==0 and r['value']=='≈ 21–26 km/h' and [v['value'] for v in claim['values']]==[21,26]) or (i==1 and r['value']=='≈ 3,54 km²' and [v['value'] for v in claim['values']]==[3.54])),'E3885-CLAIM')
        need={'fact_id':s['id'],'role':'quantitative_explainer','purpose':'magnitude','requires_direct_evidence':False}
        receipt={'fact_id':s['id'],'verified_claim':claim,'source_sha256':r['sha256'],'publish':False}
        decision=decidir(need,claim,receipt)
        A.check(decision['status']=='CHART_CANDIDATE','E3885-DECISION')
        caps=[{**g,'start':max(g['start'],a)-a,'end':min(g['end'],b)-a} for g in full['documentary_captions'] if g['end']>a and g['start']<b]
        anchor=ancorar(decision,s,f,r,caps)
        wav=ROOT/(s['id']+'.wav');A.ff('-ss',a,'-i',movie,'-vn','-t',duration,'-ar',48000,'-c:a','pcm_s16le',wav)
        audio='e202/'+sha(wav)+'.wav';shutil.copyfile(wav,public/audio)
        chart={**library['shots'][i],'id':s['id'],'start':0,'end':duration,'documentary_chart_anchor':anchor}
        props={**library,'shots':[chart],'duracao':duration,'scene_narration_asset':audio,'documentary_captions':caps,'documentary_caption_origin':'PALAVRAS_MEDIDAS'}
        (ROOT/(s['id']+'.json')).write_text(json.dumps(props,ensure_ascii=False))
        report.append({'id':s['id'],'decision':decision,'anchor':anchor,'receipt':r,'original_evidence_preserved_in_film':True,'audio_sha256':sha(wav),'publish':False})
    (ROOT/'motion-attribution.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
