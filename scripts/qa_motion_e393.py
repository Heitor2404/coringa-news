"""E393: source-authenticated causal timeline; no new voice, source or simulation."""
import json
from pathlib import Path
from scripts import qa_storyboard_e392 as S
from scripts import qa_motion_e391 as P
ROOT=Path('stage_documental/e393')
def main():
    S.main()
    p=json.loads((P.ROOT/'variant.json').read_text())
    b=json.loads((S.ROOT/'board.json').read_text())
    events=b['graph']['eventos']
    assert [e['acao'] for e in events]==['loss','collapse','result']
    assert all(abs(e['tempo_s']-s['at'])<1e-6 for e,s in zip(events,p['sequence']['states'][1:]))
    durations=[1.75,2.10,.80]
    assert all(e['tempo_s']+d < (events[i+1]['tempo_s'] if i+1<len(events) else p['duracao']) for i,(e,d) in enumerate(zip(events,durations)))
    ROOT.mkdir(parents=True,exist_ok=True)
    (ROOT/'variant.json').write_text(json.dumps(dict(p,boards=b['boards'],events=events,transitions=durations),ensure_ascii=False))
    attribution=json.loads((S.ROOT/'attribution.json').read_text())
    attribution.update(graph=b['graph'],transition_seconds=durations,physical_simulation=False,camera_policy='F2 plano geral travado',scope='isolated causal illustration; real footage remains canonical E390')
    (ROOT/'motion-attribution.json').write_text(json.dumps(attribution,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
