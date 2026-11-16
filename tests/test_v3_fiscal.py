"""V3.1 — fiscal técnico/editorial: cortes reais × planejados (PySceneDetect), loudness, repetição/monotonia, e
'id no storyboard não comprova cobertura' (ERR-013)."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from src.v3 import fiscal_editorial as F

IMG = Path(__file__).parent / 'piloto_ever_given' / 'img'


@pytest.fixture(scope='module')
def mp4(tmp_path_factory):
    """3 planos de 3 s (duas fotos diferentes, a 2ª repetida), cortes secos em 3 s e 6 s, tom de −14 LUFS aprox."""
    d = tmp_path_factory.mktemp('fis')
    out = d / 'v.mp4'
    fotos = [IMG / 'a23-g.jpg', IMG / 'a1-g.jpg', IMG / 'a1-g.jpg']
    args = []
    for f in fotos:
        args += ['-loop', '1', '-t', '3', '-i', str(f)]
    filtro = ''.join(f'[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30[v{i}];' for i in range(3))
    filtro += '[v0][v1][v2]concat=n=3:v=1:a=0[v]'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *args, '-f', 'lavfi', '-t', '9', '-i', 'sine=frequency=330:sample_rate=48000',
                    '-filter_complex', filtro + ';[3:a]volume=-6dB,loudnorm=I=-14:TP=-1.5[a]', '-map', '[v]', '-map', '[a]',
                    '-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p', '-c:a', 'aac', str(out)], check=True)
    return out


def _dados(eventos_planos):
    cenas = []
    for k, (ev, img, mov, fala) in enumerate(eventos_planos):
        cenas.append({'comp': 'doc.plano', 'start': 3.0 * k, 'end': 3.0 * k + 3, 'origem': [k], 'fala': fala, 'transicao': 'corte',
                      'params': {'img': img, 'anot': []}, 'direcao': {'evento_id': ev, 'movimento_camera': mov, 'funcao_documental': 'CONTEXTO',
                                                                       'objeto_principal': 'navio'}})
    return {'duration': 9.0, 'scenes': cenas}


def test_cortes_planejados_detectados(mp4):
    det = F.cortes(mp4)
    cc = F.comparar_cortes(det, [3.0, 6.0])
    assert cc['acertos'] >= 1 and 3.0 in [round(x) for x in det]      # o corte entre fotos diferentes aparece
    assert F.comparar_cortes([3.02, 4.9], [3.0])['inesperados'] == [4.9]


def test_repeticao_e_monotonia(mp4):
    d = _dados([('e1', 'a', 'fixo', 'um'), ('e2', 'b', 'fixo', 'dois'), ('e3', 'b', 'fixo', 'tres')])
    reg = [{'evento_id': f'e{i + 1}', 'erros': [], 'limitacoes': [], 'trechos': [i], 'camera': {'roi': None}} for i in range(3)]
    ctx = {'eventos': [{'id': f'e{i + 1}', 'tipo': 'lugar', 'critico': False, 'trechos': [i]} for i in range(3)]}
    f = F.avaliar(mp4, d, reg, ctx, {'fatos': '', 'cenas': [{'fala': 'x'}] * 3})
    cod = {a['codigo'] for a in f['achados']}
    assert 'E-REPETE' in cod and 'E-SLIDESHOW' in cod and 'E-OBJETO' in cod
    assert not [a for a in f['achados'] if a['classe'] == 'bloqueio' and a['codigo'] != 'T-LOUDNESS']
    assert f['resumo']['video']['largura'] == 1080


def test_id_no_storyboard_nao_comprova_cobertura(mp4):
    d = _dados([('e1', 'a', 'aproximar', 'um'), ('e2', 'b', 'aproximar', 'dois'), ('e2', 'c', 'aproximar', 'tres')])
    reg = [{'evento_id': 'e1', 'erros': [], 'trechos': [0], 'camera': {'roi': [0, 0, 1, 1]}},
           {'evento_id': 'e2', 'erros': [], 'trechos': [1], 'camera': {'roi': [0, 0, 1, 1]}},
           {'evento_id': 'e2', 'erros': [], 'trechos': [1], 'camera': {'roi': [0, 0, 1, 1]}}]
    ctx = {'eventos': [{'id': 'e1', 'tipo': 'lugar', 'critico': True, 'trechos': [0]},
                       {'id': 'e2', 'tipo': 'mecanismo', 'critico': True, 'trechos': [2]}]}   # e2 é dito no trecho 2
    f = F.avaliar(mp4, d, reg, ctx, {'fatos': '', 'cenas': [{'fala': 'x'}] * 3})
    cod = {a['codigo']: a['classe'] for a in f['achados']}
    assert cod.get('E-COBERTURA') == 'revisao'               # há plano com o id, mas não sobre a fala do acontecimento
    assert cod.get('E-MECANISMO') == 'bloqueio'              # mecanismo crítico só com foto CONTEXTO


def test_numero_na_tela_fora_da_pesquisa_bloqueia(mp4):
    d = _dados([('e1', 'a', 'aproximar', 'um'), ('e2', 'b', 'aproximar', 'dois'), ('e3', 'c', 'aproximar', 'tres')])
    d['scenes'][1]['params']['anot'] = [{'texto': '999 navios na fila'}]
    reg = [{'evento_id': f'e{i + 1}', 'erros': [], 'trechos': [i], 'camera': {'roi': [0, 0, 1, 1]}} for i in range(3)]
    ctx = {'eventos': []}
    f = F.avaliar(mp4, d, reg, ctx, {'fatos': 'havia 369 navios na fila', 'cenas': [{'fala': 'x'}] * 3})
    assert any(a['codigo'] == 'E-NUMERO' and a['classe'] == 'bloqueio' for a in f['achados'])


def test_data_na_tela_nao_e_numero_fora_da_pesquisa(mp4):
    d = _dados([('e1', 'a', 'aproximar', 'um'), ('e2', 'b', 'aproximar', 'dois'), ('e3', 'c', 'aproximar', 'tres')])
    d['scenes'][1]['params']['selo'] = {'texto': 'SOUTHAMPTON, 10/04/1912'}          # Titanic, rodada 3: "04" virava número
    reg = [{'evento_id': f'e{i + 1}', 'erros': [], 'trechos': [i], 'camera': {'roi': [0, 0, 1, 1]}} for i in range(3)]
    f = F.avaliar(mp4, d, reg, {'eventos': []}, {'fatos': 'partiu de Southampton em 10 de abril de 1912', 'cenas': [{'fala': 'x'}] * 3})
    assert not any(a['codigo'] == 'E-NUMERO' for a in f['achados'])
