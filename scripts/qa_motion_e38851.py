"""E388.5.1: context-before-graphic and exact sourced total area.
Private alternatives, no replacement of original film or new acquisition."""
import json,shutil
from pathlib import Path
from PIL import Image
from scripts import qa_abertura_e339 as A
from scripts.recuperar_checkpoints_documentais import api,listar_releases
from src.v3.pacote_biblioteca import sha
from src.v4.formatos.motion_direcao_e3884 import decidir,ancorar,fila_plano
ROOT=Path('stage_documental/e38851')
def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    meta=api('');A.check(meta['private'] is True and meta['id']==1454059520,'E38851-COFRE')
    rel={r['tag_name']:r for r in listar_releases(300)}
    tag='review-e376-45907502601-1'
    movie=A.download(rel,tag,'filme-integral-preto.mp4',ROOT,'e9f961c2d2257aa8946819da44ddc28f1cb52ffa1238eb0e4f77f5ec10ea74bf',30_000_000)
    full=json.loads(A.download(rel,tag,'props-candidate.json',ROOT,'8fbe773cc82a6f0c63ad58c48e90f79deee9d4dfde6d5cec3b9b2dd4b529612e',100_000).read_text())
    A.check(full['documentary_caption_origin']=='PALAVRAS_MEDIDAS','E38851-CAPTIONS')
    r=json.loads(Path('benchmarks/e342/dados.json').read_text())['entries'][1]
    library=json.loads(Path('benchmarks/e3883/props.json').read_text());public=Path('motor4/remotion/public');(public/'e202').mkdir(exist_ok=True)
    rows=[]
    for id in ('c6-0','c6-1'):
        s=next(x for x in full['shots'] if x['id']==id);a,b=s['start'],s['end'];duration=b-a
        name=Path(s['asset']).name;h=Path(name).stem
        if id=='c6-0':
            reveal=s['documentary_static_reveal']
            A.check(reveal['sha256']==h=='b6ebc2d171849a048e5b514b56364ac725f7d57860e8b85fc59791519de961ff' and reveal['label']=='35,5 KM² · QUADRO DO MAPA' and reveal['revisao_id']=='revisoes/e320-45860199613-1/evidencia-00.jpg','E38851-MAP')
            claim={'schema':'coringa.motion.claim.private.v1','publish':False,'fixture':False,'shape':'area','title':'ÁREA COBERTA PELA LAVA','scope':'Maio–agosto de 2018 · inclui o delta de lava','unit':'km²','values':[{'label':'Área total coberta','value':35.5}],'relation':'approx','source':{'url':r['source_url'],'date':'2018-08','statement':'Mapa oficial USGS E320: Total flow area 35.5 square kilometers; inclui a área de terra nova, não somar.'}}
            rec={'shot':id,'sha256':h,'source_url':r['source_url'],'value':'≈ 35,5 km²','scope':claim['scope'],'anchor':'TRINTA','publish':False}
            fact={'sha256':h,'url':rec['source_url'],'value':rec['value'],'scope':rec['scope'],'at':reveal['at'],'publish':False}
            timing='EXISTING_STATIC_REVEAL_ANCHOR_IN_MEASURED_CAPTION'
        else:
            claim=library['shots'][1]['documentary_chart_trial'];rec=r;fact=s['documentary_reported_fact']
            A.check(fact['value']==r['value']=='≈ 3,54 km²' and fact['scope']==r['scope'] and fact['sha256']==h==r['sha256'] and fact['url']==r['source_url'],'E38851-RECEIPT')
            timing='E342_MEASURED_WORD'
        tag_asset=next(t for t in (A.BASE,A.FILM,A.PHOTO,'review-e323-45864804065-1') if t in rel and any(x['name']==name for x in rel[t]['assets']))
        src=A.download(rel,tag_asset,name,public/'film_editorial',h,250_000_000)
        if s['type']=='photo':
            with Image.open(src) as im:A.check(list(im.size)==s['source_dimensions'],'E38851-DIMENSIONS')
        else:
            w,hh,d=A.probe(src);A.check([w,hh]==s['source_dimensions'] and s['source_in_seconds']+duration<=d+.05,'E38851-VIDEO')
        caps=[{**g,'start':max(g['start'],a)-a,'end':min(g['end'],b)-a} for g in full['documentary_captions'] if g['end']>a and g['start']<b]
        need={'fact_id':id,'role':'quantitative_explainer','purpose':'magnitude','requires_direct_evidence':False}
        receipt={'fact_id':id,'verified_claim':claim,'source_sha256':h,'publish':False}
        decision=decidir(need,claim,receipt)
        anchor=ancorar(decision,s,fact,rec,caps)
        wav=ROOT/(id+'.wav');A.ff('-ss',a,'-i',movie,'-vn','-t',duration,'-ar',48000,'-c:a','pcm_s16le',wav)
        audio='e202/'+sha(wav)+'.wav';shutil.copyfile(wav,public/audio)
        context={'schema':'coringa.motion.context.private.v1','publish':False,'asset':s['asset'],'sha256':h,'kind':s['type'],'sourceIn':s.get('source_in_seconds',0),'credit':s.get('source_display') or s['source']}
        chart={**library['shots'][1],'id':id,'start':0,'end':duration,'source':claim['source']['url'],'subject':claim['scope'],'lead':claim['title'],'documentary_chart_trial':claim,'documentary_chart_anchor':anchor,'documentary_chart_context':context}
        props={**library,'shots':[chart],'duracao':duration,'scene_narration_asset':audio,'documentary_captions':caps,'documentary_caption_origin':'PALAVRAS_MEDIDAS'}
        (ROOT/(id+'.json')).write_text(json.dumps(props,ensure_ascii=False))
        plan={'publicar':False,'shots':[s],'necessidades_direcao':[{'id':id,'fatos':[id],'motion_role':'quantitative_explainer','motion_purpose':'magnitude','exigir_evidencia_direta':True}],'motion_claims':[{'need_id':id,'fact_id':id,'claim':claim,'receipt':receipt}]}
        preserve=fila_plano(plan);A.check(preserve[0]['status']=='KEEP_EXISTING','E38851-DIRECT-PROTECTION')
        rows.append({'id':id,'decision':decision,'anchor':anchor,'timing_origin':timing,'context':context,'original_direct_evidence_decision':preserve,'receipt':rec,'audio_sha256':sha(wav),'publish':False})
    (ROOT/'motion-attribution.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
