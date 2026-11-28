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


def test_cache_only_sampling_reaches_a_previously_reviewed_nondefault_window():
    m=midia();n=need()
    e,normal=A.preparar_lote(m,n,frame)
    default={round(p['inicio_s'],4) for p,_ in normal}
    late=next(round(x['inicio_s'],4) for x in reversed(e['janelas']) if round(x['inicio_s'],4) not in default)
    _,selected=A.preparar_lote(m,n,frame,exploracao=e,priorizar_cache={late})
    assert late in {round(p['inicio_s'],4) for p,_ in selected}
    assert len(selected)<=3
    # The same bytes and time produce exactly the same observation ID.
    _,again=A.preparar_lote(m,n,frame,exploracao=e,priorizar_cache={late})
    assert [p['revisao_id'] for p,_ in selected]==[p['revisao_id'] for p,_ in again]
    _,excluded=A.preparar_lote(m,n,frame,exploracao=e,priorizar_cache={late},excluir={late})
    assert late not in {round(p['inicio_s'],4) for p,_ in excluded}


def test_legible_reviewed_window_is_preferred_without_rejecting_other_windows():
    m=midia();n=need();_,w=A.preparar_lote(m,n,frame)
    rows=[]
    for i,(p,frames) in enumerate(w):
        q=D.revisar_janela_visao(p,frames,lambda *_:response(True),permitir_chamada=True,evidencia_visual='movimento')
        p['revisao_assistida']=q
        p['diagnostico_tecnico']['quadros_grafismo_suspeito']=0
        box=[.1,.1,.12,.12] if i!=1 else [.1,.1,.9,.9]
        rows.append({'pacote':p,'midia':m,'decisao':{'estado':'PERTINENTE_PRIVADO','revisao_id':p['revisao_id'],'evidencia_direta_normalizada':{'bbox':box}}})
    assert D.selecionar_revisados(rows,fato_id='f')[0]['ordem']==0
    ordered=D.selecionar_revisados(rows,fato_id='f',preferir_legibilidade=True)
    assert ordered[0]['ordem']==1 and len(ordered)==3
    assert ordered[0]['preferencia_legibilidade_declarada'] is True
    assert not ordered[0]['selecao']['prova_de_acao']
    rows[1]['decisao']['revisao_id']='wrong'
    assert D.selecionar_revisados(rows,fato_id='f',preferir_legibilidade=True)[0]['ordem']==0


def test_invalid_observation_preserved_for_diagnosis_without_approval():
    _,windows=A.preparar_lote(midia(3),need(),frame)
    raw=response(False)
    raw['pontos'][1]['observacao']='curto'
    def ask(prompt,images):
        assert 'pelo menos 12 caracteres' in prompt
        return {'janelas':[{'janela':0,'resposta':raw}]}
    row=D.revisar_janelas_lote(windows,ask,evidencia_visual='movimento')['janelas'][0]
    assert row['falha']=='ValueError:D-REV-OBSERVACAO'
    assert row['resposta_invalida']==raw and 'revisao' not in row


def test_identical_observed_pixels_cannot_support_reported_motion():
    still = lambda path, t, width: Image.new('RGB', (width, 240), 'navy')
    media = midia(3)
    _, windows = A.preparar_lote(media, need(), still)
    packet, frames = windows[0]
    review = D.revisar_janela_visao(packet, frames, lambda *_: response(True),
                                    permitir_chamada=True, evidencia_visual='movimento')
    decision = R.decidir(need(), {'aquisicao': {'sha256': media['expected_sha256']}},
                         {**review, 'sha256_origem': media['expected_sha256'], 'necessidade_id': 'n'},
                         tipo='video')
    assert decision['motivo'] == 'QUADROS_INDICADOS_IDENTICOS'


def test_checkpoint_keeps_invalid_observation_and_prior_valid_decision():
    packet = {'revisao_id': 'x'}
    invalid = {'pacote': packet, 'resposta_invalida': {}, 'falha': 'D-REV-OBSERVACAO'}
    approved = {'pacote': packet, 'decisao': {'estado': 'PERTINENTE_PRIVADO'}}
    assert A.consolidar_janelas([], [invalid]) == [invalid]
    assert A.consolidar_janelas([invalid], [approved]) == [approved]
    assert A.consolidar_janelas([approved], [invalid]) == [approved]


def test_single_cut_ranks_after_change_in_both_pairs_but_remains_eligible():
    cut = {'inicio_s': 0, 'duracao_s': 3, 'contraste_min': 20, 'mudanca_px': 100,
           'pares_alterados': 1, 'diagnostico': {'quadros_grafismo_suspeito': 0}}
    gradual = {**cut, 'inicio_s': 4, 'pares_alterados': 2, 'mudanca_px': 3}
    exploration = {'duracao_origem_s': 20, 'janelas': [cut, gradual]}
    assert A.selecionar(exploration, limite=1, priorizar_movimento=True) == [gradual]
    assert cut in A.selecionar(exploration, limite=2, priorizar_movimento=True)
