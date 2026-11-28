import json,hashlib,os,subprocess
from pathlib import Path
from src.v3 import previa_telegram as T
ROOT=Path('qa_global_e396g')
def probe(f):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(f)]))['streams']
def main():
    f=ROOT/'portrait.mp4'
    if not f.is_file():return
    chat,_=T.chat_autorizado()
    # One standard MP4 video, never sendAnimation or sendDocument.
    # Silent AAC track prevents the silent-video presentation as animation.
    out=ROOT/'telegram'/'portrait.mp4';out.parent.mkdir(exist_ok=True)
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(f),'-f','lavfi','-i','anullsrc=channel_layout=stereo:sample_rate=48000','-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','96k','-shortest','-movflags','+faststart',str(out)],check=True)
    actual=T._caber(out)
    streams=probe(actual);v=next(s for s in streams if s['codec_type']=='video')
    assert (v['width'],v['height'])==(720,1280) and v['codec_name']=='h264'
    assert any(s['codec_type']=='audio' and s['codec_name']=='aac' for s in streams)
    r=T._api('sendVideo',{'chat_id':chat,'caption':'E396G · '+os.environ.get('MAP_CASE','mapa')+' · VERTICAL · prova privada; sem publicação','supports_streaming':'true','width':720,'height':1280},('video',actual))
    if not isinstance(r,dict) or not r.get('message_id') or not r.get('video') or r.get('animation'):raise ValueError('E396G-DELIVERY-NOT-VIDEO')
    (ROOT/'delivery.json').write_text(json.dumps({'publish':False,'complete':True,'items':[{'file':f.name,'mode':'sendVideo','telegram_type':'video','message_id':r['message_id'],'original_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'sent_sha256':hashlib.sha256(actual.read_bytes()).hexdigest(),'audio':'silent AAC','dimensions':[720,1280]}]},indent=2))
if __name__=='__main__':main()
