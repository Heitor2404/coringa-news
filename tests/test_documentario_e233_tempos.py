"""E233 timing regressions. Synthetic timings, no TTS, no semantic claims."""
import pytest
from scripts import qa_documentario_geografia_e219 as E

def test_e299_measured_obligation_is_not_semantic_approval():
    shots=[dict(shot='a',chapter='A',start=0,end=2,source='x',source_sha256='s',source_in=7,source_out=9)]
    rows=E.obrigacoes_visuais(shots,[dict(w='primeiro',s=0,e=1),dict(w='segundo',s=1,e=2),dict(w='fora',s=2,e=3)])
    assert rows[0]['speech']=='primeiro segundo'
    assert rows[0]['direct_evidence_verified'] is False


def test_e298_coverage_gap_is_not_semantic_approval():
    spec={'chapters':[{'title':'A','videos':[['one','x'],['two','y']]},{'title':'Map','atlas':{}}]}
    report=E.lacunas_montagem(spec,{'one':{}},[{'chapter':'A','source':'one','revisit':False}])
    assert len(report)==1 and report[0]['unavailable']==['two']
    assert report[0]['status']=='FONTE_UNICA_REVISAR_COBERTURA'
    assert report[0]['semantic_approval'] is False


def test_e297_continuity_prefers_forward_source_to_unjustified_return():
    from src.v4.formatos.direcao_eventos import continuidade_fontes
    history=[('A',0,3),('B',7,10)]
    assert continuidade_fontes([('A',5,8),('B',12,15),('C',2,5)],history)[0][0]=='C'
    assert continuidade_fontes([('A',5,8),('B',12,15),('B',1,4)],history)[0]==('B',12,15)
    assert continuidade_fontes([('A',5,8)],history)==[('A',5,8)]


def test_e297_atlas_override_keeps_authenticated_voice_and_video_rows():
    spec=E.read('benchmarks/e219/kilauea_review_e232.json')
    override=E.read('benchmarks/e219/direcao_atlas_e297.json')
    revised=E.aplicar_direcao_atlas(spec,override)
    assert [c['speech'] for c in revised['chapters']]==[c['speech'] for c in spec['chapters']]
    assert [c.get('videos') for c in revised['chapters']]==[c.get('videos') for c in spec['chapters']]
    assert revised['chapters'][1]['atlas']['roi']==override['chapters'][0]['mapa']['atlas']['roi']
    assert revised['chapters'][1]['atlas']['multiscale']['delta']==1.6
    assert 'multiscale' not in spec['chapters'][1]['atlas']


def test_map_marker_preserves_real_events_for_every_supported_frame_length():
    gap=float(E.A.REGRAS['progressao_max_s'])
    for frames in range(42,241):
        d=frames/30
        events=sorted([0,.3,d/3,E.marker_time(d),d])
        assert all(b-a<=gap+1e-9 for a,b in zip(events,events[1:]))

@pytest.mark.parametrize('words',[[],[{'e':n/7} for n in range(1,300)]])
def test_measured_cut_lengths_keep_existing_gate(words):
    for frames in range(42,1200):
        cuts=E.cortes_medidos(90,90+frames,words)
        assert cuts[0]==90 and cuts[-1]==90+frames
        assert all(42<=b-a<=113 for a,b in zip(cuts,cuts[1:]))
        assert len(cuts)-1==(frames+112)//113
