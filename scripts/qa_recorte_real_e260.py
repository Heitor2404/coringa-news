"""E260.3: private comparative proof using previously reviewed real media.
No new AI, no new source requests, no full-film or aesthetic approval.
"""
import copy,json,math,sys
from pathlib import Path
from src.v4.formatos import ponte_cobertura_filme as P,filme_editorial as F
from scripts.qa_documentario_geografia_e219 import frame
from scripts.qa_documentario_curado_e218 import PUBLIC

def main():
    root=Path(sys.argv[1])
    report=json.loads((root/'revisao.json').read_text())
    if report.get('publish') is not False or report.get('visao_chamadas_logicas')!=0 or report['rede_aquisicao']['http']!=0:
        raise ValueError('E260.3-REPLAY')
    # Select any eligible reviewed video from the existing contrasting fixture,
    # not a hard-coded provider, asset ID or timestamp.
    for n in report['triagem']:
        if n.get('evidencia_visual')!='movimento':continue
        row=next((r for r in report['cobertura'] if r['necessidade_id']==n['id']),{})
        if row.get('estado')!='CANDIDATO_PRIVADO_REVISADO':continue
        case={'tema':'Prova comparativa de recorte documental privado',
              'chapters':[{'title':'Registro real','needs':[n['id']]}]}
        sub={**report,'triagem':[n],'cobertura':[row]}
        chosen,gate=P.preparar_cobertura(sub,case,minimo_s=1.4)
        if not gate['pronto_para_tts']:continue
        x=chosen[n['id']]
        if x['kind']!='video' or not x['framing'] or x['progressao'] or x['min']<=1.4:continue
        frames=math.ceil(x['min']*30-1e-6)
        new=P.plano(case,chosen,[frames])
        oldchosen=copy.deepcopy(chosen);oldchosen[n['id']]['min']=1.4
        old=P.plano(case,oldchosen,[42])
        s=new['shots'][0];oldshot=old['shots'][0]
        assert 'video_framing' in s and 'video_framing' not in oldshot
        last=max(p['at'] for p in s['video_framing']['pontos'])
        assert oldshot['end']<last and (frames-1)/30>=last-1e-6
        assert s['source_in_seconds']==oldshot['source_in_seconds']
        # Re-decode the original at the actual inspected times and authenticate pixels.
        pk=next(r['pacote'] for r in x['candidate']['janelas'] if r['pacote']['revisao_id']==x['window']['revisao_id'])
        import hashlib
        for i,a in enumerate(pk['amostras']):
            im=frame(x['candidate']['local_source'],a['fonte_s'],width=a['px'][0])
            # Timestamps in packets are rounded; use original fractional times
            # when rounding crosses an actual frame boundary.
            if hashlib.sha256(im.tobytes()).hexdigest()!=a['pixels_sha256']:
                frac=(0,.5,.9)[i]
                im=frame(x['candidate']['local_source'],pk['inicio_s']+pk['duracao_s']*frac,width=a['px'][0])
            assert hashlib.sha256(im.tobytes()).hexdigest()==a['pixels_sha256']
            im.save(root/f'original-amostra-{i}.jpg',quality=92)
        # Alternative: keep the entire reviewed source, same duration and
        # composition. No guessing a new bbox from the disputed observation.
        context=copy.deepcopy(new)
        context['shots'][0].pop('video_framing',None)
        context['shots'][0]['video_context_layout']='cena_integral'
        for name,plan in (('antes',old),('depois',new),('contexto',context)):
            dst=root/name
            F.preparar(plan,dst,PUBLIC,fragmento_misto=True)
        proof={'publicar':False,'revisao_visual_humana':'PENDENTE','voz':False,
               'sha256_origem':x['candidate']['aquisicao']['sha256'],'revisao_id':pk['revisao_id'],
               'inicio_origem':s['source_in_seconds'],'ultimo_quadro_revisado_s':last,
               'antes_s':oldshot['end'],'depois_s':s['end'],'contexto_s':s['end'],
               'contexto_enquadramento':'integral_sem_reduzir_duracao','comparacao_contexto':'alternativa editorial privada; escolher apos inspecionar pixels',
               'ultimo_frame_depois_s':(frames-1)/30,'amostras_sha_confirmadas':3,
               'antes_enquadramento':'integral','depois_enquadramento':'dirigido',
               'comparacao':'corte permitido pela antiga alocacao minima, nao filme anterior',
               'sem_prova_de_acao_continua':True}
        (root/'comparacao.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2))
        print('E260.3',proof,flush=True)
        return
    raise ValueError('E260.3-SEM-CANDIDATO-COMPATIVEL')
if __name__=='__main__':main()
