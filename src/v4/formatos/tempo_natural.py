"""Duração do plano derivada de ÁUDIO REAL, nunca áudio acelerado para caber na foto.

Uso transversal: qualquer formato que tenha cenas de começo/fim em segundos.
O pré-flight final continua exigindo progresso editorial e fonte válida.
"""
from __future__ import annotations
import copy
import math



def progressao_amostrada(necessidade,candidato,*,inicio=None):
    """Build a private sequence from adjacent, independently reviewed windows.
    This is NOT continuous-action proof. Different referents, gaps or negative
    windows cannot be merged merely to make a longer shot."""
    from . import revisao_documental as R, direcao_eventos as D
    a=candidato.get('aquisicao') or {};sha=a.get('sha256')
    if necessidade.get('evidencia_visual')!='movimento':return None
    rows=[]
    for j in candidato.get('janelas',[]):
        p=j.get('pacote') or {};q=p.get('revisao_assistida') or {}
        if p.get('sha256_origem')!=sha or p.get('fato_id')!=necessidade['fatos'][0] or p.get('necessidade')!=necessidade['mostrar']:continue
        try:
            d=R.decidir(necessidade,candidato,q,tipo='video')
            obs=D.aceitar_observacao(p,q['resposta_observada'])
            if d['estado']!='PERTINENTE_PRIVADO' or not obs['video_framing']:continue
            nomes=set.intersection(*[{e['nome'] for e in pt['elementos']} for pt in obs['video_framing']['pontos']])
            raw=q['resposta_bruta'];idx=raw['indices_mudanca'][1]
            rows.append({'inicio_s':p['inicio_s'],'fim_s':p['inicio_s']+p['duracao_s'],
                         'revisao_id':p['revisao_id'],'referentes':sorted(nomes),
                         'fonte_s':p['amostras'][idx]['fonte_s'],'acao_visivel':raw['descricao_mudanca']})
        except (KeyError,ValueError,TypeError,AttributeError,IndexError):continue
    rows.sort(key=lambda x:x['inicio_s'])
    best=None
    for i,first in enumerate(rows):
        if inicio is not None and abs(first['inicio_s']-inicio)>.001:continue
        group=[first];names=set(first['referentes']);end=first['fim_s']
        for row in rows[i+1:]:
            if row['inicio_s']>end+.001:break
            common=names&set(row['referentes'])
            if not common or row['fim_s']<=end or row['fonte_s']<=group[-1]['fonte_s']:continue
            if row['acao_visivel'].strip().casefold() in {x['acao_visivel'].strip().casefold() for x in group}:continue
            group.append(row);names=common;end=row['fim_s']
        span=math.floor((end-first['inicio_s'])*30+1e-6)/30
        if len(group)<2 or span<=3.8 or not names or any(x['fonte_s']>=first['inicio_s']+span for x in group):continue
        packet={'tipo':'sequencia_amostrada_privada','sha256_origem':sha,'necessidade_id':necessidade['id'],
                'inspecao':'Janelas adjacentes revisadas separadamente, sem inferir ação contínua.',
                'janelas':group,'referentes':sorted(names),'prova_de_acao_continua':False,'publicar':False,
                'inicio_s':first['inicio_s'],'duracao_s':span,
                'eventos':[{'at':x['fonte_s']-first['inicio_s'],'fonte_s':x['fonte_s'],'acao_visivel':x['acao_visivel']} for x in group]}
        if best is None or span>best['duracao_s']:best=packet
    return best


def validar_sequencia_amostrada(cena,duracao,fonte):
    p=cena.get('progressao_visual') or {};sha=p.get('sha256_origem')
    if cena.get('evidence')!='representative' or p.get('publicar') is not False or p.get('prova_de_acao_continua') is not False or not isinstance(sha,str) or len(sha)!=64 or (fonte or {}).get('expected_sha256')!=sha:
        return ['sequência amostrada exige uso representativo privado e SHA da origem']
    ini=cena.get('source_in_seconds');rows=p.get('janelas');events=p.get('eventos')
    if not isinstance(ini,(int,float)) or not math.isfinite(ini) or not isinstance(rows,list) or len(rows)<2 or not isinstance(events,list) or len(events)!=len(rows):return ['sequência sem janelas e eventos vinculados']
    if p.get('inicio_s')!=ini or not isinstance(p.get('duracao_s'),(int,float)) or abs(p['duracao_s']-duracao)>1e-6:return ['sequência amostrada não pode ser retimada']
    refs=p.get('referentes')
    if not isinstance(refs,list) or not all(isinstance(x,str) and x.strip() for x in refs):return ['referentes inválidos']
    names=set(refs);end=ini;prev=-1;ids=set();changes=set()
    if not names:return ['sequência sem referente comum']
    for row,e in zip(rows,events):
        if not isinstance(row,dict) or not isinstance(e,dict):return ['janela inválida']
        a,b,t=[row.get(k) for k in ('inicio_s','fim_s','fonte_s')];rid=row.get('revisao_id')
        if not all(type(x) in (float,int) and math.isfinite(x) for x in (a,b,t)) or not ini-.001<=a<=end+.001 or b<=end or not a<=t<b or t<=prev or t>=ini+duracao or not isinstance(rid,str) or len(rid)!=64 or rid in ids or not isinstance(row.get('referentes'),list) or not all(isinstance(x,str) for x in row['referentes']) or not names<=set(row['referentes']):return ['janelas não adjacentes, sem vínculo ou referente comum']
        change=row.get('acao_visivel')
        if not isinstance(change,str) or len(change.strip())<20 or change.strip().casefold() in changes or e.get('acao_visivel')!=change or e.get('fonte_s')!=t or not isinstance(e.get('at'),(float,int)) or abs(e['at']-(t-ini))>.001:return ['evento não corresponde à observação']
        ids.add(rid);changes.add(change.strip().casefold());prev=t;end=b
    if end<ini+duracao-.001:return ['intervalo não coberto pelas janelas revisadas']
    return []

def validar_progressao_video(cena: dict, duracao: float, fonte: dict | None = None) -> list[str]:
    """Comprovação ESTRUTURAL de ação observada na fonte, não aprovação estética.

    Mais tempo só é justificável quando o mesmo acontecimento se desenvolve:
    anotações com instantes do vídeo original, mudança observável e referência
    de inspeção. Zoom, panorâmica e cartão não contam como ação.
    Sem teto arbitrário de duração: exigir novo evento a cada até 4 segundos.
    O contrato final continua exigindo bytes, SHA, direitos e inspeção humana.
    """
    if duracao<=3.8:
        return []
    problemas=[]
    if cena.get('type')!='video':
        return ['somente vídeo real com ação observável pode ultrapassar 3,8 s']
    p=cena.get('progressao_visual')
    if isinstance(p,dict) and p.get('tipo')=='sequencia_amostrada_privada':
        return validar_sequencia_amostrada(cena,duracao,fonte)
    if not isinstance(p,dict) or p.get('tipo')!='acao_observada':
        return ['falta progressão por ações reais observadas na fonte']
    sha=p.get('sha256_origem')
    if not isinstance(sha,str) or len(sha)!=64 or any(ch not in '0123456789abcdef' for ch in sha):
        problemas.append('progressão exige SHA-256 do original')
    if fonte is not None and fonte.get('expected_sha256') != sha:
        problemas.append('progressão não corresponde ao SHA da mídia da cena')
    if (not isinstance(p.get('inspecao'),str) or
            len(p['inspecao'].strip())<20):
        problemas.append('inspeção de quadros originais precisa ser descrita')
    ini=cena.get('source_in_seconds')
    if not isinstance(ini,(int,float)) or isinstance(ini,bool) or not math.isfinite(ini) or ini<0:
        problemas.append('instante inicial do original ausente')
        ini=None
    eventos=p.get('eventos')
    if not isinstance(eventos,list) or len(eventos)<2:
        return problemas+['ao menos duas ações distintas precisam estar descritas']
    tempos=[]
    for i,e in enumerate(eventos):
        if not isinstance(e,dict):
            problemas.append(f'evento {i+1} inválido')
            continue
        t,orig=e.get('at'),e.get('fonte_s')
        if (not isinstance(t,(int,float)) or isinstance(t,bool) or not math.isfinite(t)
                or not 0<=t<duracao):
            problemas.append(f'evento {i+1} fora da janela de narração')
            continue
        tempos.append(float(t))
        if ini is not None and (not isinstance(orig,(int,float)) or
                isinstance(orig,bool) or not math.isfinite(orig) or
                abs(orig-(ini+t))>.15):
            problemas.append(f'evento {i+1} não corresponde ao instante do original')
        if not isinstance(e.get('acao_visivel'),str) or len(e['acao_visivel'].strip())<12:
            problemas.append(f'evento {i+1} sem mudança física observável')
    if len(tempos)!=len(eventos) or tempos!=sorted(tempos) or len(set(tempos))!=len(tempos):
        problemas.append('eventos precisam ser cronológicos e distintos')
    elif any(b-a>4.0 for a,b in zip([0.0,*tempos],[*tempos,duracao])):
        problemas.append('mais de 4s sem acontecimento visível novo no mesmo clipe')
    if len({str(e.get('acao_visivel') or '').strip().casefold() for e in eventos if isinstance(e,dict)})<2:
        problemas.append('repetição da mesma ação não prova progressão')
    return problemas



def validar_janela_origem(cena: dict, duracao_fonte: float) -> str | None:
    """Verifica que um vídeo não terminará antes do fim da cena.

    A duração vem de ffprobe sobre o original na preparação; valores de
    metadados do roteiro são antecipação, jamais prova de bytes.
    """
    ini=cena.get('source_in_seconds',0)
    fim=cena.get('end')
    comeco=cena.get('start')
    if any(not isinstance(x,(int,float)) or isinstance(x,bool) or
           not math.isfinite(x) for x in (ini,comeco,fim,duracao_fonte)):
        return 'instantes de vídeo ou duração do original inválidos'
    span=fim-comeco
    if ini<0 or span<=0 or duracao_fonte<=0 or ini+span>duracao_fonte+.04:
        return (f'origem de {duracao_fonte:.2f}s não cobre recorte '
                f'{ini:.2f}s–{ini+span:.2f}s; risco de imagem preta no final')
    return None


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
            # Vídeos com ação REAL podem respirar no ritmo do acontecimento.
            # Fotos e vídeos sem mudanças observadas continuam curtos.
            problemas=validar_progressao_video(
                s,target,(out.get('media') or {}).get(s.get('asset'))
            )
            if problemas:
                raise ValueError(f"{s.get('id')}: voz natural de {d:.2f}s exige {target:.2f}s; "
                                 + "; ".join(problemas) +
                                 "; não acelerar narração ou prolongar imagem parada")
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
