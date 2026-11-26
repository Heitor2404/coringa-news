"""Pre-render editorial triage. Structural evidence, never an aesthetic verdict.
A normal photo, its camera zoom and text cues are not an explanatory event.
Keep laboratory replays possible; gate NEW narrated shorts in E254 before TTS.
"""
import math
from . import filme_editorial as F

def diagnosticar(plan):
    shots=plan['shots'];media=plan.get('media',{})
    if not shots:raise ValueError('E306-SEM-CENAS')
    rows=[];total=0.;passive=0.;run=0.;longest=0.
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
        rows.append({'id':shot['id'],'start':a,'end':b,'kind':kind,
            'passive_photo':static,'integral_canvas_fraction':potential,
            'observed_photo_crop_candidate':crop is not None,
            'needs':['BUSCAR_ACAO_OU_DEMONSTRACAO_PERTINENTE','AVALIAR_IMERSAO_SEM_PERDA'] if static else ['VERIFICAR_O_QUE_OS_PIXELS_DEMONSTRAM']})
    all_passive=all(r['passive_photo'] for r in rows)
    issues=[]
    if all_passive:issues.append('SLIDESHOW_PASSIVO_INTEGRAL')
    if longest>8:issues.append('SEQUENCIA_FOTOGRAFICA_LONGA_REVISAR')
    if rows[0]['passive_photo']:issues.append('GANCHO_VISUAL_REVISAR')
    return {'schema':'coringa.short.triage.v1','publicar':False,
        'pronto_para_analise_visual':not all_passive,'editorial_approval':False,
        'rendered_coverage_verified':False,'status':'REPLANEJAR' if all_passive else 'REVISAR',
        'duration_s':round(total,3),'passive_photo_s':round(passive,3),
        'longest_passive_s':round(longest,3),'issues':issues,'shots':rows,
        'remediation':'Priorizar filmagem pertinente, comparação real, mapa ou explicação visual vinculada ao fato; não adicionar movimento decorativo para cumprir quota.'}
