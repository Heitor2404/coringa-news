"""Private integration proof, not a new episode or a new animation."""
import json
from pathlib import Path
from src.v4.formatos import filme_editorial as F, ponte_mapa_atlas as A, ponte_animacao_editorial as B

def read(p): return json.loads(Path(p).read_text(encoding='utf8'))
def write(p,x): Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')

def main():
    out=Path('qa_e213');out.mkdir(exist_ok=True)
    public=Path('motor4/remotion/public')
    p=read('docs/v4/formatos/filme_panama_12s_prova.json')
    p['publicar']=False
    # Keep all documentary sources/windows; remove explicitly rejected animation.
    p['shots']=[s for s in p['shots'] if s['type']!='mechanism']
    for s in p['shots'][1:]:
        s['start']=round(s['start']+.5,4);s['end']=round(s['end']+.5,4)
    src=Path('stage_atlas/e213/mapa.mp4')
    A.confirmar(read(src.parent/'preparo_atlas.json'),src,src.parent)
    p['shots'].insert(1,{'id':'atlas','type':'atlas_map','start':3.,'end':7.4,
        'headline':'Canal do Panamá','subject':'Localização do canal','lead':'GEOGRAFIA','evidence':'explainer',
        'cues':[{'at':.3,'label':'CANAL DO PANAMÁ'}]})
    p['duracao']=12.5
    p=A.inserir_no_filme(p,'atlas',src,src.parent/'comprovante_atlas.json')
    result=F.preparar(p,out/'documental',public)
    props=read(result['props']);props.pop('safe_area_profile',None)
    lock=B.preparar('render_eclusa_hidraulica_2d.py',Path('stage_lock/ECLUSA_HIDRAULICA_MODERNA_PRIVADA.mp4'),
        public,cid='explicacao',acao='Entrada, enchimento e saída de um navio',lacuna='As filmagens selecionadas não mostram o conduto interno nem todo o ciclo',
        motivo_lacuna='IMPOSSIVEL_FILMAR',midia_adequada=False,start=7.4)
    mixed=B.inserir(props,lock,2,public)
    write(out/'panama.json',mixed)
    comp=B.preparar('render_compressor_conjunto_2d.py',Path('stage_comp/COMPRESSOR_F10_CORREIA_PARAMETRICA.mp4'),
        public,cid='compressor',acao='Movimento da correia e compressão',lacuna='Interior e transmissão em corte não demonstrados na mesma tomada',
        motivo_lacuna='IMPOSSIVEL_FILMAR',midia_adequada=False)
    write(out/'compressor.json',B.inserir({'shots':[],'duracao':0.,'preview':True},comp,0,public))
    print('E213',mixed['duracao'],[s['type'] for s in mixed['shots']],comp['end'])

if __name__=='__main__': main()
