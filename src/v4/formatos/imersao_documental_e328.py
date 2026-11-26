"""E328: prioritise real coverage weaknesses, not decorative motion or quotas.
Pre-render estimates only; actual browser geometry remains a separate QA.
"""
def diagnosticar(plan,rows):
    shots=plan['shots'];out=[];prev=None;repeated=0.;low=0.
    for s,r in zip(shots,rows,strict=True):
        span=r['end']-r['start'];m=plan.get('media',{}).get(s.get('asset'),{})
        digest=m.get('expected_sha256') or s.get('asset')
        fraction=r['integral_canvas_fraction'];tasks=[]
        if r['kind'] in ('video','photo') and fraction is not None and fraction<.28:
            low+=span
            tasks.append('BUSCAR_ANGULO_VERTICAL_OU_COMPLEMENTO_REAL')
        if r['kind']=='video' and not s.get('video_framing'):
            tasks.append('REVISAR_REGIAO_DE_ACAO_ANTES_DE_RECORTAR')
        if digest and digest==prev and r['kind']=='video':
            repeated+=span;tasks.append('REVISAR_VARIACAO_NARRATIVA_MESMA_FONTE')
        if s is shots[0]:
            tasks.append('CONFERIR_EVIDENCIA_DO_GANCHO')
        if tasks:
            out.append({'id':s['id'],'fatos':r['fatos'],'mostrar':r['mostrar'],
                'integral_canvas_fraction':fraction,'tarefas':tasks,'publicar':False})
        prev=digest
    return {'schema':'coringa.immersion.triage.v1','low_integral_fraction_s':round(low,3),
        'adjacent_same_source_video_s':round(repeated,3),'tasks':out,'publish':False,
        'actual_render_verified':False,'editorial_approval':False}
