"""E261.4: real cartographic footage integration, private and without voice.
The geographic binding is a sourced QA input, NOT general automatic identity.
Use the existing native ATLAS multiscale pipeline and existing coverage bridge.
"""
import copy,json,math,sys,hashlib
from pathlib import Path
from scripts import qa_atlas_multiscale as G,qa_documentario_geografia_e219 as E
from src.v4.formatos import ponte_cobertura_filme as P,filme_editorial as F
from scripts.qa_documentario_curado_e218 import PUBLIC

def main():
    root=Path(sys.argv[1])
    report=json.loads((root/'revisao.json').read_text())
    spec=json.loads(Path(sys.argv[2]).read_text())
    if report.get('publish') is not False or spec.get('publish') is not False or report['visao_chamadas_logicas'] or report['rede_aquisicao']['http']:
        raise ValueError('E261.4-PRIVADO')
    n=next(n for n in report['triagem'] if n['id']==spec['necessidade_id'])
    row=next(r for r in report['cobertura'] if r['necessidade_id']==n['id'])
    candidates=[c for r in row['rodadas'] for c in r['pesquisa']['candidatos']
                if (c.get('decisao') or {}).get('estado')=='PERTINENTE_PRIVADO'
                and c.get('pagina')==spec['pagina'] and (c.get('aquisicao') or {}).get('sha256')==spec['sha256']]
    if not candidates:raise ValueError('E261.4-IDENTIDADE-SEM-VINCULO')
    c=candidates[-1]
    # Preserve the reviewed source and context. No new crop from the disputed bbox.
    # Separate source identity from an assisted assertion of continuous movement.
    mn={'id':'geo','fatos':['geo-regional'],'sujeito':spec['mapa']['atlas']['label'],
        'mostrar':spec['mostrar_mapa'],'necessidade':'territorio','evidencia_visual':'estatica'}
    geo={**spec['mapa'],'fonte_continua':True}
    E.MAP=Path('stage_atlas/e2618')
    E.MAP.mkdir(parents=True,exist_ok=True)
    acquired=G.adquirir_bases(geo)
    ch,p,camera=G.resolver(geo,acquired,5.5)
    clip,proof=E.mapclip(ch,5.5,plano_resolvido=p,documentary_layout=True)
    delivery={'necessidade_id':'geo','fatos':mn['fatos'],'mostrar':mn['mostrar'],
              'origem':'CURADORIA_GEOGRAFICA_VERIFICADA','local_source':str(clip),
              'atlas_proof':str(proof),'expected_sha256':P.sha(clip)}
    sub={**report,'triagem':[mn,n],'cobertura':[{'necessidade_id':'geo','estado':'DELEGAR_ATLAS'},row]}
    case={'tema':'Prova privada de localização e registro',
          'chapters':[{'title':'Localização','needs':['geo']},{'title':'Registro real','needs':[n['id']]}]}
    chosen,gate=P.preparar_cobertura(sub,case,atlas={'geo':delivery},minimo_s=6.9)
    if not gate['pronto_para_tts']:raise ValueError(str(gate))
    x=chosen[n['id']]
    assert x['candidate']['aquisicao']['sha256']==spec['sha256']
    frames=math.ceil(x['min']*30-1e-6)
    # Conservative contextual composition for this QA, not a topic rule.
    x['framing']=None
    plan=P.plano(case,chosen,[165,165+frames])
    assert [s['type'] for s in plan['shots']]==['atlas_map','video']
    F.preparar(plan,root/'misto',PUBLIC,fragmento_misto=True)
    result={'publicar':False,'voz':False,'visao_nova':0,'origem_video':spec['pagina'],
        'fonte_identidade':spec['fonte_identidade'],'escopo':'localizacao regional; nao posicao da camera',
        'camera':camera,'rasters':acquired['metas'],'gate':gate,'plano':plan,'fonte_continua_experimental':True,
        'duracao_s':plan['duracao'],'revisao_visual':'PENDENTE'}
    (root/'misto.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print('E261.4 MAPA E VIDEO',plan['duracao'],flush=True)
if __name__=='__main__':main()
