"""Send all review material through the existing authorized private destination."""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw
from src.v3 import previa_telegram as T
ROOT=Path('stage_documental/e38832')
def main():
    if not ROOT.exists():raise RuntimeError('E3883 NO OUTPUT')
    items=[]
    def save(ok=False):(ROOT/'delivery.json').write_text(json.dumps(dict(publish=False,complete=ok,items=items),indent=2))
    try:
        chat,_=T.chat_autorizado()
        frames=sorted(ROOT.glob('chart-*.png'))
        if frames:
            sheet=Image.new('RGB',(1080,1000*((len(frames)+1)//2)),(0,0,0));d=ImageDraw.Draw(sheet)
            for i,f in enumerate(frames):
                x=(i%2)*540;y=(i//2)*1000
                with Image.open(f) as im:sheet.paste(im.convert('RGB').resize((540,960)),(x,y+40))
                d.text((x+10,y+10),f.stem,fill='white')
            p=ROOT/'library-contact.jpg';sheet.save(p,quality=93)
            r=T._api('sendDocument',{'chat_id':chat,'caption':'E388.3.2 · biblioteca motion Taiwan · versão com ajuste de glifos, seis exemplos para avaliar estética. Três dados de acervo e três exemplos fictícios identificados. Revisão privada.'},('document',p))
            if not isinstance(r,dict) or not r.get('message_id'):raise RuntimeError('RECEIPT')
            items.append(dict(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),message_id=r['message_id']));save()
        p=ROOT/'motion-library.mp4'
        if p.is_file():
            r=T._api('sendVideo',{'chat_id':chat,'caption':'E388.3.2 · motion graphics Taiwan · prova muda de linguagem visual (não é documentário narrado). Avaliar gráficos, não roteiro. NÃO PUBLICAR.','supports_streaming':'true'},('video',T._caber(p)))
            if not isinstance(r,dict) or not r.get('message_id'):raise RuntimeError('RECEIPT')
            items.append(dict(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),message_id=r['message_id']));save()
        ok=len(frames)==6 and len(items)==2
        save(ok)
        if not ok:raise RuntimeError('INCOMPLETE')
    except Exception:
        save();raise RuntimeError('E3883 DELIVERY INCOMPLETE') from None
if __name__=='__main__':main()
