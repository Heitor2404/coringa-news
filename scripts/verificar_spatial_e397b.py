import json,subprocess,hashlib,os,base64
from pathlib import Path
from PIL import Image,ImageStat,ImageDraw,ImageChops
from io import BytesIO
ROOT=Path('qa_spatial_e397b')
def main():
    f=ROOT/'portrait.mp4'
    p=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=width,height,nb_frames,codec_type,r_frame_rate','-of','json',str(f)]))
    v=next(x for x in p['streams'] if x['codec_type']=='video')
    assert (v['width'],v['height'])==(720,1280) and int(v['nb_frames'])==360 and v['r_frame_rate']=='30/1'
    subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(f),'-f','null','-'],check=True)
    frames=[];times=[.2,1.4,2.8,4.5,6.1,7.5,9.5,11.8]
    for t in times:
        im=Image.open(BytesIO(subprocess.check_output(['ffmpeg','-v','error','-ss',str(t),'-i',str(f),'-frames:v','1','-f','image2pipe','-vcodec','png','-']))).convert('RGB')
        assert max(ImageStat.Stat(im).stddev)>8,('E397B-BLANK',t)
        im.thumbnail((270,480));frames.append(im)
    delta=sum(ImageStat.Stat(ImageChops.difference(frames[0],frames[-1])).mean)/3
    assert delta>3,('E397B-NO-MOTION',delta)
    sheet=Image.new('RGB',(270*4,502*2),'#111');draw=ImageDraw.Draw(sheet)
    for i,im in enumerate(frames):
        x=i%4*270;y=i//4*502;sheet.paste(im,(x,y));draw.text((x+5,y+480),str(times[i])+'s',fill='white')
    sheet.save(ROOT/'portrait-contact.jpg',quality=88)
    (ROOT/'portrait-contact.base64.json').write_text(json.dumps({'encoding':'base64','mime':'image/jpeg','content':base64.b64encode((ROOT/'portrait-contact.jpg').read_bytes()).decode('ascii')}))
    (ROOT/'qa.json').write_text(json.dumps({'publish':False,'case':os.environ['MAP_CASE'],'visual_approval':'PENDING','sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'frames':360,'dimensions':[720,1280],'delta_rgb':delta,'geometry':'authored illustrative nominal model; 1 unit=10m'},indent=2))
if __name__=='__main__':main()
