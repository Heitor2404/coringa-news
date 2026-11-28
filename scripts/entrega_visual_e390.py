"""Only a completed current-model full render may be delivered as current."""
import json
from pathlib import Path
from src.v3 import previa_telegram as T
from src.v3.pacote_biblioteca import sha
ROOT=Path('stage_documental/e390')
def main():
    p=json.loads((ROOT/'consolidation.json').read_text());q=json.loads((ROOT/'review.json').read_text())
    f=ROOT/'CORINGA-EXPLICA-KILAUEA-ATUAL-E390.mp4'
    if p.get('status')!='RENDERED_CURRENT_PRIVATE' or p.get('fresh_full_render') is not True or p.get('audio_packets_identical') is not True or p.get('rendered_shots')!=24 or q.get('errors') or sha(f)!=p['sha256']:raise ValueError('E390-NOT-CONSOLIDATED')
    chat,_=T.chat_autorizado();items=[];receipt=ROOT/'delivery.json'
    def save(complete=False):receipt.write_text(json.dumps({'publish':False,'complete':complete,'items':items},indent=2))
    # Exact explicit inventory; never count a compression derivative.
    sent=T._caber(f)
    r=T._api('sendVideo',{'chat_id':chat,'caption':'E390 · DOCUMENTÁRIO CONSOLIDADO · 83s · Taiwan atual + 3 gráficos + ATLAS · revisão privada, não publicar · 2D causal ainda não homologado','supports_streaming':'true'},('video',sent))
    if not r.get('message_id'):raise ValueError('E390-RECEIPT')
    items.append({'file':f.name,'sha256':sha(f),'sent_file':sent.name,'sent_sha256':sha(sent),'message_id':r['message_id']});save()
    for f in sorted(ROOT.glob('current-contact-*.jpg')):
        r=T._api('sendDocument',{'chat_id':chat,'caption':'E390 · '+f.stem+' · controle visual da versão consolidada'},('document',f))
        if not r.get('message_id'):raise ValueError('E390-SHEET')
        items.append({'file':f.name,'sha256':sha(f),'message_id':r['message_id']});save()
    save(len(items)==7)
    if len(items)!=7:raise ValueError('E390-INCOMPLETE')
if __name__=='__main__':main()
