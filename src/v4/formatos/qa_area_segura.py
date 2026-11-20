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
from src.v4.formatos import layout as LAYOUT

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
    if c.get('source_of_truth')!='src/v4/formatos/plataformas.json':
        raise ValueError('SAFE-PERFIL-FONTE: usar perfis ATLAS existentes')
    full=[0,0,1080,1920]
    uni=c['universal']
    if not _dentro(uni,full):
        raise ValueError('SAFE-UNIVERSAL: fora do 9:16')
    # Camada/ATLAS já usam layout.py. O Filho FilmeEditorial não pode
    # adotar um suposto safe zone que o ATLAS considera COBERTO.
    perfis=LAYOUT.perfis(LAYOUT.CFG['ativos_seguros'])
    if set(perfis)!={'tiktok_multiplataforma','instagram_reels_multiplataforma','youtube_shorts_multiplataforma'}:
        raise ValueError('SAFE-PERFIS: motor não usa as três plataformas')
    for nome,p in perfis.items():
        if (uni[0]<p['esquerda'] or uni[1]<p['topo']
            or uni[3]>1920-p['base']
            or uni[2]>LAYOUT.limite_direito(uni[1],uni[3],[nome])):
            raise ValueError('SAFE-PLATAFORMA: caixa comum não cabe em '+nome)
    for name,rect in c['slots'].items():
        if not _dentro(rect,uni):
            raise ValueError('SAFE-SLOT: '+name+' fora da área de leitura')
    # Modos exclusivos! A legenda de voz substitui título/cue/subject;
    # sem ela os títulos usam a mesma janela, nunca se sobrepõem.
    for order in (
        ('brand','section','visual','cue','headline','subject','source'),
        ('brand','section','visual','subtitle','source')
    ):
        for a,b in zip(order,order[1:]):
            if c['slots'][a][3]>c['slots'][b][1]:
                raise ValueError('SAFE-SLOTS-SOBREPOSTOS: '+a+'/'+b)
    # Diagrama nativo reflow: o TÍTULO não pode colidir com a ação,
    # e ambos devem caber no perfil interseção de três plataformas.
    mech=c.get('mechanism_layout') or {}
    stage,step=mech.get('visual'),mech.get('step')
    if not isinstance(stage,list) or not isinstance(step,list):
        raise ValueError('SAFE-MECANISMO-LAYOUT: faltam palco e faixa de etapa')
    title=mech.get('headline')
    if not isinstance(title,list) or len(title)!=4 or not _dentro(title,uni):
        raise ValueError('SAFE-PORTRAIT-TITULO: titulo externo ao comum')
    if not (c['slots']['section'][3]<=title[1] and title[3]<=stage[1]):
        raise ValueError('SAFE-PORTRAIT-COLISAO: marca/titulo/mecanismo')
    native=mech.get('native_portrait') or []
    if not isinstance(native,list) or not native or len(native)!=len(set(native)):
        raise ValueError('SAFE-PORTRAIT-RENDERERS: lista invalida')
    dimensions=mech.get('native_dimensions')
    if dimensions!=[620,682]:
        raise ValueError('SAFE-PORTRAIT-DIMENSOES: raster nativo divergente')
    if set(native)-set((mech.get('focus') or {})):
        raise ValueError('SAFE-PORTRAIT-RENDERERS: nao reconhecido pelo catalogo')
    if 'optical_projection' not in native or 'lock_explainer' not in native:
        raise ValueError('SAFE-PORTRAIT-PROVAS: faltam dois dominios visuais')
    # Duas faixas fisicas. De y=485..830 a UI lateral ainda NAO
    # entrou; a partir de y=840 usa-se a regiao central estreita.
    # A geometria e verificada contra CADA perfil, nao so na uniao
    # conservadora (que usa a pior largura de todo o video).
    hero,support=mech.get('wide_hero'),mech.get('wide_support')
    if not (isinstance(hero,list) and isinstance(support,list) and
            len(hero)==len(support)==4 and _dentro(hero,full)
            and _dentro(support,full)):
        raise ValueError('SAFE-WIDE-CAIXA: faixas invalidas')
    if (c['slots']['section'][3]>hero[1] or
        title[3]>hero[1] or hero[3]>support[1]
        or support[3]>step[1]):
        raise ValueError('SAFE-WIDE-SOBREPOSICAO: titulo/fisica/etapa colidem')
    for nome,p in perfis.items():
        for label,box in [('hero',hero),('support',support)]:
            if (box[0]<p['esquerda'] or box[1]<p['topo']
                or box[3]>1920-p['base']
                or box[2]>LAYOUT.limite_direito(box[1],box[3],[nome])):
                raise ValueError('SAFE-WIDE-PLATAFORMA: '+nome+'/'+label)
    if hero[2]-hero[0]<800 or support[2]-support[0]<600:
        raise ValueError('SAFE-WIDE-IMPACTO: palco voltou a miniaturizar')
    if hero[3]>=840:
        raise ValueError('SAFE-WIDE-ICONES: faixa larga cruza coluna lateral')
    if not (_dentro(stage,uni) and _dentro(step,uni)):
        raise ValueError('SAFE-MECANISMO-LAYOUT: palco/etapa fora da intersecao')
    for a,b in zip((c['slots']['section'],stage,step),
                   (stage,step,c['slots']['source'])):
        if a[3]>b[1]:
            raise ValueError('SAFE-MECANISMO-COLISAO: palco/etapa/fonte sobrepostos')
    if not (0.15<=mech.get('transition_seconds',0)<=0.8):
        raise ValueError('SAFE-MECANISMO-CAMERA: transicao invalida')
    def box_valida(box):
        return isinstance(box,list) and len(box)==4 and all(
            isinstance(n,(int,float)) and not isinstance(n,bool) for n in box
        ) and _dentro(box,full)
    if not box_valida(mech.get('default_bounds')):
        raise ValueError('SAFE-MECANISMO-CAMERA: regiao principal invalida')
    for tipo,estados in (mech.get('focus') or {}).items():
        if not isinstance(estados,dict) or not estados or not tipo:
            raise ValueError('SAFE-MECANISMO-CAMERA: catalogo invalido')
        if 'default' not in estados:
            raise ValueError('SAFE-MECANISMO-CAMERA: sem camera geral '+tipo)
        for acao,box in estados.items():
            if not box_valida(box):
                raise ValueError('SAFE-MECANISMO-CAMERA: box invalido '+tipo+'/'+acao)
            # Foco com tamanho absurdamente grande/minimo gera diagramas
            # ilegíveis ou cortes excessivos. Não certificar conteúdo interno.
            w,h=box[2]-box[0],box[3]-box[1]
            escala=min((stage[2]-stage[0])/w,(stage[3]-stage[1])/h)
            if escala<0.59 or escala>1.3:
                raise ValueError('SAFE-MECANISMO-CAMERA: escala inadequada '+tipo+'/'+acao)
    # A experiência anterior mostrou que foco mais estreito PODE cortar
    # a fonte EUV e a agua da eclusa, mesmo com o retangulo SAFE verde.
    # O renderer declara a caixa que engloba TODOS os atores causais
    # imprescindíveis. Nenhum close pode cortar essa geometria.
    for tipo,essencial in (mech.get('essential_bounds') or {}).items():
        if not box_valida(essencial) or tipo not in (mech.get('focus') or {}):
            raise ValueError('SAFE-MECANISMO-ESSENCIAL: geometria ausente '+tipo)
        for acao,box in mech['focus'][tipo].items():
            if not _dentro(essencial,box):
                raise ValueError('SAFE-MECANISMO-CORTE-ESSENCIAL: '+tipo+'/'+acao)
    # Evita títulos e rodapés de SVG antigos aparecerem pela metade
    # na folga de letterboxing, duplicando a camada editorial externa.
    for tipo,limites in (mech.get('editorial_exclusion') or {}).items():
        camera=(mech.get('focus') or {}).get(tipo)
        if not camera or not isinstance(limites,dict):
            raise ValueError('SAFE-MECANISMO-TEXTO-INTERNO: configuracao ausente')
        topo,rodape=limites.get('header_bottom'),limites.get('footer_top')
        if not (isinstance(topo,(int,float)) and isinstance(rodape,(int,float))
                and 0<topo<rodape<1920):
            raise ValueError('SAFE-MECANISMO-TEXTO-INTERNO: zonas ilegais')
        for acao,box in camera.items():
            if box[1]<topo or box[3]>rodape:
                raise ValueError('SAFE-MECANISMO-TEXTO-INTERNO: '+tipo+'/'+acao)
    return {'area_universal':uni,'slots':c['slots'],
            'plataformas':list(perfis),'perfil':PERFIL}


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
        if kind=='comparison':
            add('SAFE-COMPARACAO-LEGADA',cid,
                'cena de comparação contém rótulos internos sem reflow seguro',
                bloquear_nao_homologados)
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
            if s.get('mechanism') not in (carregar().get('mechanism_layout') or {}).get('native_portrait', []):
                add('SAFE-PORTRAIT-SEM-REFLOW',cid,
                    'mecanismo sem desenho vertical nativo: usa recorte conservador antigo; revisar qualidade',
                    False)
            focus=(carregar().get('mechanism_layout') or {}).get('focus',{})
            cameras=focus.get(s.get('mechanism')) or {}
            detalhadas=any(key!='default' for key in cameras)
            for e in s.get('cues') or []:
                if not isinstance(e,dict):
                    add('SAFE-MECANISMO-ETAPA',cid,'cue de mecanismo invalida')
                    continue
                label=str(e.get('label') or '')
                if len(label)>58:
                    add('SAFE-MECANISMO-ETAPA-LONGA',cid,
                        'etapa excede a faixa editorial legivel; dividir texto')
                if detalhadas and e.get('action') not in cameras:
                    add('SAFE-MECANISMO-FOCO-AUSENTE',cid,
                        'acao sem janela visual no componente: '+str(e.get('action')))
            add('SAFE-MECANISMO-PIXELS-PENDENTES',cid,
                'palco físico reposicionado; atores e rótulos internos exigem inspeção no MP4 final',
                False)
    return {'perfil':PERFIL,'area_universal':carregar()['universal'],
            'status':'BLOQUEADO' if falhas else 'ESTRUTURA_SAFE_APTA_REVISAR_PIXELS',
            'bloqueios':falhas,'avisos':alertas,'quantidade_cenas':len(shots),
            'pixels_inspecionados':False,'publicar_aprovado':False}


def overlay(frame:Path,saida:Path)->None:
    """Visualização QA por plataforma. A fonte dos limites é layout.py,
    compartilhada com o motor ATLAS, e não um segundo cadastro de pixels.
    """
    z=carregar()
    with Image.open(frame) as orig:
        img=orig.convert('RGB')
    if img.width*16!=img.height*9:
        raise ValueError('SAFE-FRAME: análise requer 9:16 real')
    panels=[]
    entries=[('REELS','instagram_reels_multiplataforma'),
             ('TIKTOK','tiktok_multiplataforma'),
             ('SHORTS','youtube_shorts_multiplataforma'),
             ('UNIVERSAL',None)]
    for label,key in entries:
        rgba=img.convert('RGBA')
        tint=Image.new('RGBA',img.size,(0,0,0,0))
        draw=ImageDraw.Draw(tint)
        scale=img.width/1080
        univ=z['universal']
        x1,y1,x2,y2=[round(n*scale) for n in univ]
        if key is None:
            draw.rectangle((0,0,img.width,y1),fill=(210,27,42,75))
            draw.rectangle((0,y2,img.width,img.height),fill=(210,27,42,85))
            draw.rectangle((0,y1,x1,y2),fill=(210,27,42,70))
            draw.rectangle((x2,y1,img.width,y2),fill=(210,27,42,82))
        else:
            for mask in LAYOUT.mascaras(key):
                x,y,w,h=mask['caixa']
                color=(221,110,21,62) if mask.get('aviso') else (210,27,42,87)
                draw.rectangle((
                    round(x*scale),round(y*scale),
                    round((x+w)*scale),round((y+h)*scale)),
                    fill=color)
        draw.rectangle((x1,y1,x2,y2),outline=(66,235,177,255),
                       width=max(2,round(4*scale)))
        panel=Image.alpha_composite(rgba,tint).convert('RGB')
        ImageDraw.Draw(panel).text(
            (max(5,int(10*scale)),max(5,int(10*scale))),
            label+' | VERMELHO = UI | VERDE = ÁREA COMUM',
            fill=(255,255,255))
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
