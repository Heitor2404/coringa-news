"""E392: source-bound storyboard from existing F1/F2 graph and camera.
No independent mechanism simulator; no published media or video render."""
import json
from pathlib import Path
from scripts import qa_motion_e391 as previous
from src.v4.formatos import grafo_causal as G,camera_causal_svg as C
ROOT=Path('stage_documental/e392')
FAMILY='caldera_collapse_qualitative'
ACTIONS=('loss','collapse','result')
def compile_board(p):
    seq=p['sequence'];duration=p['duracao']
    if p.get('private_review_only') is not True or seq.get('publish') is not False or seq['scale']!='illustrative_not_to_scale':raise ValueError('E392-PRIVATE')
    if [s['id'] for s in seq['states']]!=['initial','drain','collapse','after']:raise ValueError('E392-SOURCE-STATES')
    if seq['sourceSha']!='f593c35a9b0124a64329fb7cc7d4c992e9d2f11738eeb350304a9987b870d8d2':raise ValueError('E392-SOURCE')
    times=tuple(s['at'] for s in seq['states'][1:])
    graph=G.montar(FAMILY,ACTIONS,momentos=times)
    G.verificar_serializado(graph,FAMILY,ACTIONS,times)
    state=dict(G.GRAFOS[FAMILY]['estado_inicial']);boards=[]
    for i,t in enumerate((1.8,4.0,7.5,12.2)):
        if i:state.update(graph['eventos'][i-1]['depois'])
        j=max(0,i-1);action=ACTIONS[j];begin=times[j] if i else 0
        cam=C.calcular(FAMILY,action,t,begin,duration)
        if not C.verificar_pose(FAMILY,cam):raise ValueError('E392-CAMERA')
        captions=next((x['words'] for x in p['captions'] if x['start']<=t<x['end']),[])
        boards.append({'id':seq['states'][i]['id'],'index':i,'time':t,'state':dict(state),'camera':{'scale':cam.scale,'tx':cam.tx,'ty':cam.ty},'focus':list(cam.focus_roles),'caption':captions})
    return {'schema':'coringa.storyboard.e392.private.v1','publish':False,'sourceSha':seq['sourceSha'],'review':seq['review'],'scale':seq['scale'],'graph':graph,'boards':boards,'visual_approval':'PENDING','physical_simulation':False}
def main():
    previous.main()
    p=json.loads((previous.ROOT/'variant.json').read_text())
    board=compile_board(p)
    ROOT.mkdir(parents=True,exist_ok=True)
    (ROOT/'board.json').write_text(json.dumps(board,ensure_ascii=False,indent=2))
    (ROOT/'attribution.json').write_text((previous.ROOT/'motion-attribution.json').read_text())
if __name__=='__main__':main()
