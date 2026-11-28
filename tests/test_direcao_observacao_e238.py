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


def test_vision_opt_in_and_bound_samples():
    p,r=fixture()
    frames=[Image.new('RGB',(8,8),color=(i*50,10,20)) for i in range(3)]
    calls=[]
    def fake(prompt, jpgs):
        calls.append((prompt,jpgs))
        return {**r,'pontos':[{**x,'indice':i,'elementos':[{'nome':'referente','bbox_xy':{'esquerda':.2,'topo':.6,'direita':.4,'base':.8}}]} for i,x in enumerate(r['pontos'])]}
    with pytest.raises(RuntimeError,match='D-REV-VISAO-DESLIGADA'):
        D.revisar_janela_visao(p,frames,fake)
    assert not calls
    q=D.revisar_janela_visao(p,frames,fake,permitir_chamada=True)
    assert len(calls)==1 and len(calls[0][1])==3
    assert q['chamadas_logicas']==1 and not q['aprovacao_editorial'] and not q['publicar']
    assert q['video_framing']['pontos'][0]['elementos'][0]['bbox']==[.2,.6,.4,.8]
    assert q['diagnostico_bbox']=='FORMATO_VALIDO_NAO_VERIFICADO'
    frames[0]=Image.new('RGB',(8,8),'white')
    with pytest.raises(ValueError,match='D-REV-PIXELS'):
        D.revisar_janela_visao(p,frames,fake,permitir_chamada=True)
    assert len(calls)==1


def test_selection_requires_matching_fact_and_semantic_observation(monkeypatch):
    p,r=fixture()
    m={'id':'original','expected_sha256':'a'*64,'duration_s':20,'width':1920,'height':1080}
    p['revisao_assistida']={'resposta_observada':r}
    calls=[]
    def framing(cena,midia,obs):
        calls.append(cena)
        return {'layout':'cena_integral','framing_positions':[]}
    monkeypatch.setattr(D,'enquadrar_observacoes',framing)
    q=D.selecionar_revisados([{'pacote':p,'midia':m}],fato_id='f1')
    assert len(q)==1 and not q[0]['selecao']['prova_de_acao']
    assert calls==[{'type':'video','start':0.,'end':3.8,'source_in_seconds':2}]
    assert q[0]['selecao']['enquadramento']['layout']=='cena_integral'
    with pytest.raises(ValueError,match='D-SEL-VINCULO'):
        D.selecionar_revisados([{'pacote':p,'midia':m}],fato_id='another')
    r['veredito']='contexto'
    assert D.selecionar_revisados([{'pacote':p,'midia':m}],fato_id='f1')==[]
    p.pop('revisao_assistida')
    assert D.selecionar_revisados([{'pacote':p,'midia':m}],fato_id='f1')==[]


def test_vision_ambiguous_bbox_preserves_semantics_but_never_crop():
    p,r=fixture()
    frames=[Image.new('RGB',(8,8),color=(i*50,10,20)) for i in range(3)]
    def fake(prompt,jpgs):
        return {**r,'pontos':[{**x,'indice':i,'elementos':[{'nome':'referente','bbox':[[.709,.443,.857,.738]]}]} for i,x in enumerate(r['pontos'])]}
    q=D.revisar_janela_visao(p,frames,fake,permitir_chamada=True)
    assert q['veredito']=='pertinente'
    assert q['diagnostico_bbox']=='FORMATO_RECUSADO'
    assert q['video_framing'] is None
    assert q['resposta_bruta']['pontos'][0]['elementos'][0]['bbox']==[[.709,.443,.857,.738]]


def test_detailed_review_uses_actual_start_and_native_framing():
    m={'id':'synthetic','expected_sha256':'a'*64,'duration_s':20,'width':1920,'height':1080}
    frames=[Image.new('RGB',(960,540),color=(i*50,10,20)) for i in range(3)]
    p=D.pacote_observacao(m,2,3.8,frames,fato_id='f1',necessidade='referente visível',fracoes=(0,.5,.9))
    assert p['amostras'][0]['fonte_s']==2 and p['amostras'][0]['at']==0
    def reviewer(prompt,jpgs):
        return {'veredito':'pertinente','inspecao':'Teste sintético de referência localizada em todos os quadros.',
                'pontos':[{'indice':i,'observacao':'Referente sintético de teste','elementos':[{'nome':'referente','bbox_xy':{'esquerda':.45,'topo':.6,'direita':.55,'base':.8}}]} for i in range(3)]}
    p['revisao_assistida']=D.revisar_janela_visao(p,frames,reviewer,permitir_chamada=True)
    q=D.candidato_revisado(p,m,fato_id='f1')
    assert q['enquadramento']['layout']=='recorte_relacional_seguro'
    assert q['enquadramento']['framing_positions'][0]['at']==0
    assert not q['prova_de_acao'] and not q['publicar']
    with pytest.raises(ValueError,match='D-REV-FRACOES'):
        D.pacote_observacao(m,2,3.8,frames,fato_id='f1',necessidade='teste',fracoes=(0,.9,1))
