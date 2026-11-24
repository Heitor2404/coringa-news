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


def _font(size,bold=False):
    return ImageFont.truetype(str(BOLD if bold else FONT),size)

def _wrap(d,text,f,width):
    lines=[]
    for word in text.split():
        if not lines or d.textlength(lines[-1]+' '+word,font=f)>width:
            if d.textlength(word,font=f)>width:
                return None
            lines.append(word)
        else:
            lines[-1]+=' '+word
    return lines

def _opening(d,titulo,subtitulo):
    # Fit by real font metrics; shorten editorial copy rather than overlap the art.
    for size in range(27,19,-1):
        ft=_font(size,True); fs=_font(16)
        titles=_wrap(d,titulo,ft,300)
        subs=_wrap(d,subtitulo,fs,300) if subtitulo else []
        if titles is None or subs is None or not titles or len(titles)>2 or len(subs)>2:
            continue
        y=184; rows=[]
        for lines,font,color in ((titles,ft,PROFILE['ink']),(subs,fs,PROFILE['muted'])):
            for line in lines:
                box=d.textbbox((80,y),line,font=font,anchor='lt')
                rows.append((line,font,color,box))
                y=box[3]+3
        if rows[-1][3][3]<=235:
            for line,font,color,box in rows:
                d.text((box[0],box[1]),line,font=font,fill=color,anchor='lt')
            return
    raise ValueError('E216-RESUMIR-TITULO-SUBTITULO')

def _caption(d,words,highlight):
    tp=PROFILE['typography']
    for size in range(tp['caption_size'],17,-1):
        f=_font(size,True); text=' '.join(words)
        width=d.textlength(text,font=f)
        if width<=276:
            x=230-width/2
            y=208
            b=d.textbbox((x,y),text,font=f,anchor='lt')
            if b[3]+4>235: continue
            d.rounded_rectangle((x-10,205,x+width+10,b[3]+4),radius=4,fill=tp['caption_bg'])
            for i,word in enumerate(words):
                d.text((x,y),word,font=f,anchor='lt',fill=tp['caption_highlight'] if i==highlight else tp['caption_ink'])
                x+=d.textlength(word+' ',font=f)
            return
    raise ValueError('E216-DIVIDIR-GRUPO-LEGENDA')

def cabecalho(titulo,subtitulo,fonte_curta,caption=None):
    p=PROFILE
    bg=Image.new('RGB',tuple(p['resolution']),p['background']); d=ImageDraw.Draw(bg)
    d.text((80,150),'CORINGA EXPLICA',font=_font(12,True),fill=p['muted'],anchor='lt')
    source='ESQUEMA · '+fonte_curta
    f=_font(11)
    if d.textlength(source,font=f)>140:
        raise ValueError('E216-FONTE-CURTA')
    d.text((380,150),source,font=f,fill=p['muted'],anchor='rt')
    d.rectangle((80,169,124,172),fill=p['accent'])
    if caption is None:
        _opening(d,titulo,subtitulo)
    else:
        # The title remains visible but secondary. The caption occupies the
        # opening subtitle lane, never the art or bottom platform UI.
        _text(d,(80,181),titulo,300,17,p['ink'],True)
        _caption(d,caption['words'],caption['highlight'])
    return bg

def validar_legendas(grupos,duracao,origem):
    if grupos and origem not in ('LAB_TEMPOS_DECLARADOS','PALAVRAS_MEDIDAS'):
        raise ValueError('E216-ORIGEM-LEGENDA')
    prev=0.
    for g in grupos:
        a,b=g['start'],g['end']; ws=g['words']; hi=g['highlight']
        if (not all(math.isfinite(v) for v in (a,b)) or a<prev or b<=a or b>duracao+1e-6
            or not isinstance(ws,list) or not 1<=len(ws)<=5
            or not all(isinstance(w,str) and w and not any(c.isspace() for c in w) for w in ws)
            or type(hi) is not int or not 0<=hi<len(ws)):
            raise ValueError('E216-LEGENDA-INVALIDA')
        prev=b


def renderizar(frames,grupo,arquivo,*,fps,titulo,fonte,subtitulo='',fonte_curta='',legendas=None,origem_legendas=None):
    """All frames are measured in an overscanned transparent raster.
    A single transform is applied to the union, never to individual pieces.
    Labels inside the physical group are retained, not claimed UI-safe.
    """
    if fps not in (24,30) or not titulo or not fonte:
        raise ValueError('E215-ENTRADA')
    arquivo=Path(arquivo);arquivo.parent.mkdir(parents=True,exist_ok=True)
    p=PROFILE; w,h=p['resolution']
    legendas=legendas or []
    if not fonte_curta: fonte_curta='MODELO DIDÁTICO'
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
        validar_legendas(legendas,len(paths)/fps,origem_legendas)
        bg=cabecalho(titulo,subtitulo,fonte_curta)
        headers=[(g,cabecalho(titulo,subtitulo,fonte_curta,g)) for g in legendas]
        proc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{w}x{h}','-r',str(fps),'-i','-','-an','-c:v','libx264','-crf','20','-pix_fmt','yuv420p',str(arquivo)],stdin=subprocess.PIPE)
        try:
            for i,path in enumerate(paths):
                with Image.open(path) as im:
                    a=im.crop(b).resize((fit.largura,fit.altura),Image.Resampling.LANCZOS)
                header=next((h for g,h in headers if g['start']<=i/fps<g['end']),bg)
                canvas=header.copy();canvas.paste(a,(fit.x,fit.y),a)
                proc.stdin.write(canvas.tobytes())
        finally:
            proc.stdin.close()
        if proc.wait()!=0:raise ValueError('E215-FFMPEG')
    report={'schema':p['schema'],'frames':len(paths),'fps':fps,'duration_s':len(paths)/fps,
            'group':grupo,'envelope':list(b),'fit':asdict(fit),'profile':p,
            'width_fraction':fit.largura/w,'height_fraction':fit.altura/h,
            'source':fonte,'source_display':fonte_curta,'typography_version':p['typography']['version'],
            'caption_origin':origem_legendas,'caption_groups':legendas,'sha256':hashlib.sha256(arquivo.read_bytes()).hexdigest(),
            'publish':False,'visual_approval':'PENDENTE','word_caption_approval':'PENDENTE'}
    arquivo.with_suffix('.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    return report
