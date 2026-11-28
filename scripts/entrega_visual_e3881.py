"""Send all generated E388.1 visual review evidence to existing authorized private Telegram."""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw
from src.v3 import previa_telegram as T
ROOT=Path('stage_documental/e3881')
def main():
    if not ROOT.exists():return
    proof=ROOT/'comparison.json';p=json.loads(proof.read_text()) if proof.exists() else {'frames':[],'errors':['render incomplete']}
    items=[];receipt=ROOT/'delivery.json'
    def save():receipt.write_text(json.dumps(dict(publish=False,items=items,complete=False),indent=2))
    try:
        chat,_=T.chat_autorizado()
        for f in sorted(ROOT.glob('motion-*.png')):
            r=T._api('sendDocument',{'chat_id':chat,'caption':'E388.1 · '+f.stem+' · dado atribuído · Taiwan limpo · revisão privada · NÃO PUBLICAR'},('document',f))
            if not isinstance(r,dict) or not r.get('message_id'):raise ValueError('receipt missing')
            items.append(dict(file=f.name,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),message_id=r['message_id']));save()
        for f in sorted(ROOT.glob('motion-*.mp4')):
            r=T._api('sendVideo',{'chat_id':chat,'caption':'E388.1 · '+f.stem+' · trecho narrado original · revisão privada · NÃO PUBLICAR','supports_streaming':'true'},('video',T._caber(f)))
            if not isinstance(r,dict) or not r.get('message_id'):raise ValueError('receipt missing')
            items.append(dict(file=f.name,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),message_id=r['message_id']));save()
        complete=len(items)==6 and len(p.get('motion',[]))==2 and not p['errors']
        receipt.write_text(json.dumps(dict(publish=False,items=items,complete=complete),indent=2))
        if not complete:raise ValueError('E388.1 incomplete evidence')
    except Exception:
        save();raise RuntimeError('E388.1 Telegram: entrega incompleta, conferir recibos antes de reenviar') from None
if __name__=='__main__':main()
