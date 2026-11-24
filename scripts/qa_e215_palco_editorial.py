"""Two existing geometry families, one editorial stage; no episode publishing."""
import json
from pathlib import Path
from src.v4.formatos import render_compressor_conjunto_2d as C, compositor_mecanismo_parametrico_2d as V, palco_editorial_render as E

def main():
    out=Path('qa_e215')
    m=json.loads(C.MANIFESTO_PADRAO.read_text())
    # Keep F10 transmission and existing P–V states.
    c=E.renderizar((C.frame_svg(i/192,m,transmissao_parametrica=True) for i in range(192)),
        'machine-assembly',out/'compressor.mp4',fps=24,titulo='COMPRESSÃO DO AR',fonte='Modelo didático P–V')
    obj=V.carregar(Path('src/v4/formatos/cenas_parametricas/vasos_comunicantes_assimetricos.json'))
    v=E.renderizar((V.frame_svg(obj,i/obj['fps']) for i in range(round(obj['duration_s']*obj['fps']))),
        'machine-stage',out/'vasos.mp4',fps=obj['fps'],titulo='EQUILÍBRIO DA ÁGUA',fonte='OpenStax · princípio físico')
    print('E215',c['fit'],v['fit'])
if __name__=='__main__':main()
