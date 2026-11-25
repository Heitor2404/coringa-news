"""Detailed private ROI review of previously selected source windows.
No theme-specific renderer, no synthetic geometry, no publication.
"""
import sys
from pathlib import Path
from PIL import Image,ImageDraw
from scripts import qa_documentario_geografia_e219 as E
from src.v4.formatos import direcao_eventos as D

def main():
    spec=E.read(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
    if spec.get('publish') is not False:raise ValueError('PRIVATE_ONLY')
    cases=spec['cases']
    if not 1<=len(cases)<=2:raise ValueError('E244-BUDGET')
    E.STAGE=out/'originais';E.STAGE.mkdir(exist_ok=True)
    acquired={};reports=[]
    for i,c in enumerate(cases):
        if c['slug'] not in acquired:
            acquired[c['slug']]=E.acquire((c['slug'],c['label']))
        m=acquired[c['slug']]
        if E.sha(Path(m['local_source']))!=c['sha256_origem'] or m['expected_sha256']!=c['sha256_origem']:
            raise ValueError('E244-SOURCE-CHANGED')
        start,span=c['inicio_s'],c['duracao_s'];fractions=(0,.5,.9)
        samples=[E.frame(m['local_source'],start+span*f,width=min(960,m['width'])) for f in fractions]
        p=D.pacote_observacao(m,start,span,samples,fato_id=c['fato_id'],necessidade=c['necessidade'],fracoes=fractions)
        p['diagnostico_tecnico']=D.diagnosticar_janela(samples)
        try:p['revisao_assistida']=D.revisar_janela_visao(p,samples,permitir_chamada=True)
        except Exception as e:p['revisao_assistida']={'estado':'FALHA','tipo':type(e).__name__}
        sel=D.candidato_revisado(p,m,fato_id=c['fato_id'])
        reports.append({'case':c,'pacote':p,'selecao':sel})
        # Side-by-side originals and visualized proposed boxes; never modify source.
        q=p['revisao_assistida'];fr=q.get('video_framing') or {}
        points=fr.get('pontos') or []
        board=Image.new('RGB',(1080,3*325+55),'#101c28');draw=ImageDraw.Draw(board)
        draw.text((12,10),c['label']+' | '+p['revisao_id'][:12]+' | '+q.get('veredito','FALHA'),fill='white')
        draw.text((12,30),'ORIGINAL',fill='white');draw.text((552,30),'BBOX CANDIDATA - REVISAO PENDENTE',fill='white')
        for j,im in enumerate(samples):
            a=im.copy();a.thumbnail((520,292));y=55+j*325
            b=a.copy();d=ImageDraw.Draw(b)
            if len(points)==3:
                for e in points[j]['elementos']:
                    x0,y0,x1,y1=e['bbox'];w,h=b.size
                    d.rectangle((x0*w,y0*h,x1*w,y1*h),outline='#ffdf40',width=3)
                    d.text((x0*w,max(0,y0*h-13)),e['nome'][:35],fill='#ffdf40')
            board.paste(a,(8,y));board.paste(b,(548,y))
            draw.text((12,y+295),f"{p['amostras'][j]['fonte_s']:.3f}s | {p['amostras'][j]['pixels_sha256'][:12]}",fill='white')
        board.save(out/f'roi-{i+1}.jpg',quality=95)
        print('E244 ROI',i+1,q.get('veredito','FALHA'),q.get('diagnostico_bbox','SEM_BBOX'),(sel.get('enquadramento') or {}).get('layout','SEM_ENQUADRAMENTO'),flush=True)
    E.write(out/'roi-review.json',{'publish':False,'human_review':'PENDING','records':reports})
if __name__=='__main__':main()
