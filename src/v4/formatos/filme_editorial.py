"""Pré-produção do FILME EDITORIAL: mídia ocupa o plano, não slides/cartões ATLAS.

Motor-piloto isolado. Recebe briefing com evidências e cortes editorialmente
escolhidos, valida coerência e prepara props do Remotion FilmeEditorial.
A aprovação estética depende de INSPECIONAR o vídeo, nunca da contagem de testes.
Sem rede ao validar; baixar só em CLI dedicada, de fontes já licenciadas.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit
from PIL import Image

LICENCAS = {'CC BY 2.0', 'CC BY 3.0', 'CC BY 4.0', 'CC BY-SA 2.0', 'CC BY-SA 3.0', 'CC BY-SA 4.0', 'CC0', 'NASA PD', 'Public domain', 'Natural Earth PD'}
ORIGENS = {'upload.wikimedia.org', 'thumb.wikimedia.org'}
TIPOS = {'photo', 'video', 'comparison', 'mechanism', 'atlas_map'}


def avaliar(plano: dict) -> dict:
    falhas = []
    def falha(cod: str, onde: str, porque: str):
        falhas.append({'codigo': cod, 'cena': onde, 'motivo': porque})
    cenas = plano.get('shots') or []
    if not cenas:
        falha('F-SEM-HISTORIA', '-', 'não há cenas')
    if plano.get('tipo') != 'PROVA_VISUAL_PRIVADA':
        # Nenhuma amostra Edge, mesmo "em tempo natural", entra na produção.
        # Preset do canal é a fonte única; nunca fallback silencioso.
        from src.v4.formatos import plano as plano_atlas
        preset = (plano_atlas.canal('coringa').get('narrador') or {})
        voz = plano.get('narrador') or {}
        if (preset.get('motor') != 'gemini' or preset.get('fallback') != 'bloquear'
                or voz.get('motor') != preset.get('motor')
                or voz.get('voz') != preset.get('voz')
                or voz.get('fallback') != 'bloquear'
                or not isinstance(voz.get('sha256_voz'), str)
                or len(voz.get('sha256_voz')) != 64):
            falha('F-VOZ-TESTE-EM-PRODUCAO', '-',
                  'FILME final exige voz Gemini do preset do canal com SHA e fallback bloqueado; Edge só é aceito em PROVA_VISUAL_PRIVADA')
        if voz.get('aprovacao_humana') is not True:
            falha('F-VOZ-SEM-APROVACAO', '-',
                  'narração final precisa de conferência auditiva humana, nunca inferida pelos testes')
    # O contrato de pré-produção é opcional SOMENTE para provas técnicas privadas.
    # Um filme documental de produção não pode passar só pelo fiscal de shots:
    # é preciso provar que a mídia prevista para cada acontecimento existe.
    if plano.get('tipo') != 'PROVA_VISUAL_PRIVADA':
        contrato = plano.get('contrato_integral')
        if not isinstance(contrato, dict):
            falha('F-PORTAO-INTEGRAL-AUSENTE', '-',
                  'filme final exige contrato integral com provas antes de render/TTS')
        else:
            from src.v4.formatos.gate_filme_completo import avaliar as avaliar_integral
            from src.v4.formatos.ponte_biblioteca import catalogo as catalogo_curado
            cenas_contrato = contrato.get('cenas') or []
            tipos = {'foto':'photo', 'video':'video', 'atlas_map':'atlas_map',
                     'comparison':'comparison', 'mechanism':'mechanism'}
            if len(cenas_contrato) != len(cenas) or any(
                c.get('id') != s.get('id') or
                abs(float(c.get('inicio', -999)) - float(s.get('start', -998))) > .05 or
                abs(float(c.get('fim', -999)) - float(s.get('end', -998))) > .05 or
                tipos.get((c.get('midia') or {}).get('tipo')) != s.get('type')
                for c, s in zip(cenas_contrato, cenas)
            ):
                falha('F-PORTAO-CONTRATO-DIVERGENTE', '-',
                      'cenas, tempos e tipos do filme não correspondem ao contrato auditado')
            else:
                for c, s in zip(cenas_contrato, cenas):
                    m = c.get('midia') or {}
                    if s.get('type') in ('photo', 'video'):
                        origem = (plano.get('media') or {}).get(s.get('asset')) or {}
                        if origem.get('catalog_asset_id') != m.get('asset_id'):
                            falha('F-PORTAO-FONTE-DIVERGENTE', str(s.get('id')),
                                  'mídia montada não corresponde ao asset curado no contrato')
                    elif s.get('type') == 'comparison':
                        ids = [((plano.get('media') or {}).get(s.get(key)) or {}).get('catalog_asset_id')
                               for key in ('asset','assetB')]
                        if ids != m.get('asset_ids'):
                            falha('F-PORTAO-FONTE-DIVERGENTE', str(s.get('id')),
                                  'fontes da comparação divergem do contrato')
                    elif s.get('type') == 'atlas_map':
                        origem = (plano.get('media') or {}).get(s.get('asset')) or {}
                        if (origem.get('local_source') != m.get('clipe') or
                                origem.get('atlas_proof') != m.get('prova')):
                            falha('F-PORTAO-MAPA-DIVERGENTE', str(s.get('id')),
                                  'clipe e comprovante ATLAS divergentes do contrato')
            resultado = avaliar_integral(contrato, catalogo_curado())
            if not resultado['pronto_para_render']:
                falha('F-PORTAO-INTEGRAL-BLOQUEADO', '-',
                      'falta prova audiovisual ou WAV autenticado: ' +
                      ', '.join(x['codigo'] for x in resultado['bloqueios'][:8]))
    visual = set()
    momentos = set()  # cenas demonstrativas contam como acontecimento, não foto decorativa
    prev_end = 0.0
    for n, cena in enumerate(cenas):
        cid = str(cena.get('id') or f'cena-{n}')
        start, end = cena.get('start'), cena.get('end')
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            falha('F-SEM-TEMPO', cid, 'início/fim inválidos')
            continue
        if abs(start - prev_end) > .05:
            falha('F-LACUNA', cid, f'intervalo vazio ou sobreposição: {prev_end}→{start}')
        span = end - start
        # Mecanismo com acontecimentos reais pode durar mais do que fotografia
        # parada. O corte é dirigido pela ação, não por uma duração fixa.
        eh_causal = cena.get('type') == 'mechanism' and cena.get('mechanism') == 'lock_causal'
        eh_ciclo = cena.get('type') == 'mechanism' and cena.get('mechanism') == 'lock_cycle'
        max_span = (float('inf') if cena.get('type') == 'video' else
                    8.0 if cena.get('type') == 'atlas_map' else
                    18.0 if eh_ciclo else 6.2 if eh_causal else
                    4.8 if cena.get('type')=='mechanism' and len(cena.get('cues') or [])>=2 else 3.8)
        if eh_causal or eh_ciclo:
            # Contrato da ponte: o mesmo arquivo continua alguns frames no corte,
            # sem saltar para outro clipe ou afirmar subida que a filmagem não mostra.
            anterior = cenas[n-1] if n else {}
            continuidade = (anterior.get('type') == 'video' and
                           cena.get('reference_asset') == anterior.get('asset') and
                           cena.get('reference_asset') in plano.get('media', {}) and
                           isinstance(cena.get('reference_from_seconds'), (int, float)) and
                           abs(cena['reference_from_seconds'] -
                               (anterior.get('source_in_seconds', 0) + anterior['end'] - anterior['start'])) < .1)
            if not continuidade:
                falha('F-PONTE-REAL', cid, 'o início do diagrama deve continuar do trecho real sem salto de origem')
            eventos = cena.get('cues') or []
            esperado = (('enter', 'seal', 'valves', 'rise', 'equalize', 'open', 'exit')
                        if eh_ciclo else
                        ('closed', 'water_enter', 'rise', 'equalize', 'release'))
            acoes = tuple(e.get('action') for e in eventos)
            tempos = [e.get('at') for e in eventos]
            tempos_validos = (len(tempos) == len(esperado) and
                             all(isinstance(t, (int, float)) for t in tempos))
            if not tempos_validos:
                falha('F-MECANISMO-CAUSAL', cid, 'ações/tempos ausentes ou inválidos')
            elif acoes != esperado or tempos != sorted(tempos) or len(set(tempos)) != len(tempos):
                falha('F-MECANISMO-CAUSAL', cid, 'ordem causal obrigatória')
            elif eh_ciclo:
                intervals = [b-a for a, b in zip(tempos, tempos[1:])]
                minimum = [2.0, 1.0, 1.0, 4.0, 1.0, 1.0]
                if (span < 15 or tempos[0] != 0 or tempos[-1] > span-1.1 or
                        any(gap < minim for gap,minim in zip(intervals,minimum))):
                    falha('F-CICLO-INCOMPLETO', cid,
                          'mostrar entrada, fecho, válvulas, enchimento longo, igualdade, abertura e saída sem pular etapas')
            elif (tempos[0] < 0 or tempos[-1] > span - .4 or
                  tempos[2] - tempos[1] < .4 or tempos[3] - tempos[1] < 1.5 or
                  tempos[4] < tempos[3]):
                falha('F-MECANISMO-CAUSAL', cid,
                      'exigir etapas distintas: fechar → entrar água → subir → igualar nível → liberar, com tempos coerentes')
        if span < 1.4 or span > max_span:
            falha('F-PLANO-SEM-DIRECAO', cid, f'{span:.1f}s: sem progressão suficiente para a duração')
        prev_end = end
        tipo = cena.get('type')
        if tipo == 'video' and span > 3.8:
            # Usa o MESMO contrato temporal do áudio natural; não forçar
            # corte a cada 3,8s quando uma ação genuína continua.
            # Declarações são apenas pré-direção: revisão dos quadros reais
            # e direitos seguem obrigatórios no portão editorial.
            from src.v4.formatos.tempo_natural import validar_progressao_video
            fonte = (plano.get('media') or {}).get(cena.get('asset'))
            for problema in validar_progressao_video(cena, span, fonte):
                falha('F-VIDEO-SEM-PROGRESSAO-COMPROVADA', cid, problema)
        if tipo == 'mechanism':
            if eh_causal or eh_ciclo:
                for e in cena.get('cues') or []:
                    if e.get('action') in ('enter', 'seal', 'valves', 'rise', 'equalize', 'open', 'exit', 'water_enter', 'release'):
                        momentos.add(('mecanismo', cid, e['action']))
            else:
                momentos.add(('mecanismo', cid))
        elif tipo == 'atlas_map' and cena.get('asset'):
            momentos.add(('ATLAS_MAPLIBRE', cid, cena['asset']))
        elif tipo == 'video' and cena.get('asset'):
            # Cortes de instantes DISTINTOS do mesmo clipe são acontecimentos
            # diferentes apenas se realmente distantes no tempo de origem.
            src_t = float(cena.get('source_in_seconds') or 0)
            momentos.add((cena['asset'], 'video', int(src_t // 3)))
        elif cena.get('asset'):
            momentos.add((cena['asset'], 'still'))
        if tipo == 'map' or cena.get('map') is not None:
            falha('F-MAPA-PROIBIDO', cid,
                  'componente vetorial simplificado retirado. Mapas finais devem usar o palco cartográfico ATLAS/MapLibre com raster licenciado; nunca substituição automática por polígonos.')
        if tipo not in TIPOS:
            falha('F-TIPO', cid, 'tipo de cena não suportado')
        if not str(cena.get('headline') or '').strip():
            falha('F-SEM-INFORMACAO', cid, 'título deve ligar imagem ao acontecimento')
        if not cena.get('cues') or any(
            not (0 <= x.get('at', -1) < span and x.get('label'))
            for x in cena.get('cues') or []
        ):
            falha('F-SEM-REVELACAO', cid, 'cena precisa acrescentar informação com objeto visível')
        if cena.get('evidence') not in ('literal', 'representative', 'explainer'):
            falha('F-SEM-PROVENIENCIA', cid, 'classifique literal, representativa ou explicativa')
        if tipo == 'mechanism':
            if (cena.get('mechanism') not in ('lock_filling', 'lock_causal', 'lock_cycle') or
                cena.get('evidence') != 'explainer' or cena.get('literal_identity')):
                falha('F-MECANISMO-NÃO-IDENTIFICADO', cid,
                      'esquema com princípio verificado, sem fingir filmagem ou identidade')
            if cena.get('asset'):
                falha('F-MECANISMO-SEM-ACERVO', cid, 'mecanismo é ilustração própria, não fotografia')
        elif tipo == 'atlas_map':
            if cena.get('evidence') != 'explainer' or cena.get('literal_identity'):
                falha('F-ATLAS-EVIDENCIA', cid,
                      'mapa ATLAS é representação cartográfica, não filmagem literal do fato')
            if cena.get('assetB') or cena.get('mechanism') or cena.get('map'):
                falha('F-ATLAS-EVIDENCIA', cid, 'mapa ATLAS usa clipe autenticado, nunca mapa simplificado/camadas extras')
        elif cena.get('evidence') == 'explainer':
            falha('F-EXPLICAÇÃO-SEM-MECANISMO', cid, 'explicativo precisa mecanismo real no compositor')
        if cena.get('evidence') == 'literal' and not cena.get('literal_identity'):
            falha('F-LITERAL-SEM-IDENTIDADE', cid, 'não alegar local/entidade exata sem identidade verificada')
        elif cena.get('evidence') == 'representative' and cena.get('literal_identity'):
            falha('F-REPRESENTATIVA-ROTULADA-LITERAL', cid, 'imagem genérica não pode alegar identidade exata')
        ids = [] if tipo == 'mechanism' else [cena.get('asset')]
        if tipo == 'comparison':
            ids.append(cena.get('assetB'))
            if len(set(ids)) != 2:
                falha('F-COMPARACAO-FAKE', cid, 'comparação precisa de dois referentes distintos')
        for mid in ids:
            if not mid or mid not in plano.get('media', {}):
                falha('F-MIDIA-SEM-CATALOGO', cid, f'{mid} não consta na curadoria')
                continue
            asset = plano['media'][mid]
            url = asset.get('url') or ''
            source = asset.get('local_source')
            if source:
                # Novo caminho autenticado: clip real produzido por PalcoMapa/MapLibre.
                # Sem atestado SHA de raster e inspeção técnica não há mídia.
                path = Path(source)
                atlas_bridge=(tipo == 'atlas_map')
                if atlas_bridge:
                    from src.v4.formatos.ponte_mapa_atlas import validar_comprovante
                    for problema in validar_comprovante(asset):
                        falha('F-ATLAS-COMPROVANTE',cid,problema)
                    if asset.get('media_type') != 'video' or not (asset.get('page') or '').startswith('https://'):
                        falha('F-ATLAS-COMPROVANTE',cid,'mapa deve ser MP4 sem áudio com fonte cartográfica')
                permitido = atlas_bridge or (
                    plano.get('tipo') == 'PROVA_VISUAL_PRIVADA' and (
                    str(path).startswith('tests/midia/') or
                    str(path).startswith('tests/piloto_ever_given/img/') or
                    str(path).startswith('motor4/formatos/dados/raster/') or
                    (str(path).startswith('stage_hero/') and
                     len(asset.get('expected_sha256') or '')==64 and
                     (asset.get('page') or '').startswith('https://www.dvidshub.net/video/'))))
                if not permitido or path.is_absolute() or '..' in path.parts:
                    falha('F-FIXTURE-NAO-AUTORIZADA', cid, 'arquivo local só na amostra privada e caminhos permitidos')
            elif urlsplit(url).scheme != 'https' or urlsplit(url).hostname not in ORIGENS:
                falha('F-ORIGEM-INSEGURA', cid, 'usar acervo real com URL verificável e confiável')
            if asset.get('license') not in LICENCAS or not asset.get('page') or not asset.get('credit'):
                falha('F-LICENCA', cid, 'mídia precisa de página, autor e licença explícitos')
            visual.add(mid)
    if cenas and abs(prev_end - plano.get('duracao', -1)) > .05:
        falha('F-DURACAO', '-', 'última cena não alcança a duração do roteiro')
    if len(momentos) < max(3, round(len(cenas)*.65)):
        falha('F-POUCO-ACERVO', '-', f'{len(momentos)} acontecimentos visuais diferentes para {len(cenas)} cenas; risco de repetição')
    if any(c.get('type') == 'comparison' for c in cenas) and len(visual) < 4:
        falha('F-COMPARACAO-REPETITIVA', '-', 'comparação deve trazer informação nova')
    from src.v4.formatos import direcao_eventos
    for item in direcao_eventos.verificar(cenas):
        falha(item['codigo'], item['cena'], item['motivo'])
    from src.v4.formatos import fiscal_progressao
    for item in fiscal_progressao.verificar(cenas, plano.get('media') or {}):
        falha(item['codigo'], item['cena'], item['motivo'])
    from src.v4.formatos import contrato_visual_comum
    comum = contrato_visual_comum.auditar(plano)
    # Gate compartilhado cobre declarações; o fiscal específico continua
    # responsável por curadoria, licença e tempos próprios do FILME.
    for erro in comum['falhas']:
        if erro['codigo'] != 'U-INSPECAO-VISUAL':
            falha(erro['codigo'], erro['id'], erro['motivo'])
    return {'pronto': not falhas, 'bloqueios': falhas, 'cenas': len(cenas),
            'medias_unicas': len(visual), 'momentos_visuais':len(momentos),
            'contrato_comum': comum,
            'visual_approval': 'NAO_FOI_AVALIADO'}


def preparar(plano: dict, destino: Path, public_root: Path, downloader=None) -> dict:
    import requests
    check = avaliar(plano)
    destino=Path(destino)
    destino.mkdir(parents=True,exist_ok=True)
    (destino/'contrato.json').write_text(json.dumps(check,ensure_ascii=False,indent=2),encoding='utf-8')
    if not check['pronto']:
        raise ValueError('pré-produção reprovada: '+json.dumps(check['bloqueios'],ensure_ascii=False))
    if downloader is None:
        def downloader(url: str) -> bytes:
            r=requests.get(url,timeout=90,headers={'User-Agent':'CoringaExplica/1.0 (license verification; contact via GitHub)'})
            r.raise_for_status()
            if len(r.content)>26_000_000:
                raise ValueError('arquivo excessivamente grande')
            return r.content
    public_root=Path(public_root)
    assets_dir=public_root/'film_editorial'
    assets_dir.mkdir(parents=True,exist_ok=True)
    medias, relatorio={},[]
    for mid,item in plano['media'].items():
        source = item.get('local_source')
        if source:
            # path traversal e symlinks são rejeitados na avaliação e no uso.
            src = (Path.cwd() / source).resolve()
            if not src.is_relative_to(Path.cwd().resolve()) or not src.is_file():
                raise ValueError(f'{mid}: arquivo de fixture não encontrado')
            data = src.read_bytes()
        else:
            data=downloader(item['url'])
        if not isinstance(data,bytes):
            raise ValueError(f'{mid}: sem bytes válidos')
        sha=hashlib.sha256(data).hexdigest()
        if item.get('expected_sha256') and item['expected_sha256']!=sha:
            raise ValueError(f'{mid}: hash da origem mudou — selecionar/curar novamente')
        if item.get('media_type') == 'video':
            if not source:
                raise ValueError(f'{mid}: vídeos de rede exigem ingestão/recorte em etapa separada')
            probe = subprocess.run(
                ['ffprobe','-v','error','-show_entries','stream=width,height',
                 '-select_streams','v:0','-of','json',str(src)],
                capture_output=True,text=True,check=True)
            streams=json.loads(probe.stdout).get('streams') or []
            if not streams or min(streams[0].get('width',0),streams[0].get('height',0))<700:
                raise ValueError(f'{mid}: vídeo sem qualidade mínima')
            w,h=streams[0]['width'],streams[0]['height']
            ext=src.suffix.lower()
            if ext not in ('.mp4','.webm'):
                raise ValueError(f'{mid}: container de vídeo inválido')
        else:
            import io
            with Image.open(io.BytesIO(data)) as img:
                if img.format not in ('JPEG','PNG','WEBP') or min(img.size)<600:
                    raise ValueError(f'{mid}: imagem inválida/pequena')
                ext={ 'PNG': '.png', 'WEBP': '.webp', 'JPEG': '.jpg' }[img.format]
                w,h=img.size
        out=assets_dir/f'{sha}{ext}'
        if not out.exists():
            out.write_bytes(data)  # preservar bytes idênticos, sem recomprimir
        medias[mid]={'asset':f'film_editorial/{sha}{ext}','sha256':sha,
                     'width':w,'height':h,'credit':item['credit'],
                     'license':item['license'],'page':item['page']}
        relatorio.append({'id':mid,'sha256':sha,'resolucao':[w,h],
                          'licenca':item['license'],'pagina':item['page']})
    shots=[]
    for c in plano['shots']:
        x={k:v for k,v in c.items() if k not in ('literal_identity','notes')}
        if c['type'] != 'mechanism':
            x['asset']=medias[c['asset']]['asset']
            x['source']=medias[c['asset']]['credit']
        else:
            x['source']='Esquema original · princípio hidráulico de uma eclusa'
            if c.get('reference_asset'):
                # Congelar um quadro do próprio master curado, antes de qualquer corte
                # interno da fonte. Evita fingir continuidade de dois instantes distintos.
                mid = c['reference_asset']
                if plano['media'][mid].get('media_type') != 'video':
                    raise ValueError('ponte causal exige vídeo real')
                src_video = public_root / medias[mid]['asset']
                pos = c['reference_from_seconds']
                frame = assets_dir / (medias[mid]['sha256'][:16] + '-ref-' +
                                      str(round(pos * 1000)) + '.png')
                subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',
                                '-ss',str(pos),'-i',str(src_video),
                                '-frames:v','1',str(frame)],check=True)
                if not frame.exists() or frame.stat().st_size < 3000:
                    raise ValueError('frame de ligação ausente')
                with Image.open(frame) as img:
                    if min(img.size) < 700:
                        raise ValueError('frame de ligação insuficiente')
                x['reference_asset'] = 'film_editorial/' + frame.name
        if c.get('assetB'):
            x['assetB']=medias[c['assetB']]['asset']
            x['sourceB']=medias[c['assetB']]['credit']
        shots.append(x)
    props={'duracao':plano['duracao'],'shots':shots,'preview':True}
    (destino/'props.json').write_text(json.dumps(props,ensure_ascii=False,indent=2),encoding='utf-8')
    (destino/'midias.json').write_text(json.dumps(relatorio,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'pronto':True,'shots':len(shots),'midias':len(medias),'props':str(destino/'props.json')}


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('plano')
    p.add_argument('saida')
    p.add_argument('public_root')
    a=p.parse_args(argv)
    plan=json.loads(Path(a.plano).read_text(encoding='utf-8'))
    r=preparar(plan,Path(a.saida),Path(a.public_root))
    print(json.dumps(r,ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
