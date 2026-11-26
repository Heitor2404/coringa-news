"""E328: prioritise real coverage weaknesses, not decorative motion or quotas.
Pre-render estimates only; actual browser geometry remains a separate QA.
"""
def diagnosticar(plan,rows):
    shots=plan['shots'];out=[];prev=None;repeated=0.;low=0.;horizontal=0.;unknown_portrait=0.
    for s,r in zip(shots,rows,strict=True):
        span=r['end']-r['start'];m=plan.get('media',{}).get(s.get('asset'),{})
        digest=m.get('expected_sha256') or s.get('asset')
        fraction=r['integral_canvas_fraction'];crop=r.get('observed_crop_candidate_fraction');tasks=[]
        if crop is not None and fraction is not None and crop>fraction+.05:
            tasks.append('COMPARAR_RECORTE_OBSERVADO_COM_FONTE_INTEGRAL')
        if r['kind'] in ('video','photo') and fraction is not None and fraction<.28:
            low+=span
            tasks.append('BUSCAR_ANGULO_VERTICAL_OU_COMPLEMENTO_REAL')
        if r['kind'] in ('video','photo') and fraction is not None and .28<=fraction<.35:
            horizontal+=span
            tasks.append('AVALIAR_COMPLEMENTO_INFORMATIVO_SEM_CROP_CEGO')
        if r['kind'] in ('video','photo') and fraction is not None and m['width']<m['height'] and not s.get('video_framing') and not s.get('photo_roi_candidate'):
            unknown_portrait+=span
            tasks.append('REVISAR_SOBREPOSICAO_E_LEGENDAS_ORIGINAIS')
        if r['kind']=='video' and not s.get('video_framing'):
            tasks.append('REVISAR_REGIAO_DE_ACAO_ANTES_DE_RECORTAR')
        if digest and digest==prev and r['kind']=='video':
            repeated+=span;tasks.append('REVISAR_VARIACAO_NARRATIVA_MESMA_FONTE')
        if s is shots[0]:
            tasks.append('CONFERIR_EVIDENCIA_DO_GANCHO')
        if tasks:
            out.append({'id':s['id'],'fatos':r['fatos'],'mostrar':r['mostrar'],
                'integral_canvas_fraction':fraction,'observed_crop_candidate_fraction':crop,'tarefas':tasks,'prioridade':('GANCHO' if s is shots[0] else 'EVIDENCIA' if r['evidencia_visual']=='movimento' or r['papel_visual'] in ('mecanismo','consequencia') else 'COMPOSICAO'),'publicar':False})
        prev=digest
    return {'schema':'coringa.immersion.triage.v1','low_integral_fraction_s':round(low,3),
        'adjacent_same_source_video_s':round(repeated,3),'moderate_integral_fraction_s':round(horizontal,3),'unknown_portrait_s':round(unknown_portrait,3),'tasks':out,'publish':False,
        'actual_render_verified':False,'editorial_approval':False}


def fracao_integral(w,h):
    """Geometric contain fraction only, not a measured render."""
    if type(w) is not int or type(h) is not int or min(w,h)<=0:return None
    return round(min((w/h)/(1080/1920),(1080/1920)/(w/h)),4)

def desempate_vertical(need,c):
    """Opt-in tie-break after existing relevance, rights, reuse and media
    ranking. Metadata is a lead, not proof of resolution or evidence."""
    if need.get('preferir_imersao_vertical') is not True or c.get('tipo') not in ('foto','video'):return 0
    from .filme_editorial import MIN_VIDEO_COMPOSITION_PX
    a=c.get('aquisicao') or {}
    if a.get('width') is not None or a.get('height') is not None:
        w,h=a.get('width'),a.get('height')
    else:w,h=c.get('largura_declarada'),c.get('altura_declarada')
    fraction=fracao_integral(w,h)
    if fraction is None or min(w,h)<(600 if c['tipo']=='foto' else MIN_VIDEO_COMPOSITION_PX):return 0
    # Only reward a materially larger native integral view. Unknown metadata
    # and horizontal records remain eligible, including very useful footage.
    return -fraction if fraction>=.60 else 0

def potencial_recorte(shot,media,photo_crop=None):
    """Existing reviewed geometry, never an assertion of safety at render."""
    if shot.get('type')=='photo':
        h=(photo_crop or {}).get('height')
        return round(h/1920,4) if h in (1080,1350,1920) else None
    if shot.get('type')!='video' or not shot.get('video_framing'):return None
    from . import filme_editorial as F
    try:
        dims=(media['width'],media['height'])
        if shot['video_framing'].get('modo')=='relacao_observada':
            r=F.resolver_relacao_video(shot,media,dims,adaptativo=True)
            if r.get('layout')!='recorte_relacional_seguro':return None
            return {'4:5':round(1350/1920,4),'1:1':round(1080/1920,4),None:1.0}.get(r.get('documentary_viewport'))
        if shot['video_framing'].get('modo')=='roi_observada':
            F.planejar_enquadramento_video(shot,media,dims)
            return 1.0
    except (ValueError,KeyError,TypeError,AttributeError):return None
    return None
