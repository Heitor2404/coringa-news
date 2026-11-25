"""E293: smoke-test pixels of the actual private compositor, not mockups."""
import json
from pathlib import Path
from PIL import Image

root=Path('stage_documental/e286/e290')
report=json.loads((root/'medidas.json').read_text())
checks=[]
for shot in ('video_horizontal_navio','foto_horizontal_roraima','qa-4-5-collision'):
    with Image.open(root/f'{shot}-2.png') as im:
        im=im.convert('RGB')
        assert im.size==(1080,1920)
        # Text-free corner and bottom patches, outside actual source media.
        # New background is neutral charcoal, not the legacy blue gradient.
        vals=[im.getpixel((x,y)) for x in range(40,130,10) for y in range(1630,1750,10)]
        neutral=sum(max(v)-min(v)<=9 and max(v)<=65 for v in vals)/len(vals)
        assert neutral>=.95,(shot,neutral)
        # The authored diagonal must be visible near the bottom-right; not just black.
        accent=[im.getpixel((x,y)) for y in range(1640,1750,2)
                for x in range(max(0,2704-y-3),min(1080,2704-y+4))]
        warm=sum(r>85 and r>g and g>b+15 for r,g,b in accent)
        assert warm>=10,(shot,warm)
        checks.append({'shot':shot,'neutral_fraction':neutral,'warm_diagonal_samples':warm})
(root/'fundo_pixels.json').write_text(json.dumps(checks,indent=2))
print('E293_BACKGROUND_PIXELS_OK',checks)
