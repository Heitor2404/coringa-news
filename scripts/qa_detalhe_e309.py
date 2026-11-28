"""Actual fixture pixels inspected in chat; private assisted annotation only."""
import json,hashlib
from pathlib import Path
from src.v4.formatos.filme_editorial import detalhe_fotografico
def main():
    root=Path('stage_documental/e286')
    p=json.loads((root/'props.json').read_text())
    photo=next(s for s in p['shots'] if s['id']=='foto_vertical_salto_angel')
    src=Path('tests/midia/foto_vertical_salto_angel.jpg')
    data=src.read_bytes()
    # Git blob identity of the image actually viewed in the assistant.
    assert hashlib.sha1(('blob '+str(len(data))+'\0').encode()+data).hexdigest()=='a0d3e9edf55d675d7e8d69aecafb43cd2c467878'
    h=hashlib.sha256(data).hexdigest()
    def roi(box):
        return detalhe_fotografico({'type':'photo','documentary_detail_intent':True,'photo_roi_candidate':
            {'sha256':h,'revisao_id':'E309-assisted-fixture','bbox':box,'escala_origem':'xy_0_1'}},{'expected_sha256':h},h)
    # Mid-column water visible in inspected real image, not a measure of height/flow.
    detail=roi([.49,.37,.56,.52])
    assert detail
    p['shots']=[{**photo,'id':name,'start':i*3,'end':(i+1)*3,**extra}
                for i,(name,extra) in enumerate([('baseline',{}),('observed',{'documentary_detail_roi':detail}),
                ('collision',{'documentary_detail_roi':roi([.49,.16,.56,.25])})])]
    p['duracao']=9
    p.pop('scene_narration_asset',None);p.pop('documentary_caption_origin',None)
    p['documentary_captions']=[]
    p['documentary_text_probe']=True
    (root/'detail-props.json').write_text(json.dumps(p))
    (root/'detail-source.json').write_text(json.dumps({'sha256':h,'git_blob':'a0d3e9edf55d675d7e8d69aecafb43cd2c467878',
          'observation':'Coluna de agua no trecho intermediario da queda visivel na foto derivada; anotacao assistida, nao revisao autonomamente produzida.',
          'bbox':detail['bbox'],'publish':False,'visual_approval':'PENDING'}))
if __name__=='__main__':main()
