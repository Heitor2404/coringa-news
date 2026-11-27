"""Send all generated E388.6 visual review evidence to existing authorized private Telegram."""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw
from src.v3 import previa_telegram as T
ROOT=Path('stage_documental/e3886')
def main():
    if not ROOT.exists():return
    proof=ROOT/'comparison.json';p=json.loads(proof.read_text()) if proof.exists() else {'frames':[],'errors':['render incomplete']}
    items=[];receipt=ROOT/'delivery.json'
    def save():receipt.write_text(json.dumps(dict(publish=False,items=items,complete=False),indent=2))
    try:
        chat,_=T.chat_autorizado()
        frames=sorted(ROOT.glob('motion-*.png'),key=lambda f:(f.stem.rsplit('-',1)[0],int(f.stem.rsplit('-',1)[1])))
        for start in range(0,len(frames),8):
            chunk=frames[start:start+8]
            board=Image.new('RGB',(1080,520*((len(chunk)+3)//4)),'black');d=ImageDraw.Draw(board)
            for i,frame in enumerate(chunk):
                x=(i%4)*270;y=(i//4)*520
                with Image.open(frame) as im:board.paste(im.convert('RGB').resize((270,480)),(x,y+32))
                d.text((x+4,y+5),frame.stem,fill='white')
            f=ROOT/f'contact-{start//8:02d}.jpg';board.save(f,quality=93)
            r=T._api('sendDocument',{'chat_id':chat,'caption':'E388.6 · '+f.stem+' · quadros diagnósticos · revisão privada · NÃO PUBLICAR'},('document',f))
            if not isinstance(r,dict) or not r.get('message_id'):raise ValueError('receipt missing')
            items.append(dict(file=f.name,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),message_id=r['message_id']));save()
        for f in sorted(ROOT.glob('motion-*.mp4')):
            r=T._api('sendVideo',{'chat_id':chat,'caption':'E388.6 · '+f.stem+' · trecho narrado original · revisão privada · NÃO PUBLICAR','supports_streaming':'true'},('video',T._caber(f)))
            if not isinstance(r,dict) or not r.get('message_id'):raise ValueError('receipt missing')
            items.append(dict(file=f.name,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),message_id=r['message_id']));save()
        complete=len(list(ROOT.glob('motion-*.mp4')))==1 and len(items)==(len(frames)+7)//8+1 and len(p.get('rows',[]))==2
        receipt.write_text(json.dumps(dict(publish=False,items=items,complete=complete),indent=2))
        if not complete:raise ValueError('E388.6 incomplete evidence')
    except Exception:
        save();raise RuntimeError('E388.6 Telegram: entrega incompleta, conferir recibos antes de reenviar') from None
if __name__=='__main__':main()
