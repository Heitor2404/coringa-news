import json,hashlib,os
from pathlib import Path
from src.v3 import previa_telegram as T
ROOT=Path('qa_global_e396e')
def main():
    f=ROOT/'portrait.mp4'
    if not f.is_file():return
    chat,_=T.chat_autorizado()
    # One vertical video per case. Original as document when possible; no duplicate,
    # no horizontal videos, no contact sheets in Telegram.
    if f.stat().st_size<=T.LIMITE_MB*1024*1024:method,field,actual='sendDocument','document',f
    else:method,field,actual='sendVideo','video',T._caber(f)
    args={'chat_id':chat,'caption':'E396E · '+os.environ.get('MAP_CASE','mapa')+' · VERTICAL · prova privada; sem publicação'}
    if method=='sendVideo':args['supports_streaming']='true'
    r=T._api(method,args,(field,actual))
    if not isinstance(r,dict) or not r.get('message_id'):raise ValueError('E396E-DELIVERY')
    (ROOT/'delivery.json').write_text(json.dumps({'publish':False,'complete':True,'items':[{'file':f.name,'mode':method,'message_id':r['message_id'],'original_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'sent_sha256':hashlib.sha256(actual.read_bytes()).hexdigest()}]},indent=2))
if __name__=='__main__':main()
