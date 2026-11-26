from PIL import Image,ImageDraw
from src.v4.formatos.direcao_eventos import diagnosticar_janela
from src.v4.formatos.amostragem_documental import selecionar

def frame(banner=True):
    im=Image.new('RGB',(240,136),'#234035')
    draw=ImageDraw.Draw(im)
    for i in range(0,240,12):
        draw.rectangle((i,0,i+6,135),fill='#a34f3e')
    if banner:
        draw.rectangle((53,58,187,74),fill='#0089c9')
        draw.text((85,60),'TITLE',fill='white')
    return im

def test_persistent_banner_is_hint_not_veto():
    yes=diagnosticar_janela([frame(),frame(),frame()])
    no=diagnosticar_janela([frame(False),frame(False),frame(False)])
    assert yes['faixa_grafica_persistente_suspeita']
    assert not no['faixa_grafica_persistente_suspeita']
    assert not yes['recorte_automatico_autorizado']
    common=dict(duracao_s=3.8,contraste_min=30,pares_alterados=2,mudanca_px=20)
    rows=[dict(common,inicio_s=0,diagnostico=yes),dict(common,inicio_s=4,diagnostico=no)]
    report=dict(duracao_origem_s=9,janelas=rows)
    assert selecionar(report,limite=1,priorizar_movimento=True)==[rows[1]]
    assert len(selecionar(report,limite=2,priorizar_movimento=True))==2
def test_flat_sky_not_persistent_banner():
    im=Image.new('RGB',(240,136),'#0089c9')
    assert not diagnosticar_janela([im,im,im])['faixa_grafica_persistente_suspeita']

def test_transient_banner_counts_without_persistence():
    d=diagnosticar_janela([frame(),frame(False),frame(False)])
    assert d['quadros_faixa_grafica_suspeita']==1
    assert not d['faixa_grafica_persistente_suspeita']
    assert not d['recorte_automatico_autorizado']
