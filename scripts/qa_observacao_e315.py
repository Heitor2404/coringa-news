"""Assisted observation of E300 verified USGS footage, no new vision."""
import json,hashlib,sys
from pathlib import Path
from src.v4.formatos import ponte_cobertura_filme as P,filme_editorial as F,direcao_eventos as D,revisao_documental as R
from scripts.qa_documentario_geografia_e219 import frame

def main():
    root=Path('stage_documental/e315');h='783f746a234d1378158d7ca3b74ed63ab0e0526664bc72c73c5222a22315b25c'
    src=root/(h+'.mp4')
    assert P.sha(src)==h
    m={'expected_sha256':h,'duration_s':62.9468}
    n={'id':'n','fatos':['f'],'mostrar':'Fragmentos incandescentes projetados acima da fissura',
       'sujeito':'Fonte de lava','necessidade':'registro','papel_visual':'acao','evidencia_visual':'movimento','exigir_evidencia_direta':True}
    frames=[frame(src,7+3.8*f,width=320) for f in (.12,.5,.86)]
    p=D.pacote_observacao(m,7,3.8,frames,fato_id='f',necessidade=n['mostrar'])
    # Same three source times in previously inspected E300 contact sheet.
    raw={'veredito':'pertinente','inspecao':'Fonte incandescente e fragmentos escuros projetados acima da borda, com distribuição variável nas três amostras.',
      'pontos':[{'indice':i,'observacao':t,'elementos':[]} for i,t in enumerate([
        'Fonte vermelha com fragmentos acima e à direita.',
        'Fragmentos escuros dispersos acima da fonte vermelha.',
        'Fonte vermelha e fragmentos dispersos à direita.'])],
      'natureza_visual':'registro_compativel','mudanca_observada':True,'indices_mudanca':[0,1],
      'descricao_mudanca':'A distribuição dos fragmentos projetados muda entre os dois quadros amostrados.',
      'rotulo_mudanca':'Fragmentos projetados',
      'evidencia_direta':{'classe':'direta','detalhe':'Fonte de lava vermelha e fragmentos acima da superfície','escala':'xy_0_1000',
      'bbox':{'esquerda':200,'topo':300,'direita':650,'base':760}}}
    q=D.revisar_janela_visao(p,frames,lambda *_:raw,permitir_chamada=True,evidencia_visual='movimento',exigir_evidencia_direta=True)
    q.update(sha256_origem=h,necessidade_id='n')
    p['revisao_assistida']=q
    c={'fonte':'curadoria_privada','source_id':'usgs-e300','tipo':'video',
       'pagina':'https://www.usgs.gov/media/videos/kilauea-volcano-fissure-8-video-compilation',
       'credito':'USGS · Hawaiian Volcano Observatory','licenca':'Public domain','local_source':str(src),
       'aquisicao':{'sha256':h,'width':1920,'height':1080,'duration_s':62.9468},
       'janelas':[{'pacote':p}]}
    c['decisao']=R.decidir(n,c,q,tipo='video')
    c['selecao_janela']=D.candidato_revisado(p,m,fato_id='f')
    row={'necessidade_id':'n','estado':'CANDIDATO_PRIVADO_REVISADO','selecionado':['curadoria_privada','usgs-e300'],
         'rodadas':[{'pesquisa':{'candidatos':[c]}}]}
    case={'tema':'Registro da fissura 8','chapters':[{'title':'Atividade da fissura','needs':['n']}]}
    chosen,gate=P.preparar_cobertura({'publish':False,'triagem':[n],'cobertura':[row]},case,minimo_s=1.4)
    assert gate['pronto_para_tts'],gate
    plan=P.plano(case,chosen,[114])
    assert plan['shots'][0]['observacao_temporal_candidata']['label']=='Fragmentos projetados'
    F.preparar(plan,root,Path('motor4/remotion/public'),fragmento_misto=True)
    props=json.loads((root/'props.json').read_text())
    assert props['shots'][0]['documentary_observed_label']['at']==1.9
    (root/'review.json').write_text(json.dumps({'publish':False,'observacao_assistida':True,'source_review':'revisoes/e300-coverage-45737009519-1/candidato-1.jpg','plan':plan,'gate':gate},ensure_ascii=False))
if __name__=='__main__':main()
