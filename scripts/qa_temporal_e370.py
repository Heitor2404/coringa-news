"""Replay existing original videos with the established local temporal selector."""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw
from src.v4.formatos import amostragem_documental as A
from scripts import qa_documentario_geografia_e219 as E

SOURCES=[
    ('noaa','5b3cd4623256d6e27a4691572170d3dc053448ef79380ae47923579e6383e85b'),
    ('usgs','9f26970678e34ecc024d40f45ada750759a0849a7d5aa97cbadf9fece2647c7a')]
def main():
    root=Path('stage_documental/e370');out=root/'proof';out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for name,sha in SOURCES:
        files=[p for p in (root/'inputs').rglob('*') if p.is_file() and p.stem==sha]
        if len(files)!=1:raise ValueError('E370_ORIGINAL_AUSENTE_'+name)
        p=files[0]
        if hashlib.sha256(p.read_bytes()).hexdigest()!=sha:raise ValueError('E370_SHA_'+name)
        w,h,dur=E.probe(p)
        midia=dict(local_source=str(p),width=w,height=h,duration_s=dur,expected_sha256=sha)
        exploration=A.explorar(midia,E.frame,max_janelas=12,largura=240)
        selected=A.selecionar(exploration,limite=3,priorizar_movimento=True)
        # Compare ranking with the same windows and the new hint disabled.
        baseline={**exploration,'janelas':[dict(j,diagnostico={**j['diagnostico'],'faixa_grafica_persistente_suspeita':False,'quadros_faixa_grafica_suspeita':0}) if 'diagnostico' in j else j for j in exploration['janelas']]}
        old=A.selecionar(baseline,limite=3,priorizar_movimento=True)
        if not selected:raise ValueError('E370_SEM_JANELAS_'+name)
        # Compare the original early sample against three existing selector windows.
        groups=[('amostra inicial',[min(2,dur*.3)])]+[
            ('janela proposta', [j['inicio_s']+j['duracao_s']*f for f in (0,.5,.9)]) for j in selected]
        sheet=Image.new('RGB',(960,220*len(groups)),'#15191d');draw=ImageDraw.Draw(sheet)
        samples=[]
        for i,(label,times) in enumerate(groups):
            for k,t in enumerate(times):
                im=E.frame(p,t,width=320).convert('RGB')
                im.thumbnail((320,194))
                x=k*320;y=i*220
                draw.text((x+5,y+4),f'{label} | {t:.2f}s',fill='white')
                sheet.paste(im,(x+(320-im.width)//2,y+22))
                samples.append(dict(label=label,t=t,pixel_sha256=hashlib.sha256(im.tobytes()).hexdigest()))
        preview=out/(name+'-temporal.jpg');sheet.save(preview,quality=91)
        rows.append(dict(provider=name,sha256=sha,width=w,height=h,duration_s=dur,selected=selected,
            exploration=exploration,baseline_starts=[j['inicio_s'] for j in old],suspect_starts=[j['inicio_s'] for j in exploration['janelas'] if j.get('diagnostico',{}).get('quadros_faixa_grafica_suspeita')],samples=samples,preview=preview.name,semantic_review='PENDING',publish=False))
    (out/'temporal.json').write_text(json.dumps(dict(publish=False,semantic_approval=False,new_ai=0,new_source_http=0,rows=rows),ensure_ascii=False,indent=2))
    print('E370_TEMPORAL',[(r['provider'],len(r['exploration']['janelas']),[round(x['inicio_s'],2) for x in r['selected']]) for r in rows])
if __name__=='__main__':main()
