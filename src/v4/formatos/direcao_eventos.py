"""Direção de cena por ACONTECIMENTO, não por título ou nome do tema.

O roteiro explicita objetivo, fato, evidência. O diretor escolhe tipo de cena
compatível com o que consegue provar, sem fazer mapa estático representar ação,
ou foto de outro episódio virar vídeo do evento. Regras genéricas para qualquer
assunto; o tipo semântico nunca contém nomes de países/guerras.
"""
from __future__ import annotations

INTENCOES={
    'localizar':('atlas_map',),
    'trajeto':('atlas_map',),
    'mostrar_registro':('photo','video'),
    'demonstrar_acao':('video','mechanism'),
    'comparar':('comparison',),
    'explicar_contexto':('photo','video'),
    'concluir':('video','comparison','photo','mechanism'),
}


def verificar(cenas: list[dict]) -> list[dict]:
    falhas=[]
    vistos=set()
    for c in cenas:
        d=c.get('direcao_evento')
        if d is None:
            continue  # legado preservado: migrar planos conscientemente
        cid=c.get('id') or '?'
        if not isinstance(d,dict) or d.get('intencao') not in INTENCOES:
            falhas.append({'codigo':'D-INTENCAO','cena':cid,
                           'motivo':'intenção visual não reconhecida'})
            continue
        intencao=d['intencao']
        fato=d.get('fato_id')
        if not isinstance(fato,str) or not fato.strip():
            falhas.append({'codigo':'D-SEM-FATO','cena':cid,
                           'motivo':'cada plano precisa de fato distinto do roteiro'})
        elif fato in vistos and not d.get('revisita_justificada'):
            falhas.append({'codigo':'D-FATO-REPETIDO','cena':cid,
                           'motivo':'mesma promessa visual repetida sem nova informação'})
        vistos.add(fato)
        if c.get('type') not in INTENCOES[intencao]:
            falhas.append({'codigo':'D-RECURSO-INCOMPATIVEL','cena':cid,
                           'motivo':f"{intencao} não pode ser demonstrado por {c.get('type')}"})
        if intencao in ('localizar','trajeto'):
            if c.get('type')!='atlas_map':
                falhas.append({'codigo':'D-EXIGE-CARTOGRAFIA-ATLAS','cena':cid,
                               'motivo':'localização/trajeto só usam clipe autenticado do PalcoMapa MapLibre'})
            mapa=(c.get('atlas_direcao') or {})
            if not isinstance(mapa,dict) or mapa.get('intencao')!=intencao or not mapa.get('roi'):
                falhas.append({'codigo':'D-MAPA-SEM-OBJETIVO','cena':cid,
                               'motivo':'a intenção e a região do mapa ATLAS devem ser explícitas no roteiro'})
        if intencao=='mostrar_registro' and c.get('evidence')!='literal':
            falhas.append({'codigo':'D-REGISTRO-SEM-PROVA','cena':cid,
                           'motivo':'imagem genérica não pode comprovar evento específico'})
        if intencao=='demonstrar_acao' and c.get('type')=='video':
            if not d.get('acao_capturada'):
                falhas.append({'codigo':'D-ACAO-NAO-VERIFICADA','cena':cid,
                               'motivo':'vídeo só representa ação após checagem por frames reais'})
        if not isinstance(d.get('aprendizado'),str) or len(d['aprendizado'].strip())<10:
            falhas.append({'codigo':'D-SEM-APRENDIZADO','cena':cid,
                           'motivo':'resultado visível esperado não definido'})
    return falhas


def aproximacao_geografica(plano:dict, *, zoom_desejado=.75)->tuple[dict,dict]:
    """Private single-beat geographic entrance using native ATLAS camera.
    No invented camera pose; retains final ROI and respects raster coverage
    and resolution at EVERY sampled instant. Does not assert a matched shot.
    """
    import copy,math
    from src.v4.formatos import plano as A
    if plano.get('formato')!='atlas' or plano.get('_resolvido') is not True:
        raise ValueError('D-IMERSAO-PLANO')
    if len(plano.get('palco',[]))!=1 or plano['palco'][0].get('tipo')!='mapa':
        raise ValueError('D-IMERSAO-BEAT')
    if not .2<=zoom_desejado<=1.2:
        raise ValueError('D-IMERSAO-ZOOM')
    duration=float(plano['duracao'])
    if not 1.4<=duration<=8:raise ValueError('D-IMERSAO-TEMPO')
    p=copy.deepcopy(plano)
    k=p['palco'][0]
    end=float(k['camera']['zoom'])
    roi=k.get('roi') or p['beats'][0]['roi']
    bases=[(r,A.raster_info(r['nome'])) for r in p.get('rasters',[])]
    # Full-resolution final framing is the original approved ROI, not
    # a post-render magnification of pixels or a larger artificial zoom.
    def covered(t):
        c=A.camera_em(p['palco'],t)
        return any(A.cobre(m,roi) and A.cobre(m,A.tela_lonlat(c))
                   and m['nitido_ate']>=c['zoom']-1e-6
                   and A.opacidade_raster(c['zoom'],r.get('de'),r.get('ate'))>.02
                   for r,m in bases)
    for delta in [round(zoom_desejado-i*.05,3) for i in range(25)]:
        if delta<.2:break
        if end-delta<A.Z_MIN:continue
        k['camera']['zoom']=end-delta
        k['movimento']='aproxima'
        k['dur_camera']=0
        k['dur_deriva']=duration
        k['deriva']=delta/duration
        k['zoom_teto']=end
        if all(covered(i*duration/60) for i in range(61)):
            errors=[v for v in A.validar(p) if v['gravidade']=='erro']
            if not errors:
                return p,{'modo':'aproximacao_regional','zoom_inicio':end-delta,'zoom_fim':end,
                          'escala':2**delta,'amostras_camera':61,'roi':roi,
                          'continuidade_optica':False,'revisao_visual':'PENDENTE'}
    raise ValueError('D-IMERSAO-SEM-BASE: manter mapa normal, sem ampliar artificialmente')


def assinatura_janela(frames):
    """Cheap perceptual features, NOT semantic object detection.
    Preserve both luminance structure and color distribution across samples.
    """
    import numpy as np
    from PIL import Image
    if len(frames)<2:raise ValueError('D-JANELA-AMOSTRAS')
    out=[]
    for im in frames:
        rgb=np.asarray(im.convert('RGB').resize((48,48),Image.Resampling.BILINEAR),dtype=float)
        gray=np.asarray(im.convert('L').resize((9,8),Image.Resampling.BILINEAR),dtype=float)
        bits=(gray[:,1:]>gray[:,:-1]).ravel()
        hist=np.concatenate([np.histogram(rgb[:,:,i],bins=8,range=(0,256))[0]/2304 for i in range(3)])
        out.append((bits,hist))
    return out


def similaridade_janelas(a,b):
    """Max over actual sample pairs: flags repeats, does not prove identical event."""
    import numpy as np
    if not a or not b:return 0.
    return max(.60*(1-float(np.mean(x!=y)))+.40*(1-float(np.abs(h-j).sum())/6)
               for x,h in a for y,j in b)


def ordenar_janelas(candidatos, historico):
    """Rank ONLY eligible candidates of the SAME editorial obligation.
    Relevance/license/window validation remains upstream. No forced substitution
    by a visually different but irrelevant event. No hard rejection threshold.
    """
    def rank(c):
        sim=max((similaridade_janelas(c['assinatura'],h) for h in historico),default=0.)
        return (sim, c['ordem'])
    return sorted(candidatos,key=rank)


def enquadrar_observacoes(cena,midia,observacoes):
    """Adapt the existing ROI resolver to explicitly reviewed source samples.
    An observer (human/model) must supply real essential regions; no saliency
    guess, no invented observations and no production approval.
    """
    from src.v4.formatos import filme_editorial as F
    if observacoes.get('sha256_origem')!=midia.get('expected_sha256'):
        raise ValueError('D-OBS-SHA')
    if observacoes.get('modo')!='relacao_observada':
        raise ValueError('D-OBS-MODO')
    return F.resolver_relacao_video({**cena,'video_framing':observacoes},midia,
        (midia['width'],midia['height']),adaptativo=True)
