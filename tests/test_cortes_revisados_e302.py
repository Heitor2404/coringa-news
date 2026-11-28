import pytest
from scripts import qa_documentario_geografia_e219 as E

def test_binding_rejects_wrong_fact_hash_or_overlap():
    cut=dict(chapter='A',speech='FRAGMENTOS',source='s',label='fonte',sha256='h',
             window_start=7,window_duration=3.8,observed='sample',review_ref='sheet')
    media={'s':dict(label='fonte',expected_sha256='h',duration_s=30)}
    words=[dict(w='FRAGMENTOS',s=0,e=2)]
    assert E.corte_revisado(cut,media,words,'A',0,2,{})==(media['s'],7)
    with pytest.raises(ValueError,match='FALA'):
        E.corte_revisado(cut,media,[dict(w='EVACUACAO',s=0,e=2)],'A',0,2,{})
    with pytest.raises(ValueError,match='VINCULO'):
        E.corte_revisado({**cut,'sha256':'other'},media,words,'A',0,2,{})
    with pytest.raises(ValueError,match='REPETICAO'):
        E.corte_revisado(cut,media,words,'A',0,2,{'h':[(8,10)]})
    with pytest.raises(ValueError,match='JANELA'):
        E.corte_revisado(cut,media,words,'A',0,4,{})

def test_explicit_full_source_binding_preserves_original_through_preflight():
    h='a'*64
    m={'expected_sha256':h,'width':1920,'height':1080}
    shot={'id':'s1','type':'video','asset':'s','video_zoom':1,'video_context_layout':'recorte_relacional_seguro','documentary_viewport':'4:5'}
    framing={'modo':'fonte_integral','sha256_origem':h,
             'inspecao':'A inscrição visível e o contexto espacial devem sobreviver ao recorte.',
             'motivo':'Preservar atribuição e contexto integral.'}
    binding={'shot':'s1','source':'s','sha256':h,'framing':framing}
    out=E.proteger_corte_revisado(shot,binding,m)
    assert out['video_context_layout']=='cena_integral' and out['video_framing']==framing
    assert 'documentary_viewport' not in out and 'video_framing' not in shot
    assert E.proteger_corte_revisado(shot,None,m)==shot
    with pytest.raises(ValueError):
        E.proteger_corte_revisado(shot,{**binding,'framing':{**framing,'sha256_origem':'b'*64}},m)
    with pytest.raises(ValueError):
        E.proteger_corte_revisado(shot,{**binding,'shot':'s2'},m)
    with pytest.raises(ValueError):
        E.proteger_corte_revisado({**shot,'video_zoom':1.2},binding,m)

def test_reviewed_windows_reserved_before_heuristic_selection():
    cuts={'a':{'sha256':'h','window_start':10,'window_duration':3.8},
          'b':{'sha256':'h','window_start':20,'window_duration':3.8}}
    assert E.reservar_cortes_revisados(cuts)=={'h':[(10,13.8),(20,23.8)]}
    with pytest.raises(ValueError,match='RESERVA'):
        E.reservar_cortes_revisados({**cuts,'c':{'sha256':'h','window_start':12,'window_duration':3.8}})

def test_restored_review_samples_must_be_inside_actual_cut_and_match_pixels(monkeypatch):
    from PIL import Image
    import hashlib
    im=Image.new('RGB',(320,180),'red')
    h=hashlib.sha256(im.tobytes()).hexdigest()
    monkeypatch.setattr(E,'frame',lambda *a,**k:im)
    cut=dict(chapter='A',speech='FRAGMENTOS',source='s',label='fonte',sha256='h',
             window_start=7,window_duration=3.8,observed='sample',review_ref='sheet',acervo_existente=True,
             samples=[{'time':t,'size':[320,180],'pixels_sha256':h} for t in (7.5,8,8.5)])
    media={'s':dict(label='fonte',expected_sha256='h',duration_s=30,local_source='s.mp4')}
    words=[dict(w='FRAGMENTOS',s=0,e=2)]
    assert E.corte_revisado(cut,media,words,'A',0,2,{})==(media['s'],7)
    with pytest.raises(ValueError,match='TEMPO-AMOSTRA'):
        E.corte_revisado(cut,media,words,'A',0,1.4,{})
    with pytest.raises(ValueError,match='PIXELS'):
        E.corte_revisado({**cut,'samples':[dict(s,pixels_sha256='x') for s in cut['samples']]},media,words,'A',0,2,{})
