"""Investigação editorial de footage licenciado: encontra MOVIMENTO de eclusas.
Nunca usa vídeo sem confirmar imagem e licença. Apenas trabalho temporário privado.
Testa fontes em ordem e gera contatos/relatório para auditoria humana.
"""
from __future__ import annotations
import html
import os
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

from PIL import Image, ImageDraw

CANDIDATOS = [
    {"id":"gatun-2017-fechamento","url":"https://www.dvidshub.net/video/543462/uscgc-tampa-panama-canal-time-lapse-video","licenca":"Public domain / DVIDS video 543462","fonte":"US Coast Guard / Lisa Ferdinando","offset_s":21},
    {"id":"comfort-2018-inicio","url":"https://www.dvidshub.net/video/634226/usns-comfort-transits-panama-canal","licenca":"Public domain / DVIDS video 634226","fonte":"US Navy / Keith Wilson","offset_s":0},
    {"id":"comfort-2018-meio","url":"https://www.dvidshub.net/video/634226/usns-comfort-transits-panama-canal","licenca":"Public domain / DVIDS video 634226","fonte":"US Navy / Keith Wilson","offset_s":27},
    {"id":"monsoor-2018-meio","url":"https://www.dvidshub.net/video/653679/panama-canal-time-lapse","licenca":"Public domain / DVIDS video 653679","fonte":"US Navy / Robert Reinheimer","offset_s":50},
    {"id":"monsoor-2018-final","url":"https://www.dvidshub.net/video/648046/uss-michael-monsoor-transits-panama-canal","licenca":"Public domain / DVIDS video 648046","fonte":"US Navy / Robert Reinheimer","offset_s":116},
]

MAX_BYTES=135_000_000

def escolher_format(info):
    fs=info.get('formats') or ([info] if info.get('url') else [])
    fs=[x for x in fs if x.get('url') and x.get('vcodec') not in ('none',None)
        and (x.get('ext')=='mp4' or '.mp4' in x.get('url',''))]
    if not fs:
        fs=[x for x in (info.get('formats') or []) if x.get('url') and x.get('vcodec') not in ('none',None)]
    # Prefer no DRM, 720p+ at reasonable size, avoid 4K downloads.
    fs=[x for x in fs if (x.get('height') or 720)<=1080
        and (x.get('filesize') or x.get('filesize_approx') or 0)<=MAX_BYTES
        and not x.get('has_drm')]
    fs.sort(key=lambda x:(min((x.get('height') or 0),1080),x.get('tbr') or 0),reverse=True)
    return fs[0] if fs else None


def capturar(entrada,destino):
    import yt_dlp
    dest=Path(destino)
    estado={'id':entrada['id'],'pagina':entrada['url'],'licenca':entrada['licenca'],'fonte':entrada['fonte']}
    try:
        with yt_dlp.YoutubeDL({'quiet':True,'no_warnings':True,'skip_download':True,'socket_timeout':20,
                               'extractor_retries':1,'retries':1,'noplaylist':True}) as ydl:
            info=ydl.extract_info(entrada['url'],download=False)
        sel=escolher_format(info)
        if not sel:
            raise ValueError('sem formato de vídeo utilizável')
        estado.update({'offset_s':entrada.get('offset_s',0),'captura':'yt-dlp','resolucao_fonte':[sel.get('width'),sel.get('height')],
                       'duracao_fonte':info.get('duration'),
                       'titulo':info.get('title'), 'fmt':sel.get('format_id')})
        url=sel['url']
    except Exception as e:
        estado['extrator_erro']=f'{type(e).__name__}: {str(e)[:200]}'
        # Pexels HTML eventualmente expõe link direto video-files.
        try:
            import requests
            r=requests.get(entrada['url'],timeout=18,headers={'User-Agent':'Mozilla/5.0'})
            r.raise_for_status()
            h=html.unescape(r.text).replace('\\/','/')
            urls=re.findall(r'https?://(?:videos|player).pexels.com/[^"\\\\\s<>]+?\.mp4(?:\?[^"<>\\\\\s]*)?',h)
            urls=[unquote(u) for u in urls if 'video-files' in u or 'videos.pexels' in u]
            if not urls: raise ValueError('sem URL de vídeo verificada no HTML')
            url=min(urls,key=len)
            estado['captura']='Pexels HTML preview'
        except Exception as exc:
            estado.update({'resultado':'SEM_FONTE','motivo':str(exc)[:240]})
            return estado
    raw=dest/(entrada['id']+'.mp4')
    hero = os.environ.get('SCOUT_HERO_HD') == '1'
    try:
        proc=subprocess.run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y',
            '-ss',str(entrada.get('offset_s',0)),'-i',url,
            '-t','11' if hero else '20','-an',
            '-vf','fps=30,scale=1920:-2' if hero else 'fps=30,scale=960:-2',
            '-c:v','libx264','-preset','medium' if hero else 'veryfast',
            '-crf','20' if hero else '24','-movflags','+faststart',
            str(raw)],capture_output=True,text=True,timeout=160)
        if proc.returncode or not raw.is_file() or raw.stat().st_size<30000:
            raise RuntimeError((proc.stderr or '')[-350:] or 'sem saída válida')
        import hashlib
        estado.update({'resultado':'CANDIDATO_SEM_REVISÃO','arquivo':raw.name,
                       'sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),
                       'bytes':raw.stat().st_size})
        return estado
    except Exception as e:
        estado.update({'resultado':'SEM_CLIP','motivo':f'{type(e).__name__}: {str(e)[:300]}'})
        return estado


def contatos(destino,casos):
    destino=Path(destino)
    for e in casos:
        if e.get('resultado')!='CANDIDATO_SEM_REVISÃO': continue
        f=destino/e['arquivo']; ims=[]
        for t in (1,5,9,13,17):
            o=destino/f"{e['id']}_{t:02}.jpg"
            p=subprocess.run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y',
                              '-ss',str(t),'-i',str(f),'-frames:v','1','-vf','scale=360:203',
                              str(o)],capture_output=True,timeout=25)
            if p.returncode==0 and o.is_file():
                ims.append((t,Image.open(o).convert('RGB')))
        if not ims:continue
        board=Image.new('RGB',(360*len(ims),258),'#080E16')
        d=ImageDraw.Draw(board)
        for i,(t,img) in enumerate(ims):
            board.paste(img,(i*360,0))
            d.text((i*360+12,214),f'{e["id"]} · {t:02d}s',fill='#FFD21F')
        board.save(destino/(e['id']+'_board.jpg'),quality=85)


def main():
    dest=Path(sys.argv[1]);dest.mkdir(parents=True,exist_ok=True)
    casos=[]
    candidatos = ([x for x in CANDIDATOS if x['id']=='comfort-2018-meio']
                  if os.environ.get('SCOUT_HERO_HD')=='1' else CANDIDATOS)
    for c in candidatos:
        print('SCOUT',c['id'],flush=True)
        r=capturar(c,dest);casos.append(r)
        print('RESULTADO',json.dumps(r,ensure_ascii=False)[:600],flush=True)
    contatos(dest,casos)
    (dest/'relatorio.json').write_text(json.dumps({'fontes':casos,'aprovacao':'PENDENTE_REVISÃO_VISUAL_HUMANA'},
                                         ensure_ascii=False,indent=2),encoding='utf-8')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
