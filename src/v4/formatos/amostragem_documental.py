"""Distributed local sampling for the existing documentary video reviewer.
Bounded work, no new AI dependency, no assertion of semantic coverage.
"""
import math
from PIL import ImageStat
from . import direcao_eventos as DE

def explorar(midia,extrair,*,max_janelas=12,largura=240):
    dur=midia['duration_s']
    if not isinstance(dur,(int,float)) or not math.isfinite(dur) or dur<1.55:raise ValueError('E257-DURACAO')
    if not 3<=max_janelas<=24:raise ValueError('E257-LIMITE')
    span=min(3.8,dur-.15)
    end=max(0,dur-span-.05)
    count=1 if end<.5 else min(max_janelas,max(1,math.ceil(end/max(span*.65,1))+1))
    starts=[end*i/max(1,count-1) for i in range(count)]
    rows=[]
    for a in starts:
        try:
            frames=[extrair(midia['local_source'],a+span*f,width=largura) for f in (0,.5,.9)]
            diag=DE.diagnosticar_janela(frames)
            # Difference is a hint, not semantic motion (camera and cuts may dominate).
            from PIL import ImageChops
            diffs=[ImageStat.Stat(ImageChops.difference(x.convert('RGB'),y.convert('RGB'))).mean for x,y in zip(frames,frames[1:])]
            change=sum(sum(d)/3 for d in diffs)/max(1,len(diffs))
            contrast=min(ImageStat.Stat(im.convert('L')).stddev[0] for im in frames)
            rows.append({'inicio_s':a,'duracao_s':span,'diagnostico':diag,
                         'mudanca_px':round(change,3),'contraste_min':round(contrast,3)})
        except Exception as e:
            rows.append({'inicio_s':a,'duracao_s':span,'falha':type(e).__name__})
    return {'duracao_origem_s':dur,'janelas':rows,'amostragem_distribuida':True,
            'cobertura_semantica_integral':False,'publicar':False}

def selecionar(exploracao,*,limite=3,priorizar_movimento=False):
    rows=[x for x in exploracao['janelas'] if 'diagnostico' in x]
    if not rows:return []
    # Prefer one candidate per temporal region, not three nearby early windows.
    # Dark/quiet real footage remains eligible; motion is only a ranking hint.
    def rank(r):
        return (r['diagnostico']['quadros_grafismo_suspeito'],
                r['contraste_min']<5,
                -r['mudanca_px'] if priorizar_movimento else -r['contraste_min'])
    result=[]
    dur=exploracao['duracao_origem_s']
    for j in range(limite):
        region=[r for r in rows if min(limite-1,int((r['inicio_s']+r['duracao_s']/2)/dur*limite))==j]
        if region:result.append(min(region,key=rank))
    for r in sorted(rows,key=rank):
        if len(result)>=limite:break
        if r not in result:result.append(r)
    return sorted(result,key=lambda r:r['inicio_s'])

def preparar_lote(midia,necessidade,extrair,*,exploracao=None,excluir=()):
    exploration=exploracao if exploracao is not None else explorar(midia,extrair)
    remaining={**exploration,'janelas':[x for x in exploration['janelas'] if round(x['inicio_s'],4) not in excluir]}
    selected=selecionar(remaining,priorizar_movimento=necessidade.get('evidencia_visual')=='movimento')
    windows=[]
    for x in selected:
        a=x['inicio_s'];span=x['duracao_s']
        try:
            frames=[extrair(midia['local_source'],a+span*f,width=min(768,midia['width'])) for f in (0,.5,.9)]
            p=DE.pacote_observacao(midia,a,span,frames,fato_id=necessidade['fatos'][0],
                necessidade=necessidade['mostrar'],fracoes=(0,.5,.9))
            p['diagnostico_tecnico']=DE.diagnosticar_janela(frames)
            windows.append((p,frames))
        except Exception as e:
            x['falha_amostra_visao']=type(e).__name__
    exploration['selecionadas_s']=[p['inicio_s'] for p,_ in windows]
    return exploration,windows
