"""Área segura MULTIPLATAFORMA para o mesmo FilmeEditorial.

O JSON é a única fonte de medidas usada tanto no Remotion quanto no
preflight Python. A heurística de comprimento não garante renderização;
os quadros anotados continuam exigindo revisão editorial humana.
Políticas ads Reels/TikTok/Shorts são referências, UI orgânica é variável.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[3]
CONFIG=ROOT/'motor4/remotion/src/formatos/safe-zones-vertical.json'
PERFIL='MULTIPLATAFORMA_CONSERVADOR_V1'


def carregar():
    return json.loads(CONFIG.read_text(encoding='utf8'))


def _dentro(child,parent):
    return parent[0]<=child[0]<child[2]<=parent[2] and parent[1]<=child[1]<child[3]<=parent[3]


def validar_contrato()->dict:
    c=carregar()
    if c.get('version')!=1 or c.get('resolution')!=[1080,1920] or c.get('profile')!=PERFIL:
        raise ValueError('SAFE-CONTRATO: versão ou proporção divergente')
    full=[0,0,1080,1920]
    uni=c['universal']
    if not _dentro(uni,full):
        raise ValueError('SAFE-UNIVERSAL: fora de 9:16')
    for platform,item in c['platforms'].items():
        if not _dentro(uni,item['safe']):
            raise ValueError('SAFE-PLATAFORMA: caixa comum não cabe em '+platform)
    for name,rect in c['slots'].items():
        if not _dentro(rect,uni):
            raise ValueError('SAFE-SLOT: '+name+' fora da área de leitura')
    # Ordem editorial sem colisão. Fundo e barra decorativa não entram.
    y=c['slots']
    order=['brand','section','visual','cue','headline','subject','source']
    for one,two in zip(order,order[1:]):
        if y[one][3]>y[two][1]:
            raise ValueError('SAFE-SLOTS-SOBREPOSTOS: '+one+'/'+two)
    return {'area_universal':uni,'slots':c['slots'],
            'plataformas':list(c['platforms']),'perfil':PERFIL}


def auditar_plano(plano:dict, *, bloquear_nao_homologados=True)->dict:
    """Audita metadados e capacidade de layout ANTES da renderização.

    O teste não interpreta conteúdo visual de fotografias nem textos
    rasterizados em vídeo / mapas. Nessas situações, reportar risco,
    nunca emitir 'aprovado' pelo simples fato de ter um bbox.
    """
    validar_contrato()
    falhas=[]
    alertas=[]
    shots=plano.get('shots') or []
    def add(code,scene,msg,block=True):
        item={'codigo':code,'cena':scene,'motivo':msg}
        (falhas if block else alertas).append(item)

    if plano.get('safe_area_profile') not in (None,PERFIL):
        add('SAFE-PERFIL-INVALIDO','-', 'perfil não está mapeado no compositor')
    if not isinstance(shots,list):
        add('SAFE-SHOTS','-', 'lista de planos inválida')
        shots=[]
    for s in shots:
        if not isinstance(s,dict):
            add('SAFE-SHOT','-', 'cena inválida')
            continue
        cid=str(s.get('id') or '?')
        kind=s.get('type')
        if kind=='atlas_map':
            add('SAFE-MAPA-SEM-CERTIFICACAO',cid,
                'o raster ATLAS possui rótulos/créditos embutidos e não teve o interior revisado para 3 UIs',
                bloquear_nao_homologados)
        if s.get('graphic_original') and not s.get('motion_graphic'):
            add('SAFE-GRAFICO-RASTER',cid,
                'card original com textos embutidos precisa inspeção/reflow antes de afirmar safe',
                bloquear_nao_homologados)
        # Informações essenciais não podem ser truncadas para corrigir UI.
        # Estes são limites conservadores de revisão, não medição tipográfica.
        lengths={
            'headline':(s.get('headline'),74),
            'lead':(s.get('lead'),52),
            'subject':(s.get('subject'),105),
            'source':(s.get('source'),120),
        }
        for name,(value,limit) in lengths.items():
            if value is not None and len(str(value).strip())>limit:
                add('SAFE-TEXTO-COMPRIDO',cid,
                    f'{name} tem {len(str(value))} caracteres; reescrever ou dividir cena (limite QA {limit})')
        if kind!='mechanism' and not s.get('graphic_original'):
            for e in s.get('cues') or []:
                lab=e.get('label') if isinstance(e,dict) else None
                if lab is not None and len(str(lab).strip())>47:
                    add('SAFE-CUE-COMPRIDA',cid,
                        'rótulo excede uma linha editorial; não cortar texto silenciosamente')
        if kind=='photo' and not s.get('graphic_original'):
            add('SAFE-FOTO-FOCO-PENDENTE',cid,
                'foto de fundo é full bleed: sujeito do enquadramento não foi garantido só por coordenada focus',
                False)
        if kind=='video':
            framing=s.get('video_framing') or {}
            if not framing:
                add('SAFE-VIDEO-SEM-ROI',cid,
                    'vídeo sem relação observada ou ROI temporal verificável',bloquear_nao_homologados)
            if s.get('video_context_layout') not in (
                None,'quadro_integral','cena_integral','recorte_relacional_seguro'
            ):
                add('SAFE-VIDEO-LAYOUT',cid,'layout de mídia desconhecido')
        if kind=='mechanism':
            add('SAFE-MECANISMO-PIXELS-PENDENTES',cid,
                'palco físico reposicionado; atores e rótulos internos exigem inspeção no MP4 final',
                False)
    return {'perfil':PERFIL,'area_universal':carregar()['universal'],
            'status':'BLOQUEADO' if falhas else 'ESTRUTURA_SAFE_APTA_REVISAR_PIXELS',
            'bloqueios':falhas,'avisos':alertas,'quantidade_cenas':len(shots),
            'pixels_inspecionados':False,'publicar_aprovado':False}


def overlay(frame:Path,saida:Path)->None:
    """Quatro visões complementares para QA, nunca inserir em entrega final."""
    z=carregar()
    with Image.open(frame) as orig:
        img=orig.convert('RGB')
    if img.width*16!=img.height*9:
        raise ValueError('SAFE-FRAME: análise requer 9:16 real')
    panels=[]
    entries=[('REELS',z['platforms']['reels']['safe']),
             ('TIKTOK',z['platforms']['tiktok']['safe']),
             ('SHORTS',z['platforms']['shorts']['safe']),
             ('UNIVERSAL',z['universal'])]
    for label,rect in entries:
        rgba=img.convert('RGBA')
        tint=Image.new('RGBA',img.size,(0,0,0,0))
        draw=ImageDraw.Draw(tint)
        scale=img.width/1080
        x1,y1,x2,y2=[round(n*scale) for n in rect]
        draw.rectangle((0,0,img.width,y1),fill=(210,27,42,77))
        draw.rectangle((0,y2,img.width,img.height),fill=(210,27,42,87))
        draw.rectangle((0,y1,x1,y2),fill=(210,27,42,77))
        draw.rectangle((x2,y1,img.width,y2),fill=(210,27,42,87))
        draw.rectangle((x1,y1,x2,y2),outline=(66,235,177,255),width=max(2,round(4*scale)))
        panel=Image.alpha_composite(rgba,tint).convert('RGB')
        ImageDraw.Draw(panel).text((max(5,int(10*scale)),max(5,int(10*scale))),
                                   label+'  |  VERMELHO = RISCO DE UI',fill=(255,255,255))
        panels.append(panel)
    canvas=Image.new('RGB',(img.width*4,img.height),(10,14,21))
    for n,part in enumerate(panels):
        canvas.paste(part,(n*img.width,0))
    saida=Path(saida)
    saida.parent.mkdir(parents=True,exist_ok=True)
    canvas.save(saida,quality=88)


def main(argv=None)->int:
    p=argparse.ArgumentParser()
    p.add_argument('plano',type=Path)
    p.add_argument('destino',type=Path)
    p.add_argument('--frame',type=Path)
    p.add_argument('--sobreposicao',type=Path)
    p.add_argument('--permitir-risco-legacy',action='store_true')
    opt=p.parse_args(argv)
    raw=json.loads(opt.plano.read_text(encoding='utf8'))
    result=auditar_plano(raw, bloquear_nao_homologados=not opt.permitir_risco_legacy)
    opt.destino.parent.mkdir(parents=True,exist_ok=True)
    opt.destino.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    if opt.frame:
        if not opt.sobreposicao:
            p.error('--sobreposicao obrigatório com --frame')
        overlay(opt.frame,opt.sobreposicao)
    print(json.dumps({'status':result['status'],'bloqueios':len(result['bloqueios']),
                      'avisos':len(result['avisos'])},ensure_ascii=False))
    return 2 if result['bloqueios'] else 0


if __name__=='__main__':
    raise SystemExit(main())
