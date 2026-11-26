"""E349: original smoke test updated to owner-approved black background."""
import json
from pathlib import Path
from PIL import Image
root=Path('stage_documental/e286/e290')
checks=[]
for shot in ('video_horizontal_navio','foto_horizontal_roraima','qa-4-5-collision'):
    with Image.open(root/f'{shot}-2.png') as im:
        im=im.convert('RGB')
        assert im.size==(1080,1920)
        vals=[im.getpixel((x,y)) for x in range(40,130,10) for y in range(1630,1750,10)]
        vals += [im.getpixel((x,y)) for y in range(1640,1750,2) for x in range(max(0,2704-y-3),min(1080,2704-y+4))]
        assert all(v==(0,0,0) for v in vals),(shot,vals[:5])
        checks.append({'shot':shot,'black_fraction':1.0,'background':'BLACK_SOLID_V1'})
(root/'fundo_pixels.json').write_text(json.dumps(checks,indent=2))
print('E349_BACKGROUND_PIXELS_OK',checks)
