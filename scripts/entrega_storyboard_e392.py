import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
from src.v3 import previa_telegram as T
ROOT=Path('stage_documental/e392')
def main():
    frames=[i for i in range(4) if (ROOT/f'board-{i}.png').is_file()]
    if not frames:
        print('E392: nenhum quadro disponivel para avaliacao')
        return
    report=ROOT/'comparison.json'
    p=json.loads(report.read_text()) if report.is_file() else {}
    approved=len(frames)==4 and len(p.get('rows',[]))==4 and p.get('errors')==[]
    status='QA TECNICO OK; ARTE PENDENTE' if approved else 'REPROVADO OU INCOMPLETO; NAO PUBLICAR'
    board=Image.new('RGB',(1080,1920),'black')
    draw=ImageDraw.Draw(board)
    for i in range(4):
        xy=((i%2)*540,(i//2)*960)
        if i in frames:
            with Image.open(ROOT/f'board-{i}.png') as im:board.paste(im.convert('RGB').resize((540,960),Image.Resampling.LANCZOS),xy)
        else:draw.text((xy[0]+40,xy[1]+400),f'QUADRO {i+1} INDISPONIVEL',fill='white')
    f=ROOT/('E392B1-STORYBOARD-2D.jpg' if approved else 'E392B1-STORYBOARD-REPROVADO.jpg')
    board.save(f,quality=95)
    chat,_=T.chat_autorizado()
    detail='; '.join(str(x) for x in p.get('errors',[]))[:220]
    r=T._api('sendDocument',{'chat_id':chat,'caption':f'E392B.1 · {status} · {len(frames)}/4 quadros · NÃO É VÍDEO · avaliação privada. {detail}'},('document',f))
    if not r.get('message_id'):raise ValueError('E392-DELIVERY')
    (ROOT/'delivery.json').write_text(json.dumps({'publish':False,'complete':True,'qa_approved':approved,'frames':frames,'items':[{'file':f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'message_id':r['message_id']}]},indent=2))
    if not approved:raise ValueError('E392-QA-REPROVADO-ENTREGUE')
if __name__=='__main__':main()
