"""Send all generated E388 visual review evidence to existing authorized private Telegram."""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw
from src.v3 import previa_telegram as T
ROOT=Path('stage_documental/e388')
def main():
    if not ROOT.exists():return
    proof=ROOT/'comparison.json';p=json.loads(proof.read_text()) if proof.exists() else {'frames':[],'errors':['render incomplete']}
    items=[];receipt=ROOT/'delivery.json'
    def save():receipt.write_text(json.dumps(dict(publish=False,items=items,complete=False),indent=2))
    try:
        chat,_=T.chat_autorizado()
        for id in sorted({f.stem.removesuffix('-baseline').removesuffix('-clean') for f in ROOT.glob('*.png') if f.stem.endswith(('-baseline','-clean'))}):
            files=[ROOT/(id+s+'.png') for s in ('-baseline','-clean')];available=[f for f in files if f.exists()]
            if not available:continue
            sheet=Image.new('RGB',(540*len(available),1000),'#000000');d=ImageDraw.Draw(sheet)
            for i,f in enumerate(available):
                with Image.open(f) as im:sheet.paste(im.convert('RGB').resize((540,960)),(540*i,40))
                d.text((540*i+8,12),f.stem,fill='white')
            dest=ROOT/(id+'-AB.jpg');sheet.save(dest,quality=94)
            r=T._api('sendDocument',{'chat_id':chat,'caption':'E388 · '+id+' · A/B Taiwan limpo · revisão privada, UI pendente · NÃO PUBLICAR'},('document',dest))
            if not isinstance(r,dict) or not r.get('message_id'):raise ValueError('receipt missing')
            items.append(dict(file=dest.name,sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),message_id=r['message_id']));save()
        for f in sorted(ROOT.glob('motion-*.png')):
            r=T._api('sendDocument',{'chat_id':chat,'caption':'E388 · '+f.stem+' · dado atribuído · revisão privada · NÃO PUBLICAR'},('document',f))
            if not isinstance(r,dict) or not r.get('message_id'):raise ValueError('receipt missing')
            items.append(dict(file=f.name,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),message_id=r['message_id']));save()
        for f in sorted([*ROOT.glob('narrated-*.mp4'),*ROOT.glob('motion-*.mp4')]):
            r=T._api('sendVideo',{'chat_id':chat,'caption':'E388 · '+f.stem+' · trecho narrado original · revisão privada · NÃO PUBLICAR','supports_streaming':'true'},('video',T._caber(f)))
            if not isinstance(r,dict) or not r.get('message_id'):raise ValueError('receipt missing')
            items.append(dict(file=f.name,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),message_id=r['message_id']));save()
        complete=len(items)==11 and len(p['frames'])==10 and len(p.get('motion',[]))==2 and not p['errors']
        receipt.write_text(json.dumps(dict(publish=False,items=items,complete=complete),indent=2))
        if not complete:raise ValueError('E388 incomplete evidence')
    except Exception:
        save();raise RuntimeError('E388 Telegram: entrega incompleta, conferir recibos antes de reenviar') from None
if __name__=='__main__':main()
