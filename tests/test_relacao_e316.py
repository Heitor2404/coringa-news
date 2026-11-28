from src.v4.formatos import reserva_janelas_e313 as R

def test_conflicts_filtered_before_vision_without_semantic_rejection():
    n={'id':'b','fatos':['result']}
    r={'a':{'id':'a','sha256':'h','pagina':'p','inicio':7.,'fim':10.8,'fatos':['action']}}
    def w(t,d=3.8):return {'inicio_s':t,'duracao_s':d}
    assert not R.janela_elegivel(n,'h','p',w(8),r)
    assert R.janela_elegivel(n,'h','p',w(10.8),r)
    assert R.janela_elegivel(n,'h','p',w(40),r)
    assert R.janela_elegivel(n,'other','other',w(8),r)
    assert not R.janela_elegivel(n,'other','p',w(40),r)
    assert not R.janela_elegivel({'id':'b','fatos':['action']},'h','p',w(40),r)
    assert R.janela_elegivel(n,'h','p',w(8),{}) # rollback reopens interval

def test_sampling_does_not_send_conflicting_windows(monkeypatch):
    from PIL import Image
    from src.v4.formatos import amostragem_documental as A
    from src.v4.formatos import direcao_eventos as D
    ex={'duracao_origem_s':60,'janelas':[{'inicio_s':t,'duracao_s':3.8,'diagnostico':{}} for t in (7.,40.)]}
    seen=[]
    monkeypatch.setattr(A,'selecionar',lambda x,**kw:x['janelas'])
    monkeypatch.setattr(D,'diagnosticar_janela',lambda ims:{})
    def extract(p,t,width):
        seen.append(t);return Image.new('RGB',(8,8))
    m={'local_source':'unused','width':768,'expected_sha256':'a'*64,'duration_s':60}
    n={'id':'b','fatos':['f'],'mostrar':'result','evidencia_visual':'estatica'}
    r={'a':{'id':'a','sha256':'a'*64,'pagina':'p','inicio':7.,'fim':10.8,'fatos':['other']}}
    _,windows=A.preparar_lote(m,n,extract,exploracao=ex,janela_elegivel=lambda w:R.janela_elegivel(n,'a'*64,'p',w,r))
    assert len(windows)==1 and windows[0][0]['inicio_s']==40
    assert len(seen)==3 and all(t>=40 for t in seen)
    assert len(ex['janelas'])==2
