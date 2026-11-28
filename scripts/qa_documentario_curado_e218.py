"""Private, data-driven documentary assembly on FilmeEditorial.
Manual editorial source receipts, not autonomous retrieval or rights clearance.
No thematic renderer, no animation fallback, no publication.
"""
from __future__ import annotations
import hashlib,io,json,math,re,shutil,subprocess,sys,concurrent.futures
from pathlib import Path
from urllib.parse import urlsplit,urljoin
import requests
from bs4 import BeautifulSoup
from PIL import Image,ImageDraw
from src.v4.formatos import filme_editorial as F, diretor_visual_e202 as D, legenda_sync as LS
from src import voz

PUBLIC=Path('motor4/remotion/public')
STAGE=Path('stage_documental/e218')
HEADERS={'User-Agent':'CoringaExplica/1.0 (private editorial QA; GitHub Heitor2404)'}
PAGE_HOST='science.nasa.gov'
ASSET_HOSTS={'assets.science.nasa.gov','science.nasa.gov'}
def write(path,x):
    Path(path).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')

def get(url,hosts,lim):
    u=urlsplit(url)
    if u.scheme!='https' or u.hostname not in hosts or u.username or u.password:
        raise ValueError('E218-ORIGEM')
    with requests.get(url,headers=HEADERS,stream=True,allow_redirects=False,timeout=(10,30)) as r:
        if r.status_code!=200:raise ValueError('HTTP '+str(r.status_code))
        chunks=bytearray()
        for b in r.iter_content(65536):
            chunks.extend(b)
            if len(chunks)>lim:raise ValueError('E218-LIMITE')
        return bytes(chunks)

def nasa_photo(row):
    slug,label=row
    if not re.fullmatch('[a-z0-9-]+',slug):raise ValueError('E218-SLUG')
    page='https://science.nasa.gov/photojournal/'+slug+'/'
    raw=get(page,{PAGE_HOST},5_000_000)
    soup=BeautifulSoup(raw,'html.parser')
    heading=soup.find('h1')
    txt=soup.get_text(' ',strip=True)
    if heading is None or not re.search(r'NASA\s*/\s*JPL(?:-Caltech)?\s*/\s*Space Science Institute',txt,re.I):
        raise ValueError('E218-CREDITO')
    code=re.search(r'\bPIA\d{5}\b',txt)
    if not code:raise ValueError('E218-IDENTIDADE')
    code=code.group(0)
    urls=[]
    for a in soup.find_all('a',href=True):
        u=urljoin(page,a['href'])
        if urlsplit(u).hostname in ASSET_HOSTS and re.search(r'\.(jpe?g|png)$',urlsplit(u).path,re.I) and code.lower() in u.lower():
            urls.append(u)
    for tag in soup.find_all('meta'):
        if tag.get('property')=='og:image' and tag.get('content') and code.lower() in tag['content'].lower():
            urls.append(tag['content'])
    for tag in soup.find_all('img'):
        u=urljoin(page,tag.get('src') or '')
        if urlsplit(u).hostname in ASSET_HOSTS and code.lower() in u.lower():urls.append(u)
    errors=[]
    for u in list(dict.fromkeys(urls))[:6]:
        try:
            data=get(u,ASSET_HOSTS,26_000_000)
            with Image.open(io.BytesIO(data)) as im:
                if im.format not in ('JPEG','PNG','WEBP') or min(im.size)<600:raise ValueError('E218-RESOLUCAO')
                w,h=im.size;ext={'JPEG':'.jpg','PNG':'.png','WEBP':'.webp'}[im.format]
                im.verify()
            sha=hashlib.sha256(data).hexdigest()
            path=STAGE/(sha+ext);path.write_bytes(data)
            credit=re.search(r'NASA\s*/\s*JPL(?:-Caltech)?\s*/\s*Space Science Institute',txt,re.I).group(0)
            return {'id':slug,'label':label,'page':page,'url_original':u,'photojournal_id':code,
                    'page_sha256':hashlib.sha256(raw).hexdigest(),'credit':credit,'license':'REVIEW_PENDING',
                    'rights_status':'REVIEW_PENDING','local_source':str(path),'expected_sha256':sha,
                    'media_type':'photo','width':w,'height':h,'subject':heading.get_text(' ',strip=True)}
        except Exception as e:errors.append(str(e)[:150])
    raise ValueError('E218-SEM-ORIGINAL '+code+' '+str(errors))

def main():
    spec=json.loads(Path(sys.argv[1]).read_text(encoding='utf8'));out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
    STAGE.mkdir(parents=True,exist_ok=True)
    if spec.get('publish') is not False:raise ValueError('E218-PRIVADO')
    rows=[r for c in spec['chapters'] for r in c['photos']]
    acquired={};fail=[]
    # A bounded parallel acquisition of known individual pages, not broad scraping.
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        jobs={pool.submit(nasa_photo,r):r for r in rows}
        for job in concurrent.futures.as_completed(jobs):
            r=jobs[job]
            try:acquired[r[0]]=job.result()
            except Exception as e:fail.append({'id':r[0],'error':str(e)[:350]})
    write(out/'acervo.json',{'acquired':acquired,'errors':fail,'publish':False,'rights_policy':spec['rights_policy']})
    print('E218 ACERVO',len(acquired),'/',len(rows),flush=True)
    if any(len([r for r in c['photos'] if r[0] in acquired])<3 for c in spec['chapters']):
        raise ValueError('E218-ACERVO-INCOMPLETO; sem substituição artificial')
    # Reuse the real project voice. Explicitly forbid fallback to Edge.
    wav,tempos,caps,dur=voz.narrar([{'fala':c['speech']} for c in spec['chapters']],out/'voz',exigir_gemini=True)
    audio=out/'narracao48k.wav'
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(wav),'-ar','48000','-ac','1',str(audio)],check=True)
    import wave
    with wave.open(str(audio),'rb') as f:duration=f.getnframes()/f.getframerate()
    if duration<60 or duration>120 or len(tempos)!=len(spec['chapters']):raise ValueError('E218-DURACAO '+str(duration))
    # Round cuts to the actual 30fps timeline, never alter voice tempo here.
    total=math.ceil(duration*30)/30
    start=0;shots=[];media={};cut_report=[]
    for i,(ch,(a,b)) in enumerate(zip(spec['chapters'],tempos)):
        end=round(b*30) if i+1<len(tempos) else round(total*30)
        frames=end-start
        available=[acquired[r[0]] for r in ch['photos'] if r[0] in acquired]
        available=[x for x in available if x['expected_sha256'] not in {m['expected_sha256'] for m in media.values()}]
        n=max(math.ceil(frames/114),min(len(available),round(frames/90)))
        if n>len(available) or frames/n<42:raise ValueError('E218-FOTOS-INSUFICIENTES '+ch['title']+' '+str(frames/30))
        for k,item in enumerate(available[:n]):
            s=(start+round(frames*k/n))/30;e=(start+round(frames*(k+1)/n))/30
            mid=item['id'];media[mid]=item
            shots.append({'id':'foto-'+mid,'type':'photo','asset':mid,'start':s,'end':e,
                'lead':ch['title'],'headline':item['label'],'subject':item['subject'],
                'evidence':'literal','literal_identity':item['photojournal_id']+' · '+item['subject'],
                'focus':[.5,.5],'photo_framing':'integral','source_display':item['credit'],
                'cues':[{'at':min(1.1,(e-s)*.45),'label':item['label']}]})
        cut_report.append({'chapter':ch['title'],'start':start/30,'end':end/30,'shots':n,'fact_sources':ch['facts']})
        start=end
    plan={'formato':'filme_editorial','tipo':'PROVA_VISUAL_PRIVADA','publicar':False,
          'titulo':spec['title'],'duracao':total,'media':media,'shots':shots}
    write(out/'plano.json',plan)
    r=F.preparar(plan,out/'documental',PUBLIC)
    props=json.loads(Path(r['props']).read_text())
    props['private_review_only']=True
    # Existing measured word timing and global caption lane, not invented text timing.
    words=D.palavras_de_caps(caps)
    groups=[]
    for g in LS.grupos(words,maximo=3):
        ws=words[g['i0']:g['i0']+g['n']]
        hi=max(range(len(ws)),key=lambda i:len(ws[i]['w']))
        a=max(0,g['ini']);b=min(duration,g['fim'])
        if groups:a=max(a,groups[-1]['end'])
        if b>a:groups.append({'start':a,'end':b,'words':[{'w':w['w'],'hl':i==hi} for i,w in enumerate(ws)]})
    sha=hashlib.sha256(audio.read_bytes()).hexdigest();asset='e202/'+sha+'.wav'
    (PUBLIC/'e202').mkdir(exist_ok=True);shutil.copyfile(audio,PUBLIC/asset)
    props=D.anexar_audio_documental(props,asset,groups,PUBLIC,'PALAVRAS_MEDIDAS')
    write(out/'props.json',props)
    write(out/'narracao.json',{'motor':'Gemini','audio_sha256':sha,'duration_s':duration,
        'words':words,'captions':groups,'chapters':cut_report,'publish':False})
    # Contact sheet of sources with their actual identifiers, before final visual review.
    cols=4; board=Image.new('RGB',(cols*270,math.ceil(len(shots)/cols)*200),'#101c28');d=ImageDraw.Draw(board)
    for i,s in enumerate(shots):
        m=media[s['asset']]
        with Image.open(m['local_source']) as im:
            im=im.convert('RGB');im.thumbnail((260,165))
            x=(i%cols)*270;y=(i//cols)*200;board.paste(im,(x+(270-im.width)//2,y))
            d.text((x+5,y+166),m['photojournal_id']+' '+s['id'][5:25],fill='white')
    board.save(out/'fontes-contato.jpg',quality=88)
    print('E218 PREPARADO',total,len(shots),'cenas reais, Gemini',flush=True)

if __name__=='__main__':main()
