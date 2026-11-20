"""Ponte de CLIPE CONTEXTUAL V3 para diretor híbrido V4.

Roteiro não escolhe o arquivo; biblioteca admite somente fonte NIST/DVIDS
identificada/inspecionada por janela e com o ORIGINAL SHA comprovado.
A anotação editorial não prova licença, ação física, empresa ou época de
outro evento. RESTRITO À QA PRIVADA E COM DIREITOS PENDENTES.
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


def _invalid(msg):
    raise ValueError('V-CURADORIA-'+msg)


def _original(path:Path,digest:str):
    if (path.is_absolute() or '..' in path.parts or
        path.parts[:1]!=('stage_documental',)):
        _invalid('CAMINHO: original deve ficar na stage_documental privada')
    real=(Path.cwd()/path).resolve()
    if not real.is_relative_to(Path.cwd().resolve()) or not real.is_file():
        _invalid('AUSENTE: original não recuperado')
    h=hashlib.sha256()
    with real.open('rb') as fd:
        for block in iter(lambda:fd.read(524288),b''):
            h.update(block)
    if h.hexdigest()!=digest:
        _invalid('SHA: fonte diferente da inspeção')
    out=subprocess.check_output([
        'ffprobe','-v','error','-show_entries',
        'stream=codec_type,width,height:format=duration',
        '-of','json',str(real)],text=True,timeout=40)
    data=json.loads(out)
    stream=[x for x in data.get('streams') or [] if x.get('codec_type')=='video']
    if len(stream)!=1:
        _invalid('STREAM: faixa video ausente/ambígua')
    w,h=int(stream[0]['width']),int(stream[0]['height'])
    dur=float(data['format']['duration'])
    if min(w,h)<700 or not math.isfinite(dur) or dur<5:
        _invalid('DIMENSOES: arquivo insuficiente')
    return {'width':w,'height':h,'duration_s':dur}


def validar_clip(x:dict, *, requer_arquivo:bool=True)->dict:
    if not isinstance(x,dict) or x.get('modo')!='CONTEXTO_PRIVADO_SEM_LICENCA':
        _invalid('MODO: somente QA privada sem liberação')
    sha=x.get('sha256_origem')
    if not isinstance(sha,str) or not re.fullmatch(r'[0-9a-f]{64}',sha):
        _invalid('HASH: falta SHA real')
    orig=x.get('arquivo')
    if not isinstance(orig,str):
        _invalid('CAMINHO: fonte obrigatória')
    path=Path(orig)
    page=urlsplit(str(x.get('pagina') or ''))
    allowed={'nist_kaltura':('www.nist.gov','/video/'),
             'dvids':('www.dvidshub.net','/video/')}
    origin=allowed.get(x.get('provedor'))
    if (not origin or page.scheme!='https' or page.hostname!=origin[0]
        or not page.path.startswith(origin[1])):
        _invalid('ORIGEM: provedor institucional não homologado para aquisição')
    if x.get('licenca')!='REVIEW_PENDING' or x.get('publicar') is not False:
        _invalid('DIREITOS: pendente deve permanecer pendente')
    if not isinstance(x.get('fonte_id'),str) or not x['fonte_id'] or (
        not isinstance(x.get('sujeito'),str) or len(x['sujeito'].strip())<8):
        _invalid('SUJEITO: falta identidade da filmagem')
    if not isinstance(x.get('credit'),str) or len(x['credit'].strip())<8:
        _invalid('CREDITO: origem sem crédito')
    if not isinstance(x.get('inspecao'),str) or len(x['inspecao'].strip())<35:
        _invalid('QUADROS: requer revisão explícita da janela na origem')
    if x.get('comprova_acao') is not False or x.get('comprova_outro_evento') is not False:
        _invalid('FATO: vídeo contextual não prova outra operação')
    if requer_arquivo:
        actual=_original(path,sha)
    else:
        actual={'width':x.get('width'),'height':x.get('height'),
                'duration_s':x.get('source_duration_s')}
    w,h,dur=actual['width'],actual['height'],actual['duration_s']
    if not isinstance(w,int) or not isinstance(h,int) or min(w,h)<700 or (
        not isinstance(dur,(float,int)) or not math.isfinite(dur)):
        _invalid('METADATA: dimensões/tempo não verificados')
    win=x.get('janela') or {}
    begin=win.get('inicio_s')
    span=win.get('duracao_s')
    if (not isinstance(begin,(int,float)) or isinstance(begin,bool)
        or not isinstance(span,(int,float)) or isinstance(span,bool)
        or not all(math.isfinite(t) for t in (begin,span))
        or begin<0 or span<2.2 or span>3.8 or begin+span>dur-.1):
        _invalid('JANELA: recorte inválido ou atravessa fim da fonte')
    points=win.get('roi')
    if not isinstance(points,list) or len(points)<2:
        _invalid('ROI: 2+ regiões observadas em quadros distintos')
    last=-1.
    for p in points:
        t=p.get('at') if isinstance(p,dict) else None
        elems=p.get('elementos') if isinstance(p,dict) else None
        if (not isinstance(t,(float,int)) or not math.isfinite(t) or
            t<0 or t>=span or t<=last or
            not isinstance(elems,list) or len(elems)<2):
            _invalid('ROI: ponto/tempo ou relação entre sujeitos ausente')
        nomes=set()
        for elem in elems:
            if not isinstance(elem,dict) or not isinstance(elem.get('nome'),str):
                _invalid('ROI: identidade de componente ausente')
            name=elem['nome'].strip()
            box=elem.get('bbox')
            if (not name or name in nomes or not isinstance(box,list)
                or len(box)!=4 or any(
                    not isinstance(v,(int,float)) or not math.isfinite(v) for v in box)
                or not 0<=box[0]<box[2]<=1 or not 0<=box[1]<box[3]<=1):
                _invalid('ROI: caixa de componente inválida')
            nomes.add(name)
        last=t
    if abs(points[0]['at'])>.001:
        _invalid('ROI: primeiro ponto precisa cobrir início')
    return actual


def catalogo_com_video(acervo:dict, manifest:dict, *, requer_arquivo=True)->dict:
    """Acrescenta candidato V3 inspecionado à consulta V4 SOMENTE em memória.

    Não promove arquivo para biblioteca permanente ou licença comercial.
    """
    if not isinstance(manifest,dict) or manifest.get('versao')!=1:
        _invalid('MANIFESTO: formato inválido')
    rows=manifest.get('videos')
    if not isinstance(rows,list):
        _invalid('MANIFESTO: lista de origens ausente')
    out=copy.deepcopy(acervo)
    ids={i.get('id') for i in out.get('itens') or []}
    for entry in rows:
        actual=validar_clip(entry,requer_arquivo=requer_arquivo)
        key='v3-'+entry['sha256_origem'][:16]
        if key in ids:
            _invalid('ID: colisão com foto no catálogo')
        ids.add(key)
        it={
            'id':key,'titulo':entry['sujeito'],'mostra':entry['sujeito']+' · '+entry['inspecao'],
            'natureza':'video','sha256_origem':entry['sha256_origem'],
            'licenca':'REVIEW_PENDING','credito':entry['credit'],
            'prova':{'midia_corresponde':True,
                     'licenca_confirmada_pela_API':False,
                     'uso_comercial':'PENDENTE',
                     'apenas_piloto_experimental':True},
            'pagina':entry['pagina'],
            'stage_source':entry['arquivo'],
            'width':actual['width'],'height':actual['height'],
            'duration_s':actual['duration_s'],
            'janela':entry['janela'],'inspecao':entry['inspecao'],
            'publicar':False,'comprova_acao':False,'comprova_outro_evento':False,
            'fonte_id':entry['fonte_id'],
        }
        out.setdefault('itens',[]).append(it)
    return out
