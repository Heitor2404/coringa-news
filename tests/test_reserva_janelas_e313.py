"""Real media bytes, deliberately synthetic semantic receipts: structural proof."""
from pathlib import Path
import hashlib,shutil
from src.v4.formatos import reserva_janelas_e313 as R,ponte_cobertura_filme as P

def test_reservation_filters_overlap_and_prefers_forward(tmp_path,monkeypatch):
    src=Path(__file__).resolve().parents[1]/'tests/midia/video_horizontal_navio.mp4'
    monkeypatch.chdir(tmp_path);Path('stage_documental').mkdir()
    p=Path('stage_documental')/'ship.mp4';shutil.copyfile(src,p)
    h=hashlib.sha256(p.read_bytes()).hexdigest()
    c={'fonte':'commons','source_id':'ship','tipo':'video',
       'pagina':'https://commons.wikimedia.org/wiki/File:Continuing_Promise_transits_the_Panama_Canal-ZLIWzvfdisQ-248%2B251.webm',
       'credito':'U.S. Navy','licenca':'Public domain','local_source':str(p),
       'aquisicao':{'sha256':h,'width':1280,'height':720,'duration_s':6.006}}
    def need(i):return {'id':i,'fatos':['f-'+i],'mostrar':'synthetic receipt for structural test','sujeito':'ship','evidencia_visual':'estatica','exigir_evidencia_direta':True}
    def dec(i):return {'estado':'PERTINENTE_PRIVADO','necessidade_id':i,'revisao_id':'r-'+i,'publicar':False,'direitos_aprovados':False}
    def win(t,d=1.8):return {'source_in_seconds':t,'duracao_s':d}
    a=R.propor(need('a'),c,win(2),dec('a'));assert a
    options=[(None,win(2.5),dec('b')),(None,win(0),dec('b')),(None,win(4),dec('b'))]
    ranked=[{'ordem':i} for i in range(3)]
    k,b=R.escolher(need('b'),c,options,ranked,{'a':a},{'a':0,'b':1},pages={c['pagina']},hashes={h})
    assert k==2 and b['inicio']==4
    assert R.escolher(need('b'),c,options[:1],ranked[:1],{'a':a},{'a':0,'b':1}) is None
    assert not R.compativel({**b,'fatos':a['fatos']},{'a':a})
    assert not R.compativel(b,{},pages={c['pagina']})
    assert not R.compativel({**b,'pagina':'different'},{'a':a})
    rows=[]
    for i,w in [('a',win(2)),('b',win(4))]:
        rows.append({'necessidade_id':i,'estado':'CANDIDATO_PRIVADO_REVISADO','selecionado':['commons','ship'],
          'rodadas':[{'pesquisa':{'candidatos':[{**c,'selecao_janela':w,'decisao':dec(i)}]}}]})
    case={'tema':'structural proof','chapters':[{'title':'test','needs':['a','b']}]}
    chosen,gate=P.preparar_cobertura({'publish':False,'triagem':[need('a'),need('b')],'cobertura':rows},case,minimo_s=1.4)
    assert gate['pronto_para_tts'],gate
    plan=P.plano(case,chosen,[108])
    assert [s['source_in_seconds'] for s in plan['shots']]==[2,4]
    assert plan['shots'][0]['asset']==plan['shots'][1]['asset']
