"""Resgate V3.1 — testes das causas estruturais confirmadas: degradação silenciosa (agora classificada), sincronia na
palavra, objetos não localizados, vídeo indisponível, receitas sem aprovação humana, plano audiovisual, revisão
multimodal, geometria e masterização (ERR-023)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import v3_material as M  # noqa: E402

from src.v2 import diretor  # noqa: E402
from src.v3 import biblioteca as B, pipeline as P, plano_av, receitas, revisao_multimodal as RM, fiscal_editorial as F  # noqa: E402

PAL = [{'w': 'o', 's': 0.2}, {'w': 'navio', 's': 0.6}, {'w': 'bloqueou', 's': 1.4}, {'w': 'o', 's': 2.0}, {'w': 'canal', 's': 2.3}]


def _ac(tmp_path):
    v = M.roteiro()
    bib = B.Biblioteca(tmp_path / 'b.sqlite3', tmp_path / 'arm')
    ac, _ = P.acervo_diretor(v, bib, 'v', 'Ever Given')
    return v, bib, ac


def _plano(ac, **kw):
    k = next(iter(ac))
    p = M.plano([0], foto=k, tempo_inicio=0, tempo_fim=4, fala='o navio bloqueou o canal', **kw)
    return p, ac[k]


# ---------------------------------------------------------------- degradação classificada (nada some em silêncio)
def test_objeto_nao_localizado_bloqueia_em_plano_critico_e_e_revisao_fora(tmp_path):
    v, bib, ac = _ac(tmp_path)
    p, x = _plano(ac, critico=True)
    _, r = diretor.montar({'planos': [p]}, ac, {}, PAL, {'f1'})
    assert any(d['impacto'] == 'bloqueio' and d['codigo'] == 'OBJETO-NAO-LOCALIZADO' for d in r[0]['degradacoes'])
    p['critico'] = False
    _, r = diretor.montar({'planos': [p]}, ac, {}, PAL, {'f1'})
    assert [d['impacto'] for d in r[0]['degradacoes'] if d['codigo'] == 'OBJETO-NAO-LOCALIZADO'] == ['revisao']


def test_anotacao_essencial_retirada_bloqueia(tmp_path):
    v, bib, ac = _ac(tmp_path)
    p, x = _plano(ac, anotacoes=[{'tipo': 'circulo', 'alvo': 'casco', 'texto': 'CASCO', 'na_palavra': 'navio', 'essencial': True}])
    reg = {x['sha']: {'objetos': {'navio': {'caixa': [.3, .3, .3, .2], 'visivel': True, 'ancoravel': True}}}}
    cenas, r = diretor.montar({'planos': [p]}, ac, reg, PAL, {'f1'})
    assert cenas and not cenas[0]['params']['anot']
    assert any(d['codigo'] == 'ANOTACAO-RETIRADA' and d['impacto'] == 'bloqueio' and d['essencial'] for d in r[0]['degradacoes'])
    perda = next(d['texto'] for d in r[0]['degradacoes'] if d['codigo'] == 'ANOTACAO-RETIRADA')
    assert P._perdas_criticas(r) == {0: perda}        # vai para o replanejamento


def test_movimento_imperceptivel_vira_fixo_sem_percurso_inventado(tmp_path):
    v, bib, ac = _ac(tmp_path)
    p, x = _plano(ac, plano_inicial='geral', plano_final='geral', movimento_camera='aproximar', objeto_principal=None)
    cenas, r = diretor.montar({'planos': [p]}, ac, {}, PAL, {'f1'})
    cam = cenas[0]['params']['cam']
    assert cam[0]['caixa'][0] == pytest.approx(cam[-1]['caixa'][0], abs=.02)            # sem percurso lateral
    assert any(d['codigo'] == 'MOVIMENTO-VIRA-FIXO' and d['impacto'] == 'aceitavel' for d in r[0]['degradacoes'])


def test_palavra_nao_achada_e_revisao_de_sincronia(tmp_path):
    v, bib, ac = _ac(tmp_path)
    p, x = _plano(ac, anotacoes=[{'tipo': 'circulo', 'alvo': 'navio', 'texto': 'NAVIO', 'na_palavra': 'cargueiro'}])
    reg = {x['sha']: {'objetos': {'navio': {'caixa': [.3, .3, .3, .2], 'visivel': True, 'ancoravel': True}}}}
    _, r = diretor.montar({'planos': [p]}, ac, reg, PAL, {'f1'})
    assert any(d['codigo'] == 'SINCRONIA-PALAVRA' and d['impacto'] == 'revisao' for d in r[0]['degradacoes'])


def test_corte_sem_palavra_e_registrado_e_planos_contiguos():
    sb = {'planos': [{'trechos': [0]}, {'trechos': [1]}, {'trechos': [1], 'comeca_na_palavra': 'inexistente'}]}
    P.aplicar_tempos(sb, [(0, 2), (2, 6)], PAL, 6.5)
    t = [(p['tempo_inicio'], p['tempo_fim']) for p in sb['planos']]
    assert t[0][0] == 0 and t[-1][1] == 6.5 and all(a[1] == b[0] for a, b in zip(t, t[1:]))
    assert sb['planos'][2]['_degr'][0][1] == 'CORTE-POR-TEMPO-IGUAL'


def test_video_indisponivel_vira_quadro_com_revisao(tmp_path):
    v, bib, ac = _ac(tmp_path)
    k = next(iter(ac))
    sb = {'planos': [M.plano([0], foto=k, composicao='video.documental', recurso_visual={'tipo': 'video', 'id': k})]}
    P.preparar_params(sb, v, ac)
    assert sb['planos'][0]['composicao'] == 'doc.plano'
    assert ('revisao', 'VIDEO-VIRA-QUADRO') in [(d[0], d[1]) for d in sb['planos'][0]['_degr']]


# ---------------------------------------------------------------- sincronia de câmera, anotação e avanço na palavra
def test_camera_anotacao_e_avanco_entram_na_palavra(tmp_path):
    v, bib, ac = _ac(tmp_path)
    p, x = _plano(ac, objeto_principal='navio', anotacoes=[{'tipo': 'ponto', 'alvo': 'navio', 'texto': 'NAVIO', 'na_palavra': 'bloqueou', 't1_palavra': 'canal'}],
                  camera_chaves=[{'na_palavra': 'canal', 'objeto': 'navio', 'enquadramento': 'detalhe', 'dur': 1}],
                  avanco={'etapas': [{'na_palavra': 'navio', 'centro': [.5, .5], 'raio': .1}, {'na_palavra': 'canal', 'centro': [.5, .5], 'raio': .3}]})
    reg = {x['sha']: {'objetos': {'navio': {'caixa': [.3, .3, .3, .2], 'visivel': True, 'ancoravel': True}}}}
    cenas, r = diretor.montar({'planos': [p]}, ac, reg, PAL, {'f1'})
    pa = cenas[0]['params']
    assert pa['anot'][0]['t0'] == 1.4 and pa['anot'][0]['t1'] == 2.3
    assert [e['t'] for e in pa['avanco']['etapas']] == [0.6, 2.3]
    # a câmera começa NA palavra; o fim respeita a duração pedida OU a mínima pela distância (Plano Mestre §4.2, 16/11:
    # não acelerar porque a palavra mudou) — antes o fim era sempre palavra + dur
    from src.v3 import geometria
    ks = pa['cam']
    i = next(i for i, k in enumerate(ks) if k['t'] == 2.3)
    minima = geometria.duracao_minima(ks[i]['caixa'], ks[i + 1]['caixa'], x['wh'])
    assert ks[i + 1]['t'] >= min(2.3 + max(1, minima), 3.9) - .01


def test_palavra_composta_alinhada_como_um_token():
    pal = [{'w': 'na', 's': 1.0}, {'w': 'segunda feira', 's': 1.2}]
    assert diretor.tempo_da_palavra(pal, '', 'segunda', 0, 3) == 1.2


# ---------------------------------------------------------------- receitas: aprovação só com evidência humana
def test_nenhuma_receita_aprovada_sem_registro_humano(tmp_path, monkeypatch):
    assert receitas.problemas() == [] and not [r for r in receitas.todas() if r['estado'] == 'aprovado']
    d = json.loads(receitas.ARQ.read_text(encoding='utf-8'))
    r = d['receitas'][0]
    r.update(estado='aprovado', exemplo_aprovado='x', aprovacao='a V3 melhorou')
    arq = tmp_path / 'r.json'
    arq.write_text(json.dumps(d, ensure_ascii=False))
    assert any('sem evidência humana' in p for p in receitas.problemas(arq))
    r['aprovacao'] = 'humano:heitor:2026-11-20:londres_1666:00:41'
    arq.write_text(json.dumps(d, ensure_ascii=False))
    assert receitas.problemas(arq) == []


# ---------------------------------------------------------------- plano audiovisual antes do storyboard
def test_fichas_do_plano_audiovisual(tmp_path):
    v, bib, ac = _ac(tmp_path)
    p, ctx = P.montar_prompt(v, ac, bib)
    f = ctx['plano_av'][0]
    for k in ('sujeito', 'estado_inicial', 'acao', 'transformacao', 'consequencia', 'representacao_necessaria', 'midia_disponivel',
              'evidencia', 'criterio_visual', 'status'):
        assert k in f
    assert 'PLANO AUDIOVISUAL' in p and 'DEMONSTRAÇÕES' in p and 'um plano por DEMONSTRAÇÃO, não por frase' in p


def test_ajuste_de_narracao_nao_aceita_numero_novo_nem_tamanho_absurdo():
    v = M.roteiro()
    ok, nao = plano_av.validar_ajustes([{'trecho': 1, 'texto': v['cenas'][1]['fala'] + ' com 999 navios'},
                                        {'trecho': 2, 'texto': 'curto'},
                                        {'trecho': 3, 'texto': v['cenas'][3]['fala'].replace('*', '')}], v, v['fatos'])
    assert [a['trecho'] for a in ok] == [3] and any('999' in n for n in nao) and any('tamanho' in n for n in nao)


# ---------------------------------------------------------------- revisão multimodal (diagnóstico, não nota)
def test_revisao_multimodal_produz_diagnostico_especifico_e_nao_aprova_por_omissao():
    planos = [{'plano': 0, 'inicio': 0, 'fim': 3, 'evento_id': 'e6', 'critico': True, 'tira': 't0.jpg',
               'veredito': {'demonstra': 'nao', 'midia_corresponde': True, 'objeto_principal_visivel': True, 'mapa_ou_grafico_informativo': 'nao',
                            'texto_na_tela_legivel': True, 'texto_interno_ou_tecnico_na_tela': True,
                            'problemas': ['quadro 2: mapa parado, sem avanço'], 'correcao': 'revelar a área em etapas'}},
              {'plano': 1, 'inicio': 3, 'fim': 6, 'evento_id': 'e7', 'critico': False, 'tira': 't1.jpg', 'veredito': {'_nao_revisado': 'sem modelo'}}]
    a = RM.achados(planos)
    cod = [x['codigo'] for x in a]
    assert cod.count('M-NAO-DEMONSTRA') == 1 and 'M-MAPA-DECORATIVO' in cod and 'M-TEXTO-INTERNO' in cod and 'M-NAO-REVISADO' in cod
    assert all(x['classe'] == 'revisao' and x['dimensao'] == 'semantica' for x in a)
    assert 'quadro 2' in next(x for x in a if x['codigo'] == 'M-NAO-DEMONSTRA')['problema']


def test_dimensoes_do_fiscal_separadas():
    assert F.dimensao('T-LOUDNESS') == 'tecnica' and F.dimensao('E-MECANISMO') == 'semantica' and F.dimensao('M-MIDIA-DIVERGE') == 'semantica'
    assert F.dimensao('E-PARADO') == 'estetica' and F.dimensao('S-MONOTONIA') == 'estetica'


# ---------------------------------------------------------------- geometria e textos
def test_choque_grave_de_texto_aponta_o_plano():
    dados = {'scenes': [{'start': 0, 'end': 3, 'origem': [0]}, {'start': 3, 'end': 6, 'origem': [4]}]}
    geo = [{'tipo': 'choque', 'grave': True, 'cap': False, 't': 4.0, 'txt': 'A × B'}, {'tipo': 'choque', 'grave': True, 'cap': True, 't': 1.0, 'txt': 'legenda'}]
    g = P._choques({'problemas_geometria': geo}, dados)
    assert list(g) == [4] and 'ERR-008' in g[4]


# ---------------------------------------------------------------- áudio (ERR-023)
def _sint(d: Path, crista: bool) -> tuple[Path, Path]:
    f = "[0]volume=enable='lt(mod(t,2),1.2)':volume=1,volume=enable='gte(mod(t,2),1.2)':volume=0.05[a];" \
        "[1]volume=0.02,volume=enable='lt(mod(t,5),0.03)':volume=40[b];[a][b]amix=inputs=2:normalize=0"
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'anoisesrc=color=pink:amplitude=0.08:duration=12', '-f', 'lavfi', '-i',
                    'sine=frequency=180:duration=12', '-filter_complex', f if crista else '[0][1]amix=inputs=2', '-ar', '48000', str(d / 'm.wav')], check=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'color=black:s=320x568:d=12:r=10', '-c:v', 'libx264', '-preset', 'ultrafast',
                    str(d / 'v.mp4')], check=True)
    return d / 'm.wav', d / 'v.mp4'


def test_master_de_crista_alta_fica_na_meta_depois_do_aac(tmp_path):
    from src.render import render
    m, v = _sint(tmp_path, True)
    out = render.final_medido(v, m, tmp_path / 'f.mp4')
    med = render._ebur(tmp_path / 'f.mp4')
    assert abs(med['lufs'] - (-14)) <= .5 and med['pico_dbtp'] <= -1.0 and out['escolhida']
    hist = json.loads((tmp_path / 'f.audio.json').read_text())
    assert sum(1 for h in hist if h.get('escolhida')) == 1


def test_a_melhor_tentativa_e_a_gravada(tmp_path, monkeypatch):
    from src.render import render
    m, v = _sint(tmp_path, True)
    medidas = iter([{'lufs': -14.6, 'pico_dbtp': -1.5}, {'lufs': -16.8, 'pico_dbtp': -4.0}, {'lufs': -15.5, 'pico_dbtp': -2.0}, {'lufs': -15.9, 'pico_dbtp': -2}])
    monkeypatch.setattr(render, '_ebur', lambda p: next(medidas) if str(p).endswith('.mp4') else {'lufs': -20.0, 'pico_dbtp': -3.0})
    out = render.final_medido(v, m, tmp_path / 'f.mp4')
    assert out['lufs'] == -14.6                       # antes: a ÚLTIMA (−15,9) era gravada


def test_corte_detectado_durante_movimento_planejado_nao_e_falso_alarme():
    cena = {'params': {'cam': [{'t': 0, 'caixa': [0, 0, 1, 1]}, {'t': 4, 'caixa': [.3, .3, .3, .3]}], 'anot': [{'t0': 6.0, 'texto': 'X'}],
                       'avanco': {'etapas': [{'t': 8.0, 'dur': 1.0}]}}}
    assert 'câmera' in F._mudanca_planejada(cena, 2.0) and 'anotação' in F._mudanca_planejada(cena, 6.3)
    assert F._mudanca_planejada(cena, 8.5) == 'etapa do avanço' and F._mudanca_planejada(cena, 11.0) is None


def test_revisao_multimodal_entrega_bytes_ao_modelo_de_visao(tmp_path):
    """ERR-040: a revisão passava o caminho da tira (Path) ao Gemini, que exige bytes — falhou em todos os planos das
    microcenas (16/11) e o fiscal ficou sem revisão semântica. O modelo falso agora exige bytes JPEG, como o real."""
    mp4 = tmp_path / 'v.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'color=gray:s=320x568:d=4:r=30', '-c:v', 'libx264', '-preset',
                    'ultrafast', str(mp4)], check=True)
    vistos = []

    def visao(prompt, imagens):
        assert all(isinstance(b, (bytes, bytearray)) and b[:2] == b'\xff\xd8' for b in imagens), [type(b) for b in imagens]
        vistos.append(len(imagens))
        return {'demonstra': 'sim', 'midia_corresponde': True, 'objeto_principal_visivel': True, 'problemas': []}

    r = RM.revisar(mp4, {'scenes': [{'start': 0, 'end': 4, 'fala': 'x', 'direcao': {'evento_id': 'e1'}}]}, [], visao, tmp_path / 'rv')
    assert vistos == [1] and r['chamadas'] == 1 and 'M-NAO-REVISADO' not in [a['codigo'] for a in r['achados']]
