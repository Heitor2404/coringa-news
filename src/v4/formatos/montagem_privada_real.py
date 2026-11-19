"""Prepara corte documental REAL no FilmeEditorial, com mídia verificada.

ADAPTADOR leve, NÃO novo motor: lê uma receita editorial multitema, copia
arquivos institucionais por SHA, baixa fotos do Commons, e gera o MESMO
plano/props do FilmeEditorial. Toda mídia NIST com direitos pendentes é
restrita a PREVIA PRIVADA (sem TTS/Telegram/publicação).
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import requests
from PIL import Image, ImageDraw, ImageFont

from src.v4.formatos import filme_editorial as FILME
from src.v4.formatos import ponte_mapa_atlas as MAPA

ALLOWED={'commons.wikimedia.org','upload.wikimedia.org','thumb.wikimedia.org'}
MAX_BYTES=23_000_000


def digest(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):
            h.update(b)
    return h.hexdigest()


def _arquivo_dentro(p:Path)->Path:
    p=Path(p)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError('arquivo deve ser relativo e não conter traversal')
    root=Path.cwd().resolve()
    out=(root/p).resolve()
    if not out.is_relative_to(root) or not out.is_file():
        raise ValueError(f'arquivo ausente ou fora do projeto: {p}')
    return out


def baixar_imagem(url:str)->bytes:
    first=urlparse(url)
    if first.scheme!='https' or first.hostname not in ALLOWED:
        raise ValueError('origem da foto deve ser Wikimedia Commons HTTPS')
    with requests.get(url,timeout=(15,60),headers={
        'User-Agent':'CoringaDocumental/1.0 (research; see github.com/Heitor2404/coringa-news)'
    },stream=True,allow_redirects=True) as r:
        if (r.url and (urlparse(r.url).scheme!='https'
                       or urlparse(r.url).hostname not in ALLOWED)):
            raise ValueError('download redirecionado fora do Commons')
        r.raise_for_status()
        out=io.BytesIO();total=0
        for b in r.iter_content(262144):
            total+=len(b)
            if total>MAX_BYTES:
                raise ValueError('foto maior que o limite seguro')
            out.write(b)
        data=out.getvalue()
    if len(data)<4_000:raise ValueError('foto vazia')
    with Image.open(io.BytesIO(data)) as im:
        im.verify()
    with Image.open(io.BytesIO(data)) as im:
        if im.format not in ('JPEG','PNG') or min(im.size)<600:
            raise ValueError('foto com formato/tamanho não aceito pelo compositor')
    return data


def _font(t:int,bold:bool=False):
    path='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    try:return ImageFont.truetype(path,t)
    except OSError:return ImageFont.load_default()


def grafico_original(config:dict,dest:Path)->None:
    """Gráfico de fato primário, original do canal, NÃO foto de acontecimento."""
    if config.get('design') not in ('numero','relacao'):
        raise ValueError('visualização factual não suportada')
    canvas=Image.new('RGB',(1080,1920),(8,18,31))
    d=ImageDraw.Draw(canvas)
    gold=(255,210,31);white=(240,245,247);soft=(170,188,198)
    d.rounded_rectangle((70,280,1010,1530),radius=32,
                        fill=(15,33,49),outline=(62,97,116),width=3)
    d.rectangle((85,305,995,315),fill=gold)
    d.text((108,395),str(config.get('etiqueta') or 'FATO DOCUMENTADO')[:55],
           fill=soft,font=_font(30,True))
    if config['design']=='numero':
        valor=str(config.get('valor') or '')
        if len(valor)>8:raise ValueError('valor gráfico muito extenso')
        d.text((105,550),valor,fill=gold,font=_font(210,True))
        a=str(config.get('linha1') or '')
        b=str(config.get('linha2') or '')
        d.text((110,910),a[:40],fill=white,font=_font(50,True))
        d.text((110,1000),b[:42],fill=soft,font=_font(43))
        # Barra contextual como dado: só representa a fração declarada.
        frac=config.get('fracao')
        # Valores absolutos (ex.: magnitude 7,4) NÃO são porcentagens.
        # Só mostrar barra quando a fonte descreve fração de um total.
        if frac is not None:
            if (not isinstance(frac,(int,float)) or isinstance(frac,bool)
                    or not 0<=frac<=1):
                raise ValueError('fração documentada inválida')
            d.rounded_rectangle((110,1260,960,1295),radius=12,fill=(49,70,83))
            if frac>0:
                d.rounded_rectangle((110,1260,110+int(850*frac),1295),radius=12,fill=gold)
    else:
        nomes=config.get('etapas') or []
        if len(nomes)!=3 or any(not isinstance(n,str) or len(n)>24 for n in nomes):
            raise ValueError('relação exige três elementos factuais')
        for i,n in enumerate(nomes):
            y=520+i*340
            d.rounded_rectangle((170,y,910,y+190),radius=24,
                                fill=(28,54,69),outline=gold if i==1 else (95,128,144),width=4)
            box=d.textbbox((0,0),n,font=_font(46,True))
            text_w=box[2]-box[0]
            d.text(((1080-text_w)//2,y+64),n,fill=white,font=_font(46,True))
            if i<2:
                d.line((540,y+200,540,y+310),fill=gold,width=9)
                d.polygon([(523,y+295),(557,y+295),(540,y+324)],fill=gold)
    fonte=str(config.get('rotulo_fonte') or '')
    d.text((110,1450),fonte[:48],fill=soft,font=_font(27))
    dest.parent.mkdir(parents=True,exist_ok=True)
    canvas.save(dest)


def _substituir_arquivo(asset_id:str,item:dict,stage:Path)->tuple[Path,str]:
    """Fonte real: foto Commons, original já recuperado, clipe ATLAS, ou gráfico."""
    mode=item.get('modo')
    ext='.mp4' if mode in ('video_institucional','atlas_map') else '.png' if mode=='grafico' else '.jpg'
    dest=stage/f'{asset_id}{ext}'
    if mode=='foto_commons':
        raw=baixar_imagem(item['url'])
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(raw)
    elif mode=='grafico':
        grafico_original(item['dados'],dest)
    elif mode in ('foto_existente','video_institucional','atlas_map'):
        src=_arquivo_dentro(Path(item['origem']))
        esperado=item.get('sha256_esperado')
        if not isinstance(esperado,str) or len(esperado)!=64 or digest(src)!=esperado:
            raise ValueError(f'{asset_id}: SHA de artefato comprovado divergente')
        if mode=='atlas_map':
            # A ponte original exige que o mapa permaneça no staging ATLAS.
            # Nunca copiar para outro diretório para burlar procedência.
            return Path(item['origem']),esperado
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(src,dest)
    else:
        raise ValueError(f'{asset_id}: tipo de fonte desconhecido')
    sha=digest(dest)
    fixado=item.get('sha256_esperado')
    if fixado and sha!=fixado:
        raise ValueError(f'{asset_id}: hash mudou depois de copiar a fonte')
    return dest,sha


def preparar_receita(receita:dict,saida:Path,public_root:Path)->dict:
    if (receita.get('versao')!=1 or receita.get('tipo')!='PROVA_VISUAL_PRIVADA'
            or receita.get('publicar') is not False):
        raise ValueError('somente receita v1 de montagem PRIVADA e NÃO publicada')
    assets=receita.get('assets')
    cenas=receita.get('cenas')
    if not isinstance(assets,dict) or not isinstance(cenas,list) or not cenas:
        raise ValueError('receita sem fontes/cenas')
    if len({c.get('id') for c in cenas})!=len(cenas):
        raise ValueError('cenas repetidas')
    stage=Path('stage_documental')
    stage.mkdir(parents=True,exist_ok=True)
    midias={};provas=[]
    usados={c.get('asset') for c in cenas}
    if None in usados or not usados.issubset(assets.keys()):
        raise ValueError('cenas referenciam mídia inexistente')
    for mid in sorted(usados):
        if not mid.replace('-','').replace('_','').isalnum():
            raise ValueError('id de mídia inválido')
        item=assets[mid]
        origem,sha=_substituir_arquivo(mid,item,stage)
        lic=item.get('licenca')
        if (not isinstance(lic,str) or
                (lic not in FILME.LICENCAS and lic!='REVIEW_PENDING')):
            raise ValueError('licença ausente ou desconhecida')
        media={'local_source':str(origem),'expected_sha256':sha,
               'url':item.get('url') or item.get('pagina'),
               'page':item.get('pagina'),'credit':item.get('credito'),
               'license':lic,
               'media_type':'video' if item.get('modo') in ('video_institucional','atlas_map') else 'photo'}
        if item.get('modo')=='grafico':
            media['original_graphic']=True
        if item.get('modo')=='video_institucional':
            if lic!='REVIEW_PENDING':
                raise ValueError('esta receita não pode homologar vídeo institucional automaticamente')
            media['rights_status']='REVIEW_PENDING'
        if item.get('modo')=='atlas_map':
            from src.v4.formatos.ponte_mapa_atlas import validar_comprovante
            origem_prova=Path(item.get('comprovante') or '')
            if not origem_prova.is_file():
                raise ValueError('mapa sem comprovante')
            media['atlas_proof']=str(origem_prova)
            problemas=validar_comprovante({'local_source':str(origem),
                                           'atlas_proof':str(origem_prova),
                                           'expected_sha256':sha})
            if problemas:raise ValueError('MAPA: '+'; '.join(problemas))
        if media['media_type']=='video':
            j=json.loads(subprocess.check_output(
                ['ffprobe','-v','error','-select_streams','v:0',
                 '-show_entries','stream=width,height:format=duration',
                 '-of','json',str(origem)],text=True,timeout=30))
            streams=j.get('streams') or []
            if not streams:raise ValueError('video sem stream '+mid)
            media['width']=int(streams[0]['width'])
            media['height']=int(streams[0]['height'])
            media['duration_s']=float((j.get('format') or {}).get('duration') or 0)
        else:
            with Image.open(origem) as im:
                media['width'],media['height']=im.size
        if not media['page'] or not media['credit']:
            raise ValueError('mídia sem fonte e crédito')
        midias[mid]=media
        provas.append({
            'id':mid,'sha256':sha,
            'hash_fixado_antes':bool(item.get('sha256_esperado')),
            'licenca_declarada':lic,'origem':str(origem),
            'dimensoes':[media['width'],media['height']],
            'direitos_pendentes':lic=='REVIEW_PENDING'})
    t=0.;shots=[]
    for i,x in enumerate(cenas):
        span=x.get('segundos')
        if (not isinstance(span,(int,float)) or not math.isfinite(span)
                or not 1.4<=span<=8):
            raise ValueError('duração de cena individual inválida')
        asset=x['asset']; m=midias[asset]
        typ='atlas_map' if assets[asset]['modo']=='atlas_map' else m['media_type']
        typ='photo' if typ=='photo' else typ
        if typ=='video' and x.get('fonte_s',0)+span>m['duration_s']+.05:
            raise ValueError('recorte ultrapassa o vídeo real: '+x['id'])
        shot={
            'id':x['id'],'start':round(t,3),'end':round(t+span,3),
            'type':typ,'asset':asset,
            'lead':x['lead'],'headline':x['headline'],
            'subject':x['subject'],'evidence':x.get('evidence','representative'),
            'highlight':x.get('highlight'),
            'focus':x.get('focus',[.5,.5]),
            'cues':[{'at':round(max(.45,span-2.35),3) if typ=='photo' else min(.55,span*.25),
                     'label':x['cue']}],
            'direcao_evento':{'intencao':x['intencao'],
                             'fato_id':x['id'],'aprendizado':x['aprendizado']},
        }
        if typ=='video':
            shot['source_in_seconds']=float(x.get('fonte_s') or 0)
        if typ=='atlas_map':
            proof=json.loads(Path(assets[asset]['comprovante']).read_text())
            shot['atlas_direcao']={'intencao':'localizar','roi':proof['mapeamento']['roi']}
            shot['evidence']='explainer'
        if shot['evidence']=='literal':
            shot['literal_identity']=x.get('identidade_literal') or x['subject']
        shots.append(shot)
        t+=span
    plano={
        'formato':'filme_editorial','tipo':'PROVA_VISUAL_PRIVADA',
        'publicar':False,'titulo':receita.get('titulo','Revisão privada'),
        'duracao':round(t,3),'media':midias,'shots':shots,
        'observacao':'Montagem REAL sem voz e sem publicação. NIST com direitos pendentes.',
    }
    saida=Path(saida);saida.mkdir(parents=True,exist_ok=True)
    (saida/'plano.json').write_text(json.dumps(plano,ensure_ascii=False,indent=2),encoding='utf8')
    (saida/'proveniencia.json').write_text(json.dumps({
        'status':'PREVIA_PRIVADA_NAO_PUBLICAR',
        'sem_narracao':True,'sem_aprovacao_visual':True,
        'duracao_s':plano['duracao'],'fontes':provas,
    },ensure_ascii=False,indent=2),encoding='utf8')
    resultado=FILME.preparar(plano,saida,public_root)
    return {**resultado,'duracao_s':plano['duracao'],
            'fontes_com_direitos_pendentes':[p['id'] for p in provas if p['direitos_pendentes']]}


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('receita',type=Path);p.add_argument('saida',type=Path)
    p.add_argument('public',type=Path)
    a=p.parse_args(argv)
    receita=json.loads(a.receita.read_text(encoding='utf8'))
    print(json.dumps(preparar_receita(receita,a.saida,a.public),
                     ensure_ascii=False,indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
