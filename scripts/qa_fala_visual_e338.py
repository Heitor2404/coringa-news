"""Authenticate archived plan and speech report; no media transfer or rendering."""
import base64,hashlib,json
from pathlib import Path
from scripts.recuperar_checkpoints_documentais import api
from src.v4.formatos.auditoria_fala_visual_e338 import organizar
REF='d6b3281bb490fabbb41b8284857f5945313b067e'
FILES={'plano.json':'ac3e9b3bd35818b15c1b87f14e88e9d7d052008a','obrigacoes-visuais.json':'48afda9011e3166067398c08eb3ceb22e0091590'}
def read(name):
    x=api('/contents/revisoes/e326-45870900796-1/'+name+'?ref='+REF)
    raw=base64.b64decode(x['content'])
    if x['sha']!=FILES[name] or len(raw)!=x['size'] or hashlib.sha1(('blob '+str(len(raw))).encode()+bytes(1)+raw).hexdigest()!=FILES[name]:
        raise ValueError('E338-BLOB')
    return json.loads(raw)
def main():
    if api('')['private'] is not True:raise ValueError('E338-COFRE')
    result=organizar(read('plano.json'),read('obrigacoes-visuais.json'))
    root=Path('stage_documental/e338');root.mkdir(parents=True,exist_ok=False)
    (root/'queue.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    if result['media_shots']!=23 or len(result['specialized_shots'])!=1:raise ValueError('E338-COBERTURA')
    print('E338',result['media_shots'],result['unreviewed_shots'],result['sample_reviewed_shots'],len(result['source_batches']))
if __name__=='__main__':main()
