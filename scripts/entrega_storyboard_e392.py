import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
from src.v3 import previa_telegram as T
ROOT=Path('stage_documental/e392')
def main():
    p=json.loads((ROOT/'comparison.json').read_text())
    if p['errors'] or len(p['rows'])!=4:raise ValueError('E392-QA')
    board=Image.new('RGB',(1080,1920),'black')
    for i in range(4):
        with Image.open(ROOT/f'board-{i}.png') as im:board.paste(im.convert('RGB').resize((540,960),Image.Resampling.LANCZOS),((i%2)*540,(i//2)*960))
    f=ROOT/'E392-STORYBOARD-2D.jpg';board.save(f,quality=95)
    chat,_=T.chat_autorizado()
    r=T._api('sendDocument',{'chat_id':chat,'caption':'E392 · quatro quadros 2.5D · direção artística para avaliação · NÃO É VÍDEO · não publicar'},('document',f))
    if not r.get('message_id'):raise ValueError('E392-DELIVERY')
    (ROOT/'delivery.json').write_text(json.dumps({'publish':False,'complete':True,'items':[{'file':f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'message_id':r['message_id']}]},indent=2))
if __name__=='__main__':main()
