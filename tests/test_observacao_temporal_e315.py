import hashlib
from pathlib import Path
from scripts.qa_documentario_geografia_e219 import frame
from src.v4.formatos import observacao_temporal_e315 as O,direcao_eventos as D, revisao_documental as R

def test_existing_review_binds_label_and_pixels(monkeypatch):
    # Actual footage bytes, synthetic labels/review only for structural testing.
    src=Path(__file__).resolve().parent/'midia/video_horizontal_navio.mp4'
    h=hashlib.sha256(src.read_bytes()).hexdigest()
    m={'expected_sha256':h,'duration_s':6.006}
    n={'id':'n','fatos':['f'],'mostrar':'observacao de teste','evidencia_visual':'movimento'}
    frames=[frame(src,3*f,width=320) for f in (0,.5,.9)]
    p=D.pacote_observacao(m,0,3,frames,fato_id='f',necessidade=n['mostrar'],fracoes=(0,.5,.9))
    raw={'veredito':'pertinente','inspecao':'Descricao de teste estrutural sem aprovacao editorial.',
        'pontos':[{'indice':i,'observacao':'Observacao de teste estrutural','elementos':[]} for i in range(3)],
        'natureza_visual':'registro_compativel','mudanca_observada':True,'indices_mudanca':[0,1],
        'descricao_mudanca':'Mudanca hipotetica para teste de vinculo de amostras.',
        'rotulo_mudanca':'Rótulo de teste'}
    q=D.revisar_janela_visao(p,frames,lambda *_:raw,permitir_chamada=True,evidencia_visual='movimento')
    q.update(sha256_origem=h,necessidade_id='n')
    p['revisao_assistida']=q
    c={'aquisicao':{'sha256':h},'janelas':[{'pacote':p}]}
    c['decisao']=R.decidir(n,c,q,tipo='video')
    w={'source_in_seconds':0,'revisao_id':p['revisao_id']}
    result=O.candidato(n,c,w,3)
    assert result['at']==1.5 and not result['prova_de_acao_continua']
    shot={'id':'n','type':'video','start':0,'end':3,'source_in_seconds':0,'observacao_temporal_candidata':result}
    source={**m,'local_source':str(src)}
    assert O.validar(shot,source,h,n)['label']=='Rótulo de teste'
    assert O.candidato(n,c,w,2) is None
    assert O.candidato({**n,'fatos':['different']},c,w,3) is None
    assert O.validar(shot,source,'0'*64,n) is None
    assert O.validar({**shot,'observacao_temporal_candidata':{**result,'at':0}},source,h,n) is None
    result['samples'][0]['pixels_sha256']='0'*64
    assert O.validar(shot,source,h,n) is None
    raw.pop('rotulo_mudanca')
    assert O.candidato(n,c,w,3) is None
