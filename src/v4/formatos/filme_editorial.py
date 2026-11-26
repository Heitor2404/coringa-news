"""Pré-produção do FILME EDITORIAL: mídia ocupa o plano, não slides/cartões ATLAS.

Motor-piloto isolado. Recebe briefing com evidências e cortes editorialmente
escolhidos, valida coerência e prepara props do Remotion FilmeEditorial.
A aprovação estética depende de INSPECIONAR o vídeo, nunca da contagem de testes.
Sem rede ao validar; baixar só em CLI dedicada, de fontes já licenciadas.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit
from PIL import Image

LICENCAS = {'CC BY 2.0', 'CC BY 3.0', 'CC BY 4.0', 'CC BY-SA 2.0', 'CC BY-SA 3.0', 'CC BY-SA 4.0', 'CC0', 'NASA PD', 'Public domain', 'Natural Earth PD'}
ORIGENS = {'upload.wikimedia.org', 'thumb.wikimedia.org'}
MIN_VIDEO_COMPOSITION_PX = 700  # existing compositor threshold; review separately with real visual evidence
TIPOS = {'photo', 'video', 'comparison', 'mechanism', 'atlas_map'}


def recibo_documental_valido(asset:dict)->bool:
    """Structural binding for private, already acquired provider bytes.

    Provider declarations are not commercial approval. No new remote hosts
    are enabled by this bridge; the acquisition adapter owns transport.
    """
    def valid_sha(x):
        return isinstance(x,str) and bool(re.fullmatch(r'[0-9a-f]{64}',x))
    def exact(url,host,path=None):
        if not isinstance(url,str):return False
        try:
            u=urlsplit(url)
            return (u.scheme=='https' and u.hostname==host and not u.username
                    and not u.password and u.port in (None,443)
                    and (path is None or u.path==path) and not u.fragment)
        except ValueError:return False
    d=asset.get('documentary_receipt')
    if not isinstance(d,dict) or asset.get('rights_status')!='REVIEW_PENDING' or d.get('publicar') is not False or d.get('direitos_aprovados') is not False:return False
    if not valid_sha(asset.get('expected_sha256')) or d.get('sha256_origem')!=asset['expected_sha256']:return False
    receipt=d.get('recibo');url=d.get('url_adquirida')
    if not isinstance(receipt,dict) or receipt.get('direitos')!='PENDENTE_AUDITORIA_INDIVIDUAL':return False
    if d.get('provedor') in ('nasa','nasa_video'):
        nid=receipt.get('nasa_id')
        if not isinstance(nid,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',nid):return False
        rows=receipt.get('variantes_declaradas')
        return (asset.get('license')=='REVIEW_PENDING' and valid_sha(receipt.get('asset_response_sha256'))
                and exact(asset.get('page'),'images.nasa.gov','/details/'+nid)
                and exact(url,'images-assets.nasa.gov')
                and isinstance(rows,list) and any(isinstance(row,dict) and row.get('href_https')==url for row in rows))
    if d.get('provedor')=='usgs_pagina':
        kind=receipt.get('tipo');page=receipt.get('pagina')
        role='videos' if kind=='video' else 'images' if kind=='foto' else None
        if not role or not isinstance(page,str) or not re.fullmatch(r'https://www\.usgs\.gov/media/'+role+r'/[a-z0-9-]+',page):return False
        hosts={'usgs-ocapsv2-public-input-media.s3.us-west-2.amazonaws.com','www.usgs.gov','prd-wret.s3.us-west-2.amazonaws.com'} if kind=='video' else {'d9-wret.s3.us-west-2.amazonaws.com','prd-wret.s3.us-west-2.amazonaws.com'}
        rows=receipt.get('variantes')
        return (page==asset.get('page') and valid_sha(receipt.get('page_sha256')) and asset.get('license')=='Public domain'
                and receipt.get('licenca_declarada')=='Public Domain' and receipt.get('credito_curado')==asset.get('credit')
                and bool(asset.get('credit')) and (asset.get('media_type') is None or asset.get('media_type')==('video' if kind=='video' else 'photo'))
                and type(d.get('bytes')) is int and d['bytes']>0 and any(exact(url,h) for h in hosts)
                and isinstance(rows,list) and any(isinstance(row,dict) and row.get('url')==url for row in rows))
    if d.get('provedor')=='archive_video':
        ident=receipt.get('identifier')
        if not isinstance(ident,str) or ident in ('.','..') or not re.fullmatch(r'[A-Za-z0-9_.-]{1,150}',ident):return False
        licenses={'https://creativecommons.org/licenses/by/4.0':'CC BY 4.0',
                  'https://creativecommons.org/publicdomain/zero/1.0':'CC0',
                  'https://creativecommons.org/publicdomain/mark/1.0':'Public domain'}
        if not valid_sha(receipt.get('metadata_sha256')) or licenses.get(receipt.get('licenca_url'))!=asset.get('license') or not exact(asset.get('page'),'archive.org','/details/'+ident):return False
        try:host=urlsplit(url).hostname
        except (ValueError,TypeError,AttributeError):return False
        if not isinstance(host,str) or not re.fullmatch(r'ia[0-9]+(?:\.us)?\.archive\.org',host) or not exact(url,host):return False
        rows=receipt.get('variantes')
        return isinstance(rows,list) and any(isinstance(row,dict) and row.get('url')==url
            and type(row.get('size')) is int and row['size']==d.get('bytes') and row['size']>0
            and isinstance(row.get('md5'),str) and bool(re.fullmatch(r'[0-9a-f]{32}',row['md5']))
            for row in rows)
    return False


def propor_recorte_foto(cena, midia, dimensoes):
    """Private alternative only: geometry from a direct observation bound to the
    actual image. It does not certify semantics, context or publication.
    Keep the complete original if the observed region and surrounding margin
    cannot fit, or if the crop would cover that region with text.
    """
    import math
    r=cena.get('photo_roi_candidate')
    if not isinstance(r,dict) or r.get('sha256')!=midia.get('expected_sha256') or not r.get('revisao_id'):
        return None
    if r.get('escala_origem') not in ('xy_0_1','xy_0_1000'):
        return None
    b=r.get('bbox')
    if not isinstance(b,list) or len(b)!=4 or any(type(x) not in (int,float) or not math.isfinite(x) for x in b):
        return None
    x0,y0,x1,y1=b
    w,h=dimensoes
    if not (0<=x0<x1<=1 and 0<=y0<y1<=1 and min(w,h)>=600 and w/h>1.15):
        return None
    # Keep at least 12% of the observed region on each side where the source allows.
    a0,a1=max(0,x0-.12*(x1-x0)),min(1,x1+.12*(x1-x0))
    b0,b1=max(0,y0-.12*(y1-y0)),min(1,y1+.12*(y1-y0))
    for height in (1350,1080):
        scale=max(1080/w,height/h)
        vw,vh=min(1.,1080/(w*scale)),min(1.,height/(h*scale))
        if a1-a0>vw+1e-9 or b1-b0>vh+1e-9:continue
        left=max(0,min(1-vw,(a0+a1-vw)/2))
        top=max(0,min(1-vh,(b0+b1-vh)/2))
        if not (left<=a0+1e-9 and left+vw>=a1-1e-9 and top<=b0+1e-9 and top+vh>=b1-1e-9):
            continue
        # Keep caption/credit lane clear of the *essential* area. Do not invent
        # a new UI-safe text position or silently shrink the source.
        screen=[(x0-left)/vw*1080,(y0-top)/vh*height,(x1-left)/vw*1080,(y1-top)/vh*height]
        if screen[3]>1020 and screen[0]<760 and screen[2]>160:continue
        if screen[1]<405 and screen[3]>300 and screen[0]<760 and screen[2]>150:continue
        return {'height':height,'position':[.5 if vw>=1 else left/(1-vw),.5 if vh>=1 else top/(1-vh)],
                'status':'PRIVATE_CANDIDATE_REVIEW_PENDING','essential_screen':screen,'revisao_id':r['revisao_id']}
    return None


def planejar_enquadramento_video(cena: dict, midia: dict, dimensoes: tuple[int,int], *, viewport: tuple[int,int]=(1080,1920)) -> list[dict]:
    """Converte ROIs inspecionadas em posições CSS de object-fit:cover para 9:16.

    Não detecta pessoas/objetos automaticamente. Confere matematicamente que a
    região declarada cabe no recorte final (com margem), sem 'fundo desfocado'.
    A inspeção dos quadros e a revisão do vídeo renderizado permanecem humanas.
    """
    import math
    contrato=cena.get('video_framing')
    if not isinstance(contrato,dict) or contrato.get('modo')!='roi_observada':
        raise ValueError('F-ROI-CONTRATO: enquadramento exige modo roi_observada')
    if cena.get('type')!='video':
        raise ValueError('F-ROI-TIPO: enquadramento dirigido só aceita vídeo')
    if abs(float(cena.get('video_zoom') or 1)-1)>1e-6:
        raise ValueError('F-ROI-ZOOM: zoom adicional invalida a garantia de visibilidade')
    sha=contrato.get('sha256_origem')
    if not isinstance(sha,str) or len(sha)!=64 or any(x not in '0123456789abcdef' for x in sha):
        raise ValueError('F-ROI-SHA: SHA original inválido')
    if midia.get('expected_sha256')!=sha:
        raise ValueError('F-ROI-SHA: enquadramento de outra fonte')
    inspecao=contrato.get('inspecao')
    if not isinstance(inspecao,str) or len(inspecao.strip())<24:
        raise ValueError('F-ROI-INSPECAO: informar inspeção de quadros reais do original')
    w,h=dimensoes
    if (not isinstance(w,int) or not isinstance(h,int) or isinstance(w,bool)
            or isinstance(h,bool) or min(w,h)<240):
        raise ValueError('F-ROI-DIMENSOES: dimensões da fonte inválidas')
    if viewport not in ((1080,1920),(1080,1350),(1080,1080)):
        raise ValueError('F-ROI-VIEWPORT: proporção não registrada')
    dw,dh=viewport
    escala=max(dw/w,dh/h)
    vw=min(1.0,dw/(escala*w))
    vh=min(1.0,dh/(escala*h))
    margem_x=vw*.03 if vw<.999999 else 0.0
    margem_y=vh*.03 if vh<.999999 else 0.0
    pontos=contrato.get('pontos')
    if not isinstance(pontos,list) or not pontos:
        raise ValueError('F-ROI-PONTOS: enquadramento sem referências visuais')
    inicio=cena.get('source_in_seconds',0)
    dur=float(cena.get('end',0))-float(cena.get('start',0))
    if (not isinstance(inicio,(int,float)) or isinstance(inicio,bool) or
            not math.isfinite(inicio) or inicio<0 or dur<=0 or not math.isfinite(dur)):
        raise ValueError('F-ROI-TEMPO: corte de origem inválido')
    resultado=[]
    ultimo=-1.0
    for indice,p in enumerate(pontos):
        if not isinstance(p,dict):
            raise ValueError(f'F-ROI-PONTO: posição {indice+1} inválida')
        t,fonte_s=p.get('at'),p.get('fonte_s')
        if (not isinstance(t,(int,float)) or isinstance(t,bool) or
                not math.isfinite(t) or not 0<=t<dur or t<=ultimo):
            raise ValueError(f'F-ROI-TEMPO: ponto {indice+1} fora de ordem')
        ultimo=float(t)
        if (not isinstance(fonte_s,(int,float)) or isinstance(fonte_s,bool) or
                not math.isfinite(fonte_s) or abs(fonte_s-(inicio+t))>.12):
            raise ValueError(f'F-ROI-FONTE: ponto {indice+1} não coincide com o original')
        box=p.get('area_essencial')
        if (not isinstance(box,list) or len(box)!=4 or
                any(not isinstance(v,(int,float)) or isinstance(v,bool) or
                    not math.isfinite(v) for v in box)):
            raise ValueError(f'F-ROI-AREA: ponto {indice+1} sem bbox normalizada')
        x0,y0,x1,y1=box
        if not (0<=x0<x1<=1 and 0<=y0<y1<=1):
            raise ValueError(f'F-ROI-AREA: ponto {indice+1} fora do original')
        if x1-x0+2*margem_x>vw+1e-9 or y1-y0+2*margem_y>vh+1e-9:
            raise ValueError(
                f'F-ROI-NAO-CABE: área essencial de ponto {indice+1} não cabe em 9:16; '
                'selecionar outra tomada ou composição em vez de cortar a ação'
            )
        def pos(a,b,vis,margem):
            if vis>=.999999:
                return .5
            minimo=max(0.0,b+margem-vis)
            maximo=min(1.0-vis,a-margem)
            if minimo>maximo+1e-9:
                raise ValueError('F-ROI-NAO-CABE: margem da área essencial inviável')
            ideal=(a+b-vis)/2
            esquerda=max(minimo,min(ideal,maximo))
            return min(1.0,max(0.0,esquerda/(1-vis)))
        px=pos(x0,x1,vw,margem_x)
        py=pos(y0,y1,vh,margem_y)
        resultado.append({'at':round(float(t),4),
                          'position':[round(px,6),round(py,6)]})
    if abs(resultado[0]['at'])>.001:
        raise ValueError('F-ROI-PRIMEIRO: enquadramento deve cobrir o início da tomada')
    return resultado



def resolver_relacao_video(cena:dict, midia:dict, dimensoes:tuple[int,int], *, adaptativo:bool=False)->dict:
    """Determina apresentação de um clipe REAL com 1+ referentes observados.

    Se todas as regiões essenciais cabem JUNTAS no 9:16, recorta com câmera
    dirigida. Senão, preserva a filmagem inteira em faixa panorâmica.
    Não esconder metade de uma relação (pessoa+máquina) em zoom 9:16.
    A decisão é geométrica e ainda exige inspeção do MP4 renderizado.
    """
    import math
    d=cena.get('video_framing') or {}
    if d.get('modo')!='relacao_observada':
        raise ValueError('F-RELACAO-CONTRATO: referências de objetos ausentes')
    if d.get('sha256_origem')!=midia.get('expected_sha256'):
        raise ValueError('F-RELACAO-SHA: anotação não pertence a este original')
    if not isinstance(d.get('inspecao'),str) or len(d['inspecao'].strip())<35:
        raise ValueError('F-RELACAO-INSPECAO: falta análise da sequência original')
    w,h=dimensoes
    if (not isinstance(w,int) or not isinstance(h,int)
        or min(w,h)<MIN_VIDEO_COMPOSITION_PX or w<h):
        raise ValueError('F-RELACAO-DIMENSOES: modo panorâmico exige origem real de boa resolução')
    points=d.get('pontos')
    if not isinstance(points,list) or len(points)<2:
        raise ValueError('F-RELACAO-PONTOS: revisar vários quadros originais')
    span=cena['end']-cena['start']
    origin=cena.get('source_in_seconds')
    if (not isinstance(origin,(int,float)) or not math.isfinite(origin) or
        origin<0 or span<=0):
        raise ValueError('F-RELACAO-TEMPO: janela de origem inválida')
    union=[]
    last=-1
    for item in points:
        if not isinstance(item,dict):
            raise ValueError('F-RELACAO-ITEM: ponto inválido')
        at=item.get('at')
        fonte=item.get('fonte_s')
        if (not isinstance(at,(int,float)) or not isinstance(fonte,(int,float))
            or not math.isfinite(at) or not math.isfinite(fonte)
            or at<=last or at<0 or at>=span or abs(fonte-(origin+at))>.12):
            raise ValueError('F-RELACAO-TEMPO: anotação e original não correspondem')
        last=at
        elems=item.get('elementos')
        if not isinstance(elems,list) or not elems:
            raise ValueError('F-RELACAO-ELEMENTOS: referente ausente')
        bbs=[]
        nomes=set()
        for e in elems:
            if not isinstance(e,dict) or not isinstance(e.get('nome'),str):
                raise ValueError('F-RELACAO-ELEMENTOS: rótulo obrigatório')
            nome=e['nome'].strip()
            box=e.get('bbox')
            if (not nome or nome in nomes or not isinstance(box,list)
                or len(box)!=4 or any(
                    not isinstance(n,(int,float)) or not math.isfinite(n) for n in box)
                or not 0<=box[0]<box[2]<=1 or not 0<=box[1]<box[3]<=1):
                raise ValueError('F-RELACAO-ELEMENTOS: bbox/nome inválido')
            nomes.add(nome)
            bbs.append(box)
        union.append({
            'at':at,'fonte_s':fonte,
            'area_essencial':[
                min(b[0] for b in bbs),min(b[1] for b in bbs),
                max(b[2] for b in bbs),max(b[3] for b in bbs),
            ]})
    roi={**cena,'video_framing':{
        'modo':'roi_observada','sha256_origem':d['sha256_origem'],
        'inspecao':d['inspecao'],'pontos':union,
    }}
    try:
        positions=planejar_enquadramento_video(roi,midia,dimensoes)
        return {'layout':'recorte_relacional_seguro',
                'framing_positions':positions,
                'elementos_protegidos':sorted({e['nome'] for x in points
                                               for e in x['elementos']})}
    except ValueError as exc:
        if not str(exc).startswith('F-ROI-NAO-CABE'):
            raise
        if adaptativo:
            for viewport,ratio in (((1080,1350),'4:5'),((1080,1080),'1:1')):
                try:
                    positions=planejar_enquadramento_video(roi,midia,dimensoes,viewport=viewport)
                    return {'layout':'recorte_relacional_seguro','documentary_viewport':ratio,
                            'framing_positions':positions,
                            'elementos_protegidos':sorted({e['nome'] for x in points for e in x['elementos']})}
                except ValueError as err:
                    if not str(err).startswith('F-ROI-NAO-CABE'):raise
        return {'layout':'cena_integral',
                'framing_positions':[],
                'motivo':'referentes separados fisicamente; recorte vertical/intermediário não comprovado',
                'elementos_protegidos':sorted({e['nome'] for x in points
                                               for e in x['elementos']})}




def proteger_fonte_integral(cena:dict, midia:dict, dimensoes:tuple[int,int])->str:
    """Quando a origem traz uma relação física, exibir a fonte INTEIRA
    é mais honesto do que supor que o centro contém todas as etapas.
    Especialmente câmeras quadradas de missões e processos industriais.
    """
    meta=cena.get('video_framing') or {}
    if meta.get('modo')!='fonte_integral':
        raise ValueError('F-ROI-CONTRATO: fonte integral exige declaração específica')
    if meta.get('sha256_origem')!=midia.get('expected_sha256'):
        raise ValueError('F-ROI-SHA: enquadramento de outra mídia')
    if (not isinstance(meta.get('inspecao'),str) or len(meta['inspecao'])<35
        or not isinstance(meta.get('motivo'),str) or len(meta['motivo'])<25):
        raise ValueError('F-ROI-INSPECAO: fonte integral precisa de motivo factual')
    if abs(float(cena.get('video_zoom') or 1)-1)>1e-6:
        raise ValueError('F-ROI-ZOOM: preservar fonte sem zoom')
    w,h=dimensoes
    if (not isinstance(w,int) or isinstance(w,bool)
        or not isinstance(h,int) or isinstance(h,bool)
        or min(w,h)<500):
        raise ValueError('F-ROI-DIMENSOES: dimensões da fonte insuficientes')
    return 'quadro_integral' if .75<=w/h<=1.25 else 'cena_integral'



def avaliar(plano: dict, *, fragmento_misto=False) -> dict:
    # Mesmo preflight para storyboard manual ou gerado do evento:
    # autor/editor não precisam nomear mecanismo nem inventar tempos dos cues.
    from src.v4.formatos import diretor_processos, diretor_roteiro
    erro_roteiro = None
    erro_diretor = None
    try:
        plano = diretor_roteiro.expandir_preview(plano)
        plano = diretor_processos.expandir(plano)
    except diretor_roteiro.RoteiroBloqueado as exc:
        erro_roteiro = exc
        plano = {**plano, 'shots': []}
    except diretor_processos.FalhaDiretor as exc:
        erro_diretor = exc
        plano = {**plano, 'shots': []}
    falhas = []
    def falha(cod: str, onde: str, porque: str):
        falhas.append({'codigo': cod, 'cena': onde, 'motivo': porque})
    if erro_diretor is not None:
        falha(erro_diretor.codigo, erro_diretor.cena, erro_diretor.motivo)
    if erro_roteiro is not None:
        for pendencia in erro_roteiro.relatorio['bloqueios']:
            falha(pendencia['codigo'], pendencia['cena'], pendencia['motivo'])
    cenas = plano.get('shots') or []
    area_segura=None
    from src.v4.formatos import qa_area_segura
    privado=plano.get('tipo')=='PROVA_VISUAL_PRIVADA'
    if not privado and plano.get('safe_area_profile')!=qa_area_segura.PERFIL:
        falha('F-SAFE-SEM-PERFIL','-',
              'filme final deve declarar o perfil multiplaforma e passar na inspeção de zonas')
    if plano.get('safe_area_profile') is not None:
        area_segura=qa_area_segura.auditar_plano(plano)
        for erro in area_segura['bloqueios']:
            falha('F-'+erro['codigo'],erro['cena'],erro['motivo'])
    if fragmento_misto and not (privado and plano.get('publicar') is False):
        falha('F-FRAGMENTO-PRIVADO','-','preflight de fragmento misto só em revisão privada')
    if not cenas:
        falha('F-SEM-HISTORIA', '-', 'não há cenas')
    if plano.get('tipo') != 'PROVA_VISUAL_PRIVADA':
        # Nenhuma amostra Edge, mesmo "em tempo natural", entra na produção.
        # Preset do canal é a fonte única; nunca fallback silencioso.
        from src.v4.formatos import plano as plano_atlas
        preset = (plano_atlas.canal('coringa').get('narrador') or {})
        voz = plano.get('narrador') or {}
        if (preset.get('motor') != 'gemini' or preset.get('fallback') != 'bloquear'
                or voz.get('motor') != preset.get('motor')
                or voz.get('voz') != preset.get('voz')
                or voz.get('fallback') != 'bloquear'
                or not isinstance(voz.get('sha256_voz'), str)
                or len(voz.get('sha256_voz')) != 64):
            falha('F-VOZ-TESTE-EM-PRODUCAO', '-',
                  'FILME final exige voz Gemini do preset do canal com SHA e fallback bloqueado; Edge só é aceito em PROVA_VISUAL_PRIVADA')
        if voz.get('aprovacao_humana') is not True:
            falha('F-VOZ-SEM-APROVACAO', '-',
                  'narração final precisa de conferência auditiva humana, nunca inferida pelos testes')
    # O contrato de pré-produção é opcional SOMENTE para provas técnicas privadas.
    # Um filme documental de produção não pode passar só pelo fiscal de shots:
    # é preciso provar que a mídia prevista para cada acontecimento existe.
    if plano.get('tipo') != 'PROVA_VISUAL_PRIVADA':
        contrato = plano.get('contrato_integral')
        if not isinstance(contrato, dict):
            falha('F-PORTAO-INTEGRAL-AUSENTE', '-',
                  'filme final exige contrato integral com provas antes de render/TTS')
        else:
            from src.v4.formatos.gate_filme_completo import avaliar as avaliar_integral
            from src.v4.formatos.ponte_biblioteca import catalogo as catalogo_curado
            cenas_contrato = contrato.get('cenas') or []
            tipos = {'foto':'photo', 'video':'video', 'atlas_map':'atlas_map',
                     'comparison':'comparison', 'mechanism':'mechanism'}
            if len(cenas_contrato) != len(cenas) or any(
                c.get('id') != s.get('id') or
                abs(float(c.get('inicio', -999)) - float(s.get('start', -998))) > .05 or
                abs(float(c.get('fim', -999)) - float(s.get('end', -998))) > .05 or
                tipos.get((c.get('midia') or {}).get('tipo')) != s.get('type')
                for c, s in zip(cenas_contrato, cenas)
            ):
                falha('F-PORTAO-CONTRATO-DIVERGENTE', '-',
                      'cenas, tempos e tipos do filme não correspondem ao contrato auditado')
            else:
                for c, s in zip(cenas_contrato, cenas):
                    m = c.get('midia') or {}
                    if s.get('type') in ('photo', 'video'):
                        origem = (plano.get('media') or {}).get(s.get('asset')) or {}
                        if origem.get('catalog_asset_id') != m.get('asset_id'):
                            falha('F-PORTAO-FONTE-DIVERGENTE', str(s.get('id')),
                                  'mídia montada não corresponde ao asset curado no contrato')
                    elif s.get('type') == 'comparison':
                        ids = [((plano.get('media') or {}).get(s.get(key)) or {}).get('catalog_asset_id')
                               for key in ('asset','assetB')]
                        if ids != m.get('asset_ids'):
                            falha('F-PORTAO-FONTE-DIVERGENTE', str(s.get('id')),
                                  'fontes da comparação divergem do contrato')
                    elif s.get('type') == 'atlas_map':
                        origem = (plano.get('media') or {}).get(s.get('asset')) or {}
                        if (origem.get('local_source') != m.get('clipe') or
                                origem.get('atlas_proof') != m.get('prova')):
                            falha('F-PORTAO-MAPA-DIVERGENTE', str(s.get('id')),
                                  'clipe e comprovante ATLAS divergentes do contrato')
            resultado = avaliar_integral(contrato, catalogo_curado())
            if not resultado['pronto_para_render']:
                falha('F-PORTAO-INTEGRAL-BLOQUEADO', '-',
                      'falta prova audiovisual ou WAV autenticado: ' +
                      ', '.join(x['codigo'] for x in resultado['bloqueios'][:8]))
    visual = set()
    momentos = set()  # cenas demonstrativas contam como acontecimento, não foto decorativa
    prev_end = 0.0
    from src.v4.formatos import catalogo_mecanismos
    for n, original in enumerate(cenas):
        # Seleção automática só entre renderers realmente implementados.
        # Exigências de entrada/saída impedem usar card que só demonstra subida.
        renderer, lacunas = catalogo_mecanismos.decidir(original)
        cid = str(original.get('id') or f'cena-{n}')
        for item in lacunas:
            falha(item['codigo'], cid, item['motivo'])
        cena = ({**original, 'mechanism': renderer}
                if original.get('mechanism') == 'auto' and renderer else original)
        start, end = cena.get('start'), cena.get('end')
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            falha('F-SEM-TEMPO', cid, 'início/fim inválidos')
            continue
        if abs(start - prev_end) > .05:
            falha('F-LACUNA', cid, f'intervalo vazio ou sobreposição: {prev_end}→{start}')
        span = end - start
        # Mecanismo com acontecimentos reais pode durar mais do que fotografia
        # parada. O corte é dirigido pela ação, não por uma duração fixa.
        eh_causal = cena.get('type') == 'mechanism' and cena.get('mechanism') == 'lock_causal'
        eh_ciclo = cena.get('type') == 'mechanism' and cena.get('mechanism') in ('lock_cycle', 'lock_cycle_standalone')
        eh_optico = cena.get('type') == 'mechanism' and cena.get('mechanism') == 'optical_projection'
        eh_hidraulico = cena.get('type') == 'mechanism' and cena.get('mechanism') == 'lock_explainer'
        max_span = (float('inf') if cena.get('type') == 'video' else
                    8.0 if cena.get('type') == 'atlas_map' else
                    18.0 if eh_ciclo else 7.8 if eh_optico else
                    10.8 if eh_hidraulico else 6.2 if eh_causal else
                    4.8 if cena.get('type')=='mechanism' and len(cena.get('cues') or [])>=2 else 3.8)
        if eh_causal or eh_ciclo:
            # Contrato da ponte: o mesmo arquivo continua alguns frames no corte,
            # sem saltar para outro clipe ou afirmar subida que a filmagem não mostra.
            anterior = cenas[n-1] if n else {}
            continuidade = (anterior.get('type') == 'video' and
                           cena.get('reference_asset') == anterior.get('asset') and
                           cena.get('reference_asset') in plano.get('media', {}) and
                           isinstance(cena.get('reference_from_seconds'), (int, float)) and
                           abs(cena['reference_from_seconds'] -
                               (anterior.get('source_in_seconds', 0) + anterior['end'] - anterior['start'])) < .1)
            if cena.get('mechanism') != 'lock_cycle_standalone' and not continuidade:
                falha('F-PONTE-REAL', cid, 'o início do diagrama deve continuar do trecho real sem salto de origem')
            if cena.get('mechanism') == 'lock_cycle_standalone' and (
                    cena.get('reference_asset') or cena.get('reference_from_seconds') is not None):
                falha('F-PONTE-SEM-PROVA', cid,
                      'demonstração autônoma não pode fingir continuidade com filmagem')
            eventos = cena.get('cues') or []
            esperado = (('enter', 'seal', 'valves', 'rise', 'equalize', 'open', 'exit')
                        if eh_ciclo else
                        ('closed', 'water_enter', 'rise', 'equalize', 'release'))
            acoes = tuple(e.get('action') for e in eventos)
            tempos = [e.get('at') for e in eventos]
            tempos_validos = (len(tempos) == len(esperado) and
                             all(isinstance(t, (int, float)) for t in tempos))
            if not tempos_validos:
                falha('F-MECANISMO-CAUSAL', cid, 'ações/tempos ausentes ou inválidos')
            elif acoes != esperado or tempos != sorted(tempos) or len(set(tempos)) != len(tempos):
                falha('F-MECANISMO-CAUSAL', cid, 'ordem causal obrigatória')
            elif eh_ciclo:
                intervals = [b-a for a, b in zip(tempos, tempos[1:])]
                minimum = [2.0, 1.0, 1.0, 4.0, 1.0, 1.0]
                if (span < 15 or tempos[0] != 0 or tempos[-1] > span-1.1 or
                        any(gap < minim for gap,minim in zip(intervals,minimum))):
                    falha('F-CICLO-INCOMPLETO', cid,
                          'mostrar entrada, fecho, válvulas, enchimento longo, igualdade, abertura e saída sem pular etapas')
            elif (tempos[0] < 0 or tempos[-1] > span - .4 or
                  tempos[2] - tempos[1] < .4 or tempos[3] - tempos[1] < 1.5 or
                  tempos[4] < tempos[3]):
                falha('F-MECANISMO-CAUSAL', cid,
                      'exigir etapas distintas: fechar → entrar água → subir → igualar nível → liberar, com tempos coerentes')
        if eh_optico or eh_hidraulico:
            # Duas demonstrações FÍSICAS independentes no mesmo compositor.
            # O catálogo de ações é fechado: etiquetas não viram simulação
            # de acontecimentos sem renderer e encadeamento definidos.
            esperado = (('source', 'reticle', 'projection', 'wafer')
                        if eh_optico else
                        ('closed', 'water_enter', 'rise', 'equalize', 'release'))
            eventos = cena.get('cues') or []
            acoes = tuple(e.get('action') for e in eventos if isinstance(e, dict))
            tempos = [e.get('at') for e in eventos if isinstance(e, dict)]
            valido = (len(eventos) == len(esperado) == len(tempos)
                      and acoes == esperado
                      and all(isinstance(t, (float, int)) and
                              not isinstance(t, bool) and math.isfinite(t)
                              for t in tempos)
                      and tempos[0] == 0
                      and all(b-a >= .65 for a,b in zip(tempos,tempos[1:]))
                      and tempos[-1] <= span-.6
                      # Explicação hidráulica precisa de tempo VISÍVEL para válvula,
                      # enchimento, deslocamento do navio, equalização e liberação.
                      and (not eh_hidraulico or (
                          tempos[2]-tempos[1] >= 1.2 and
                          tempos[3]-tempos[2] >= 2.8 and
                          tempos[4]-tempos[3] >= 1.0 and
                          span-tempos[4] >= .9)))
            if not valido:
                falha('F-MECANISMO-PROCESSO', cid,
                      'cada etapa física requer ação, ordem e tempo distintos')
            if cena.get('reference_asset') or cena.get('reference_from_seconds') is not None:
                falha('F-PONTE-SEM-PROVA', cid,
                      'demonstração autônoma não pode fingir continuidade com filmagem')
        if span < 1.4 or span > max_span:
            falha('F-PLANO-SEM-DIRECAO', cid, f'{span:.1f}s: sem progressão suficiente para a duração')
        prev_end = end
        tipo = cena.get('type')
        if tipo == 'video':
            fonte=(plano.get('media') or {}).get(cena.get('asset')) or {}
            if fonte.get('duration_s') is not None:
                from src.v4.formatos.tempo_natural import validar_janela_origem
                motivo=validar_janela_origem(cena, fonte['duration_s'])
                if motivo:
                    falha('F-VIDEO-FONTE-INSUFICIENTE',cid,motivo)
        if tipo == 'video':
            origem_enquadramento=(plano.get('media') or {}).get(cena.get('asset')) or {}
            contrato_roi=cena.get('video_framing')
            largura=origem_enquadramento.get('width')
            altura=origem_enquadramento.get('height')
            if contrato_roi is not None:
                try:
                    if contrato_roi.get('modo')=='relacao_observada':
                        resolver_relacao_video(cena,origem_enquadramento,(largura,altura),
                            adaptativo=privado and plano.get('publicar') is False and plano.get('documentary_framing')=='ADAPTIVE_REVIEW_V1')
                    elif contrato_roi.get('modo')=='fonte_integral':
                        proteger_fonte_integral(cena,origem_enquadramento,(largura,altura))
                    else:
                        planejar_enquadramento_video(cena,origem_enquadramento,(largura,altura))
                except (ValueError,TypeError) as exc:
                    motivo=str(exc)
                    codigo=motivo.split(':',1)[0] if motivo.startswith('F-ROI-') else 'F-ROI-INVALIDO'
                    falha(codigo,cid,motivo)
            elif plano.get('tipo')!='PROVA_VISUAL_PRIVADA':
                if not isinstance(largura,int) or not isinstance(altura,int):
                    falha('F-ROI-DIMENSOES',cid,'vídeo final exige dimensões verificadas da fonte')
                elif largura>altura:
                    falha('F-ROI-SEM-DIRECAO',cid,
                          'vídeo horizontal final exige região essencial e inspeção do recorte vertical')
        if isinstance(cena.get('progressao_visual'),dict) and cena['progressao_visual'].get('tipo')=='sequencia_amostrada_privada' and not (privado and plano.get('publicar') is False):
            falha('F-SEQUENCIA-PRIVADA',cid,'amostras não homologam continuidade nem filme final')
        if tipo == 'video' and span > 3.8:
            # Usa o MESMO contrato temporal do áudio natural; não forçar
            # corte a cada 3,8s quando uma ação genuína continua.
            # Declarações são apenas pré-direção: revisão dos quadros reais
            # e direitos seguem obrigatórios no portão editorial.
            from src.v4.formatos.tempo_natural import validar_progressao_video
            fonte = (plano.get('media') or {}).get(cena.get('asset'))
            for problema in validar_progressao_video(cena, span, fonte):
                falha('F-VIDEO-SEM-PROGRESSAO-COMPROVADA', cid, problema)
        if tipo == 'mechanism':
            if eh_causal or eh_ciclo or eh_optico or eh_hidraulico:
                for e in cena.get('cues') or []:
                    if e.get('action') in ('enter', 'seal', 'valves', 'rise', 'equalize', 'open', 'exit', 'water_enter', 'release', 'closed', 'source', 'reticle', 'projection', 'wafer'):
                        momentos.add(('mecanismo', cid, e['action']))
            else:
                momentos.add(('mecanismo', cid))
        elif tipo == 'atlas_map' and cena.get('asset'):
            momentos.add(('ATLAS_MAPLIBRE', cid, cena['asset']))
        elif tipo == 'video' and cena.get('asset'):
            # Cortes de instantes DISTINTOS do mesmo clipe são acontecimentos
            # diferentes apenas se realmente distantes no tempo de origem.
            src_t = float(cena.get('source_in_seconds') or 0)
            momentos.add((cena['asset'], 'video', int(src_t // 3)))
            # Movimento REAL pode apresentar mais de uma informação dentro
            # da mesma tomada. Contar apenas etapas com fonte_s, SHA e
            # descrição validadas; zoom/efeito de câmera não contam.
            # Nunca confundir esse gate estrutural com aprovação dos pixels.
            progress=cena.get('progressao_visual')
            if isinstance(progress,dict):
                from src.v4.formatos.tempo_natural import validar_progressao_video
                fonte=(plano.get('media') or {}).get(cena['asset'])
                if not validar_progressao_video(cena,span,fonte):
                    for evento in progress.get('eventos') or []:
                        momentos.add((
                            cena['asset'],'acao_original',
                            round(float(evento['fonte_s']),3),
                            str(evento['acao_visivel']).strip().casefold()
                        ))
        elif cena.get('asset'):
            momentos.add((cena['asset'], 'still'))
        if tipo == 'map' or cena.get('map') is not None:
            falha('F-MAPA-PROIBIDO', cid,
                  'componente vetorial simplificado retirado. Mapas finais devem usar o palco cartográfico ATLAS/MapLibre com raster licenciado; nunca substituição automática por polígonos.')
        if tipo not in TIPOS:
            falha('F-TIPO', cid, 'tipo de cena não suportado')
        if not str(cena.get('headline') or '').strip():
            falha('F-SEM-INFORMACAO', cid, 'título deve ligar imagem ao acontecimento')
        if not cena.get('cues') or any(
            not (0 <= x.get('at', -1) < span and x.get('label'))
            for x in cena.get('cues') or []
        ):
            falha('F-SEM-REVELACAO', cid, 'cena precisa acrescentar informação com objeto visível')
        if cena.get('evidence') not in ('literal', 'representative', 'explainer'):
            falha('F-SEM-PROVENIENCIA', cid, 'classifique literal, representativa ou explicativa')
        if tipo == 'mechanism':
            if (cena.get('mechanism') not in ('lock_filling', 'lock_causal', 'lock_cycle', 'lock_cycle_standalone', 'lock_explainer', 'optical_projection', 'auto') or
                cena.get('evidence') != 'explainer' or cena.get('literal_identity')):
                falha('F-MECANISMO-NÃO-IDENTIFICADO', cid,
                      'esquema com princípio verificado, sem fingir filmagem ou identidade')
            if cena.get('asset'):
                falha('F-MECANISMO-SEM-ACERVO', cid, 'mecanismo é ilustração própria, não fotografia')
        elif tipo == 'atlas_map':
            if cena.get('evidence') != 'explainer' or cena.get('literal_identity'):
                falha('F-ATLAS-EVIDENCIA', cid,
                      'mapa ATLAS é representação cartográfica, não filmagem literal do fato')
            if cena.get('assetB') or cena.get('mechanism') or cena.get('map'):
                falha('F-ATLAS-EVIDENCIA', cid, 'mapa ATLAS usa clipe autenticado, nunca mapa simplificado/camadas extras')
        elif cena.get('evidence') == 'explainer':
            falha('F-EXPLICAÇÃO-SEM-MECANISMO', cid, 'explicativo precisa mecanismo real no compositor')
        if cena.get('evidence') == 'literal' and not cena.get('literal_identity'):
            falha('F-LITERAL-SEM-IDENTIDADE', cid, 'não alegar local/entidade exata sem identidade verificada')
        elif cena.get('evidence') == 'representative' and cena.get('literal_identity'):
            falha('F-REPRESENTATIVA-ROTULADA-LITERAL', cid, 'imagem genérica não pode alegar identidade exata')
        ids = [] if tipo == 'mechanism' else [cena.get('asset')]
        if tipo == 'comparison':
            ids.append(cena.get('assetB'))
            if len(set(ids)) != 2:
                falha('F-COMPARACAO-FAKE', cid, 'comparação precisa de dois referentes distintos')
        for mid in ids:
            if not mid or mid not in plano.get('media', {}):
                falha('F-MIDIA-SEM-CATALOGO', cid, f'{mid} não consta na curadoria')
                continue
            asset = plano['media'][mid]
            if (tipo=='photo' and asset.get('original_graphic') is True
                    and cena.get('evidence')=='literal'):
                falha('F-GRAFICO-COMO-REGISTRO',cid,
                      'infografia original representa dados, nunca fotografia literal do acontecimento')
            motion=cena.get('motion_graphic')
            if motion is not None:
                if (tipo!='photo' or asset.get('original_graphic') is not True or
                        cena.get('evidence')=='literal' or not isinstance(motion,dict) or
                        motion.get('kind') not in ('stat_reveal','causal_flow')):
                    falha('F-MOTION-SEM-CONTRATO',cid,
                          'animação explicativa precisa ser gráfico original não literal')
                elif motion['kind']=='stat_reveal':
                    if any(not isinstance(motion.get(k),str) or not motion[k].strip()
                           for k in ('eyebrow','value','line1','line2')):
                        falha('F-MOTION-SEM-DADOS',cid,'número exige contexto e unidade documentados')
                elif (not isinstance(motion.get('stages'),list) or
                      len(motion['stages'])!=3 or
                      any(not isinstance(x,str) or not x.strip() for x in motion['stages'])):
                    falha('F-MOTION-SEM-DADOS',cid,'sequência exige três etapas legíveis')
            url = asset.get('url') or ''
            source = asset.get('local_source')
            if source:
                # Novo caminho autenticado: clip real produzido por PalcoMapa/MapLibre.
                # Sem atestado SHA de raster e inspeção técnica não há mídia.
                path = Path(source)
                atlas_bridge=(tipo == 'atlas_map')
                if atlas_bridge:
                    from src.v4.formatos.ponte_mapa_atlas import validar_comprovante
                    for problema in validar_comprovante(asset):
                        falha('F-ATLAS-COMPROVANTE',cid,problema)
                    if asset.get('media_type') != 'video' or not (asset.get('page') or '').startswith('https://'):
                        falha('F-ATLAS-COMPROVANTE',cid,'mapa deve ser MP4 sem áudio com fonte cartográfica')
                stage_privado=(
                    plano.get('tipo')=='PROVA_VISUAL_PRIVADA'
                    and plano.get('publicar') is False
                    and path.parts[:1]==('stage_documental',)
                    and isinstance(asset.get('expected_sha256'),str)
                    and len(asset['expected_sha256'])==64
                    and (
                        recibo_documental_valido(asset) or
                        urlsplit(str(asset.get('page') or '')).hostname in (
                            'www.nist.gov','commons.wikimedia.org','earthquake.usgs.gov',
                            'svs.gsfc.nasa.gov','science.nasa.gov', 'www.usgs.gov'
                        ) or (
                            asset.get('original_graphic') is True
                            and asset.get('license')=='CC0'
                            and asset.get('media_type')=='photo'
                            and urlsplit(str(asset.get('page') or '')).hostname in (
                                'www.sec.gov','pr.tsmc.com','www.usgs.gov',
                            'www.tsmc.com','www.asml.com','investor.tsmc.com'
                            )
                        )
                    )
                    and asset.get('media_type') in ('video','photo')
                )
                permitido = atlas_bridge or stage_privado or (
                    plano.get('tipo') == 'PROVA_VISUAL_PRIVADA' and (
                    str(path).startswith('tests/midia/') or
                    str(path).startswith('tests/piloto_ever_given/img/') or
                    str(path).startswith('motor4/formatos/dados/raster/') or
                    (str(path).startswith('stage_hero/') and
                     len(asset.get('expected_sha256') or '')==64 and
                     (asset.get('page') or '').startswith('https://www.dvidshub.net/video/'))))
                if not permitido or path.is_absolute() or '..' in path.parts:
                    falha('F-FIXTURE-NAO-AUTORIZADA', cid, 'arquivo local só na amostra privada e caminhos permitidos')
            elif urlsplit(url).scheme != 'https' or urlsplit(url).hostname not in ORIGENS:
                falha('F-ORIGEM-INSEGURA', cid, 'usar acervo real com URL verificável e confiável')
            direitos_pendentes=(
                plano.get('tipo')=='PROVA_VISUAL_PRIVADA'
                and plano.get('publicar') is False
                and asset.get('license')=='REVIEW_PENDING'
                and asset.get('rights_status')=='REVIEW_PENDING'
                and bool(source) and str(source).startswith('stage_documental/')
                and isinstance(asset.get('expected_sha256'),str)
                and len(asset['expected_sha256'])==64
                and (recibo_documental_valido(asset) or urlsplit(str(asset.get('page') or '')).hostname in (
                    'www.nist.gov','svs.gsfc.nasa.gov','science.nasa.gov'))
            )
            if asset.get('rights_status')=='REVIEW_PENDING' and not (privado and plano.get('publicar') is False):
                falha('F-DIREITOS-PENDENTES',cid,'declaração de licença não substitui auditoria; somente revisão privada')
            if asset.get('documentary_receipt') is not None and not recibo_documental_valido(asset):
                falha('F-RECIBO-DOCUMENTAL',cid,'recibo documental sem vínculo com origem, variante ou SHA')
            if (asset.get('license') not in LICENCAS and not direitos_pendentes
                    or not asset.get('page') or not asset.get('credit')):
                falha('F-LICENCA', cid, 'mídia precisa de página, autor e licença explícitos; '
                      'licença pendente apenas em montagem privada sem publicação')
            visual.add(mid)
    if cenas and abs(prev_end - plano.get('duracao', -1)) > .05:
        falha('F-DURACAO', '-', 'última cena não alcança a duração do roteiro')
    minimo_momentos=min(3,len(cenas)) if fragmento_misto and privado and plano.get('publicar') is False else 3
    if len(momentos) < max(minimo_momentos, round(len(cenas)*.65)):
        falha('F-POUCO-ACERVO', '-', f'{len(momentos)} acontecimentos visuais diferentes para {len(cenas)} cenas; risco de repetição')
    if any(c.get('type') == 'comparison' for c in cenas) and len(visual) < 4:
        falha('F-COMPARACAO-REPETITIVA', '-', 'comparação deve trazer informação nova')
    from src.v4.formatos import direcao_eventos
    for item in direcao_eventos.verificar(cenas):
        falha(item['codigo'], item['cena'], item['motivo'])
    from src.v4.formatos import fiscal_progressao
    for item in fiscal_progressao.verificar(cenas, plano.get('media') or {}):
        falha(item['codigo'], item['cena'], item['motivo'])
    from src.v4.formatos import contrato_visual_comum
    comum = contrato_visual_comum.auditar(plano)
    # Gate compartilhado cobre declarações; o fiscal específico continua
    # responsável por curadoria, licença e tempos próprios do FILME.
    for erro in comum['falhas']:
        if erro['codigo'] != 'U-INSPECAO-VISUAL':
            falha(erro['codigo'], erro['id'], erro['motivo'])
    return {'pronto': not falhas, 'bloqueios': falhas, 'cenas': len(cenas),
            'medias_unicas': len(visual), 'momentos_visuais':len(momentos),
            'contrato_comum': comum,
            'area_segura':area_segura,
            'visual_approval': ('REPROVADO_ESTILO_LEGADO'
                                if plano.get('perfil_visual') ==
                                   'LEGADO_REJEITADO_SOMENTE_QA'
                                else 'NAO_FOI_AVALIADO')}


def preparar(plano: dict, destino: Path, public_root: Path, downloader=None, *, fragmento_misto=False) -> dict:
    import requests
    check = avaliar(plano,fragmento_misto=fragmento_misto)
    destino=Path(destino)
    destino.mkdir(parents=True,exist_ok=True)
    (destino/'contrato.json').write_text(json.dumps(check,ensure_ascii=False,indent=2),encoding='utf-8')
    if not check['pronto']:
        raise ValueError('pré-produção reprovada: '+json.dumps(check['bloqueios'],ensure_ascii=False))
    # Gerar props com as MESMAS cenas que passaram na validação.
    # Não inserir este passo antes de criar o contrato bloqueador.
    from src.v4.formatos import diretor_processos, diretor_roteiro
    plano = diretor_processos.expandir(diretor_roteiro.expandir_preview(plano))
    # E211: o preflight histórico é estrutural; o gate de render é visual.
    # Resolve também 'auto' antes de permitir qualquer aquisição ou composição.
    from src.v4.formatos import politica_animacao as PA, catalogo_mecanismos as CM
    rotas=[]
    for s in plano['shots']:
        if s.get('type')=='mechanism' and s.get('mechanism')=='auto':
            renderer, issues=CM.decidir(s)
            if issues or not renderer:
                raise ValueError('mecanismo automatico sem capacidade: '+str(issues))
            s={**s,'mechanism':renderer}
        rotas.append(s)
    modo=PA.LEGACY if plano.get('perfil_visual')==PA.LEGACY else None
    privado=plano.get('tipo')=='PROVA_VISUAL_PRIVADA' and plano.get('publicar') is False
    gate=PA.avaliar(rotas,modo=modo,privado=privado)
    (destino/'politica_animacao.json').write_text(json.dumps(gate,ensure_ascii=False,indent=2),encoding='utf8')
    PA.exigir(rotas,modo=modo,privado=privado)
    if downloader is None:
        def downloader(url: str) -> bytes:
            r=requests.get(url,timeout=90,headers={'User-Agent':'CoringaExplica/1.0 (license verification; contact via GitHub)'})
            r.raise_for_status()
            if len(r.content)>26_000_000:
                raise ValueError('arquivo excessivamente grande')
            return r.content
    public_root=Path(public_root)
    assets_dir=public_root/'film_editorial'
    assets_dir.mkdir(parents=True,exist_ok=True)
    medias, relatorio={},[]
    for mid,item in plano['media'].items():
        source = item.get('local_source')
        if source:
            # path traversal e symlinks são rejeitados na avaliação e no uso.
            src = (Path.cwd() / source).resolve()
            if not src.is_relative_to(Path.cwd().resolve()) or not src.is_file():
                raise ValueError(f'{mid}: arquivo de fixture não encontrado')
            data = src.read_bytes()
        else:
            data=downloader(item['url'])
        if not isinstance(data,bytes):
            raise ValueError(f'{mid}: sem bytes válidos')
        sha=hashlib.sha256(data).hexdigest()
        if item.get('expected_sha256') and item['expected_sha256']!=sha:
            raise ValueError(f'{mid}: hash da origem mudou — selecionar/curar novamente')
        receipt=item.get('documentary_receipt')
        if receipt is not None:
            if not recibo_documental_valido(item) or len(data)!=receipt.get('bytes'):
                raise ValueError(f'{mid}: recibo documental ou tamanho divergente')
            if receipt['provedor']=='archive_video':
                variants=receipt['recibo']['variantes']
                if not any(v.get('url')==receipt['url_adquirida'] and v.get('size')==len(data)
                           and v.get('md5')==hashlib.md5(data).hexdigest() for v in variants if isinstance(v,dict)):
                    raise ValueError(f'{mid}: MD5 de arquivo Archive divergente')
        if item.get('media_type') == 'video':
            if not source:
                raise ValueError(f'{mid}: vídeos de rede exigem ingestão/recorte em etapa separada')
            probe = subprocess.run(
                ['ffprobe','-v','error','-show_entries',
                 'stream=width,height:format=duration',
                 '-select_streams','v:0','-of','json',str(src)],
                capture_output=True,text=True,check=True)
            informacao=json.loads(probe.stdout)
            streams=informacao.get('streams') or []
            duracao_origem=float((informacao.get('format') or {}).get('duration') or 0)
            if not streams or min(streams[0].get('width',0),streams[0].get('height',0))<MIN_VIDEO_COMPOSITION_PX:
                raise ValueError(f'{mid}: vídeo sem qualidade mínima')
            w,h=streams[0]['width'],streams[0]['height']
            ext=src.suffix.lower()
            if ext not in ('.mp4','.webm'):
                raise ValueError(f'{mid}: container de vídeo inválido')
        else:
            import io
            with Image.open(io.BytesIO(data)) as img:
                if img.format not in ('JPEG','PNG','WEBP') or min(img.size)<600:
                    raise ValueError(f'{mid}: imagem inválida/pequena')
                ext={ 'PNG': '.png', 'WEBP': '.webp', 'JPEG': '.jpg' }[img.format]
                w,h=img.size
        out=assets_dir/f'{sha}{ext}'
        if not out.exists():
            out.write_bytes(data)  # preservar bytes idênticos, sem recomprimir
        medias[mid]={'asset':f'film_editorial/{sha}{ext}','sha256':sha,
                     'width':w,'height':h,'credit':item['credit'],
                     'license':item['license'],'page':item['page']}
        if item.get('media_type')=='video':
            medias[mid]['duration_s']=duracao_origem
        relatorio.append({'id':mid,'sha256':sha,'resolucao':[w,h],
                          'licenca':item['license'],'pagina':item['page'],
                          'direitos_status':item.get('rights_status','NAO_DECLARADO_NO_CONTRATO')})
    shots=[]
    from src.v4.formatos import catalogo_mecanismos
    for c in plano['shots']:
        x={k:v for k,v in c.items() if k not in ('literal_identity','notes','documentary_roi_points','documentary_integral_required','documentary_atlas_layout','documentary_safe_trial')}
        if c.get('mechanism') == 'auto':
            resolved, issues = catalogo_mecanismos.decidir(c)
            if issues or not resolved:
                raise ValueError('mecanismo automático sem capacidade real: '+str(issues))
            x['mechanism'] = resolved
        if c['type'] != 'mechanism':
            x['asset']=medias[c['asset']]['asset']
            x['source']=medias[c['asset']]['credit']
            if c['type'] in ('photo','video'):
                x['source_dimensions']=[medias[c['asset']]['width'],medias[c['asset']]['height']]
            if privado and c['type']=='atlas_map':
                # Proof already validated by the ATLAS bridge before preparing media.
                proof=json.loads(Path(plano['media'][c['asset']]['atlas_proof']).read_text(encoding='utf-8'))
                if proof.get('documentary_layout') is True:
                    x['documentary_atlas_layout']=True
        else:
            # Fonte descritiva, sem fingir que o desenho é filmagem.
            # Preserva a legenda das eclusas legadas (não mudar outros vídeos).
            # Sempre usar o mecanismo RESOLVIDO, jamais o campo original
            # "auto" do storyboard. O bug fazia cenas EUV herdarem
            # o crédito de uma eclusa quando o diretor decidia o renderer.
            # Atribuição explicitamente por família; sem default hidráulico.
            resolved = x.get('mechanism')
            if resolved == 'optical_projection':
                x['source'] = 'ASML · https://www.asml.com/en/technology/lithography-principles'
                x['source_display'] = 'ASML · asml.com'
            elif resolved in (
                'lock_explainer','lock_cycle_standalone','lock_cycle',
                'lock_causal','lock_filling'
            ):
                x['source'] = 'ACP · https://pancanal.com/en/history-of-the-panama-canal/'
                x['source_display'] = 'Autoridade do Canal do Panamá · pancanal.com'
            else:
                raise ValueError('F-MECANISMO-FONTE: crédito não definido para '+str(resolved))
            if c.get('reference_asset'):
                # Congelar um quadro do próprio master curado, antes de qualquer corte
                # interno da fonte. Evita fingir continuidade de dois instantes distintos.
                mid = c['reference_asset']
                if plano['media'][mid].get('media_type') != 'video':
                    raise ValueError('ponte causal exige vídeo real')
                src_video = public_root / medias[mid]['asset']
                pos = c['reference_from_seconds']
                frame = assets_dir / (medias[mid]['sha256'][:16] + '-ref-' +
                                      str(round(pos * 1000)) + '.png')
                subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',
                                '-ss',str(pos),'-i',str(src_video),
                                '-frames:v','1',str(frame)],check=True)
                if not frame.exists() or frame.stat().st_size < 3000:
                    raise ValueError('frame de ligação ausente')
                with Image.open(frame) as img:
                    if min(img.size) < 700:
                        raise ValueError('frame de ligação insuficiente')
                x['reference_asset'] = 'film_editorial/' + frame.name
        if c['type']=='video':
            from src.v4.formatos.tempo_natural import validar_janela_origem
            motivo=validar_janela_origem(c,medias[c['asset']]['duration_s'])
            if motivo:
                raise ValueError(c['id']+': '+motivo)
            if c.get('video_framing') is not None:
                dimensoes_reais=(medias[c['asset']]['width'],medias[c['asset']]['height'])
                dimensoes_declaradas=(plano['media'][c['asset']].get('width'),
                                      plano['media'][c['asset']].get('height'))
                if dimensoes_reais!=dimensoes_declaradas:
                    raise ValueError(c['id']+': dimensões reais diferem do enquadramento auditado')
                if c['video_framing'].get('modo')=='relacao_observada':
                    strategy=resolver_relacao_video(
                        c,plano['media'][c['asset']],dimensoes_reais,
                        adaptativo=plano.get('tipo')=='PROVA_VISUAL_PRIVADA' and plano.get('documentary_framing')=='ADAPTIVE_REVIEW_V1')
                    x['video_context_layout']=strategy['layout']
                    x['framing_positions']=strategy['framing_positions']
                    if strategy.get('documentary_viewport'):
                        x['documentary_viewport']=strategy['documentary_viewport']
                elif c['video_framing'].get('modo')=='fonte_integral':
                    x['video_context_layout']=proteger_fonte_integral(
                        c,plano['media'][c['asset']],dimensoes_reais)
                    x['framing_positions']=[]
                else:
                    x['framing_positions']=planejar_enquadramento_video(
                        c,plano['media'][c['asset']],dimensoes_reais
                    )
            elif plano.get('tipo')!='PROVA_VISUAL_PRIVADA' and medias[c['asset']]['width']>medias[c['asset']]['height']:
                raise ValueError(c['id']+': vídeo horizontal final sem enquadramento dirigido')
        # E291: forward only observations already validated by the framing
        # contract above. Sampled geometry is NOT continuous motion certification.
        if privado and c['type']=='video' and x.get('framing_positions'):
            contract=c.get('video_framing') or {}
            points=[]
            for point in contract.get('pontos',[]):
                box=point.get('area_essencial')
                if contract.get('modo')=='relacao_observada':
                    boxes=[e['bbox'] for e in point['elementos']]
                    box=[min(b[0] for b in boxes),min(b[1] for b in boxes),
                         max(b[2] for b in boxes),max(b[3] for b in boxes)]
                if box is not None:
                    points.append({'at':point['at'],'bbox':box})
            if points:x['documentary_roi_points']=points
        if privado and c['type']=='video' and c.get('video_framing') is not None:
            # An explicitly reviewed integral source, including a relation
            # resolver that rejected crop, must never be enlarged blindly.
            if c['video_framing'].get('modo')=='fonte_integral' or not x.get('documentary_roi_points'):
                x['documentary_integral_required']=True
        if c.get('assetB'):
            x['assetB']=medias[c['assetB']]['asset']
            x['sourceB']=medias[c['assetB']]['credit']
        # Never accept a renderer-ready crop from arbitrary storyboard data.
        x.pop('photo_crop_preview',None)
        if privado and c.get('type')=='photo' and not plano['media'][c['asset']].get('original_graphic'):
            crop=propor_recorte_foto(c,plano['media'][c['asset']],(medias[c['asset']]['width'],medias[c['asset']]['height']))
            if crop:x['photo_crop_preview']=crop
        if c.get('type')=='photo' and plano['media'][c['asset']].get('original_graphic') is True:
            # Gráfico autoral já comunica dados/etapas dentro dos pixels.
            # Não duplicar título e CTA por cima dele no compositor.
            x['graphic_original']=True
        shots.append(x)
    pendentes=[mid for mid,item in plano['media'].items()
              if item.get('license')=='REVIEW_PENDING' or item.get('rights_status')=='REVIEW_PENDING']
    from src.v4.formatos import qa_area_segura
    props={'duracao':plano['duracao'],'shots':shots,'preview':True,
           'private_review_only':privado or bool(pendentes) or modo==PA.LEGACY,
           'safe_area_profile':plano.get('safe_area_profile') or qa_area_segura.PERFIL,
           'direitos_pendentes':pendentes}
    if privado and modo!=PA.LEGACY and plano.get('documentary_framing')=='ADAPTIVE_REVIEW_V1':
        props['documentary_media_preview']=True
    if modo==PA.LEGACY:
        props['animation_policy_mode']=modo
    (destino/'props.json').write_text(json.dumps(props,ensure_ascii=False,indent=2),encoding='utf-8')
    (destino/'midias.json').write_text(json.dumps(relatorio,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'pronto':True,'shots':len(shots),'midias':len(medias),'props':str(destino/'props.json')}


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('plano')
    p.add_argument('saida')
    p.add_argument('public_root')
    a=p.parse_args(argv)
    plan=json.loads(Path(a.plano).read_text(encoding='utf-8'))
    r=preparar(plan,Path(a.saida),Path(a.public_root))
    print(json.dumps(r,ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
