"""Send all generated E394 visual review evidence to existing authorized private Telegram."""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw
from src.v3 import previa_telegram as T
ROOT=Path('stage_documental/e393')
def main():
    if not ROOT.exists():return
    proof=ROOT/'comparison.json';p=json.loads(proof.read_text()) if proof.exists() else {'frames':[],'errors':['render incomplete']}
    if not list(ROOT.glob('motion-*.png')) and not (ROOT/'motion-causal-2d.mp4').is_file():return
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
            r=T._api('sendDocument',{'chat_id':chat,'caption':'E394 · '+('QA REPROVADO · ' if p.get('errors') else 'QA técnico · ')+f.stem+' · quadros diagnósticos · revisão privada · NÃO PUBLICAR'},('document',f))
            if not isinstance(r,dict) or not r.get('message_id'):raise ValueError('receipt missing')
            items.append(dict(file=f.name,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),message_id=r['message_id']));save()
        videos=[ROOT/n for n in ('motion-causal-2d.mp4','motion-gears-2d.mp4') if (ROOT/n).is_file()]
        for f in videos:
            r=T._api('sendVideo',{'chat_id':chat,'caption':'E394 · '+f.stem+' · '+('trecho narrado original' if 'causal' in f.stem else 'prova mecânica muda')+' · revisão privada · NÃO PUBLICAR','supports_streaming':'true'},('video',T._caber(f)))
            if not isinstance(r,dict) or not r.get('message_id'):raise ValueError('receipt missing')
            items.append(dict(file=f.name,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),message_id=r['message_id']));save()
        complete=len(videos)==2 and len(items)==(len(frames)+7)//8+2 and len(p.get('rows',[]))>=12 and not p.get('errors')
        receipt.write_text(json.dumps(dict(publish=False,items=items,complete=complete),indent=2))
        if not complete:raise ValueError('E394 incomplete evidence')
    except Exception:
        save();raise RuntimeError('E394 Telegram: entrega incompleta, conferir recibos antes de reenviar') from None
if __name__=='__main__':main()
