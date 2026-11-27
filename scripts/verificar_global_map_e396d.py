import json,subprocess,hashlib
from pathlib import Path
from PIL import Image,ImageStat,ImageDraw
from io import BytesIO
ROOT=Path('qa_global_e396d')
def main():
    receipt={}
    dur=json.loads((ROOT/'manifest.json').read_text())['camera']['duration'];total=dur*30
    times=tuple(round(x*(dur-.2)/7,2) for x in range(8))
    for name,dim in [('wide',(1280,640)),('portrait',(720,1280))]:
        f=ROOT/(name+'.mp4')
        p=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=width,height,nb_frames,codec_type,r_frame_rate','-of','json',str(f)]))
        v=next(x for x in p['streams'] if x['codec_type']=='video')
        assert (v['width'],v['height'])==dim and int(v['nb_frames'])==total and v['r_frame_rate']=='30/1'
        subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(f),'-f','null','-'],check=True)
        frames=[]
        for t in times:
            im=Image.open(BytesIO(subprocess.check_output(['ffmpeg','-v','error','-ss',str(t),'-i',str(f),'-frames:v','1','-f','image2pipe','-vcodec','png','-']))).convert('RGB')
            assert max(ImageStat.Stat(im).stddev)>9,('E396-BLANK',name,t)
            im.thumbnail((320,480));frames.append(im)
        w,h=frames[0].size;sheet=Image.new('RGB',(w*4,(h+22)*2),'#111111');d=ImageDraw.Draw(sheet)
        for i,im in enumerate(frames):
            x=i%4*w;y=i//4*(h+22);sheet.paste(im,(x,y));d.text((x+5,y+h+3),str(times[i])+'s',fill='white')
        sheet.save(ROOT/(name+'-contact.jpg'),quality=94)
        receipt[name]={'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'frames':total,'dimensions':dim}
    (ROOT/'qa.json').write_text(json.dumps({'publish':False,'visual_approval':'PENDING','videos':receipt},indent=2))
if __name__=='__main__':main()
