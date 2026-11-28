"""Regressão multiassunto do contrato compartilhado. NÃO atesta qualidade estética.

Panamá: storyboard + mecanismo; Taiwan: filme documental e ATLAS que falhou
sem prova; Hindenburg: gabarito hipotético, não arquivo histórico conferido.
Teste de VLM é INJETADO: comprova funcionamento do gate, não acerto de um modelo.
"""
import copy
import json
from pathlib import Path

from PIL import Image

from src.v4.formatos import contrato_visual_comum as C
from src.v4.formatos import triagem_editorial, filme_editorial, revisao_filme_editorial

ROOT=Path(__file__).resolve().parents[1]


def _json(p):
    return json.loads((ROOT/p).read_text(encoding="utf-8"))


def _panama():
    return _json('docs/v4/formatos/filme_panama_ciclo_19s.json')


def _taiwan():
    return _json('docs/v4/formatos/filme_taiwan_prova.json')


def _taiwan_atlas():
    return _json('src/v4/formatos/planos/reuso/atlas_chips_v2_prova_25s.json')


def _hindenburg():
    return _json('tests/evidencia/generalizacao_v2.json')['dominios']['dirigivel_hindenburg']


def _visao_teste(**kwargs):
    return {**{
        'referente_visivel':True, 'aprendizado_demonstrado':True,
        'enquadramento_adequado':True,'imagem_celular_legivel':True,
        'mapa_informativo':True, 'acao_ou_relacao_visivel':True, 'problemas':[],
    },**kwargs}


def test_panama_exige_todas_etapas_declaradas_sem_depender_do_tema():
    p=_panama()
    r=C.auditar(p)
    assert r['total_compromissos']==2
    assert r['acoes_com_expectativa_declarada']==1
    assert r['acoes_programadas_em_ordem']==1
    assert r['estrutura_declarada_ok'] is True
    assert r['prova_visual']=='NAO_INSPECIONADA'
    assert r['aprovacao_humana']=='PENDENTE'

    p['shots'][1]['cues'].pop(3)
    r=C.auditar(p)
    assert 'U-COBERTURA-ACAO' in {x['codigo'] for x in r['falhas']}
    assert r['acoes_programadas_em_ordem']==0


def test_taiwan_usa_mesma_regra_sem_exigir_animacao_hidraulica():
    p=_taiwan()
    r=C.auditar(p)
    assert r['total_compromissos']==6
    assert r['estrutura_declarada_ok'] is True
    assert r['inspecoes_com_veredito']==0
    assert r['prova_visual']=='NAO_INSPECIONADA'
    assert r['aprovacao_humana']=='PENDENTE'
    assert filme_editorial.avaliar(p)['pronto']
    assert filme_editorial.avaliar(p)['contrato_comum']['prova_visual']=='NAO_INSPECIONADA'


def test_atlas_taiwan_ja_bloqueado_sem_contrato_nao_vira_aprovado_com_modulo_comum():
    pl=_taiwan_atlas()
    old=triagem_editorial.avaliar(pl)
    assert not old['pronto']
    assert 'E-SEM-CONTRATO-VISUAL' in {x['codigo'] for x in old['bloqueios']}
    assert not old['contrato_comum']['estrutura_declarada_ok']
    assert old['contrato_comum']['aprovacao_humana']=='PENDENTE'


def test_hindenburg_usa_fixture_existente_e_nao_promove_cenario_a_foto_real():
    d=_hindenburg()
    casos={x['id']:x for x in d['casos']}
    assert casos['g-hb-01']['esperado']=='PROVA'
    assert casos['g-hb-03']['esperado']=='CONTEXTO'
    assert casos['g-hb-04']['esperado']=='INCOMPATIVEL'
    assert all(d['imagens'][k]['imagem_hipotetica'] for k in ('fogo','voo_1936','r101'))
    # O gabarito de correspondência não é a licença nem os bytes de uma imagem.
    plano={'formato':'filme_editorial','shots':[{
        'id':'fogo_hindenburg','type':'photo','asset':'foto-de-teste',
        'subject':'Dirigível Hindenburg em chamas, 1937',
        'headline':'Incêndio e queda do Hindenburg',
        'evidence':'literal','literal_identity':'Hindenburg, 6 de maio de 1937',
        'cues':[{'at':.1,'label':'INCÊNDIO'}],
        'start':0,'end':2,
    }], 'media':{} ,'duracao':2}
    rel=C.auditar(plano)
    assert not rel['estrutura_declarada_ok']
    assert 'U-SEM-PROVA' in {x['codigo'] for x in rel['falhas']}
    assert rel['prova_visual']=='NAO_INSPECIONADA'
    assert not filme_editorial.avaliar(plano)['pronto']


def test_mesma_rubrica_detecta_falseamento_sem_premiar_pixels():
    falha_acao=C.julgar_inspecao('DEMONSTRAR',False,
                                _visao_teste(acao_ou_relacao_visivel=False))
    assert any(x.startswith('V-acao_ou_relacao_visivel') for x in falha_acao)
    assert C.julgar_inspecao('MOSTRAR',False,
                            _visao_teste(referente_visivel=False))[0].startswith('V-referente_visivel')
    assert C.julgar_inspecao('CONECTAR',False,
                            _visao_teste(acao_ou_relacao_visivel=False))
    assert C.julgar_inspecao('REVELAR',False,
                            _visao_teste(aprendizado_demonstrado=False))
    assert C.julgar_inspecao('DEMONSTRAR',False,{'referente_visivel':1})
    assert 'SEM-REVISAO' in C.julgar_inspecao('MOSTRAR',False,None)[0]


def test_revisor_filme_aplica_uma_verificacao_a_cada_evento_sem_pular_saida():
    p=_panama()
    eventos=revisao_filme_editorial.janelas(p)
    assert len(eventos)==8  # uma cena real + 7 etapas da eclusa
    assert [x['etapa'] for x in eventos[1:]] == [
        'enter','seal','valves','rise','equalize','open','exit']
    assert all(x['t1']>x['t0'] for x in eventos)


def test_revisor_falha_se_uma_so_etapa_nao_aparece(tmp_path,monkeypatch):
    p=_panama()
    video=tmp_path/'video.mp4'
    video.write_bytes(b'fake-video-do-teste'*1000)
    def frame_falso(_video,t,destino):
        destino.parent.mkdir(parents=True,exist_ok=True)
        Image.new('RGB',(405,720),(35,56,78)).save(destino)
        return destino
    monkeypatch.setattr(revisao_filme_editorial,'_quadro',frame_falso)
    chamadas=[]
    def modelo_falso(prompt,imagens):
        chamadas.append(prompt)
        # ETAPA SAÍDA: um mock negativo verifica o bloqueio, não avalia imagens reais.
        return _visao_teste(acao_ou_relacao_visivel=('exit' not in prompt))
    r=revisao_filme_editorial.revisar(p,video,tmp_path/'out',chamar_visao=modelo_falso)
    assert len(chamadas)==8
    assert not r['revisao_semantica_sem_bloqueio']
    assert not r['pronto_para_aprovacao_humana']
    assert r['publicavel'] is False
    assert r['aprovacao_humana']=='PENDENTE'
    assert any(x['etapa']=='exit' and x['problemas']
               for xs in r['etapas'].values() for x in xs)


def test_mesmo_com_modelo_todo_verde_nunca_libera_publicacao(tmp_path,monkeypatch):
    p=_taiwan()
    video=tmp_path/'teste.mp4';video.write_bytes(b'nao_e_um_video'*1000)
    def frame_falso(_video,t,destino):
        destino.parent.mkdir(parents=True,exist_ok=True)
        Image.new('RGB',(405,720),(32,61,78)).save(destino)
        return destino
    monkeypatch.setattr(revisao_filme_editorial,'_quadro',frame_falso)
    r=revisao_filme_editorial.revisar(
        p,video,tmp_path/'saida',chamar_visao=lambda *_: _visao_teste())
    assert r['revisao_semantica_sem_bloqueio'] is True
    assert r['publicavel'] is False
    assert r['aprovacao_humana']=='PENDENTE'
    assert r['prova_visual']=='INSPECIONADA_POR_MODELO_NAO_HOMOLOGADA'
