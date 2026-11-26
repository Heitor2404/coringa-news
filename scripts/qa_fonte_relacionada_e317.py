"""Private two-cut proof with one authentic USGS original.
Assisted observations, no claim of continuous cause or autonomous selection.
"""
import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
from src.v4.formatos import ponte_cobertura_filme as P,filme_editorial as F,direcao_eventos as D,revisao_documental as R
from src.v4.formatos import reserva_janelas_e313 as RJ
from scripts.qa_documentario_geografia_e219 import frame

def main():
    root=Path('stage_documental/e317');h='783f746a234d1378158d7ca3b74ed63ab0e0526664bc72c73c5222a22315b25c'
    src=root/(h+'.mp4');assert P.sha(src)==h
    page='https://www.usgs.gov/media/videos/kilauea-volcano-fissure-8-video-compilation'
    m={'expected_sha256':h,'duration_s':62.9468}
    needs=[];rows=[];reservations={};board=Image.new('RGB',(960,400),'#191919');draw=ImageDraw.Draw(board)
    specs=[
      ('a','f1','Fragmentos projetados','Fonte de lava e fragmentos acima da fissura','acao','movimento',7,(.12,.5,.86),
       ['Fonte vermelha e fragmentos acima da superfície.','Fragmentos dispersos em torno da fonte vermelha.','Fonte vermelha com material disperso à direita.'],
       [200,300,650,760]),
      ('b','f2','Material depositado na rua','Rua coberta de fragmentos escuros, identificados como rocha resfriada na cartela da USGS','consequencia','estatica',25,(0,2/3.8,.9),
       ['Via coberta de material escuro granular entre vegetação.','Material escuro cobre a rua e marcas de pneus.','Via com material granular escuro; não afirmar a queda neste quadro.'],
       [50,570,850,990])]
    for i,(nid,fid,subject,show,role,ev,t,frac,obs,box) in enumerate(specs):
        n={'id':nid,'fatos':[fid],'mostrar':show,'sujeito':subject,'necessidade':'registro','papel_visual':role,'evidencia_visual':ev,'exigir_evidencia_direta':True}
        ims=[frame(src,t+3.8*f,width=320) for f in frac]
        p=D.pacote_observacao(m,t,3.8,ims,fato_id=fid,necessidade=show,fracoes=frac)
        for j,im in enumerate(ims):
            draw.text((j*320+5,i*200+2),f"{nid} {p['amostras'][j]['fonte_s']:.3f}s",fill='white')
            board.paste(im,(j*320,i*200+18))
        if nid=='b':
            assert p['amostras'][0]['pixels_sha256']=='fbee8ee64ef7bc20d7b0d849a774a8d965fac566817eeed353817c482ce2ae2c'
            assert p['amostras'][1]['pixels_sha256']=='d7acc4d3d1937c2a6e58342d0172c332d4fb761854032caeae42bce668c3ccdc'
        raw={'veredito':'pertinente','inspecao':'Observação assistida de material visível nas amostras do original USGS, sem certificar continuidade ou identidade dos fragmentos.',
             'pontos':[{'indice':j,'observacao':o,'elementos':[]} for j,o in enumerate(obs)],
             'natureza_visual':'registro_compativel','evidencia_direta':{'classe':'direta','detalhe':show,'escala':'xy_0_1000',
                'bbox':dict(zip(('esquerda','topo','direita','base'),box))}}
        if ev=='movimento':raw.update(mudanca_observada=True,indices_mudanca=[0,1],descricao_mudanca='A distribuição dos fragmentos projetados muda entre os quadros amostrados.')
        q=D.revisar_janela_visao(p,ims,lambda *_:raw,permitir_chamada=True,evidencia_visual=ev,exigir_evidencia_direta=True)
        q.update(sha256_origem=h,necessidade_id=nid);p['revisao_assistida']=q
        c={'fonte':'curadoria_privada','source_id':'usgs-e300','tipo':'video','pagina':page,
           'credito':'USGS · Hawaiian Volcano Observatory','licenca':'Public domain','local_source':str(src),
           'aquisicao':{'sha256':h,'width':1920,'height':1080,'duration_s':62.9468},'janelas':[{'pacote':p}]}
        c['decisao']=R.decidir(n,c,q,tipo='video');w=D.candidato_revisado(p,m,fato_id=fid)
        assert c['decisao']['estado']=='PERTINENTE_PRIVADO',c['decisao']
        # Preserve source width: the USGS credit and spatial context must survive.
        w['video_framing']={'modo':'fonte_integral','sha256_origem':h,
            'inspecao':'A fonte inclui o contexto do acontecimento e a marca da USGS, ambos preservados.',
            'motivo':'Não cortar elementos de contexto ou crédito embutido.'}
        c['selecao_janela']=w
        res=RJ.propor(n,c,w,c['decisao']);assert RJ.compativel(res,reservations)
        reservations[nid]=res
        needs.append(n);rows.append({'necessidade_id':nid,'estado':'CANDIDATO_PRIVADO_REVISADO','selecionado':['curadoria_privada','usgs-e300'],'rodadas':[{'pesquisa':{'candidatos':[c]}}]})
    case={'tema':'Da fonte de lava ao material depositado','fatos':[{'id':'f1','fonte':page},{'id':'f2','fonte':page}],
       'chapters':[{'title':'Fragmentos projetados','needs':['a']},{'title':'Material na rua','needs':['b']}]}
    chosen,gate=P.preparar_cobertura({'publish':False,'triagem':needs,'cobertura':rows},case,minimo_s=1.4)
    assert gate['pronto_para_tts'],gate
    plan=P.plano(case,chosen,[114,228])
    assert len(plan['media'])==1 and [s['source_in_seconds'] for s in plan['shots']]==[7,25]
    F.preparar(plan,root,Path('motor4/remotion/public'),fragmento_misto=True)
    props=json.loads((root/'props.json').read_text())
    assert all(s['documentary_integral_required'] for s in props['shots'])
    board.save(root/'source-samples.jpg',quality=92)
    (root/'proof.json').write_text(json.dumps({'publish':False,'assisted':True,'visual_approval':'PENDING','gate':gate,'plan':plan,
       'source_relation':'Cartela USGS no original, 57–61s: primeiro registro da fissura e segundo da rua Kupono onde rocha resfriada cai como chuva. Não identifica os mesmos fragmentos nem demonstra queda contínua.'},ensure_ascii=False))
if __name__=='__main__':main()
