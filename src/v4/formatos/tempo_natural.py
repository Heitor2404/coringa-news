"""Duração do plano derivada de ÁUDIO REAL, nunca áudio acelerado para caber na foto.

Uso transversal: qualquer formato que tenha cenas de começo/fim em segundos.
O pré-flight final continua exigindo progresso editorial e fonte válida.
"""
from __future__ import annotations
import copy
import math


def retemporizar(plano: dict, duracoes: list[float], pausa: float = .24) -> dict:
    shots=plano.get('shots') or []
    if not shots or len(shots)!=len(duracoes):
        raise ValueError('cada cena precisa de duração real da narração')
    if not 0.08<=pausa<=.7:
        raise ValueError('pausa de respiração inválida')
    out=copy.deepcopy(plano)
    cursor=0.
    for s,d in zip(out['shots'],duracoes):
        if (not isinstance(d,(int,float)) or isinstance(d,bool) or
            not math.isfinite(d) or d<=0):
            raise ValueError('duração de áudio inválida')
        if s.get('type')=='mechanism':
            raise ValueError('simulação causal exige marcações de ação próprias; não acelerar ou retimar automaticamente')
        # áudio toca naturalmente em velocidade 1, com pequena folga final.
        target=max(1.4,math.ceil((d+pausa)*30)/30)
        # Nunca esticar uma foto/legenda além do limite que o fiscal detecta.
        # A solução para voz longa é fragmentar a fala e acrescentar mídia útil.
        if target>3.8:
            raise ValueError(f"{s.get('id')}: voz natural de {d:.2f}s exige {target:.2f}s;"
                             " dividir a fala em mais ações/mídias, NÃO aplicar atempo")
        prev=float(s['end'])-float(s['start'])
        if any(not (0<=float(c['at'])<target) for c in s.get('cues') or []):
            raise ValueError(f"{s.get('id')}: cue fora da duração natural; reescrever storyboard")
        s['start']=round(cursor,3)
        cursor=round(cursor+target,3)
        s['end']=cursor
        s['voice_duration']=round(d,3)
        s['voice_tempo']=1.
        s['retime_from']=round(prev,3)
    out['duracao']=cursor
    out['sincronia_voz']={'metodo':'DURACAO_DE_ARQUIVO_REAL',
                         'tempo_audio':1.0,
                         'pausa_s':pausa,
                         'estetica_aprovada':False}
    return out


def avaliar_destinos(duracao: float, destinos: tuple[str,...] = (
        'tiktok','youtube_shorts','instagram_reels'), config: dict | None = None) -> dict:
    """Metas de FORMATO, não garantia de monetização nem aprovação para publicar.

    Sem teto artístico: uma história de 220 s continua com 220 s no master.
    A distribuição em Shorts é outra decisão, e nunca corta a narrativa
    automaticamente. Os 65 s são meta comercial preferida, NÃO padding.
    """
    import json
    from pathlib import Path

    if (not isinstance(duracao,(int,float)) or isinstance(duracao,bool) or
            not math.isfinite(duracao) or duracao<=0):
        raise ValueError("duração narrativa precisa ser um número positivo")
    if config is None:
        arquivo=Path(__file__).with_name('plataformas.json')
        config=json.loads(arquivo.read_text(encoding='utf8'))['duracao_editorial']
    if not isinstance(destinos,(tuple,list)) or not destinos:
        raise ValueError("informar plataformas de destino")
    conhecidos={'tiktok','youtube_shorts','instagram_reels'}
    if any(x not in conhecidos for x in destinos):
        raise ValueError("plataforma de destino não cadastrada")
    minimo=float(config['requisito_tiktok_creator_rewards_acima_de_s'])
    meta=float(config['piso_preferencial_tiktok_creator_rewards_s'])
    teto_shorts=float(config['youtube_shorts_limite_s'])
    if not (0<minimo<meta<teto_shorts):
        raise ValueError("configuração de duração editorial inválida")
    saidas={}
    for plataforma in dict.fromkeys(destinos):
        if plataforma=='tiktok':
            if duracao<=minimo:
                estado='ABAIXO_MINIMO_CREATOR_REWARDS'
            elif duracao<meta:
                estado='ACIMA_DE_UM_MINUTO_MAS_SEM_MARGEM_PREFERIDA'
            else:
                estado='DURACAO_COMPATIVEL_CREATOR_REWARDS'
            saidas[plataforma]={'estado':estado,'requisito_exclusivo_s':minimo,
                                'meta_nao_obrigatoria_s':meta}
        elif plataforma=='youtube_shorts':
            saidas[plataforma]={
                'estado':'SHORTS_COMPATIVEL' if duracao<=teto_shorts else 'EXIGE_OUTRO_FORMATO_OU_VERSAO',
                'maximo_short_s':teto_shorts}
        else:
            saidas[plataforma]={'estado':'SEM_MINIMO_UNIVERSAL_DE_60S',
                                'nota':'avaliar elegibilidade por recurso/conta, não por duração isolada'}
    return {'duracao_master_s':round(float(duracao),3),
            'duracao_maxima_editorial_s':None,
            'metodo':'HISTORIA_DETERMINA_DURACAO_SEM_PADDING',
            'nao_esticar_nem_cortar_automaticamente':True,
            'destinos':saidas,
            'garante_monetizacao':False}
