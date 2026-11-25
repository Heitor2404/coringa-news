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
