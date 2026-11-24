"""Private review delivery of a narrated FilmeEditorial, using the existing bot.
No publication; no alternative destination; no secret or Telegram response logged.
"""
from __future__ import annotations
import argparse,json,math,subprocess
from pathlib import Path
from src.v3 import previa_telegram as T
from src.v4.formatos import politica_animacao as P

def validar(pasta):
    pasta=Path(pasta)
    video=pasta/'filme.mp4';props=pasta/'props.json'
    qa=json.loads((pasta/'qa.json').read_text(encoding='utf8'))
    p=json.loads(props.read_text(encoding='utf8'))
    if (qa.get('publish') is not False or qa.get('visual_approval')!='PENDING'
        or qa.get('voice_approval')!='PENDING' or p.get('private_review_only') is not True
        or p.get('preview') is not True):
        raise ValueError('E223-ESCOPO-PRIVADO')
    P.validar_entrega_privada(props,video,qa)
    dur=float(qa['duration'])
    if not math.isfinite(dur) or dur<60 or abs(float(p['duracao'])-dur)>.1:
        raise ValueError('E223-DURACAO')
    verificar_video(video,dur)
    return video,dur

def verificar_video(video,dur):
    q=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)],timeout=45))
    streams=q['streams']
    v=next((x for x in streams if x['codec_type']=='video'),{})
    if ((v.get('width'),v.get('height')) not in ((540,960),(1080,1920))
        or not any(x['codec_type']=='audio' for x in streams)
        or abs(float(q['format']['duration'])-dur)>.2):
        raise ValueError('E223-MP4-DIVERGENTE')

def entregar(pasta,titulo):
    video,dur=validar(pasta)
    # All failures from the bot are sanitized: requests exceptions may contain its token.
    try:
        chat,info=T.chat_autorizado()
        envio=T._caber(video)
        verificar_video(envio,dur)
        result=T._api('sendVideo',{'chat_id':chat,'caption':
            ('CORINGA EXPLICA · PRÉVIA PRIVADA\n'+titulo+
             f'\n{dur:.1f}s · narrado\nAGUARDANDO REVISÃO HUMANA · NÃO PUBLICADO')[:1000],
            'supports_streaming':'true'},('video',envio))
        if not isinstance(result,dict) or not result.get('message_id'):
            raise RuntimeError('Telegram sem recibo')
    except Exception:
        raise RuntimeError('E223-TELEGRAM: entrega privada não confirmada; consultar bot e configuração') from None
    return {'enviado':True,'publicado':False,'duracao':dur,'recomprimido':envio!=video}

def main():
    a=argparse.ArgumentParser()
    a.add_argument('pasta',type=Path);a.add_argument('--titulo',required=True)
    args=a.parse_args()
    print(json.dumps(entregar(args.pasta,args.titulo),ensure_ascii=False))
if __name__=='__main__':main()
