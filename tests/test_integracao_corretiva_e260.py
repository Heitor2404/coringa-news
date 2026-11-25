import copy
from PIL import Image
from src.v4.formatos import tempo_natural as T,direcao_eventos as D,revisao_documental as R
from scripts.recuperar_checkpoints_documentais import relevance

def candidate():
    sha='a'*64
    n={'id':'n','fatos':['f'],'mostrar':'mudança de um referente observável','evidencia_visual':'movimento'}
    m={'expected_sha256':sha,'duration_s':20}
    c={'aquisicao':{'sha256':sha},'janelas':[]}
    for i,start in enumerate((0,3.5)):
        frames=[Image.new('RGB',(800,600),(20+i*30+j*12,80,90)) for j in range(3)]
        p=D.pacote_observacao(m,start,3.8,frames,fato_id='f',necessidade=n['mostrar'],fracoes=(0,.5,.9))
        raw={'veredito':'pertinente','natureza_visual':'registro_compativel','inspecao':'Observação detalhada de três quadros reais vinculados ao referente.',
             'mudanca_observada':True,'indices_mudanca':[0,2],
             'descricao_mudanca':'Alteração observada e descrita em intervalo número '+str(i),
             'pontos':[{'indice':j,'observacao':'Referente visível no quadro '+str(j),'elementos':[{'nome':'referente','bbox_xy':{'esquerda':.2,'topo':.3,'direita':.4,'base':.6}}]} for j in range(3)]}
        q=D.revisar_janela_visao(p,frames,lambda *_:raw,permitir_chamada=True,evidencia_visual='movimento')
        q.update(sha256_origem=sha,necessidade_id='n');p['revisao_assistida']=q
        c['janelas'].append({'pacote':p,'decisao':R.decidir(n,c,q,tipo='video')})
    return n,c

def test_adjacent_windows_with_common_referent_only_private():
    n,c=candidate();p=T.progressao_amostrada(n,c,inicio=0)
    assert p and p['duracao_s']>7 and not p['prova_de_acao_continua']
    shot={'type':'video','evidence':'representative','source_in_seconds':0,'progressao_visual':p}
    assert not T.validar_progressao_video(shot,p['duracao_s'],{'expected_sha256':'a'*64})
    assert T.validar_progressao_video(shot,p['duracao_s']+1,{'expected_sha256':'a'*64})
    bad=copy.deepcopy(c)
    for pt in bad['janelas'][1]['pacote']['revisao_assistida']['resposta_observada']['pontos']:
        pt['elementos'][0]['nome']='outro_referente'
    assert T.progressao_amostrada(n,bad,inicio=0) is None
    bad=copy.deepcopy(c)
    bad['janelas'][1]['pacote']['inicio_s']=5
    assert T.progressao_amostrada(n,bad,inicio=0) is None

def test_checkpoint_relevance_respects_requested_media():
    n=[{'necessidade':'registro','evidencia_visual':'movimento','consultas_en':['lava flow channel']}]
    assert relevance({'tipo':'video','titulo':'Lava flow in channel'},n)>0
    assert relevance({'tipo':'foto','titulo':'Lava flow in channel'},n)==0
    assert relevance({'tipo':'video','titulo':'Polar bear'},n)==0


def test_progressive_cache_only_does_not_inspect_remote_or_require_vision():
    n={'id':'n','necessidade':'registro','evidencia_visual':'movimento',
       'pesquisa':{'consultas_en':['lava flow']}}
    local={'fonte':'biblioteca_v3','source_id':'local','tipo':'video'}
    remote={'fonte':'remote','source_id':'remote','tipo':'video'}
    seen=[]
    def search(*args):
        return {'id':'n','buscas':[],'candidatos':[remote,local]}
    def inspect(c,n):
        seen.append(c['source_id'])
        return {'estado':'PERTINENTE_PRIVADO','necessidade_id':'n','revisao_id':'verified',
                'publicar':False,'direitos_aprovados':False}
    row=R.cobertura_progressiva(n,search,inspect,pode_buscar=lambda:True,
        pode_inspecionar=lambda:False,max_buscas=4,
        pode_reusar=lambda c:c['fonte']=='biblioteca_v3')
    assert row['estado']=='CANDIDATO_PRIVADO_REVISADO'
    assert seen==['local'] and not row['publicar']
    seen.clear()
    row=R.cobertura_progressiva(n,search,inspect,pode_buscar=lambda:True,
        pode_inspecionar=lambda:False,max_buscas=4)
    assert row['estado']=='LACUNA_PENDENTE' and seen==[]


def test_cut_keeps_last_reviewed_sample_and_framing():
    from src.v4.formatos import ponte_cobertura_filme as P
    n,c=candidate()
    pk=c['janelas'][0]['pacote']
    win={'revisao_id':pk['revisao_id'],'source_in_seconds':pk['inicio_s'],'duracao_s':pk['duracao_s']}
    q=pk['revisao_assistida']
    framing=D.aceitar_observacao(pk,q['resposta_observada'])['video_framing']
    minimum=P.duracao_minima_revisada(c,win,3.8,framing)
    assert minimum<=3.8 and minimum-1/30>=3.42-1e-6
    assert P.duracao_minima_revisada(c,win,3.0,framing) is None
    assert P.duracao_minima_revisada(c,{**win,'revisao_id':'other'},3.8)==3.8

def test_integral_nasa_variant_ranking_retains_high_quality_options():
    from scripts.qa_pesquisa_documental_e246 import nasa_receipt
    import json
    urls=['https://images-assets.nasa.gov/video/ID/ID~'+x+'.mp4' for x in ('small','medium','orig','large')]
    class T:
        def get(self,*args):
            return json.dumps({'collection':{'items':[{'href':u} for u in urls]}}).encode()
    c={'source_id':'ID','tipo':'video'}
    choices=nasa_receipt(c,T(),progressivo=True,min_video_px=700)
    assert [x['url'] for x in choices]==[urls[1],urls[3],urls[2],urls[0]]


def test_short_credit_preserves_author_and_license_without_inventing():
    from src.v4.formatos import ponte_cobertura_filme as P
    c='Title — USGS Volcanoes (Public domain), Wikimedia Commons'
    assert P.credito_em_tela(c)=='USGS Volcanoes (Public domain), Wikimedia Commons'
    assert P.credito_em_tela('Original credit from other provider')=='Original credit from other provider'
    assert P.credito_em_tela('Title — Author — Other provider')=='Title — Author — Other provider'


def test_checkpoint_relevance_also_for_explanatory_need():
    n=[{'necessidade':'lacuna_explicativa','evidencia_visual':'movimento','consultas_en':['lava flow channel']}]
    assert relevance({'tipo':'video','titulo':'Lava flow in channel'},n)>0
    assert relevance({'tipo':'foto','titulo':'Lava flow in channel'},n)==0


def test_reviewed_negative_handoff_is_scoped_and_not_approval():
    from src.v4.formatos import cobertura_documental as C
    n,c=candidate()
    n.update(necessidade='lacuna_explicativa',lacuna='Não está claro o deslocamento')
    pk=c['janelas'][0]['pacote']
    q=pk['revisao_assistida']
    q['resposta_observada']['veredito']='insuficiente'
    c['janelas'][0]['decisao'].update(estado='INSUFICIENTE',motivo='SEM_PERTINENCIA')
    row={'estado':'LACUNA_PENDENTE','rodadas':[{'pesquisa':{'buscas':[{'estado':'OK','consulta':'source action'}],
        'candidatos':[c]},'cobertura':{'trilha':[]}}]}
    route=C.encaminhar(n,row)
    assert route['rota']=='REAVALIAR_COMPLEMENTO' and not route['animacao_autorizada']
    assert route['evidencia_lacuna']['escopo']=='APENAS_JANELAS_INSPECIONADAS'
    assert len(route['evidencia_lacuna']['revisoes_negativas'])==1
    assert C.encaminhar({**n,'mostrar':'outra ação'},row)['rota']=='REPLANEJAR_REGISTRO'
