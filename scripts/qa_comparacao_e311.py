"""E311 actual fixture pair, independently inspected by ChatGPT.
Qualitative form of cliff faces only; no measurement or temporal claim.
"""
import hashlib,json,shutil
from pathlib import Path
from src.v4.formatos import ponte_cobertura_filme as P,filme_editorial as F
def preparar(root,public):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    rows=[];needs=[];members=[]
    for i,(name,git,subject,label,wh) in enumerate([
        ('foto_horizontal_roraima','e730d92b6d41e02b5c5394175af1e377aaa15b9b','Monte Roraima e Kukenán','Escarpas à distância',(1800,1200)),
        ('foto_vertical_salto_angel','a0d3e9edf55d675d7e8d69aecafb43cd2c467878','Salto Ángel','Parede de perto',(946,1600))]):
        src=Path('tests/midia')/(name+'.jpg');data=src.read_bytes()
        assert hashlib.sha1(('blob '+str(len(data))+'\0').encode()+data).hexdigest()==git
        meta=json.loads(src.with_suffix('.json').read_text());h=hashlib.sha256(data).hexdigest()
        target=root/(name+'.jpg');shutil.copyfile(src,target)
        nid='n'+str(i);rid='E311-assisted-'+nid
        need={'id':nid,'fatos':['f'+str(i)],'mostrar':label,'sujeito':subject,'papel_visual':'comparacao',
            'evidencia_visual':'estatica','exigir_evidencia_direta':True}
        candidate={'fonte':'commons','source_id':name,'tipo':'foto','pagina':meta['pagina'],
            'credito':meta['autor']+' · '+meta['licenca'],'licenca':meta['licenca'],'local_source':str(target),
            'aquisicao':{'sha256':h,'width':wh[0],'height':wh[1],'duration_s':None},
            'decisao':{'estado':'PERTINENTE_PRIVADO','necessidade_id':nid,'revisao_id':rid,'publicar':False,'direitos_aprovados':False}}
        rows.append({'necessidade_id':nid,'estado':'CANDIDATO_PRIVADO_REVISADO','selecionado':['commons',name],
            'rodadas':[{'pesquisa':{'candidatos':[candidate]}}]})
        needs.append(need)
        members.append({'necessidade_id':nid,'fatos':need['fatos'],'mostrar':label,'sha256':h,
            'revisao_id':rid,'rotulo':label,'criterio_observado':'Paredes rochosas'})
    for m,box in zip(members,([.35,.20,.83,.30],[.27,.19,.76,.34])):
        m['roi_observada']={'sha256':m['sha256'],'revisao_id':m['revisao_id'],'origem':'OBSERVACAO_PRIVADA','bbox':box}
    pair={'apresentacao':'painel_observado','id':'qualitative','tipo':'qualitativa','origem':'INSPECAO_ASSISTIDA_PRIVADA','criterio':'Paredes rochosas',
        'membros':members,'escala_comparavel':False,'inferir_causalidade':False,'inferir_cronologia':False,
        'publicar':False,'direitos_aprovados':False}
    case={'tema':'Relevo em duas vistas','chapters':[{'title':'Relevo','needs':['n0','n1']}],
          'comparacoes_revisadas':[pair]}
    chosen,gate=P.preparar_cobertura({'publish':False,'triagem':needs,'cobertura':rows},case,minimo_s=1.4)
    assert gate['pronto_para_tts'],gate
    p=P.plano(case,chosen,[180])
    assert p['comparacoes_documentais'][0]['estado']=='PAR_QUALITATIVO_MONTADO_PRIVADO'
    assert [s['lead'] for s in p['shots']]==['Paredes rochosas · Escarpas à distância','Paredes rochosas · Parede de perto']
    F.preparar(p,root,Path(public),fragmento_misto=True)
    props=json.loads((root/'props.json').read_text())
    assert not props['shots'][0].get('documentary_comparison_panel')
    assert props['shots'][1]['documentary_comparison_panel']['scale_comparable'] is False
    (root/'comparison.json').write_text(json.dumps({'publish':False,'visual_approval':'PENDING','packet':pair,'result':p['comparacoes_documentais'],
        'note':'Duas vistas de referentes distintos, não antes/depois nem escala comum.'},ensure_ascii=False))
    return case,chosen,p
if __name__=='__main__':preparar('stage_documental/e311','motor4/remotion/public')
