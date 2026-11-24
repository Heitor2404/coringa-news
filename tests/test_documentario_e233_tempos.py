"""E233 timing regressions. Synthetic timings, no TTS, no semantic claims."""
import pytest
from scripts import qa_documentario_geografia_e219 as E

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
