import pytest
from PIL import Image, ImageDraw
from src.v4.formatos import amostragem_documental as A,direcao_eventos as D,revisao_documental as R

def midia(duration=60):
    return {'expected_sha256':'a'*64,'duration_s':duration,'local_source':'fixture','width':960}
def need():
    return {'id':'n','fatos':['f'],'mostrar':'Mudança do referente visível','evidencia_visual':'movimento'}
def frame(path,t,width):
    im=Image.new('RGB',(width,width//2),'#596d77')
    ImageDraw.Draw(im).rectangle((int(t*2)%max(1,width-40),20,int(t*2)%max(1,width-40)+30,60),fill='white')
    return im
def response(positive):
    return {'veredito':'pertinente' if positive else 'insuficiente',
            'natureza_visual':'registro_compativel',
            'inspecao':'Observação da amostra, sem inferir continuidade entre quadros.',
            'mudanca_observada':positive,'indices_mudanca':[0,2] if positive else [],
            'descricao_mudanca':'Alteração visível do referente entre dois quadros distintos.' if positive else '',
            'pontos':[{'indice':i,'observacao':'Observação específica do quadro '+str(i),'elementos':[]} for i in range(3)]}

def test_full_duration_local_sampling_and_single_batched_request():
    m=midia();n=need()
    e,w=A.preparar_lote(m,n,frame)
    assert len(e['janelas'])<=12 and len(w)==3
    assert e['janelas'][0]['inicio_s']==0 and e['janelas'][-1]['inicio_s']>55
    assert w[0][0]['inicio_s']<20 and w[-1][0]['inicio_s']>=40
    calls=[]
    def ask(prompt,images):
        calls.append(len(images))
        assert 'Nao combine quadros' in prompt
        return {'janelas':[{'janela':i,'resposta':response(i==2)} for i in (2,0,1)]}
    batch=D.revisar_janelas_lote(w,ask,evidencia_visual='movimento')
    assert calls==[9] and batch['chamadas_logicas']==1
    for i,((p,_),row) in enumerate(zip(w,batch['janelas'])):
        q={**row['revisao'],'sha256_origem':m['expected_sha256'],'necessidade_id':'n'}
        dec=R.decidir(n,{'aquisicao':{'sha256':m['expected_sha256']}},q,tipo='video')
        assert (dec['estado']=='PERTINENTE_PRIVADO')==(i==2)
        assert q['revisao_id']==p['revisao_id'] and not dec['prova_de_acao_continua']
        assert not dec['publicar']

def test_short_clip_and_malformed_group():
    m=midia(3);e,w=A.preparar_lote(m,need(),frame)
    assert len(w)==1 and w[0][0]['duracao_s']<3
    with pytest.raises(ValueError,match='D-LOTE-VINCULO'):
        D.revisar_janelas_lote(w,lambda p,ims:{'janelas':[{'janela':9,'resposta':response(True)}]},evidencia_visual='movimento')

def test_failed_decode_not_a_semantic_rejection():
    def fail(*args,**kwargs):raise RuntimeError('decode')
    e,w=A.preparar_lote(midia(),need(),fail)
    assert not w and all('falha' in x for x in e['janelas'])
    assert e['cobertura_semantica_integral'] is False
