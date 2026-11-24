"""E215/E216: reuse authorial SVG geometry and render a common private visual stage.
This is an adapter to the existing renderers, not a solver or new mechanism template.
"""
import io,json,math,hashlib,subprocess,tempfile
from pathlib import Path
from dataclasses import asdict
import cairosvg
from PIL import Image, ImageDraw, ImageFont
from .palco_vertical import CaixaVisivel, ajustar_envelope, extrair_grupo_svg

PROFILE=json.loads(Path(__file__).with_name('perfil_palco_editorial.json').read_text())
FONT=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
BOLD=FONT.with_name('DejaVuSans-Bold.ttf')

def _text(d,xy,txt,maxwidth,size,fill,bold=False):
    f=ImageFont.truetype(str(BOLD if bold else FONT),size)
    while d.textlength(txt,font=f)>maxwidth and size>12:
        size-=1
        f=ImageFont.truetype(str(BOLD if bold else FONT),size)
    if d.textlength(txt,font=f)>maxwidth:
        raise ValueError('E216-TEXTO-LONGO')
    d.text(xy,txt,font=f,fill=fill)

def renderizar(frames,grupo,arquivo,*,fps,titulo,fonte):
    """All frames are measured in an overscanned transparent raster.
    A single transform is applied to the union, never to individual pieces.
    Labels inside the physical group are retained, not claimed UI-safe.
    """
    if fps not in (24,30) or not titulo or not fonte:
        raise ValueError('E215-ENTRADA')
    arquivo=Path(arquivo);arquivo.parent.mkdir(parents=True,exist_ok=True)
    p=PROFILE; w,h=p['resolution']
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp); boxes=[]; paths=[]
        for i,svg in enumerate(frames):
            if i>=900:raise ValueError('E215-DURACAO')
            data=cairosvg.svg2png(bytestring=extrair_grupo_svg(svg,grupo).encode())
            with Image.open(io.BytesIO(data)) as im:
                layer=im.convert('RGBA')
            b=layer.getchannel('A').getbbox()
            if not b or b[0]<=1 or b[1]<=1 or b[2]>=layer.width-1 or b[3]>=layer.height-1:
                raise ValueError('E215-ALPHA-CORTADO')
            boxes.append(b)
            dest=root/f'{i:04d}.png';layer.save(dest);paths.append(dest)
        if not paths:raise ValueError('E215-SEM-QUADROS')
        b=(min(x[0] for x in boxes),min(x[1] for x in boxes),max(x[2] for x in boxes),max(x[3] for x in boxes))
        fit=ajustar_envelope(CaixaVisivel(*b),CaixaVisivel(*p['stage']),p['scale_max'])
        # Header intentionally within the conservative text zone, physically
        # separate from the visual stage. No lab progress bars or old footers.
        bg=Image.new('RGB',(w,h),p['background']);d=ImageDraw.Draw(bg)
        _text(d,(80,150),'CORINGA EXPLICA',300,13,p['muted'],True)
        d.rectangle((80,171,140,174),fill=p['accent'])
        _text(d,(80,179),titulo,300,24,p['ink'],True)
        _text(d,(80,210),'ESQUEMA ILUSTRATIVO · '+fonte,300,14,p['muted'])
        proc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{w}x{h}','-r',str(fps),'-i','-','-an','-c:v','libx264','-crf','20','-pix_fmt','yuv420p',str(arquivo)],stdin=subprocess.PIPE)
        try:
            for path in paths:
                with Image.open(path) as im:
                    a=im.crop(b).resize((fit.largura,fit.altura),Image.Resampling.LANCZOS)
                canvas=bg.copy();canvas.paste(a,(fit.x,fit.y),a)
                proc.stdin.write(canvas.tobytes())
        finally:
            proc.stdin.close()
        if proc.wait()!=0:raise ValueError('E215-FFMPEG')
    report={'schema':p['schema'],'frames':len(paths),'fps':fps,'duration_s':len(paths)/fps,
            'group':grupo,'envelope':list(b),'fit':asdict(fit),'profile':p,
            'width_fraction':fit.largura/w,'height_fraction':fit.altura/h,
            'source':fonte,'sha256':hashlib.sha256(arquivo.read_bytes()).hexdigest(),
            'publish':False,'visual_approval':'PENDENTE','word_caption_approval':'PENDENTE'}
    arquivo.with_suffix('.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    return report
