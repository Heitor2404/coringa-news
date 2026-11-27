import json,hashlib
from pathlib import Path
from src.v3 import previa_telegram as T
ROOT=Path('qa_neo_map_e396')
def main():
    files=[p for p in [ROOT/'wide-contact.jpg',ROOT/'portrait-contact.jpg',ROOT/'wide.mp4',ROOT/'portrait.mp4'] if p.is_file()]
    if not files:return
    chat,_=T.chat_autorizado();items=[]
    for f in files:
        video=f.suffix=='.mp4';field='video' if video else 'document'
        args={'chat_id':chat,'caption':'E396 · cartografia premium · '+f.name+' · prova privada, sem voz, sem publicação'}
        if video:args['supports_streaming']='true'
        r=T._api('sendVideo' if video else 'sendDocument',args,(field,T._caber(f) if video else f))
        if not isinstance(r,dict) or not r.get('message_id'):raise ValueError('E396-DELIVERY')
        items.append({'file':f.name,'message_id':r['message_id'],'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
        (ROOT/'delivery.json').write_text(json.dumps({'publish':False,'items':items,'complete':len(items)==4},indent=2))
    if len(items)!=4:raise ValueError('E396-INCOMPLETE')
if __name__=='__main__':main()
