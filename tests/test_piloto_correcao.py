"""Correção cirúrgica do piloto real Ever Given (V2.2 → V2.3). Tudo roda sobre o material ORIGINAL do piloto
(tests/piloto_ever_given): roteiro, acervo, cenas com os tempos da voz de produção, imagens e áudio. Sem IA."""
import copy
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import _piloto  # noqa: E402
from src.v2 import contrato, fiscal_v2, montagem, piloto, preparo  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent


@pytest.fixture(scope='module')
def prep():
    v = _piloto.roteiro()
    rel = preparo.preparar(v)
    return v, rel


@pytest.fixture(scope='module')
def depois(prep):
    """Montagem + fiscal do piloto com as correções (sem render)."""
    v, rel = prep
    d1 = _piloto.cenas_v1(v)
    d1['meta']['preparo'] = rel
    v2, dire = montagem.converter(copy.deepcopy(d1))
    return d1, v2, dire, fiscal_v2.avaliar(v2, dire, None, d1, audio={'lufs': -14.2, 'pico_dbtp': -1.6})


@pytest.fixture(scope='module')
def antes():
    """O que o piloto REALMENTE montou, julgado pelo fiscal corrigido."""
    d1 = _piloto.cenas_v1()
    v2 = _piloto.ler('v2_dados_original.json')
    for sc in v2['scenes']:
        if (sc.get('fundo') or {}).get('img'):
            sc['fundo']['img'] = _piloto._local(sc['fundo']['img'])
    return v2, fiscal_v2.avaliar(v2, _piloto.ler('direcao_original.json'), None, d1, audio={'lufs': -18.5, 'pico_dbtp': -1.3})


def _eventos(rel):
    return {e['id']: e for e in rel['eventos']}


def _bloq(r, cod=None):
    return [a for a in r['achados'] if a['gravidade'] == 'bloqueio' and (cod is None or a['codigo'] == cod)]


# ───────── 1. contratos validados ANTES da narração ─────────
def test_1_contratos_validados_antes_da_narracao(monkeypatch, tmp_path):
    import main
    v = _piloto.roteiro()
    chamadas = []
    monkeypatch.setenv('MOTOR_VISUAL', 'v2')
    monkeypatch.setattr(main, '_midia_do_acervo', lambda *a, **k: chamadas.append('mídia') or ({}, {}, [], set()))
    monkeypatch.setattr(main.voz, 'narrar', lambda *a, **k: chamadas.append('narração') or (_ for _ in ()).throw(AssertionError('narrou')))
    monkeypatch.setattr(main, 'RAIZ', tmp_path)
    with pytest.raises(ValueError, match='roteiro incompleto antes da narração') as e:
        main.montar_video(v, tmp_path, 'piloto')
    assert chamadas == [], chamadas                                   # nada baixado, nada narrado
    assert 'e9' in str(e.value) and 'flutuando livremente' in str(e.value)
    rel = json.loads((tmp_path / 'piloto-preparo.json').read_text(encoding='utf-8'))
    assert [b['evento'] for b in rel['bloqueios']] == ['e9']


# ───────── 2. críticos com dados adequados ou bloqueio antecipado ─────────
def test_2_criticos_tem_representacao_ou_bloqueio_com_o_que_falta(prep):
    v, rel = prep
    for e in rel['eventos']:
        if not e['critico']:
            continue
        modo = e['representacao']['modo']
        if modo == 'bloqueio':
            assert e['representacao']['faltam'], e
            assert any(e['id'] == b['evento'] for b in rel['bloqueios'])
        else:
            assert modo in ('composicao', 'foto_direta', 'editorial'), (e['id'], modo)
    ev = _eventos(rel)
    assert ev['e9']['representacao']['modo'] == 'bloqueio'
    assert any('flutuando livremente' in f for f in ev['e9']['representacao']['faltam'])
    assert any('comparacao.antes_depois' in f for f in ev['e9']['representacao']['faltam'])


def test_2b_classificacao_corrigida(prep):
    ev = _eventos(prep[1])
    assert ev['e3']['tipo'] == 'movimento' and 'vento' in ev['e3']['reclassificacao']          # vento ≠ rota geográfica
    assert ev['e10']['tipo'] == 'numero' and ev['e10']['tipo_original'] == 'citacao'            # cobrança ≠ citação
    assert ev['e10']['dados']['moeda'] == 'USD' and ev['e10']['dados']['valor'] == 916
    assert ev['e7']['tipo'] == 'numero' and ev['e7']['dados']['valor'] == 15                    # contagens ≠ etapas
    assert ev['e4']['tipo'] == 'mecanismo' and ev['e4']['representacao']['modo'] == 'foto_direta'  # sem diagrama à força


def test_2c_mesmo_contrato_em_todos_os_planos(prep):
    v, _ = prep
    por_id = {}
    for c in v['cenas']:
        ac = c.get('acontecimento') or {}
        if ac.get('id'):
            por_id.setdefault(ac['id'], []).append(ac)
    for eid, acs in por_id.items():
        assert all(a['partes'] == len(acs) for a in acs), eid
        assert all(a['representacao'] == acs[0]['representacao'] and a['tipo'] == acs[0]['tipo'] for a in acs), eid


# ───────── 3. foto real que mostra o fato é aceita ─────────
def test_3_foto_real_que_mostra_o_fato_e_aceita(prep, depois):
    v, rel = prep
    ev = _eventos(rel)
    for eid, foto in (('e1', 'a3'), ('e3', 'a9'), ('e4', 'a6')):
        assert ev[eid]['representacao']['modo'] == 'foto_direta' and ev[eid]['foto'] == foto, (eid, ev[eid])
    *_, r = depois
    eids_bloqueados = {a['evidencia'].split(':')[0] for a in _bloq(r, 'S5')}
    assert not eids_bloqueados & {'e1', 'e3', 'e4', 'e5'}, eids_bloqueados


def test_3b_foto_de_outra_epoca_ou_sem_o_estado_nao_prova_o_fato():
    ac = {'tipo': 'transformacao', 'sujeito': 'Ever Given', 'estado_final': 'flutuando livremente', 'mostrar': 'Navio liberado no canal'}
    acervo = {x['id']: x for x in _piloto.roteiro()['acervo']}
    preso = preparo.avaliar_imagem(acervo['a9'], ac, {'mostrar': 'Foto de satélite do Ever Given flutuando no canal.'}, 2021)
    assert preso['forca'] < 3                                       # mostra o navio PRESO, não liberado
    navegando = preparo.avaliar_imagem(acervo['a10'], {**ac, 'estado_final': 'navegando em mar aberto'}, {}, 2021)
    assert navegando['forca'] < 3 and any('2011' in m for m in navegando['motivos'])


# ───────── 4. fragmentos do mesmo acontecimento preservam a sincronização ─────────
def test_4_sincronia_encontra_palavras_em_outro_plano_do_mesmo_acontecimento(prep):
    v, _ = prep
    d1 = _piloto.cenas_v1(v)
    e3 = [k for k, s in enumerate(d1['scenes']) if (s.get('acontecimento') or {}).get('id') == 'e3']
    assert len(e3) == 2
    # as palavras "ventos fortes" estão no 2º plano; o resolvedor antigo (por plano) perdia no 1º
    antigo = contrato.resolver_sincronia(d1['scenes'][e3[0]]['acontecimento'],
                                         [w for c in d1['captions'] for w in c['words'] if d1['scenes'][e3[0]]['start'] <= w['s'] < d1['scenes'][e3[0]]['end']],
                                         d1['scenes'][e3[0]]['start'])
    assert antigo.get('sincronia_faltou')
    res = {r['evento']: r for r in piloto._sincronia(d1)}
    assert not res['e3']['faltou'], res['e3']
    t1 = d1['scenes'][e3[0]]['acontecimento']['dados']['vento'][0]['t']
    t2 = d1['scenes'][e3[1]]['acontecimento']['dados']['vento'][0]['t']
    dito = next(w['s'] for c in d1['captions'] for w in c['words'] if w['w'].lower().startswith('vento'))
    assert abs(d1['scenes'][e3[0]]['start'] + t1 - dito) < .01 and abs(d1['scenes'][e3[1]]['start'] + t2 - dito) < .01


def test_4b_planos_do_mesmo_acontecimento_viram_uma_cena(depois):
    d1, v2, dire, _ = depois
    e7 = [k for k, sc in enumerate(v2['scenes']) if any((d1['scenes'][i].get('acontecimento') or {}).get('id') == 'e7' for i in sc['origem'])]
    assert len(e7) == 1 and v2['scenes'][e7[0]]['comp'] == 'numero.animado' and len(v2['scenes'][e7[0]]['origem']) == 2


# ───────── 5. avisos técnicos nunca aparecem no vídeo ─────────
def test_5_numero_bloqueado_nao_vira_texto_na_tela():
    d1 = _piloto.cenas_v1()                                         # piloto original: o 369 sem fonte
    v2, dire = montagem.converter(d1)
    textos = \
        ' '.join(t for sc in v2['scenes'] for t in fiscal_v2._textos(sc.get('params') or {})).upper()
    assert 'BLOQUEADO' not in textos and 'SEM VERIFICA' not in textos
    assert any(d.get('bloqueio') for d in dire)                    # o bloqueio continua REGISTRADO (fiscal D9)


def test_5b_fiscal_bloqueia_mensagem_interna(antes):
    v2, r = antes
    d14 = _bloq(r, 'D14')
    assert len(d14) == 1 and 'NÚMERO BLOQUEADO' in d14[0]['evidencia']


# ───────── 6. cena sem conteúdo visual não é aprovada ─────────
def test_6_tela_preta_do_piloto_e_bloqueada_uma_vez(antes):
    v2, r = antes
    d13 = _bloq(r, 'D13')
    assert len(d13) == 1 and 'cenas 9–10' in d13[0]['evidencia']    # mesma causa contínua = um achado


def test_6b_montagem_nao_gera_mais_foto_vazia():
    d1 = _piloto.cenas_v1()
    v2, _ = montagem.converter(d1)
    for sc in v2['scenes']:
        if sc['comp'] in fiscal_v2.COMPS_FOTO:
            assert (sc.get('fundo') or {}).get('img') or (sc.get('params') or {}).get('img'), sc
    vazia = next(sc for sc in v2['scenes'] if 10 in sc['origem'])            # V1 10–11: o 'esquema pendente' sem foto
    assert vazia['comp'] == 'destaque.palavras' and 'rebocadores' in vazia['params']['frase']


def test_6c_quadro_escuro_e_detectado(tmp_path):
    preto = tmp_path / 'preto.jpg'
    im = Image.new('RGB', (1080, 1920), (8, 10, 12))
    im.paste((240, 200, 40), (150, 1260, 930, 1400))              # só a legenda
    im.save(preto)
    assert fiscal_v2._quadro_vazio(preto)
    assert not fiscal_v2._quadro_vazio(_piloto.F / 'img' / 'a22-g.jpg')


# ───────── 7. informações factuais com fontes rastreáveis ─────────
def test_7_numeros_tem_fonte_rastreavel(prep, depois):
    v, rel = prep
    ev = _eventos(rel)
    for eid, valor in (('e7', 15), ('e10', 916)):
        d = ev[eid]['dados']
        assert d['fonte'] and str(valor) in d['rastreio'], (eid, d)
    c369 = next(c for c in v['cenas'] if c.get('tipo') == 'numero')
    assert c369['fonte'] == 'Wikipedia (inglês)'                   # estava na pesquisa; faltava a integração
    assert 'iG Economia' in v['fontes'] and 'iG Economia' in rel['fontes_adicionadas']
    *_, r = depois
    assert not _bloq(r, 'D9')                                       # nenhum número sem validação


def test_7b_numero_fora_da_pesquisa_nao_ganha_fonte():
    v = _piloto.roteiro()
    linhas = preparo.pesquisa(v)
    assert len(linhas) == 25                                       # inclusive as linhas "(Wikipedia (inglês))"
    assert preparo.rastrear(370, 'Wikipedia (inglês)', linhas) is None
    assert preparo.rastrear(369, 'Wikipedia (inglês)', linhas)['fonte'] == 'Wikipedia (inglês)'


def test_7c_capacidade_apresentada_como_carga_vai_para_revisao(prep, depois):
    v, rel = prep
    assert any(r['evento'] == 'e2' and 'capacidade' in r['problema'] for r in rel['revisoes'])
    *_, r = depois
    assert any(a['codigo'] == 'S7' and a['gravidade'] == 'revisao' and a['evidencia'].startswith('e2') for a in r['achados'])
    assert r['aprovacao_automatica'] is False


# ───────── 8. áudio final na meta ─────────
def test_8_masterizacao_atinge_a_meta_com_crista_alta(tmp_path):
    """A classe do piloto (−18,5 LUFS com o limitador no teto): mistura com pico ~24 dB acima do volume médio."""
    from src.fiscal import medir_audio
    from src.render import render
    mix = tmp_path / 'mix.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(RAIZ / 'tests/midia/voz_venezuela.ogg'), '-f', 'lavfi', '-i',
                    "aevalsrc='0.97*sin(2*PI*70*t)*exp(-30*mod(t,2.5))*lt(mod(t,2.5),0.25)':s=48000:d=80",
                    '-filter_complex', '[0:a]aresample=48000,aformat=channel_layouts=mono,volume=-12dB[v];[v][1:a]amix=inputs=2:normalize=0:duration=first[a]',
                    '-map', '[a]', '-c:a', 'pcm_s16le', str(mix)], check=True)
    m = medir_audio(mix)
    assert m['pico'] - m['lufs'] > 20
    r = render.masterizar(mix, tmp_path / 'm.wav')
    assert abs(r['saida']['lufs'] + 14) <= 1, r
    assert r['saida']['pico'] <= -1.0, r


def test_8b_fiscal_bloqueia_loudness_fora_da_meta(antes):
    v2, r = antes
    assert any('−18,5' in a['evidencia'].replace('-18.5', '−18,5') or '-18.5' in a['evidencia'] for a in _bloq(r, 'A1'))


# ───────── fiscal: causa única, comparação e fiscal antigo ─────────
def test_fiscal_conta_cada_causa_uma_vez(antes):
    v2, r = antes
    s5 = _bloq(r, 'S5')
    eids = [a['evidencia'].split(':')[0] for a in s5]
    assert len(eids) == len(set(eids))                              # nenhum acontecimento contado duas vezes
    assert not _bloq(r, 'S1') and not _bloq(r, 'S2')               # frase isolada não vira causa extra
    assert len(_bloq(r)) == 12


def test_fiscal_depois_so_bloqueia_o_que_falta_de_verdade(depois):
    *_, r = depois
    b = _bloq(r)
    assert [a['codigo'] for a in b] == ['S5'] and b[0]['evidencia'].startswith('e9:')
    assert 'flutuando livremente' in b[0]['evidencia']


def test_fiscal_antigo_nao_libera_o_que_o_v22_reprova():
    import main
    v = {'titulo': 'Teste', 'parte': 0}
    q = {'nota': 10, 'cont': {}, 'ideias': 12, 'dur': 64, 'palavras': 150, 'motivos': [], 'ia': False,
         'v22': {'bloqueios': ['S5 cena 10: ...'], 'aprovacao_automatica': False}}
    q['motivos'] = [f"fiscal V2.2 reprovou ({len(q['v22']['bloqueios'])} problema(s))"]
    txt = main.resumo_telegram(v, q)
    assert 'NÃO RECOMENDO POSTAR' in txt and 'pode postar' not in txt and 'quem decide é o fiscal V2.2' in txt


# ───────── imagens: idioma, relação e créditos ─────────
def test_imagem_com_texto_em_arabe_sai_e_a_foto_pedida_entra(prep):
    v, rel = prep
    troca = next(t for t in rel['trocas'] if t['evento'] == 'e3')
    assert troca['de'] == 'a5' and troca['para'] == 'a9' and 'escrita incompatível' in troca['motivo']
    acervo = {x['id']: x for x in v['acervo']}
    ac = {'tipo': 'localizacao', 'sujeito': 'Trecho do canal', 'mostrar': 'Corte transversal do canal'}
    assert preparo.avaliar_imagem(acervo['a0'], ac, {'mostrar': 'Diagrama em corte do canal estreito.'}, 2021)['compativel']   # inglês: ok


def test_creditos_seguem_o_arquivo_que_aparece(prep, tmp_path):
    import main
    v, _ = prep
    por_id = {x['id']: x for x in v['acervo']}
    d1 = _piloto.cenas_v1(v)
    for s, c in zip(d1['scenes'], v['cenas']):
        if s.get('img') and c.get('acervo_id') and s.get('tipo') != 'revelacao':
            assert Path(s['img']).name == por_id[c['acervo_id']]['arquivo'] and c['credito'] == por_id[c['acervo_id']]['credito']
    main.pacote_diagnostico(v, {'scenes': []}, tmp_path, 'diag')
    with zipfile.ZipFile(tmp_path / 'diag-diagnostico.zip') as z:
        ac = json.loads(z.read('acervo.json'))
    assert all(x['arquivo'] == Path(por_id[x['id']]['arq']).name for x in ac if por_id[x['id']].get('arq'))


def test_satelite_de_deserto_nao_vira_faixa_de_scanner():
    from src.v2 import acervo_v2
    assert acervo_v2.recorte_conteudo(_piloto.F / 'img' / 'a5-g.jpg') == [0.0, 0.0, 1.0, 1.0]
