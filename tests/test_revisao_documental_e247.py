from PIL import Image
from src.v4.formatos import revisao_documental as R
from src.v4.formatos import diretor_visual_e202 as D

SHA='a'*64
def need(ev='estatica'):
    return {'id':'n','mostrar':'referente ou transformação específica','evidencia_visual':ev,'fatos':['f']}
def candidate(i=1,kind='foto',**kw):
    return {'source_id':i,'fonte':'commons','tipo':kind,'url':f'https://example.org/{i}',
            'direitos':'DECLARACAO_INDIVIDUAL_PENDENTE_AUDITORIA','aquisicao':{'sha256':SHA},**kw}
def review(**kwargs):
    return {'sha256_origem':SHA,'necessidade_id':'n','revisao_id':'r',
            'resposta':{'natureza_visual':'registro_compativel','veredito':'pertinente',**kwargs}}

def test_declared_simulation_beats_visual_plausibility():
    c=candidate(source='Created with Celestia')
    assert R.decidir(need(),c,review(),tipo='foto')['motivo']=='REPRESENTACAO_DECLARADA'
    assert R.natureza_declarada({'descricao_integral':'A computer-generated animation'})=='REPRESENTACAO_DECLARADA'
    assert R.natureza_declarada({'descricao':'Mosaic of photographs taken by spacecraft'})=='PENDENTE_INSPECAO'

def test_motion_requires_observed_change_and_not_photo():
    n=need('movimento');c=candidate(kind='video')
    assert R.decidir(n,c,review(),tipo='video')['motivo']=='MUDANCA_NAO_OBSERVADA'
    q=review(mudanca_observada=True,indices_mudanca=[0,2],descricao_mudanca='A textura mudou entre os dois quadros.')
    assert R.decidir(n,c,q,tipo='foto')['motivo']=='FOTO_NAO_PROVA_MOVIMENTO'
    d=R.decidir(n,c,q,tipo='video')
    assert d['estado']=='PERTINENTE_PRIVADO' and not d['prova_de_acao_continua'] and not d['direitos_aprovados']
    q['resposta']['indices_mudanca']=[1,1]
    assert R.decidir(n,c,q,tipo='video')['motivo']=='MUDANCA_NAO_OBSERVADA'

def test_wrong_sha_or_need_cannot_satisfy():
    q=review();q['sha256_origem']='b'*64
    assert R.decidir(need(),candidate(),q,tipo='foto')['motivo']=='REVISAO_SEM_VINCULO'

def test_queue_continues_past_downloads_and_incompatible_media():
    a,b,c=candidate(1,source='Created with Celestia'),candidate(2),candidate(3)
    calls=[]
    def inspect(x,n):
        calls.append(x['source_id'])
        return R.decidir(n,x,review(veredito='insuficiente' if x['source_id']==2 else 'pertinente'),tipo='foto')
    r=D.revisar_cobertura_documental(need(),{'id':'n','candidatos':[a,b,c]},inspect)
    assert calls==[2,3] and r['estado']=='CANDIDATO_PRIVADO_REVISADO'
    assert not r['pronto_para_render'] and not r['publicar']
    assert R.fila_cobertura(need(),[b],lambda *a:{'estado':'FALHA_AQUISICAO'})['estado']=='LACUNA_PENDENTE'

def test_photo_review_uses_pixels_and_binding():
    im=Image.new('RGB',(10,10),'white')
    q=R.revisar_foto({'expected_sha256':SHA},im,need(),lambda p,imgs:{'veredito':'pertinente','natureza_visual':'registro_compativel','inspecao':'Descrição concreta da estrutura visível nesta imagem.'})
    assert q['necessidade_id']=='n' and q['sha256_origem']==SHA and len(q['pixels_sha256'])==64
    assert R.decidir(need(),candidate(),q,tipo='foto')['estado']=='PERTINENTE_PRIVADO'

def test_explicit_thousand_alias_not_ambiguous_scale():
    from src.v4.formatos import revisao_documental as R
    e={'classe':'direta','detalhe':'specific visible detail of sufficient length','escala':'1000','bbox':{'esquerda':10,'topo':20,'direita':900,'base':950}}
    assert R.normalizar_evidencia_direta(e)['bbox']==[.01,.02,.9,.95]
    for scale in ('600_800','500_500'):
        assert R.normalizar_evidencia_direta({**e,'escala':scale}) is None
