"""Adaptador NASA SVS de prospecção de ações reais — SEM homologação.

Reutiliza FFprobe e frames do coletor por ações; NÃO usa descrição oficial
como substituto da inspeção de pixels. Vídeo pode ser sequência de fotografias
de exploração espacial: distinguir sempre de filmagem contínua real-time.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from urllib.parse import urlsplit
from PIL import Image,ImageDraw
from src.v4.formatos import prospeccao_video_acao as BASE

MAX_BYTES=30_000_000


def validar_origem(x):
    if not isinstance(x,dict) or x.get('provedor')!='nasa_svs':
        raise ValueError('N-PROVEDOR: somente adaptador NASA SVS')
    if x.get('aprovacao_editorial') is not False or x.get('media_tipo')!='video/mp4':
        raise ValueError('N-GATE: arquivo não foi homologado editorialmente')
    if not isinstance(x.get('id'),str) or not re.fullmatch(r'[a-z][a-z0-9_]{5,60}',x['id']):
        raise ValueError('N-ID: registro inválido')
    for k in ('processo_declarado','evento_real_declarado','credito','nota_direitos'):
        minimum = 20 if k in ('processo_declarado','evento_real_declarado','nota_direitos') else 7
        if not isinstance(x.get(k),str) or len(x[k].strip())<minimum:
            raise ValueError('N-METADATA: falta '+k)
    site=urlsplit(str(x.get('pagina') or ''))
    dl=urlsplit(str(x.get('download') or ''))
    if (site.scheme!='https' or site.hostname!='svs.gsfc.nasa.gov'
        or not re.fullmatch(r'/\d{4,6}/?',site.path)
        or dl.scheme!='https' or dl.hostname!='svs.gsfc.nasa.gov'
        or not dl.path.startswith('/vis/') or not dl.path.endswith('.mp4')
        or dl.username or dl.password or dl.port or dl.query or dl.fragment):
        raise ValueError('N-URL: apenas NASA SVS oficial')
    if x.get('expected_sha256') is not None and (
       not isinstance(x['expected_sha256'],str)
       or not re.fullmatch('[0-9a-f]{64}',x['expected_sha256'])):
        raise ValueError('N-SHA: hash pinado inválido')
    if not isinstance(x.get('cap_bytes'),int) or not 1500000<=x['cap_bytes']<=MAX_BYTES:
        raise ValueError('N-LIMITE: teto incompatível')


def baixar(x,destino,fetch=None):
    validar_origem(x)
    if fetch is None:
        import requests
        def fetch(url):
            with requests.get(url,stream=True,timeout=(12,50),allow_redirects=False,
                              headers={'User-Agent':'CoringaExplica/QA-Research/1.0'}) as resp:
                if resp.status_code!=200:
                    raise ValueError(f'N-HTTP: status {resp.status_code}; sem burlar bloqueio')
                ctype=resp.headers.get('Content-Type','').lower()
                if not any(t in ctype for t in ('video/mp4','application/octet-stream')):
                    raise ValueError('N-TIPO: arquivo não é vídeo MP4')
                if int(resp.headers.get('Content-Length') or 0)>x['cap_bytes']:
                    raise ValueError('N-TAMANHO: fonte acima do teto')
                total=bytearray()
                for chunk in resp.iter_content(256*1024):
                    total.extend(chunk)
                    if len(total)>x['cap_bytes']:
                        raise ValueError('N-TAMANHO: fonte acima do teto')
                return bytes(total)
    content=fetch(x['download'])
    if not isinstance(content,bytes) or len(content)<200_000 or len(content)>x['cap_bytes']:
        raise ValueError('N-BYTES: original ausente/incompleto')
    digest=hashlib.sha256(content).hexdigest()
    if x.get('expected_sha256') is not None and digest!=x['expected_sha256']:
        raise ValueError('N-SHA: arquivo mudou desde a aprovação de bytes')
    destino=Path(destino)
    destino.parent.mkdir(parents=True,exist_ok=True)
    destino.write_bytes(content)
    return {'sha256':digest,'bytes':len(content),
            'integridade':'BAIXADO_E_MEDIDO_SEM_HASH_PUBLICADO' if not x.get('expected_sha256') else 'BAIXADO_SHA256_TRAVADO'}


def inspecionar(master:Path,destino:Path)->dict:
    info=BASE.ffprobe(master)
    if not 3<=info['duracao_s']<=600:
        raise ValueError('N-DURACAO: fonte inviável')
    contato=Image.new('RGB',(4*432,3*273),(10,20,30))
    d=ImageDraw.Draw(contato)
    stamps=[]
    for j in range(12):
        at=round(info['duracao_s']*(j+.5)/12,3)
        img=BASE.frame(master,at)
        img.thumbnail((420,238))
        col,row=j%4,j//4
        contato.paste(img,(col*432+(432-img.width)//2,row*273))
        d.text((col*432+8,row*273+243),
               f'ORIGINAL NASA SVS {at:.2f}s  |  frame {j+1}/12',fill=(240,242,244))
        stamps.append(at)
    destino.parent.mkdir(parents=True,exist_ok=True)
    contato.save(destino,quality=91)
    return {'sonda':info,'contato':destino.name,'quadros':stamps,
            'tipo_original':'SEQUENCIA_DAS_CAMERAS_DO_ROVER',
            'fato_corresponde_a_narrativa':'EXIGE_INSPECAO_DOS_QUADROS',
            'direitos_terceiros':'REVISAO_PENDENTE',
            'acao_comprovada':False}


def executar(plan,stage,saida):
    if (not isinstance(plan,dict) or plan.get('versao')!=1
        or plan.get('publicar') is not False
        or plan.get('modo')!='PROSPECCAO_PRIVADA'):
        raise ValueError('N-CONTRATO: apenas QA privada')
    itens=plan.get('itens')
    if not isinstance(itens,list) or not itens:
        raise ValueError('N-CONTRATO: lista vazia')
    for x in itens:validar_origem(x)
    stage,saida=Path(stage),Path(saida)
    saida.mkdir(parents=True,exist_ok=True)
    rows=[]
    for x in itens:
        dst=stage/(x['id']+'.mp4')
        try:
            proof=baixar(x,dst)
            samples=inspecionar(dst,saida/(x['id']+'_contato.jpg'))
            rows.append({'id':x['id'],'status':'FONTE_OFICIAL_SHA256_MEDIDO',
                         'sujeito_evento_declarado':x['evento_real_declarado'],
                         'fonte':x['pagina'],'credito':x['credito'],
                         'sha256':proof['sha256'],'tamanho_bytes':proof['bytes'],
                         'identidade_original':proof['integridade'],'inspecao':samples,
                         'revisao_humana':'PENDENTE','publicar':False})
        except Exception as exc:
            dst.unlink(missing_ok=True)
            rows.append({'id':x['id'],'status':'FONTE_INDISPONIVEL',
                         'motivo':str(exc)[:220],'publicar':False})
    output={'status':'PESQUISA_SEM_APROVACAO','fontes':rows,
            'originais_verificados':sum(x['status']=='FONTE_OFICIAL_SHA256_MEDIDO' for x in rows),
            'acoes_confirmadas':0,'publicar':False,'telegram':False}
    (saida/'relatorio_nasa.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    return output


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('fonte_json',type=Path)
    p.add_argument('stage',type=Path)
    p.add_argument('saida',type=Path)
    v=p.parse_args(argv)
    plan=json.loads(v.fonte_json.read_text('utf8'))
    result=executar(plan,v.stage,v.saida)
    print(json.dumps({'originais':result['originais_verificados'],'acoes':result['acoes_confirmadas']}))
    return 0 if result['originais_verificados']==len(plan['itens']) else 2


if __name__=='__main__':raise SystemExit(main())
