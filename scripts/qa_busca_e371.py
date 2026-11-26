"""Live director search probe, metadata only, no AI or rendering."""
import json
from pathlib import Path
from src.v4.acervo_v4 import pesquisar_cobertura
def main():
    cases=[
      ('geologia','movimento','Kilauea lava fountaining','volcanic eruption lava'),
      ('oceanos','movimento','deep sea octopus','underwater octopus'),
      ('biologia','estatica','hummingbird hovering','hummingbird bird'),
      ('engenharia','estatica','antenna measurement robot','antenna calibration laboratory')]
    rows=[]
    for cid,ev,q,alt in cases:
        need=dict(id=cid,necessidade='registro',evidencia_visual=ev,preferencia_midia='foto_preferencial' if ev=='estatica' else 'video_preferencial',sujeito=q,
                  pesquisa=dict(consultas_en=[q,alt]))
        try:
            r=pesquisar_cobertura(need,progressivo=True,max_buscas=2,max_candidatos=8)
            rows.append(dict(case=cid,query=q,state=r['estado'],searches=r['buscas'],
                candidates=[dict(provider=c['fonte'],title=c['titulo'],page=c['pagina'],w=c['largura_declarada'],h=c['altura_declarada']) for c in r['candidatos']]))
        except Exception as exc:rows.append(dict(case=cid,query=q,state='ERROR',error=type(exc).__name__))
    out=Path('stage_documental/e371');out.mkdir(parents=True,exist_ok=True)
    proof=dict(publish=False,semantic_approval=False,metadata_only=True,new_ai=0,max_logical_queries=8,rows=rows)
    (out/'proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2))
    print('E371_SEARCH',[(r['case'],r['state'],len(r.get('candidates',[])),[s['fonte'] for s in r.get('searches',[])]) for r in rows])
if __name__=='__main__':main()
