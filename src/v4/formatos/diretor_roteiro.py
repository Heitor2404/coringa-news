"""Triagem de roteiro V2 → decisões de DIREÇÃO visual do FilmeEditorial.

Reusa o contrato de acontecimento V2 e a linguagem visual V3. Consulta o
catálogo de mecanismos V4 e a biblioteca comprovada V4, mas distingue
CANDIDATO de PROVA REAL PRONTA: arquivos/identidade/direitos não são
certificados por coincidência de palavras. Não faz NLP por regex da fala.

NÃO prepara mídia, não cria mecanismo, não inventa fatos, não publica.
O relatório sempre explica o que está faltando; sem fonte/capacidade
verdadeira o status de produção é bloqueado.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import unicodedata
from pathlib import Path

from src.v2 import contrato as contrato_v2
from src.v3 import linguagem
from src.v4.formatos import catalogo_mecanismos


# Apenas termos genéricos, nenhum nome de país/assunto/empresa.
COMUNS = frozenset(
    'de da do das dos e a o em no na para por com um uma os as sua seus '
    'sobre onde quando qual como foi sao era que tem mais mesmo'.split()
)


def _normal(s: object) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD',str(s or '').lower())
                   if not unicodedata.combining(c))


def _tokens(s: object) -> set[str]:
    return {t for t in re.findall(r'[a-z0-9]+',_normal(s))
            if (len(t)>=3 or t.isdigit()) and t not in COMUNS}


def _aprovacao_interna(x: dict) -> bool:
    """Suficiente para SUGERIR candidato; não comprova arquivo local."""
    p = x.get('prova') or {}
    sha = x.get('sha256_origem')
    return (
        x.get('natureza') in ('foto','video','documento')
        and p.get('midia_corresponde') is True
        and isinstance(sha,str) and len(sha)==64
        and x.get('licenca') and x.get('credito')
        and x.get('id')
    )


def candidatos(cena: dict, tipo: str, biblioteca: dict) -> list[dict]:
    """Encontra candidatos por identidade do sujeito, não prova ação física.

    Retorna somente candidatos. Nenhuma nota textual equivale a prova nova,
    licença revalidada, continuidade ou bytes locais.
    """
    ac = cena['acontecimento']
    sujeito = str(ac.get('sujeito') or '').strip()
    identidade = _tokens(sujeito)
    if not identidade:
        return []
    reprovados = {x.get('id') for x in biblioteca.get('reprovados') or []}
    formas = {'documento': {'documento','foto'},
              'citacao': {'documento'},
              'pessoa': {'foto','video'},
              'lugar': {'foto','video'},
              'ambiente': {'foto','video'},
              'evento_historico': {'foto','video','documento'}}
    permitidas = formas.get(tipo,{'foto','video'})
    out = []
    for x in biblioteca.get('itens') or []:
        if not isinstance(x,dict) or x.get('id') in reprovados or (
            not _aprovacao_interna(x) or x.get('natureza') not in permitidas
        ):
            continue
        descritivo = _tokens(' '.join(str(x.get(k) or '') for k in ('titulo','mostra')))
        # "TSMC Fab 18" precisa aparecer no inventário, e não somente "Taiwan".
        # Sujeitos de uma palavra precisam ter ao menos 6 caracteres e ocorrência
        # literal, para "água" ou "navio" não converterem foto genérica em prova.
        coincidiu = (
            len(identidade)>=2 and identidade.issubset(descritivo)
        ) or (
            len(identidade)==1 and len(next(iter(identidade)))>=6
            and next(iter(identidade)) in descritivo
        )
        if not coincidiu:
            continue
        out.append({'asset_id':x['id'],'natureza':x['natureza'],
                    'mostra':x.get('mostra'),'sha_catalogo':x['sha256_origem'],
                    'estado':'CANDIDATO_NAO_REIDRATADO',
                    'revisao_de_evento':'PENDENTE'})
    return sorted(out,key=lambda x:x['asset_id'])


def _issue(code: str, cena: str, detail: str) -> dict:
    return {'codigo':code,'cena':cena,'motivo':detail}


def analisar(plano: dict, biblioteca: dict | None = None) -> dict:
    """Plano com roteiro.cenas: contratos V2 e fala, mas SEM recursos escolhidos."""
    if not isinstance(plano,dict):
        return {'pronto_para_render':False,'bloqueios':[
            _issue('R-CONTRATO','-','plano inválido')], 'decisoes':[]}
    if biblioteca is None:
        from src.v4.formatos import ponte_biblioteca
        biblioteca = ponte_biblioteca.catalogo()
    if not isinstance(biblioteca,dict):
        biblioteca={'itens':[],'reprovados':[]}
    shots = plano.get('roteiro')
    cenas = shots.get('cenas') if isinstance(shots,dict) else None
    failures, decisions, seen, total = [], [], set(), 0.0
    if not isinstance(cenas,list) or not cenas:
        failures.append(_issue('R-SEM-ROTEIRO','-','falta roteiro.cenas'))
        cenas=[]
    if plano.get('publicar') is not False or plano.get('tipo') != 'PROVA_VISUAL_PRIVADA':
        failures.append(_issue('R-SEM-GATE','-','triagem limitada a prévia privada, sem publicação'))
    if plano.get('shots') or plano.get('eventos_diretor'):
        failures.append(_issue('R-RECURSO-PREDEFINIDO','-',
                               'não testar direção automática com recursos previamente escolhidos'))
    for i,c in enumerate(cenas):
        cid = str(c.get('id') or f'cena-{i+1}') if isinstance(c,dict) else f'cena-{i+1}'
        if not isinstance(c,dict):
            failures.append(_issue('R-CENA',cid,'cena não é objeto'))
            continue
        ac = contrato_v2.declarado(c)
        if not ac or not ac.get('tipo'):
            failures.append(_issue('R-ACONTECIMENTO-AUSENTE',cid,
                                   'não inferir tipo/ação/objeto de texto livre por palavras-chave'))
            continue
        if ac.get('capacidade') or c.get('asset') or c.get('mechanism') or c.get('modalidade'):
            failures.append(_issue('R-RECURSO-PREDEFINIDO',cid,
                                   'o roteiro não deve selecionar recurso visual neste teste'))
            continue
        fid = ac.get('id')
        if not isinstance(fid,str) or not fid.strip() or fid in seen:
            failures.append(_issue('R-ID',cid,'acontecimento sem id único'))
            continue
        seen.add(fid)
        dur = c.get('duracao_s')
        if (not isinstance(dur,(int,float)) or isinstance(dur,bool)
                or not math.isfinite(dur) or dur<=0):
            failures.append(_issue('R-TEMPO',cid,'sem duração medida/dirigida; não inventar tempo de voz'))
            continue
        total += float(dur)
        tipo = ac['tipo']
        forma = linguagem.FORMA_DO_TIPO.get(tipo,'indisponivel')
        row = {'cena':cid,'fato_id':fid,'fala':c.get('fala'),
               'sujeito':ac.get('sujeito'),'tipo_v2':tipo,'forma_v3':forma,
               'estado':'BLOQUEADO','capacidade':None,'candidatos':[],
               'source_declarada':ac.get('fonte'),
               'prova_factual_verificada':False,'revisao_mp4':'PENDENTE',
               'duracao_s':float(dur),'bloqueios':[]}
        def bloquear(code: str, description: str):
            item=_issue(code,cid,description)
            row['bloqueios'].append(item)
            failures.append(item)

        # Tipos físicos não podem ser substituídos por foto de máquina, zoom
        # ou diagrama de palavras. Só os renderizadores concretos homologados.
        if tipo in linguagem.ACAO_ESSENCIAL:
            data=ac.get('dados') or {}
            actions=data.get('acoes_necessarias')
            phases=data.get('fases_necessarias')
            if (not isinstance(actions,list) or not actions or
                    not isinstance(phases,list) or not phases):
                bloquear('R-ACOES-SEM-CONTRATO',
                         'contrato V2 não explicita ações e fases observáveis; revisão semântica necessária')
            else:
                choices=[cap for cap in catalogo_mecanismos.CAPACIDADES.values()
                         if not cap.media_real_obrigatoria and cap.acoes==tuple(actions)
                         and set(phases).issubset(cap.fases)]
                if len(choices)==1:
                    cap=choices[0]
                    row.update(estado='CAPACIDADE_TECNICA_DISPONIVEL',
                               capacidade=cap.id,
                               acoes=list(cap.acoes),fases=list(phases))
                    # Sem fonte factual aprovada e aprovação de MP4 isso é só
                    # contrato técnico, não licença de produção ou de publicar.
                else:
                    bloquear('R-SEM-MECANISMO',
                             'nenhum mecanismo implementado representa as ações físicas e fases solicitadas')
        elif tipo in ('pessoa','lugar','ambiente','evento_historico','documento','citacao'):
            options=candidatos({**c,'acontecimento':ac},tipo,biblioteca)
            row['candidatos']=options
            if options:
                row['estado']='CANDIDATO_DOCUMENTAL_SEM_BYTES'
                bloquear('R-ASSET-NAO-REVALIDADO',
                         'foto/vídeo candidato identificado; faltam bytes originais, proveniência da cena e revisão factual')
            else:
                bloquear('R-SEM-REGISTRO',
                         'nenhuma mídia candidata com identidade específica no acervo comprovado')
        elif tipo in ('localizacao','territorio','deslocamento'):
            row['estado']='MAPA_ATLAS_PENDENTE'
            bloquear('R-MAPA-SEM-PROVA',
                     'mapa precisa de roi, clipe ATLAS e comprovante vinculados ao acontecimento')
        else:
            bloquear('R-FORMA-NAO-IMPLEMENTADA',
                     'recurso adequado não disponível no FilmeEditorial ou dados/fonte insuficientes')
        if not ac.get('fonte'):
            bloquear('R-FONTE-NAO-DECLARADA',
                     'fato não tem fonte; sem isso não é possível aprovar roteiro')
        decisions.append(row)

    return {'versao':1,'motor':'filme_editorial',
            'status':'BLOQUEADO' if failures else 'CONTRATO_TECNICO_SEM_APROVACAO',
            'pronto_para_render':False, # esta triagem jamais dá aprovação de MP4
            'duracao_declarada_s':round(total,3),
            'total_cenas':len(cenas),
            'capacidade_tecnica':sum(x['estado']=='CAPACIDADE_TECNICA_DISPONIVEL' for x in decisions),
            'midia_candidata':sum(x['estado']=='CANDIDATO_DOCUMENTAL_SEM_BYTES' for x in decisions),
            'cenas_bloqueadas':sum(bool(x['bloqueios']) for x in decisions),
            'bloqueios':failures,'decisoes':decisions,
            'proxima_etapa':'validar fatos, contratos de ações, bytes/licença das mídias e inspeção visual antes de produzir',
            'publicar':False,'telegram':False,'chamadas_ia':0}


def main(argv=None) -> int:
    cli=argparse.ArgumentParser(description='Diagnóstico privado do roteiro até escolha da forma visual')
    cli.add_argument('roteiro_json')
    cli.add_argument('saida_json')
    args=cli.parse_args(argv)
    inp=json.loads(Path(args.roteiro_json).read_text(encoding='utf8'))
    report=analisar(inp)
    path=Path(args.saida_json)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:report[k] for k in (
        'status','total_cenas','capacidade_tecnica','midia_candidata','cenas_bloqueadas')},
        ensure_ascii=False))
    return 0 if not report['bloqueios'] else 2


if __name__ == '__main__':
    sys.exit(main())
