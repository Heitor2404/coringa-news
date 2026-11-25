import pytest
from PIL import Image
from src.v4.formatos import direcao_eventos as D

def fixture():
    frames=[Image.new('RGB',(8,8),color=(i*50,10,20)) for i in range(3)]
    m={'expected_sha256':'a'*64,'duration_s':20}
    p=D.pacote_observacao(m,2,3.8,frames,fato_id='f1',necessidade='movimento observado')
    r={'revisao_id':p['revisao_id'],'veredito':'pertinente',
        'inspecao':'Exemplo sintético de contrato, não uma ação real observada.',
        'pontos':[{'pixels_sha256':x['pixels_sha256'],'observacao':'Amostra sintética de teste',
                    'elementos':[{'nome':'referente','bbox':[.2,.2,.4,.4]}]} for x in p['amostras']]}
    return p,r

def test_review_remains_private():
    p,r=fixture()
    q=D.aceitar_observacao(p,r)
    assert not q['publicar'] and q['revisao_humana']=='PENDENTE'
    assert q['video_framing']['sha256_origem']=='a'*64
    assert q['video_framing']['pontos'][0]['fonte_s']==pytest.approx(2.456)

@pytest.mark.parametrize('key,code',[('revisao_id','D-REV-ID'),('veredito','D-REV-VEREDITO'),('inspecao','D-REV-INSPECAO')])
def test_reject_invalid_response(key,code):
    p,r=fixture();r[key]='invalid'
    with pytest.raises(ValueError,match=code):D.aceitar_observacao(p,r)

def test_reject_wrong_sample():
    p,r=fixture();r['pontos'][0]['pixels_sha256']='x'
    with pytest.raises(ValueError,match='D-REV-PIXELS'):D.aceitar_observacao(p,r)

def test_context_never_infers_crop():
    p,r=fixture();r['veredito']='contexto'
    assert D.aceitar_observacao(p,r)['video_framing'] is None
