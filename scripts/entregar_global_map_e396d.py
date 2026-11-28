import json,hashlib,os
from pathlib import Path
from src.v3 import previa_telegram as T
ROOT=Path('qa_global_e396d')
def main():
    files=[p for p in [ROOT/'wide-contact.jpg',ROOT/'portrait-contact.jpg',ROOT/'wide.mp4',ROOT/'portrait.mp4'] if p.is_file()]
    if not files:return
    chat,_=T.chat_autorizado();items=[]
    for f in files:
        video=f.suffix=='.mp4';field='video' if video else 'document'
        args={'chat_id':chat,'caption':'E396D · '+os.environ.get('MAP_CASE','mapa')+' · '+f.name+' · prova privada, sem voz, sem publicação'}
        if video:args['supports_streaming']='true'
        r=T._api('sendVideo' if video else 'sendDocument',args,(field,T._caber(f) if video else f))
        if not isinstance(r,dict) or not r.get('message_id'):raise ValueError('E396-DELIVERY')
        items.append({'file':f.name,'message_id':r['message_id'],'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
        (ROOT/'delivery.json').write_text(json.dumps({'publish':False,'items':items,'complete':len(items)==4},indent=2))
    if len(items)!=4:raise ValueError('E396-INCOMPLETE')
    # Also deliver original vertical as a document to avoid playback recompression.
    original=ROOT/'portrait.mp4'
    if original.stat().st_size<=T.LIMITE_MB*1024*1024:
        r=T._api('sendDocument',{'chat_id':chat,'caption':'E396D · '+os.environ.get('MAP_CASE','mapa')+' · ORIGINAL VERTICAL · arquivo sem recompressão do bot'},('document',original))
        if not isinstance(r,dict) or not r.get('message_id'):raise ValueError('E396-ORIGINAL')
        items.append({'file':'portrait.mp4','mode':'original_document','message_id':r['message_id'],'sha256':hashlib.sha256(original.read_bytes()).hexdigest()})
    (ROOT/'delivery.json').write_text(json.dumps({'publish':False,'items':items,'complete':True,'original_document':len(items)==5},indent=2))
if __name__=='__main__':main()
