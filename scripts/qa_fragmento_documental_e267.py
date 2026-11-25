"""Private fragment of already reviewed documentary evidence, never a finished film."""
import json,math,sys
from pathlib import Path
from src.v4.formatos import ponte_cobertura_filme as P,filme_editorial as F,reuso_documental as RE
from scripts.qa_documentario_curado_e218 import PUBLIC

def selecionar_spec(spec,old,ids):
    if spec.get('publish') is not False or old.get('publish') is not False:raise ValueError('E267-PRIVADO')
    if not 3<=len(ids)<=8 or len(set(ids))!=len(ids):raise ValueError('E267-FRAGMENTO')
    case=next(c for c in spec['cases'] if c['id']==old['case']['id'])
    verified={r['necessidade_id'] for r in old['cobertura'] if r['estado']=='CANDIDATO_PRIVADO_REVISADO'}
    if not set(ids)<=verified:raise ValueError('E267-NAO-REVISADO')
    nmap={n['id']:n for n in old['triagem']}
    needs=[n for n in case['necessidades'] if n['id'] in ids]
    if len(needs)!=len(ids) or any(RE.escopo(n)!=RE.escopo(nmap[n['id']]) for n in needs):raise ValueError('E267-ESCOPO')
    chapters=[{**ch,'needs':[i for i in ch['needs'] if i in ids]} for ch in case['chapters'] if set(ch['needs'])&set(ids)]
    return {**spec,'cases':[{**case,'chapters':chapters,'necessidades':needs}]}

def preparar(root):
    root=Path(root);report=json.loads((root/'revisao.json').read_text())
    if report.get('publish') is not False or report['visao_chamadas_logicas'] or report['rede_aquisicao']['http'] or report['cobertura_documentario']['consumo']['buscas']:raise ValueError('E267-REPLAY')
    case=report['case'];chosen,gate=P.preparar_cobertura(report,case,minimo_s=1.4)
    if not gate['pronto_para_tts']:raise ValueError(str(gate))
    end=0;ends=[]
    for ch in case['chapters']:
        for nid in ch['needs']:
            x=chosen[nid];end+=max(math.ceil(x['min']*30-1e-6),min(96,math.floor(x['cap']*30+1e-6)))
        ends.append(end)
    plan=P.plano(case,chosen,ends)
    F.preparar(plan,root/'fragmento',PUBLIC,fragmento_misto=True)
    proof={'publicar':False,'voz':False,'visao_nova':0,'tipo':'FRAGMENTO_PRIVADO_INCOMPLETO','revisao_visual':'PENDENTE','duracao_s':plan['duracao'],'cenas':[{'id':s['id'],'tipo':s['type'],'inicio':s['start'],'fim':s['end']} for s in plan['shots']],'gate':gate}
    (root/'fragmento.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2))
    print('E267 FRAGMENTO',proof,flush=True)

if __name__=='__main__':
    if sys.argv[1]=='selecionar':
        spec=json.loads(Path(sys.argv[2]).read_text());old=json.loads(Path(sys.argv[3]).read_text())
        Path(sys.argv[4]).write_text(json.dumps(selecionar_spec(spec,old,sys.argv[5:]),ensure_ascii=False))
    elif sys.argv[1]=='preparar':preparar(sys.argv[2])
    else:raise ValueError('E267-MODO')
