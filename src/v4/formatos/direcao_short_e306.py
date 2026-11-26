"""Pre-render editorial triage. Structural evidence, never an aesthetic verdict.
A normal photo, its camera zoom and text cues are not an explanatory event.
Keep laboratory replays possible; gate NEW narrated shorts in E254 before TTS.
"""
import math
from . import filme_editorial as F

def direcao_explicativa(shot,need,media):
    """Describe what still needs evidence; never grant a renderer or infer causality."""
    role=need.get('papel_visual','a_definir')
    kind=shot['type']
    detail=F.detalhe_fotografico(shot,media,media.get('expected_sha256')) if kind=='photo' else None
    if role=='detalhe':
        state='CANDIDATO_DESTAQUE_OBSERVADO' if detail else 'REVISAR_REGIAO_ESPECIFICA'
    elif role=='comparacao':
        state='REVISAR_PARES_E_CRITERIO_COMUM'
    elif role=='mecanismo':
        state='REVISAR_ETAPAS_E_RELACOES_FUNDAMENTADAS'
    elif role=='consequencia':
        state='REVISAR_CONSEQUENCIA_VISIVEL_SEM_INFERIR_CAUSA'
    elif role=='localizacao':
        state='REVISAR_VINCULO_GEOGRAFICO'
    elif role=='acao':
        state='REVISAR_ACAO_NOS_PIXELS_E_NO_TEMPO'
    elif role=='estrutura':
        state='REVISAR_ELEMENTOS_E_RELACAO_ESPACIAL'
    else:
        state='REVISAR_CONTRIBUICAO_A_NARRATIVA'
    return {'necessidade_id':shot['id'],'fatos':need.get('fatos',[]),'mostrar':need.get('mostrar'),
            'papel_visual':role,'estado':state,'tipo_atual':kind,
            'evidencia_visual':need.get('evidencia_visual'),
            'destaque_candidato':detail is not None,'aprovacao_editorial':False,
            'autoriza_animacao':False,'publicar':False}


def diagnosticar(plan):
    shots=plan['shots'];media=plan.get('media',{})
    if not shots:raise ValueError('E306-SEM-CENAS')
    needs={n['id']:n for n in plan.get('necessidades_direcao',[])}
    rows=[];explanation=[];total=0.;passive=0.;run=0.;longest=0.
    for shot in shots:
        a,b=shot['start'],shot['end'];span=b-a
        if not math.isfinite(span) or span<=0:raise ValueError('E306-TEMPO')
        m=media.get(shot.get('asset'),{});kind=shot['type']
        # Authored graphics and other renderers are candidates for explanation,
        # NOT proof of their semantic correctness; existing gates remain mandatory.
        static=kind=='photo' and m.get('original_graphic') is not True
        if static:passive+=span;run+=span;longest=max(run,longest)
        else:run=0.
        total+=span
        w,h=m.get('width'),m.get('height');potential=None;crop=None
        if type(w) is int and type(h) is int and min(w,h)>0 and kind in ('photo','video'):
            scale=min(1080/w,1920/h)
            potential=round(w*h*scale*scale/(1080*1920),4)
            if static:crop=F.propor_recorte_foto(shot,m,(w,h))
        n=needs.get(shot['id']) or {}
        explanation.append(direcao_explicativa(shot,n,m))
        rows.append({'id':shot['id'],'start':a,'end':b,'kind':kind,
            'fatos':n.get('fatos',[]),'mostrar':n.get('mostrar'),'papel_visual':n.get('papel_visual','a_definir'),
            'evidencia_visual':n.get('evidencia_visual'),'preferencia_midia':n.get('preferencia_midia','adequada_ao_fato'),
            'passive_photo':static,'integral_canvas_fraction':potential,
            'observed_photo_crop_candidate':crop is not None,
            'needs':['BUSCAR_ACAO_OU_DEMONSTRACAO_PERTINENTE','AVALIAR_IMERSAO_SEM_PERDA'] if static else ['VERIFICAR_O_QUE_OS_PIXELS_DEMONSTRAM']})
    all_passive=all(r['passive_photo'] for r in rows)
    issues=[]
    if all_passive:issues.append('SLIDESHOW_PASSIVO_INTEGRAL')
    if longest>8:issues.append('SEQUENCIA_FOTOGRAFICA_LONGA_REVISAR')
    if rows[0]['passive_photo']:issues.append('GANCHO_VISUAL_REVISAR')
    tasks=tarefas_replanejamento(rows)
    return {'schema':'coringa.short.triage.v1','tarefas_replanejamento':tasks,'direcao_explicativa':explanation,'publicar':False,
        'pronto_para_analise_visual':not all_passive,'editorial_approval':False,
        'rendered_coverage_verified':False,'status':'REPLANEJAR' if all_passive else 'REVISAR',
        'duration_s':round(total,3),'passive_photo_s':round(passive,3),
        'longest_passive_s':round(longest,3),'issues':issues,'shots':rows,
        'remediation':'Priorizar filmagem pertinente, comparação real, mapa ou explicação visual vinculada ao fato; não adicionar movimento decorativo para cumprir quota.'}

def tarefas_replanejamento(rows):
    """Same factual obligations before and after the film preflight."""
    tasks=[{'necessidade_id':r['id'],'fatos':r['fatos'],'mostrar':r['mostrar'],
        'acao':'REVISAR_ALTERNATIVA_REAL_MAIS_EXPLICATIVA' if r['preferencia_midia']=='video_preferencial' else 'REAVALIAR_CONTRIBUICAO_VISUAL_SEM_ALTERAR_FATO',
        'preservar_evidencia_visual':r['evidencia_visual'],'publicar':False,'autoriza_animacao':False}
        for r in rows if r['passive_photo'] and r['fatos'] and r['mostrar']]
    return tasks
