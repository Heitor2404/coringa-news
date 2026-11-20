"""Vídeo de processo REAL via eventos visíveis anotados no ORIGINAL.

Contratos V2 escolhem a capacidade com a evidência: exato evento factual,
ações em ordem, tempos de origem e mídia em stage com SHA conferido.
Um vídeo verdadeiro não prova outra empresa, outro evento ou a etapa
que as imagens não mostram. Uso só em QA privada; direitos e aprovação
editorial permanecem pendentes mesmo quando a observação está documentada.

A prova visual é assistida, não homologa o licenciamento nem a publicação.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

_SHA=re.compile(r"[0-9a-f]{64}")


class ProvaInvalida(ValueError):
    pass


def _fail(code,why):
    raise ProvaInvalida(f'VA-{code}: {why}')


def validar(video:dict, *, bytes_obrigatorios=True)->dict:
    if not isinstance(video,dict):
        _fail('CONTRATO','fonte não é registro')
    if (video.get('provedor')!='nasa_svs' or video.get('publicar') is not False
        or video.get('licenca')!='REVIEW_PENDING'
        or video.get('direitos_revisados') is not False):
        _fail('PORTAO','somente NASA SVS na prova técnica privada; direitos pendentes')
    if video.get('inspecao_status')!='QUADROS_AMOSTRADOS_ASSISTENTE_REVISOR_HUMANO_PENDENTE':
        _fail('INSPECAO','não mascarar revisão assistida como homologação')
    if video.get('temporalidade')!='SEQUENCIA_ACELERADA_DE_IMAGENS':
        _fail('TEMPO','não exibir sequência condensada como vídeo em tempo real')
    for k in ('id','evento_origem_id','sujeito','fonte_id','credit','observacao'):
        if not isinstance(video.get(k),str) or len(video[k].strip())<(
            35 if k=='observacao' else 7):
            _fail('CONTRATO',f'campo {k} ausente/incompleto')
    sha=video.get('sha256_origem')
    if not isinstance(sha,str) or not _SHA.fullmatch(sha):
        _fail('SHA','hash de original obrigatório')
    page=urlsplit(str(video.get('pagina') or ''))
    if (page.scheme!='https' or page.hostname!='svs.gsfc.nasa.gov'
        or not re.fullmatch(r'/\d{4,6}/?',page.path)):
        _fail('ORIGEM','página oficial NASA SVS inválida')
    path=Path(str(video.get('arquivo') or ''))
    if (path.is_absolute() or '..' in path.parts or
        path.parts[:1]!=('stage_documental',) or path.suffix!='.mp4'):
        _fail('ARQUIVO','exigir stage_documental e MP4 original')
    w,h,d=video.get('width'),video.get('height'),video.get('duration_s')
    if (any(not isinstance(x,int) or isinstance(x,bool) or x<400
            for x in (w,h))
        or not isinstance(d,(float,int)) or isinstance(d,bool)
        or not math.isfinite(d) or d<5):
        _fail('DIMENSOES','metadados originais inválidos')
    if bytes_obrigatorios:
        local=(Path.cwd()/path).resolve()
        if not local.is_relative_to(Path.cwd().resolve()) or not local.is_file():
            _fail('ARQUIVO','original real ausente')
        hashobj=hashlib.sha256()
        with local.open('rb') as fd:
            for chunk in iter(lambda:fd.read(1024*1024),b''):
                hashobj.update(chunk)
        if hashobj.hexdigest()!=sha:
            _fail('SHA','arquivo original adulterado')
        probe=json.loads(subprocess.check_output([
            'ffprobe','-v','error','-show_entries',
            'stream=codec_type,width,height:format=duration','-of','json',
            str(local)],text=True,timeout=30))
        tracks=[x for x in probe.get('streams') or [] if x.get('codec_type')=='video']
        if len(tracks)!=1 or (int(tracks[0]['width']),int(tracks[0]['height']))!=(w,h):
            _fail('DIMENSOES','resolução real não corresponde à curadoria')
        realdur=float(probe['format']['duration'])
        if abs(realdur-d)>.08:
            _fail('TEMPO','duração original não corresponde ao inventário')
    j=video.get('janela')
    if not isinstance(j,dict):
        _fail('JANELA','recorte não está registrado')
    begin,span=j.get('inicio_s'),j.get('duracao_s')
    if (not isinstance(begin,(float,int)) or isinstance(begin,bool)
        or not isinstance(span,(float,int)) or isinstance(span,bool)
        or not math.isfinite(begin) or not math.isfinite(span)
        or begin<0 or not 1.4<=span<=15 or begin+span>d-.05):
        _fail('JANELA','trecho não cabe no original')
    actions=j.get('acoes_necessarias')
    observations=j.get('eventos')
    if (not isinstance(actions,list) or len(actions)<2 or
        len(set(actions))!=len(actions) or
        any(not isinstance(a,str) or len(a)<8 for a in actions)
        or not isinstance(observations,list) or len(observations)!=len(actions)):
        _fail('ACOES','ação sem progresso observável ou incompleta')
    last=-1.0
    for act,event in zip(actions,observations):
        if not isinstance(event,dict) or event.get('acao_id')!=act:
            _fail('ACAOINCORRETA','observação não cobre etapa exigida em ordem')
        t,orig=event.get('at'),event.get('fonte_s')
        if (not isinstance(t,(float,int)) or isinstance(t,bool)
            or not isinstance(orig,(float,int)) or isinstance(orig,bool)
            or not math.isfinite(t) or not math.isfinite(orig)
            or t<=last or not 0<=t<span or abs((begin+t)-orig)>.09):
            _fail('TEMPO','evidência visual deve corresponder a fonte_s')
        if not isinstance(event.get('acao_visivel'),str) or len(event['acao_visivel'].strip())<25:
            _fail('ACOES','observação real de quadros muito vaga')
        last=t
    return {'sha256':sha,'inicio_s':begin,'duracao_s':span,
            'acoes':tuple(actions),'fonte_evento_id':video['evento_origem_id'],
            'revisao_humana':'PENDENTE','publicar':False}


def catalogo_com_acoes(acervo:dict,manifesto:dict, *, bytes_obrigatorios=True)->dict:
    if (not isinstance(manifesto,dict) or manifesto.get('versao')!=1
        or manifesto.get('modo')!='CURADORIA_ASSISTIDA_PRIVADA'
        or manifesto.get('publicar') is not False):
        _fail('MANIFESTO','somente curadoria assistida privada')
    fontes=manifesto.get('videos')
    if not isinstance(fontes,list) or not fontes:
        _fail('MANIFESTO','nenhuma fonte')
    copia=copy.deepcopy(acervo)
    seen={x.get('id') for x in copia.get('itens') or []}
    for fonte in fontes:
        proof=validar(fonte,bytes_obrigatorios=bytes_obrigatorios)
        uid='acao-'+proof['sha256'][:16]
        if uid in seen:
            _fail('DUPLICACAO','mesma origem duplicada')
        seen.add(uid)
        copia.setdefault('itens',[]).append({
            **copy.deepcopy(fonte),
            'id':uid,'natureza':'video_acao_real',
            'sha256_origem':proof['sha256'],
            'pode_publicar':False,'prova':{
                'midia_corresponde':True,
                'acao_ou_relacao_visivel':'AMOSTRA_REVISAO_ASSISTIDA',
                'aprovacao_humana':False,
                'autorizacao_comercial':False,
            }})
    return copia


def candidatos(acontecimento:dict,biblioteca:dict)->list[dict]:
    """Exigir id do MESMO fato e ações idênticas; título nunca basta."""
    dado=acontecimento.get('dados') or {}
    required=dado.get('acoes_necessarias')
    if not isinstance(required,list) or not required:
        return []
    out=[]
    for fonte in biblioteca.get('itens') or []:
        if fonte.get('natureza')!='video_acao_real':
            continue
        if (acontecimento.get('id')==fonte.get('evento_origem_id')
            and acontecimento.get('fonte')==fonte.get('pagina')
            and required==(fonte.get('janela') or {}).get('acoes_necessarias')
            and fonte.get('publicar') is False
            and fonte.get('prova',{}).get('aprovacao_humana') is False):
            out.append({'asset_id':fonte['id'],'natureza':'video_acao_real',
                        'estado':'V4_ACAO_OBSERVADA_PRIVADA',
                        'sha_catalogo':fonte['sha256_origem']})
    return out


def montar_cena(cena:dict,indice:dict,fonte:dict,inicio:float)->tuple[dict,str,dict]:
    """A mesma cena física pode ser mostrada com vídeo real quando a ação
    anotada cobre o contrato V2, sem construir novo renderer por episódio.
    """
    from src.v2 import contrato as cv2
    action=cv2.declarado(cena)
    proof=validar(fonte,bytes_obrigatorios=False)
    if not candidatos(action,{'itens':[fonte]}):
        # candidatos() exige natureza/id de acervo já normalizados
        normalized={**fonte,'natureza':'video_acao_real'}
        if not candidatos(action,{'itens':[normalized]}):
            _fail('FATO','o evento do roteiro ou as ações diferem da fonte')
    if abs(float(cena['duracao_s'])-proof['duracao_s'])>.05:
        _fail('NARRACAO','não mudar velocidade do original para caber no roteiro')
    uid='acao-'+proof['sha256'][:16]
    seq=fonte['janela']['eventos']
    sha=proof['sha256']
    video={
        'local_source':fonte['arquivo'],'expected_sha256':sha,
        'url':fonte['pagina'],'page':fonte['pagina'],
        'license':'REVIEW_PENDING','rights_status':'REVIEW_PENDING',
        'credit':fonte['credit'],'media_type':'video',
        'width':fonte['width'],'height':fonte['height'],'duration_s':fonte['duration_s'],
    }
    shot={
        'id':str(cena['id']),'start':round(inicio,4),
        'end':round(inicio+proof['duracao_s'],4),'type':'video',
        'asset':uid,'source_in_seconds':proof['inicio_s'],
        'evidence':'literal',
        'literal_identity':str(action['id'])+' · '+fonte['sujeito'],
        'lead':'REGISTRO DOCUMENTAL · NASA',
        'headline':fonte['sujeito'].upper(),
        'subject':'SEQUÊNCIA TEMPORAL CONDENSADA · NASA/JPL-CALTECH',
        'cues':[{'at':e['at'],
                 # Linguagem de tela deriva do identificador do evento visível,
                 # sem palavras duplicadas e sem narrar "pedra solta".
                 'label':e['acao_id'].replace('_',' ').upper()[:42]}
                for e in seq],
        'video_framing':{
            'modo':'fonte_integral','sha256_origem':sha,
            'inspecao':fonte['observacao'],
            'motivo':'preservar integralmente a rocha, a broca e o braço visível'},
        'progressao_visual':{
            'tipo':'acao_observada','sha256_origem':sha,
            'inspecao':fonte['observacao'],
            'eventos':[{'at':e['at'],'fonte_s':e['fonte_s'],'acao_visivel':e['acao_visivel']}
                       for e in seq],
        },
        'direcao_evento':{
            'intencao':'mostrar_registro',
            'fato_id':action['id'],
            'aprendizado':'Mostrar posições distintas do braço, sem afirmar ver o instante exato da liberação da pedra',
        },
    }
    return shot,uid,video
