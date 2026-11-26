import json
from pathlib import Path
from PIL import Image,ImageChops
def main():
    root=Path('stage_documental/e286')
    rows=json.loads((root/'detail-measures.json').read_text())['rows']
    images=[Image.open(root/('detail-'+r['shot']+'.png')).convert('RGB') for r in rows]
    assert all(im.size==(1080,1920) for im in images)
    a,b,c=images
    diff=ImageChops.difference(a,b)
    assert diff.getbbox() is not None,'E309 marker not rendered'
    assert ImageChops.difference(a,c).getbbox() is None,'E309 collision changed pixels'
    x,y,r,s=rows[1]['box']
    inside=(int(x+14)+1,int(y+14)+1,int(r-14),int(s-14))
    assert diff.crop(inside).getbbox() is None,'E309 evidence pixels changed'
    changed=diff.getbbox()
    assert changed[0]>=x-5 and changed[1]>=y-5 and changed[2]<=r+5 and changed[3]<=s+5
    (root/'detail-pixels.json').write_text(json.dumps({'publish':False,'evidence_pixels_unchanged':True,'collision_identical':True,'changed_bbox':changed,'visual_approval':'PENDING'}))
if __name__=='__main__':main()
