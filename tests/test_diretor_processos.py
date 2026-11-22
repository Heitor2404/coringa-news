"""Diretor automático de mecanismos: prova sem escolher manualmente cenas/cues.

Dois domínios diferentes e casos impossíveis.
Não usa IA, não inspeciona pixels nem concede aprovação factual.
"""
import copy
import json
from pathlib import Path

import pytest

from src.v4.formatos import diretor_processos as DP
from src.v4.formatos import filme_editorial as F
from src.v4.formatos import catalogo_mecanismos as CAT

ROOT=Path(__file__).resolve().parents[1]
FICHA=ROOT/'docs/v4/formatos/DEMO_DIRETOR_EVENTOS_20261120.json'


def plano():
    return json.loads(FICHA.read_text(encoding='utf8'))


def codigos(p):
    return {x['codigo'] for x in F.avaliar(p)['bloqueios']}


def test_evento_estrutura_sozinha_dois_dominios():
    fonte=plano()
    assert not fonte.get('shots') and 'duracao' not in fonte
    assert not any('mechanism' in e or 'cues' in e or 'start' in e or 'end' in e
                   for e in fonte['eventos_diretor'])
    material=DP.expandir(fonte)
    assert F.avaliar(fonte)['pronto'],F.avaliar(fonte)['bloqueios']
    assert len(material['shots'])==2
    assert material['duracao']==24.4
    assert [CAT.decidir(s)[0] for s in material['shots']]==[
        'optical_projection','lock_cycle_standalone']
    assert [len(s['cues']) for s in material['shots']]==[4,7]
    assert material['diretor_automatico']['revisao_visual']=='PENDENTE'
    assert [e['action'] for e in material['shots'][1]['cues']]==[
        'enter','seal','valves','rise','equalize','open','exit']
    assert fonte.get('shots') is None  # não altera dado original


def test_preparar_clona_exatamente_a_versao_validada(tmp_path):
    p=plano()
    check=F.preparar(p,tmp_path/'run',tmp_path/'public')
    assert check['pronto']
    props=json.loads((tmp_path/'run/props.json').read_text('utf8'))
    assert [s['mechanism'] for s in props['shots']]==[
        'optical_projection','lock_cycle_standalone']
    assert all(not s.get('reference_asset') for s in props['shots'])
    # A gramática causal deve chegar nos props consumidos pelo Remotion,
    # não ficar apenas no relatório abstrato da fase de planejamento.
    assert all(s['processo_visual']['grafo_causal_requerido'] for s in props['shots'])
    assert [s['plano_causal']['capacidade'] for s in props['shots']]==[
        'optical_projection','lock_cycle_standalone']
    assert [len(s['plano_causal']['eventos']) for s in props['shots']]==[4,7]
    assert all(e['camera']['alvos'] and e['relacoes_em_foco']
               for scene in props['shots']
               for e in scene['plano_causal']['eventos'])
    assert all(scene['plano_causal']['revisao_visual']=='PENDENTE'
               for scene in props['shots'])
    assert props['duracao']==24.4
    assert not props.get('publicar',False)
    assert p.get('shots') is None


def test_promessa_de_entrada_saida_com_recurso_sem_saida_e_bloqueada():
    p=plano()
    s=p['eventos_diretor'][1]['direcao_evento']
    s['acoes_necessarias']=['closed','water_enter','rise','equalize','release']
    # Mesmo com uma lista válida de ações, o registro da eclusa parcial não
    # demonstra a entrada e a saída exigidas pela ficha.
    assert 'F-DIRETOR-SEM-CAPACIDADE' in codigos(p)


def test_evento_sem_mecanismo_suficiente_falha_sem_render():
    p=plano()
    p['eventos_diretor'][1]['direcao_evento']['acoes_necessarias']=[
        'enter','scan','classify','exit']
    assert 'F-DIRETOR-SEM-CAPACIDADE' in codigos(p)


def test_proibido_inferir_fisica_de_assunto_livre():
    p=plano()
    p['eventos_diretor'][1]['direcao_evento']={
        'intencao':'demonstrar_acao',
        'fato_id':'objetivo_tornado',
        'aprendizado':'Mostrar como o vento gira em um tornado',
    }
    assert 'F-DIRETOR-SEM-ACOES' in codigos(p)


def test_roteiro_sem_duracao_nao_pode_inventar_segundos():
    p=plano()
    del p['eventos_diretor'][1]['duracao_s']
    assert 'F-DIRETOR-TEMPO' in codigos(p)
    p=plano()
    p['eventos_diretor'][1]['duracao_s']=2
    # Eventuais distorções temporais ficam com o pré-flight original.
    assert not F.avaliar(p)['pronto']


def test_nao_aceita_misturar_manual_e_auto():
    p=plano()
    p['shots']=[{'id':'x'}]
    assert 'F-DIRETOR-AMBIGUO' in codigos(p)


def test_nao_pode_gerar_final_com_biblioteca_vazia_e_sem_voz():
    p=plano()
    p['tipo']='FILME_FINAL'
    p['publicar']=True
    assert 'F-DIRETOR-SEM-GATE' in codigos(p)


def test_sem_prova_ou_intencao_distinta_bloqueia():
    p=plano()
    p['eventos_diretor'][1]['direcao_evento']['fato_id']='principio_otico_euv'
    assert 'F-DIRETOR-SEM-FATO' in codigos(p)
    p=plano()
    p['eventos_diretor'][1]['direcao_evento']['intencao']='mostrar_registro'
    assert 'F-DIRETOR-INTENCAO' in codigos(p)


def test_roteiro_mantem_pistas_tematica_mas_decisao_vem_das_acoes():
    p=plano()
    for e in p['eventos_diretor']:
        e['headline']='QUAL É O MECANISMO?'
        e['lead']='OUTRO ASSUNTO'
        e['subject']='Esquema didático do objeto hipotético'
    expanded=DP.expandir(p)
    assert [CAT.decidir(s)[0] for s in expanded['shots']]==[
        'optical_projection','lock_cycle_standalone']


def test_legacy_continua_validando_sem_auto():
    p=json.loads((ROOT/'docs/v4/formatos/filme_panama_ciclo_19s.json').read_text('utf8'))
    assert F.avaliar(p)['pronto']
    assert DP.expandir(p) is p
