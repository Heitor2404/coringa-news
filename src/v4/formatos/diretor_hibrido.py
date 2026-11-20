"""Montagem híbrida PRIVADA a partir do roteiro V2, sem escolher shots/asset manualmente.

Reutiliza:
  - diretor_roteiro: forma V3 e candidatos realmente disponíveis
  - diretor_processos: estado/tempo de mecanismos existentes
  - filme_editorial: portas de origem, SHA, licença, preparo e Remotion

Única exceção permitida à triagem R-ASSET-NAO-REVALIDADO:
fotografia contextual específica com proveniência verificada no catálogo.
O SHA real é conferido pelo FILME.preparar ANTES de um frame ir para o render.
A cena é sempre representative/explicar_contexto: NÃO é prova literal de ação.
Não cria vídeo genérico, não cria mapas fictícios, não publica e não usa APIs IA.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from urllib.parse import urlsplit

from src.v2 import contrato as contrato_v2
from src.v4.formatos import diretor_roteiro
from src.v4.formatos import filme_editorial as FILME


class MontagemHibridaBloqueada(ValueError):
    def __init__(self, bloqueios: list[dict], relatorio: dict | None = None):
        self.bloqueios = bloqueios
        self.relatorio = relatorio
        super().__init__('montagem híbrida sem evidência completa: ' +
                         json.dumps(bloqueios, ensure_ascii=False)[:800])


def _erro(codigo: str, cena: str, motivo: str):
    return {'codigo': codigo, 'cena': cena, 'motivo': motivo}


def _prova_candidata_foto(row: dict, biblioteca: dict) -> dict:
    """Confere metadados ANTES do download, não finge validar bytes."""
    cid = row['cena']
    if not row.get('candidatos') or len(row['candidatos']) != 1:
        raise MontagemHibridaBloqueada([_erro(
            'H-CANDIDATO-AMBIGUO', cid,
            'foto literal exige um único referente candidato; revisão humana se houver mais'
        )])
    candidato = row['candidatos'][0]
    id_ref = candidato['asset_id']
    itens = [x for x in biblioteca.get('itens', []) if x.get('id') == id_ref]
    if len(itens) != 1:
        raise MontagemHibridaBloqueada([_erro('H-REFERENCIA-AUSENTE',cid,
                                              'candidato não está no acervo atual')])
    it = itens[0]
    prova = it.get('prova') or {}
    url = it.get('url') or ''
    page = it.get('pagina') or it.get('page') or ''
    valid = (
        it.get('natureza') == 'foto'
        and it.get('licenca') in ('CC BY 2.0', 'CC BY 3.0', 'CC BY 4.0', 'CC0', 'Public domain')
        and prova.get('midia_corresponde') is True
        and (prova.get('licenca_confirmada_pela_API') is True or
             prova.get('confirmacao_humana') is True)
        and isinstance(it.get('sha256_origem'),str)
        and len(it['sha256_origem']) == 64
        and all(c in '0123456789abcdef' for c in it['sha256_origem'])
        and (urlsplit(url).scheme == 'https'
             and urlsplit(url).hostname in ('upload.wikimedia.org','thumb.wikimedia.org'))
        and (urlsplit(page).scheme == 'https'
             and urlsplit(page).hostname == 'commons.wikimedia.org')
        and bool(it.get('credito'))
    )
    if not valid:
        raise MontagemHibridaBloqueada([_erro(
            'H-MIDIA-SEM-PROVENIENCIA',cid,
            'revisar identidade, licença exata, fonte Wikimedia e SHA do candidato')])
    return it



def _cena_video_contextual(cena:dict, row:dict, biblioteca:dict, inicio:float)->tuple[dict,str,dict]:
    """Clipes são contextuais, sem afirmar que apresentam ação específica.
    Exige janela e ROI anexadas ao ORIGINAL. Não inventa ponto de câmera.
    """
    cid=row['cena']
    options=row['candidatos']
    if len(options)!=1 or options[0].get('natureza')!='video':
        raise MontagemHibridaBloqueada([_erro('H-VIDEO-AMBIGUO',cid,
                                           'seleção exige 1 única origem em vídeo contextual')])
    matches=[x for x in biblioteca.get('itens') or []
             if x.get('id')==options[0]['asset_id'] and x.get('natureza')=='video']
    if len(matches)!=1:
        raise MontagemHibridaBloqueada([_erro('H-VIDEO-SEM-FONTE',cid,
                                           'vídeo não está na biblioteca V3 curada')])
    it=matches[0]
    ac=contrato_v2.declarado(cena)
    if ac.get('tipo') not in ('lugar','ambiente','pessoa'):
        raise MontagemHibridaBloqueada([_erro('H-VIDEO-REGISTRO-ESPECIFICO',cid,
                'vídeo contextual não demonstra evento histórico, ação técnica ou processo')])
    if it.get('licenca')!='REVIEW_PENDING' or it.get('publicar') is not False or (
        it.get('comprova_acao') is not False or it.get('comprova_fato_tsmc') is not False):
        raise MontagemHibridaBloqueada([_erro('H-VIDEO-DIREITOS',cid,
                'somente vídeo com direitos pendentes e declarações de não comprovação')])
    win=it.get('janela') or {}
    source=it.get('stage_source')
    sha=it.get('sha256_origem')
    if (not isinstance(source,str) or not source.startswith('stage_documental/') or
        not isinstance(sha,str) or len(sha)!=64 or
        not isinstance(it.get('inspecao'),str) or len(it['inspecao'])<35):
        raise MontagemHibridaBloqueada([_erro('H-VIDEO-PROVA',cid,
                'origem, SHA, inspeção e região de vídeo ausentes')])
    start=win.get('inicio_s')
    source_dur=win.get('duracao_s')
    dur=cena['duracao_s']
    if (not isinstance(start,(int,float)) or not isinstance(source_dur,(int,float))
        or not math.isfinite(start) or not math.isfinite(source_dur)
        or abs(source_dur-dur)>.05):
        raise MontagemHibridaBloqueada([_erro('H-VIDEO-JANELA',cid,
                'duração do roteiro deve coincidir com a janela curada; não acelerar a fonte')])
    points=win.get('roi') or []
    video_fr={
        'modo':'roi_observada','sha256_origem':sha,
        'inspecao':it['inspecao'],
        'pontos':[
            {'at':p['at'],'fonte_s':round(start+p['at'],4),
             'area_essencial':p['area_essencial']} for p in points
        ],
    }
    mid='v3-'+sha[:16]
    media={
        'local_source':source,'expected_sha256':sha,
        'url':it['pagina'],'page':it['pagina'],
        'license':'REVIEW_PENDING','rights_status':'REVIEW_PENDING',
        'credit':it['credito'],'media_type':'video',
        'width':it['width'],'height':it['height'],
        'duration_s':it['duration_s'],
    }
    ref=str(ac.get('sujeito') or '').strip()
    shot={
        'id':cid,'start':round(inicio,4),'end':round(inicio+dur,4),
        'type':'video','asset':mid,'source_in_seconds':start,
        'video_framing':video_fr,
        'evidence':'representative','lead':'VÍDEO REAL · REGISTRO CONTEXTUAL',
        'headline':ref.upper(),'subject':'Imagem institucional de origem identificada, sem prova de ação específica',
        'cues':[{'at':min(.48,dur*.20),'label':'ACERVO INSTITUCIONAL · CONTEXTO'}],
        'direcao_evento':{
            'intencao':'explicar_contexto','fato_id':ac['id'],
            'aprendizado':'Local e equipamentos da fonte, sem atribuir o laboratório ao evento narrado',
        },
    }
    return shot,mid,media



def planejar(plano: dict, biblioteca: dict | None = None) -> dict:
    """Resolver roteiro híbrido somente com fotos contextuais e mecanismos
    já executáveis. Não inventa cena para satisfazer duração.
    """
    if not isinstance(plano,dict):
        raise MontagemHibridaBloqueada([_erro('H-CONTRATO','-','roteiro inválido')])
    if plano.get('tipo')!='PROVA_VISUAL_PRIVADA' or plano.get('publicar') is not False:
        raise MontagemHibridaBloqueada([_erro('H-PUBLICACAO','-',
                                             'somente prova técnica privada')])
    if plano.get('shots') or plano.get('eventos_diretor'):
        raise MontagemHibridaBloqueada([_erro('H-RECURSO-PRESELECIONADO','-',
                                             'entrada deve ser contrato V2 sem visual escolhido')])
    if biblioteca is None:
        from src.v4.formatos import ponte_biblioteca
        biblioteca = ponte_biblioteca.catalogo()
    report = diretor_roteiro.analisar(plano,biblioteca)
    rows = report['decisoes']
    cenas = ((plano.get('roteiro') or {}).get('cenas') or [])
    if len(rows)!=len(cenas) or not rows:
        raise MontagemHibridaBloqueada(report['bloqueios'] or [_erro(
            'H-ROTEIRO','-','roteiro sem cenas V2 completas')],report)
    impedimentos=[]
    for row in rows:
        if row['estado']=='CAPACIDADE_TECNICA_DISPONIVEL' and not row['bloqueios']:
            continue
        if (row['estado']=='CANDIDATO_DOCUMENTAL_SEM_BYTES'
            and len(row['bloqueios'])==1
            and row['bloqueios'][0]['codigo']=='R-ASSET-NAO-REVALIDADO'):
            continue
        impedimentos.extend(row['bloqueios'] or [_erro(
            'H-FORMA-INDISPONIVEL',row['cena'],'forma sem renderer ou prova')])
    if impedimentos:
        raise MontagemHibridaBloqueada(impedimentos,report)

    start=0.0
    generated=[]
    media={}
    used=set()
    for c,row in zip(cenas,rows):
        cid=row['cena']
        ac=contrato_v2.declarado(c)
        dur=c['duracao_s']
        if row['estado']=='CAPACIDADE_TECNICA_DISPONIVEL':
            # Reusa mesmo contrato de eventos sem nomear o componente.
            single={**plano, 'roteiro':{'cenas':[c]}}
            passage=diretor_roteiro.expandir_preview(single,biblioteca)
            if len(passage['shots'])!=1:
                raise MontagemHibridaBloqueada([_erro('H-PROCESSO',cid,
                                                   'diretor não gerou o mecanismo')],report)
            shot=dict(passage['shots'][0])
            shot['start']=round(start,4)
            shot['end']=round(start+dur,4)
        else:
            if len(row.get('candidatos') or [])==1 and row['candidatos'][0]['natureza']=='video':
                shot,mid,metadados=_cena_video_contextual(c,row,biblioteca,start)
                if mid in used:
                    raise MontagemHibridaBloqueada([_erro('H-VIDEO-REPETIDO',cid,
                            'não reutilizar mesmo vídeo como novo acontecimento')],report)
                used.add(mid)
                media[mid]=metadados
                generated.append(shot)
                start=round(start+dur,4)
                continue
            # Contrato de REGISTRO ainda é uma proposta; sem revisão humana de
            # identidade nesta rodada, só exibimos a foto como CONTEXTO.
            if ac.get('tipo') not in ('lugar','ambiente','pessoa'):
                raise MontagemHibridaBloqueada([_erro(
                    'H-REGISTRO-ESPECIFICO',cid,
                    'foto candidata não prova acontecimento histórico/ação sem inspeção dedicada'
                )],report)
            it=_prova_candidata_foto(row,biblioteca)
            if it['id'] in used:
                raise MontagemHibridaBloqueada([_erro(
                    'H-FOTO-REPETIDA',cid,'mesmo arquivo não vira nova informação por zoom'
                )],report)
            used.add(it['id'])
            mid='bib-'+it['sha256_origem'][:16]
            media[mid]={
                'url':it['url'],
                'expected_sha256':it['sha256_origem'],
                'page':it['pagina'],
                'license':it['licenca'],
                'credit':it['credito'],
                'media_type':'photo',
            }
            # "mostrar ..." é INSTRUÇÃO INTERNA de direção, não legenda.
            # O texto público só vem da identidade factual do sujeito;
            # nenhuma frase de roteiro é transformada em slogan por regex.
            title=str(ac.get('sujeito') or '').strip()
            if len(title)>70 or not title:
                raise MontagemHibridaBloqueada([_erro(
                    'H-LEGENDA',cid,'sujeito não é título público legível; revisar narrativa'
                )],report)
            ano=it.get('ano')
            if not isinstance(ano,int) or not 1800<=ano<=2100:
                ano=None
            context='Foto de arquivo'+(f' · {ano}' if ano else '')
            shot={
                'id':cid, 'start':round(start,4),'end':round(start+dur,4),
                'type':'photo','asset':mid,
                'evidence':'representative','lead':'REGISTRO CONTEXTUAL · ARQUIVO',
                'headline':title.upper(),'subject':context,
                'focus':it.get('roi') and [
                    (it['roi'][0]+it['roi'][2])/2,(it['roi'][1]+it['roi'][3])/2
                ] or [.5,.5],
                'cues':[{'at':min(.55,dur*.22),
                         'label':f'FOTOGRAFIA · {ano}' if ano else 'REGISTRO CONTEXTUAL'}],
                'direcao_evento':{
                    'intencao':'explicar_contexto',
                    'fato_id':str(ac['id']),
                    'aprendizado':str(ac.get('mostrar') or ac.get('acao') or '')[:220],
                },
            }
        generated.append(shot)
        start=round(start+dur,4)
    composed={
        'formato':'filme_editorial','tipo':'PROVA_VISUAL_PRIVADA',
        'publicar':False,'titulo':plano.get('titulo') or 'Prova editorial',
        'duracao':start,'media':media,'shots':generated,
        'observacao':'QA PRIVADA: fotografia contextual com SHA verificado no preparar; '
                     'nenhum registro de ação ou aprovação humana implícitos.',
    }
    gate=FILME.avaliar(composed)
    if not gate['pronto']:
        raise MontagemHibridaBloqueada(gate['bloqueios'],report)
    return {'plano':composed,'triagem':report,
            'proveniencia':{
                'estado':'PLANEJADO_SEM_BYTES',
                'reidratacao_SHA':'EXIGIDA_NO_PREPARAR',
                'revisao_contextual':'PENDENTE',
                'aprovacao_editorial':False,
                'publicar':False,'telegram':False,
            }}


def preparar(plano: dict, destino: Path, public_root: Path, downloader=None,
             biblioteca: dict | None = None) -> dict:
    """A saída só recebe status SHA_VERIFICADO depois do FILME.preparar validar
    os bytes; por padrão usa o downloader seguro do FilmeEditorial.
    """
    pre=planejar(plano,biblioteca)
    destino=Path(destino)
    destino.mkdir(parents=True,exist_ok=True)
    (destino/'triagem.json').write_text(json.dumps(
        pre['triagem'],ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    (destino/'plano_hibrido.json').write_text(json.dumps(
        pre['plano'],ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    if downloader is None:
        # Não reimplementar downloader/HTTP: usar somente o de Commons
        # do adaptador já existente, com host e redirects controlados.
        from src.v4.formatos.montagem_privada_real import baixar_imagem
        downloader=baixar_imagem
    result=FILME.preparar(pre['plano'],destino,public_root,downloader=downloader)
    public_assets=Path(public_root)/'film_editorial'
    checks={}
    for asset,meta in pre['plano']['media'].items():
        expected=meta['expected_sha256']
        files=list(public_assets.glob(expected+'.*'))
        if len(files)!=1 or not files[0].is_file():
            raise ValueError('H-BYTES-MISSING: mídia verificada ausente '+asset)
        import hashlib
        digest=hashlib.sha256(files[0].read_bytes()).hexdigest()
        if digest != expected:
            raise ValueError('H-BYTES-CHANGED: mídia alterada após ingestão '+asset)
        checks[asset]={'sha256_verificado':digest,'status':'BYTES_VERIFICADOS'}
    prov={**pre['proveniencia'],
          'estado':'ORIGINAIS_SHA_VERIFICADOS',
          'reidratacao_SHA':'CONFERIDA',
          'midias':checks}
    (destino/'proveniencia_hibrida.json').write_text(json.dumps(
        prov,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return {**result,'proveniencia_hibrida':prov}



def main(argv=None):
    import argparse
    import sys
    parser=argparse.ArgumentParser(description='Prova híbrida V2: foto original SHA + mecanismo físico sem falsear fatos')
    parser.add_argument('roteiro_json')
    parser.add_argument('saida')
    parser.add_argument('public_root')
    parser.add_argument('--so-planejar',action='store_true',
                        help='sem rede; relatório de candidatos e preflight, não valida bytes')
    args=parser.parse_args(argv)
    plano=json.loads(Path(args.roteiro_json).read_text('utf8'))
    pasta=Path(args.saida)
    pasta.mkdir(parents=True,exist_ok=True)
    try:
        if args.so_planejar:
            plan=planejar(plano)
            (pasta/'plano_hibrido.json').write_text(json.dumps(
                plan['plano'],ensure_ascii=False,indent=2)+'\n',encoding='utf8')
            (pasta/'triagem.json').write_text(json.dumps(
                plan['triagem'],ensure_ascii=False,indent=2)+'\n',encoding='utf8')
            print(json.dumps({'status':'PLANEJADO_NAO_VERIFICADO',
                              'publicar':False,'duracao':plan['plano']['duracao']},
                             ensure_ascii=False))
            return 0
        result=preparar(plano,pasta,Path(args.public_root))
        print(json.dumps({'status':'PRIVADO_ORIGINAIS_SHA_VERIFICADOS',
                          'publicar':False,'pronto_qa':result['pronto']},
                         ensure_ascii=False))
        return 0
    except MontagemHibridaBloqueada as exc:
        (pasta/'bloqueios_hibridos.json').write_text(json.dumps({
            'status':'BLOQUEADO','bloqueios':exc.bloqueios,
            'triagem':exc.relatorio,'publicar':False,
        },ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        print(str(exc),file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
