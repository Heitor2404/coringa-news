"""Private coarse inspection of previously acquired source, not semantic approval."""
import json,subprocess,io,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
def main():
    root=Path('stage_documental/e316')
    h='783f746a234d1378158d7ca3b74ed63ab0e0526664bc72c73c5222a22315b25c'
    src=root/(h+'.mp4')
    times=list(range(23,63,2))
    board=Image.new('RGB',(960,200*((len(times)+2)//3)),'#17191b')
    draw=ImageDraw.Draw(board);samples=[]
    for i,t in enumerate(times):
        raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(t),'-i',str(src),'-frames:v','1','-vf','scale=320:-2','-f','image2pipe','-vcodec','png','pipe:1'],timeout=30)
        im=Image.open(io.BytesIO(raw)).convert('RGB')
        x=i%3*320;y=i//3*200
        draw.text((x+7,y+3),str(t)+' s',fill='white')
        board.paste(im,(x,y+18))
        samples.append({'fonte_s':t,'px':list(im.size),'pixels_sha256':hashlib.sha256(im.tobytes()).hexdigest()})
    board.save(root/'scan.jpg',quality=93)
    (root/'scan.json').write_text(json.dumps({'publish':False,'sha256':h,'samples':samples,'semantic_review':'PENDING'}))
if __name__=='__main__':main()
