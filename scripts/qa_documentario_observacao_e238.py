"""Private source-window review on real decoded frames, no TTS or AI.
Reuse USGS acquisition, the cut scanner and the common documentary direction.
"""
import json,sys
from pathlib import Path
from PIL import Image,ImageDraw
from scripts import qa_documentario_geografia_e219 as E
from src.v4.formatos import direcao_eventos as D

def main():
    spec=E.read(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
    if spec.get('publish') is not False:raise ValueError('PRIVATE_ONLY')
    E.STAGE=out/'originais';E.STAGE.mkdir(exist_ok=True)
    args=sys.argv[3:]
    budget=0
    if args:
        if len(args)!=2 or args[0]!='--vision-budget':raise ValueError('E241-ARGS')
        budget=int(args[1])
        if not 1<=budget<=4:raise ValueError('E241-BUDGET')
    attempted=0
    report=[];rows=[]
    for need in spec['needs']:
        for item in need['sources']:
            row={'need':need['id'],'slug':item['slug'],'status':'PENDING','windows':[]}
            try:
                m=E.acquire((item['slug'],item['label']))
                if E.sha(Path(m['local_source']))!=m['expected_sha256']:raise ValueError('SOURCE_SHA')
                for t,_ in E.windows(m,3.8,review_technical=True)[:2]:
                    samples=[E.frame(m['local_source'],t+3.8*f) for f in (.12,.5,.86)]
                    packet=D.pacote_observacao(m,t,3.8,samples,fato_id=need['id'],
                        necessidade=need['description']+' | '+item['note'])
                    packet['diagnostico_tecnico']=D.diagnosticar_janela(samples)
                    if attempted<budget:
                        attempted+=1
                        try:packet['revisao_assistida']=D.revisar_janela_visao(packet,samples,permitir_chamada=True)
                        except Exception as e:packet['revisao_assistida']={'estado':'FALHA','tipo':type(e).__name__}
                    row['windows'].append(packet)
                    rows.append((packet,item,samples))
                row['status']='SAMPLED' if row['windows'] else 'NO_ELIGIBLE_WINDOW'
                row['source']={k:m[k] for k in ('page','expected_sha256','width','height','duration_s')}
            except Exception as e:row.update(status='REJECTED',error=str(e)[:200])
            report.append(row)
            print('E238 REVIEW',row['slug'],row['status'],len(row['windows']),flush=True)
    E.write(out/'review.json',{'publish':False,'records':report,'semantic_review':'PENDING','vision_logical_budget':budget,'vision_logical_attempts':attempted})
    if not rows:raise ValueError('NO_REVIEW_WINDOWS')
    # One chronological row per window, three unaltered samples at known times.
    # The sheet is a visual aid, not a replacement for full-motion inspection.
    for start in range(0,len(rows),6):
        chunk=rows[start:start+6]
        board=Image.new('RGB',(1080,250*len(chunk)), '#101c28')
        draw=ImageDraw.Draw(board)
        for i,(packet,item,frames) in enumerate(chunk):
            y=i*250
            diag=packet['diagnostico_tecnico']
            draw.text((12,y+5),item['label']+' | '+packet['revisao_id'][:12]+' | cards? '+str(diag['quadros_grafismo_suspeito'])+' | barras? '+str(diag['barras_candidatas']),fill='white')
            for j,(im,a) in enumerate(zip(frames,packet['amostras'])):
                copy=im.copy();copy.thumbnail((350,198))
                x=j*360+5
                board.paste(copy,(x+(350-copy.width)//2,y+25+(198-copy.height)//2))
                draw.text((x+5,y+230),f"{a['fonte_s']:.2f}s | {a['pixels_sha256'][:10]}",fill='white')
        board.save(out/f'contato-{start//6+1}.jpg',quality=92)
if __name__=='__main__':main()
