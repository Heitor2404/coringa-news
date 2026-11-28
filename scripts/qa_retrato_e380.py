"""Bounded private acquisition proof: same two E377 queries, no AI or approval."""
import json
from pathlib import Path
from src import midia
from src.v4.acervo_v4 import _candidato_documental
from src.v4.aquisicao_documental import Transporte
from src.v4.formatos.filme_editorial import MIN_VIDEO_COMPOSITION_PX
from scripts.qa_pesquisa_documental_e246 import sample,variants
from scripts.qa_documentario_geografia_e219 import frame

def eligible(c):
    if c.get('direitos')!='DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA' or c.get('natureza_preliminar')=='REPRESENTACAO_DECLARADA':return False
    return any(type(v.get('width')) is int and type(v.get('height')) is int and v['height']>v['width']>=MIN_VIDEO_COMPOSITION_PX for v in variants(c))

def main():
    out=Path('stage_documental/e380');out.mkdir(parents=True,exist_ok=True)
    originals=out/'originais';originals.mkdir(exist_ok=True)
    t=Transporte(max_http=4,max_bytes=85_000_000,max_wait=20)
    rows=[]
    for i,q in enumerate(('waterfall','train arriving')):
        row=dict(query=q,status='NO_ELIGIBLE_PORTRAIT')
        try:
            raw=midia.candidatos_arquivo(q,estrito=True,preferir_vertical=True,pesquisa_retrato=True)
            cs=[c for x in raw if (c:=_candidato_documental(x,'commons_video','video'))]
            row['leads']=[dict(title=c['titulo'],page=c['pagina'],w=c['largura_declarada'],h=c['altura_declarada'],eligible=eligible(c)) for c in cs]
            c=next((c for c in cs if eligible(c)),None)
            if c:
                row.update(status='ACQUISITION_PENDING',page=c['pagina'],credit=c['credito'],license=c['licenca'],license_url=c.get('licenca_url'),rights=c['direitos'])
                meta,visual,path=sample(c,originals,t,progressivo=True,max_variantes=1,min_video_px=MIN_VIDEO_COMPOSITION_PX)
                if meta['height']<=meta['width']:raise ValueError('E380-NOT-NATIVE-PORTRAIT')
                row.update(status='PORTRAIT_BYTES_VERIFIED_SEMANTICS_PENDING',meta=meta,frames=[])
                for j,f in enumerate((.18,.5,.82)):
                    name=f'portrait-{i}-{j}.jpg';at=meta['duration_s']*f
                    frame(path,at,width=480).convert('RGB').save(out/name,quality=87)
                    row['frames'].append(dict(file=name,t=at))
        except Exception as e:row.update(status='ERROR',reason=str(e)[:180])
        rows.append(row)
    (out/'proof.json').write_text(json.dumps(dict(publish=False,semantic_approval=False,new_ai=0,logical_searches=2,transport=t.resumo(),rows=rows),ensure_ascii=False,indent=2))
    print('E380_PROOF',[(r['query'],r['status']) for r in rows])
if __name__=='__main__':main()
