"""Private review mirror: small JSON/images and sampled frames, never public.
Full MP4 stays in Telegram/private release; this mirror is for visual inspection.
"""
import argparse,base64,hashlib,json,os,re,subprocess,tempfile
from pathlib import Path
import requests
from PIL import Image

REPO='Heitor2404/coringa-cofre'
REPO_ID=1454059520
BRANCH='revisao-privada'
API='https://api.github.com/repos/'+REPO
MAX_FILE=850_000
MAX_TOTAL=12_000_000

def checked_api(token):
    session=requests.Session()
    session.headers.update({'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json',
                            'X-GitHub-Api-Version':'2022-11-28'})
    def call(method,path,body=None):
        r=session.request(method,API+path,json=body,timeout=(10,45),allow_redirects=False)
        if not 200<=r.status_code<300:
            raise RuntimeError('COFRE_HTTP_'+str(r.status_code)+' '+method+' '+path.split('?')[0])
        return r.json()
    repo=call('GET','')
    if repo.get('id')!=REPO_ID or repo.get('private') is not True or repo.get('full_name')!=REPO:
        raise RuntimeError('COFRE_PRIVADO_NAO_CONFIRMADO')
    return call

def image_bytes(path):
    import io
    with Image.open(path) as im:
        im=im.convert('RGB');im.thumbnail((1080,1800))
        for quality in (88,78,65,50):
            buf=io.BytesIO();im.save(buf,format='JPEG',quality=quality)
            if len(buf.getvalue())<=MAX_FILE:return buf.getvalue()
    raise ValueError('COFRE_IMAGEM_GRANDE')

def collect(paths):
    files={};entries=[]
    def put(name,data,origin,kind):
        if not re.fullmatch(r'[a-zA-Z0-9_.-]+',name) or name in files or not data or len(data)>MAX_FILE:
            raise ValueError('COFRE_ARQUIVO_INVALIDO')
        if sum(map(len,files.values()))+len(data)>MAX_TOTAL:raise ValueError('COFRE_ORCAMENTO')
        files[name]=data
        entries.append({'arquivo':name,'origem':origin,'tipo':kind,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    for p in paths:
        p=Path(p)
        if not p.is_file():raise ValueError('COFRE_ARQUIVO_AUSENTE')
        if p.suffix.lower()=='.json':
            data=p.read_bytes();json.loads(data)
            if len(data)<=MAX_FILE:
                put(p.name,data,p.name,'relatorio')
            else:
                # Preserve exact UTF-8 bytes via bounded base64 JSON chunks.
                # Do not drop or summarize any original report fields.
                step=480_000
                parts=[]
                for i,pos in enumerate(range(0,len(data),step)):
                    block=data[pos:pos+step];name=f'{p.stem}-parte-{i:03d}.json'
                    put(name,json.dumps({'base64':base64.b64encode(block).decode(),'parte':i}).encode(),p.name,'relatorio_parte')
                    parts.append(name)
                manifest={'schema':'coringa.json.parts.v1','original':p.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'partes':parts,'encoding':'base64'}
                put(p.stem+'-partes.json',json.dumps(manifest).encode(),p.name,'relatorio_indice')
        elif p.suffix.lower() in ('.jpg','.jpeg','.png'):
            put(p.stem+'.jpg',image_bytes(p),p.name,'imagem_revisao')
        elif p.suffix.lower()=='.mp4':
            raw=subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(p)])
            probe=json.loads(raw);dur=float(probe['format']['duration'])
            if not 0<dur<=3600:raise ValueError('COFRE_VIDEO_DURACAO')
            # Avoid dumping arbitrary ffprobe tags/paths; preserve technical fields only.
            info={'duracao_s':dur,'sha256_original':None,'bytes':p.stat().st_size,'streams':[],'quadros':[],'reproducao_integral':False}
            digest=hashlib.sha256()
            with p.open('rb') as f:
                for block in iter(lambda:f.read(1024*1024),b''):digest.update(block)
            info['sha256_original']=digest.hexdigest()
            for s in probe.get('streams',[]):
                info['streams'].append({k:s[k] for k in ('codec_type','codec_name','width','height','r_frame_rate','sample_rate','channels') if k in s})
            # Up to 12 evenly spaced review samples, not proof of continuous motion.
            count=min(12,max(3,int(dur)+1))
            with tempfile.TemporaryDirectory() as tmp:
                for i in range(count):
                    t=round(min(max(0.,dur-.15),dur*i/(count-1)),3)
                    frame=Path(tmp)/'frame.jpg'
                    subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(p),'-frames:v','1','-vf','scale=960:960:force_original_aspect_ratio=decrease',str(frame)],check=True,stdout=subprocess.DEVNULL)
                    name=f'{p.stem}-frame-{i:02d}.jpg'
                    put(name,image_bytes(frame),p.name,'quadro_amostrado')
                    info['quadros'].append({'arquivo':name,'tempo_s':t})
            put(p.stem+'-video.json',json.dumps(info,ensure_ascii=False).encode(),p.name,'metadados_video')
        else:raise ValueError('COFRE_TIPO_NAO_PERMITIDO')
    if not files:raise ValueError('COFRE_SEM_ARQUIVOS')
    return files,entries

def publish(files,entries,ident,call):
    if not re.fullmatch(r'[a-z0-9-]{1,100}',ident):raise ValueError('COFRE_ID')
    root='revisoes/'+ident
    ref=call('GET','/git/ref/heads/'+BRANCH)['object']['sha']
    parent=call('GET','/git/commits/'+ref)
    # No overwrite of a prior review ID, no force push.
    tree=call('GET','/git/trees/'+parent['tree']['sha']+'?recursive=1')
    if tree.get('truncated') or any(x['path'].startswith(root+'/') for x in tree['tree']):
        raise RuntimeError('COFRE_ID_EXISTENTE_OU_ARVORE_TRUNCADA')
    manifest={'id':ident,'publicar':False,'origem_run_id':os.environ.get('GITHUB_RUN_ID'),
              'origem_commit':os.environ.get('GITHUB_SHA'),'arquivos':entries,'mp4_integral_no_espelho':False}
    files={**files,'index.json':json.dumps(manifest,ensure_ascii=False,indent=2).encode()}
    rows=[]
    for name,data in files.items():
        blob=call('POST','/git/blobs',{'content':base64.b64encode(data).decode(),'encoding':'base64'})
        rows.append({'path':root+'/'+name,'mode':'100644','type':'blob','sha':blob['sha']})
    newtree=call('POST','/git/trees',{'base_tree':parent['tree']['sha'],'tree':rows})
    commit=call('POST','/git/commits',{'message':'Private review '+ident,'tree':newtree['sha'],'parents':[ref]})
    call('PATCH','/git/refs/heads/'+BRANCH,{'sha':commit['sha'],'force':False})
    print('COFRE_ESPELHO_OK',ident,len(files),commit['sha'],flush=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('id');ap.add_argument('paths',nargs='+');args=ap.parse_args()
    token=os.environ.get('GH_TOKEN')
    if not token:raise RuntimeError('COFRE_TOKEN_AUSENTE')
    call=checked_api(token)
    files,entries=collect(args.paths)
    publish(files,entries,args.id,call)

if __name__=='__main__':main()
