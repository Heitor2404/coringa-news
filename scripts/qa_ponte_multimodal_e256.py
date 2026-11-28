"""E256: real ATLAS delivery into the coverage bridge plus bounded video discovery.
No TTS, AI, or claim of a complete documentary.
"""
import json,sys,subprocess
from pathlib import Path
from scripts import qa_documentario_geografia_e219 as E
from src.v4.formatos import ponte_cobertura_filme as P
from src.v4 import acervo_v4 as A

def main():
    root=Path(sys.argv[1]);root.mkdir(parents=True,exist_ok=True)
    n={'id':'m1','fatos':['f1'],'sujeito':'Ilha do Havaí','mostrar':'localização regional da ilha do Havaí',
       'necessidade':'territorio','evidencia_visual':'estatica'}
    case={'tema':'Localização — prova privada','chapters':[{'title':'Onde aconteceu','needs':['m1']}]}
    report={'publish':False,'triagem':[n],'cobertura':[{'necessidade_id':'m1','estado':'DELEGAR_ATLAS'}]}
    ch=next(c for c in E.read('benchmarks/e219/kilauea_2018.json')['chapters'] if 'atlas' in c)
    E.MAP=Path('stage_atlas/e256')
    clip,proof=E.mapclip(ch,5.5)
    delivery={'necessidade_id':'m1','fatos':['f1'],'mostrar':n['mostrar'],
        'origem':'CURADORIA_GEOGRAFICA_VERIFICADA','local_source':str(clip),'atlas_proof':str(proof),
        'expected_sha256':P.sha(clip)}
    chosen,gate=P.preparar_cobertura(report,case,atlas={'m1':delivery},minimo_s=5)
    assert gate['pronto_para_tts'] and chosen['m1']['cap']==5.5
    plan=P.plano(case,chosen,[165])
    assert plan['shots'][0]['type']=='atlas_map' and not plan['publicar']
    assert not P.B.validar_comprovante(plan['media'][plan['shots'][0]['asset']])
    E.write(root/'mapa-ponte.json',{'gate':gate,'plano':plan,'publicar':False,'teste_curto':True})
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(clip),'-vf','fps=1,scale=270:480,tile=3x2','-frames:v','1',str(root/'mapa-contato.jpg')],check=True)
    rows=[]
    for subject,queries in [('biologia',['octopus camouflage','octopus color change']),('geologia',['volcano eruption lava','lava flow'])]:
        need={'id':subject,'necessidade':'registro','evidencia_visual':'movimento','pesquisa':{'consultas_en':queries}}
        rows.append(A.pesquisar_cobertura(need,max_buscas=4))
    E.write(root/'descoberta-video.json',{'publicar':False,'pesquisas':rows,'visao_chamadas':0})
    print('E256 MAPA REAL NA PONTE',plan['duracao'],'segundos; descoberta de video',[(r['id'],len(r['candidatos'])) for r in rows])
if __name__=='__main__':main()
