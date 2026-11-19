"""Duração escolhida pelos acontecimentos, sem pad para monetização nem teto arbitrário."""
import copy
import json
from pathlib import Path

import pytest
from src.v4.formatos import tempo_natural as T, diretor as D
from src.v4.formatos import gate_filme_completo as G

ROOT=Path(__file__).resolve().parents[1]
BRIEF=ROOT/'docs/v4/formatos/CONTRATO_PILOTO_TAIWAN_INTEGRAL_20261119.json'


def brief():
    return json.loads(BRIEF.read_text(encoding='utf8'))


@pytest.mark.parametrize('dur,tk,yt',[
    (42,'ABAIXO_MINIMO_CREATOR_REWARDS','SHORTS_COMPATIVEL'),
    (60,'ABAIXO_MINIMO_CREATOR_REWARDS','SHORTS_COMPATIVEL'),
    (61,'ACIMA_DE_UM_MINUTO_MAS_SEM_MARGEM_PREFERIDA','SHORTS_COMPATIVEL'),
    (65,'DURACAO_COMPATIVEL_CREATOR_REWARDS','SHORTS_COMPATIVEL'),
    (120,'DURACAO_COMPATIVEL_CREATOR_REWARDS','SHORTS_COMPATIVEL'),
    (180,'DURACAO_COMPATIVEL_CREATOR_REWARDS','SHORTS_COMPATIVEL'),
    (220,'DURACAO_COMPATIVEL_CREATOR_REWARDS','EXIGE_OUTRO_FORMATO_OU_VERSAO'),
])
def test_duracao_adequacao_comercial_independe_da_historia(dur,tk,yt):
    r=T.avaliar_destinos(dur)
    assert r['duracao_master_s']==dur
    assert r['destinos']['tiktok']['estado']==tk
    assert r['destinos']['youtube_shorts']['estado']==yt
    assert r['destinos']['instagram_reels']['estado']=='SEM_MINIMO_UNIVERSAL_DE_60S'
    assert r['duracao_maxima_editorial_s'] is None
    assert not r['garante_monetizacao']
    assert r['nao_esticar_nem_cortar_automaticamente']


@pytest.mark.parametrize('valor',[0,-1,float('nan'),float('inf'),True])
def test_rejeita_duracao_invalida(valor):
    with pytest.raises(ValueError):
        T.avaliar_destinos(valor)


def test_nao_altera_montagem_para_bater_65():
    p={'shots':[{'id':'a','start':0,'end':2,'type':'video','cues':[]}]}
    r=T.retemporizar(p,[2.1])
    assert r['duracao']<65
    assert r['sincronia_voz']['tempo_audio']==1
    assert T.avaliar_destinos(r['duracao'])['destinos']['tiktok']['estado']=='ABAIXO_MINIMO_CREATOR_REWARDS'


@pytest.mark.parametrize('dur',[27.445,68.0,125.0,225.0])
def test_gate_narrativo_nunca_impoe_max_global(dur):
    p=brief()
    p['politica_duracao']={'modo':'narrativa'}
    p.pop('janela_duracao_s')
    p['duracao_planejada_s']=dur
    # A mudança é só na última cena; faltará prova/ritmo de verdade, o que
    # deve continuar BLOQUEANDO. Verificar que NÃO há bloqueio por teto global.
    p['cenas'][-1]['fim']=dur
    r=G.avaliar(p,{'itens':[]},conferir_bytes=False)
    assert 'E-TEMPO' not in {x['codigo'] for x in r['bloqueios']}
    assert r['modo_duracao']=='narrativa'
    assert r['diagnostico_plataformas']['duracao_master_s']==dur
    assert not r['pronto_para_tts']
    assert not r['pronto_para_render']


def test_contrato_antigo_mantem_regressao_nao_muda_sem_optin():
    p=brief()
    p['duracao_planejada_s']=65
    r=G.avaliar(p,{'itens':[]},conferir_bytes=False)
    assert 'E-TEMPO' in {x['codigo'] for x in r['bloqueios']}
    assert r['modo_duracao']=='janela_legada'


def test_diretor_pede_historia_completa_sem_teto_60_90_segundos():
    fatos=[{'id':'f1','texto':'A descoberta foi registrada em fonte primária.'}]
    txt=D.prompt(fatos,'atlas',None,'sem mídia no catálogo')
    assert 'DURAÇÃO EDITORIAL' in txt
    assert 'Sem teto global narrativo' in txt
    assert 'NÃO imponha 60–90 s' in txt
    assert 'reporte a incompatibilidade' in txt


def test_politica_nao_pode_ser_string_nem_crashar_o_gate():
    p=brief()
    p['politica_duracao']='narrativa'
    r=G.avaliar(p,{'itens':[]},conferir_bytes=False)
    assert 'E-POLITICA-DURACAO' in {x['codigo'] for x in r['bloqueios']}
    assert not r['pronto_para_tts']
