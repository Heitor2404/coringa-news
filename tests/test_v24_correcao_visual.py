"""V2.4 — correção visual prioritária após o MP4 43730252500 (nota 2/10): regras novas do fiscal, da montagem,
do áudio final e da edição editorial do checkpoint. Cada teste corresponde a um defeito confirmado no vídeo."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess

import pytest

from src.v2 import checkpoint, contrato, fiscal_v2, montagem


def _cena(comp, ini, fim, img=None, params=None, origem=None):
    sc = {'comp': comp, 'start': ini, 'end': fim, 'params': params or {}, 'origem': origem or []}
    if img:
        sc['fundo'] = {'img': img}
    return sc


def _cods(r, grav='bloqueio'):
    return [a['codigo'] for a in r['achados'] if a['gravidade'] == grav]


# ───────────── fiscal: mecanismo crítico só escrito na tela (processo.etapas com frases do contrato) ─────────────
def test_fiscal_bloqueia_mecanismo_critico_em_cartao_de_frases():
    ac = {'id': 'e5', 'tipo': 'mecanismo', 'importancia': 'critica', 'mostrar': 'dipolo',
          'representacao': {'modo': 'composicao', 'comp': 'processo.etapas'}}
    v1 = {'scenes': [{'tipo': 'historia', 'fala': 'x', 'start': 0, 'end': 5, 'acontecimento': ac}]}
    frases = {'etapas': ['deslocamento temporário da nuvem eletrônica em uma molécula', 'cria um dipolo instantâneo']}
    r = fiscal_v2.avaliar({'scenes': [_cena('processo.etapas', 0, 5, params=frases, origem=[0])], 'captions': []}, [{}], dados_v1=v1)
    assert _cods(r) == ['S8']
    ok = {'esquema': {'objetos': [{'id': 'a', 'forma': 'corpo', 'rotulo': 'A'}, {'id': 'b', 'forma': 'superficie'}],
                      'estados': [{'rotulo': 'x'}, {'rotulo': 'y', 'objetos': {'a': {'dy': .2}}}]}}
    ac2 = {**ac, 'representacao': {'modo': 'composicao', 'comp': 'mecanismo.estados'}}
    r2 = fiscal_v2.avaliar({'scenes': [_cena('mecanismo.estados', 0, 5, params=ok, origem=[0])], 'captions': []}, [{}],
                           dados_v1={'scenes': [{**v1['scenes'][0], 'acontecimento': ac2}]})
    assert _cods(r2) == []


def test_fiscal_ilustracao_identificada_e_revisao_nao_bloqueio(tmp_path):
    img = tmp_path / 'a3.jpg'
    img.write_bytes(b'')
    ac = {'id': 'e2', 'tipo': 'mecanismo', 'importancia': 'critica', 'mostrar': 'lamelas',
          'representacao': {'modo': 'foto_ilustrativa', 'foto': 'a3', 'nao_prova': True}}
    v1 = {'scenes': [{'tipo': 'historia', 'fala': 'x', 'start': 0, 'end': 3, 'acontecimento': ac}]}
    r = fiscal_v2.avaliar({'scenes': [_cena('banner.discreto', 0, 3, img=str(img), params={'rotulo': 'ILUSTRAÇÃO'}, origem=[0])], 'captions': []},
                          [{}], dados_v1=v1)
    assert 'S5' not in _cods(r) and 'S7' in _cods(r, 'revisao')


def test_fiscal_foto_parada_e_repetida_em_cenas_seguidas(tmp_path):
    a, b = tmp_path / 'a.jpg', tmp_path / 'b.jpg'
    a.write_bytes(b''); b.write_bytes(b'')
    cenas = [_cena('foto.documental', 0, 2.5, img=str(a)), _cena('foto.documental', 2.5, 5.1, img=str(a)),
             _cena('foto.documental', 5.1, 8.9, img=str(b))]
    r = fiscal_v2.avaliar({'scenes': cenas, 'captions': []}, [{}] * 3)
    assert sorted(_cods(r)) == ['D15', 'D16']                    # a: 5,1 s seguidos em 2 cenas; b: 3,8 s (ok)
    assert any('5.1 s' in x['evidencia'] for x in r['achados'] if x['codigo'] == 'D15')


def test_fiscal_bloqueia_cena_critica_com_esquema_pendente():
    ac = {'id': 'e7', 'tipo': 'processo', 'importancia': 'critica', 'mostrar': 'x'}
    v1 = {'scenes': [{'tipo': 'historia', 'fala': 'x', 'start': 0, 'end': 4, 'acontecimento': ac,
                      'resolucao': {'tipo': 'esquema_pendente', 'pendente': True}}]}
    r = fiscal_v2.avaliar({'scenes': [_cena('destaque.palavras', 0, 4, params={'frase': 'x'}, origem=[0])], 'captions': []}, [{}], dados_v1=v1)
    assert 'S9' in _cods(r)


# ───────────── montagem ─────────────
def test_kicker_nunca_corta_palavra():
    assert montagem._kicker('CIÊNCIA', 'Sem nenhuma gota de cola') == 'CIÊNCIA'      # era "CIÊNCIA · SEM NENHUMA GOTA DE CO"
    assert montagem._kicker('CIÊNCIA', 'Natureza') == 'CIÊNCIA · NATUREZA'


def test_detalhe_da_revelacao_vem_do_conteudo_final():
    longa = 'Sem ventosas ou cola, a lagartixa se prende graças à atração entre moléculas muito próximas.'
    assert montagem._detalhe_validado({'fala': longa, 'detalhe': 'Dipolos elétricos instantâneos grudam as patas sem usar cola.'}) is None
    assert montagem._detalhe_validado({'fala': longa, 'detalhe': 'Atração entre moléculas muito próximas.'}) == 'Atração entre moléculas muito próximas.'
    assert montagem._detalhe_validado({'fala': 'A água desce e enche a câmara.', 'detalhe': 'outra coisa'}) == 'A água desce e enche a câmara.'


def test_falas_repetidas_de_uma_ideia_entram_uma_vez():
    v1 = [{'fala': 'Essas faixas são lamelas.'}, {'fala': 'Essas faixas são lamelas.'}, {'fala': 'E têm cerdas.'}]
    assert montagem._juntar(v1, [0, 1, 2]) == 'Essas faixas são lamelas. E têm cerdas.'


def test_revelacao_fica_sobre_o_resultado_do_esquema_sem_textos():
    esq = {'objetos': [{'id': 'a', 'forma': 'corpo', 'rotulo': 'A'}, {'id': 'b', 'forma': 'superficie', 'rotulo': 'B'}],
           'estados': [{'rotulo': 'x'}, {'rotulo': 'y', 'objetos': {'a': {'dy': .2}}}]}
    ac = {'id': 'e1', 'tipo': 'mecanismo', 'importancia': 'critica', 'mostrar': 'm', 'dados': {'esquema': esq},
          'representacao': {'modo': 'composicao', 'comp': 'mecanismo.estados'}}
    d = {'duration': 10, 'meta': {'titulo': 'T'}, 'captions': [],
         'scenes': [{'tipo': 'historia', 'fala': 'Mecanismo.', 'start': 0, 'end': 5, 'acontecimento': ac},
                    {'tipo': 'revelacao', 'fala': 'Resposta.', 'pergunta': 'P?', 'resposta': 'R', 'start': 5, 'end': 9}]}
    v2, _ = montagem.converter(d)
    rev = v2['scenes'][-1]
    assert rev['comp'] == 'revelacao.surpresa' and rev['base']['comp'] == 'mecanismo.estados' and rev['base']['params']['limpa'] is True


# ───────────── áudio: medido NO MP4 final (depois do AAC) ─────────────
@pytest.mark.skipif(shutil.which('ffmpeg') is None, reason='sem ffmpeg')
def test_audio_final_corrigido_depois_do_aac(tmp_path):
    from src.render import render
    video, master = tmp_path / 'v.mp4', tmp_path / 'm.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'color=c=black:s=64x64:d=8', '-c:v', 'libx264', str(video)], check=True)
    # fala sintética baixa com picos: −20 LUFS aprox. (o AAC e o ganho precisam de correção medida)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'sine=f=220:d=8,volume=0.08', '-f', 'lavfi', '-i',
                    'anoisesrc=d=8:a=0.05', '-filter_complex', 'amix=inputs=2:normalize=0', '-ar', '48000', str(master)], check=True)
    out = render.final_medido(video, master, tmp_path / 'final.mp4')
    assert abs(out['lufs'] + 14) <= .6 and out['pico_dbtp'] <= -1.0, out
    assert json.loads((tmp_path / 'final.audio.json').read_text())        # histórico das passadas fica registrado


# ───────────── checkpoint: troca auditada de um trecho do roteiro ─────────────
def _ck(tmp_path):
    v = {'fatos': 'FATOS:\n- a (X)', 'fontes': ['X'], 'resumo': 'velho', 'cenas': [
        {'tipo': 'gancho', 'fala': 'Abre.', 'acontecimento': {'id': 'e1', 'tipo': 'ambiente'}},
        {'tipo': 'historia', 'fala': 'Velho um.', 'acontecimento': {'id': 'e2', 'tipo': 'processo'}},
        {'tipo': 'historia', 'fala': 'Velho dois', 'sub': 0, 'fala_ideia': 'Velho dois e três.', 'acontecimento': {'id': 'e3', 'tipo': 'processo'}},
        {'tipo': 'historia', 'fala': 'e três.', 'sub': 1, 'acontecimento': {'id': 'e3', 'tipo': 'processo'}},
        {'tipo': 'fechamento', 'fala': 'Segue.', 'acontecimento': {'id': 'e4', 'tipo': 'ambiente'}}]}
    (tmp_path / 'roteiro.json').write_text(json.dumps({'v': v}, ensure_ascii=False))
    return tmp_path


def test_edicao_substitui_trecho_com_trava_e_regenera_resumo(tmp_path):
    ck = _ck(tmp_path)
    sha = hashlib.sha256('Velho um.\nVelho dois\ne três.'.encode()).hexdigest()
    nova = {'tipo': 'historia', 'fala': 'Novo.', 'acontecimento': {'id': 'e2', 'tipo': 'mecanismo'}}
    with pytest.raises(ValueError, match='não são as esperadas'):
        checkpoint.editar(ck, {'operacoes': [{'substituir_eventos': ['e2', 'e3'], 'esperado_sha256': 'x' * 64, 'cenas': [nova]}]})
    with pytest.raises(ValueError, match='sem fonte'):
        checkpoint.editar(ck, {'operacoes': [{'acrescentar_fatos': ['fato sem fonte']}]})
    r = checkpoint.editar(ck, {'operacoes': [{'acrescentar_fatos': ['Fato novo. [contexto] (Fonte Y)'], 'acrescentar_fontes': ['Fonte Y']},
                                             {'substituir_eventos': ['e2', 'e3'], 'esperado_sha256': sha, 'cenas': [nova]},
                                             {'campo': 'resumo', 'regenerar': True}]})
    v = json.loads((ck / 'roteiro.json').read_text())['v']
    assert [c['fala'] for c in v['cenas']] == ['Abre.', 'Novo.', 'Segue.']
    assert v['resumo'] == 'Abre. Novo.' and v['fatos'].endswith('- Fato novo. [contexto] (Fonte Y)') and 'Fonte Y' in v['fontes']
    assert any('e2, e3' in a for a in r['aplicadas']) and (ck / 'edicao_aplicada.json').exists()


def test_edicao_do_piloto_versionada_e_rastreavel():
    """A edição que vai para a retomada única: base_run certo, só fatos com fonte, esquemas válidos, sem foto de prova."""
    from pathlib import Path
    ed = json.loads((Path(__file__).parents[1] / '.github' / 'piloto' / 'edicao.json').read_text())
    assert ed['base_run'] == '43730252500'
    ops = ed['operacoes']
    fatos = next(o for o in ops if o.get('acrescentar_fatos'))['acrescentar_fatos']
    assert all(f.rstrip().endswith(')') for f in fatos)
    troca = next(o for o in ops if o.get('substituir_eventos'))
    for c in troca['cenas']:
        ac = c['acontecimento']
        if ac.get('capacidade') == 'mecanismo.estados':
            assert contrato.esquema_problemas(ac['dados']['esquema']) == [] and ac['observavel'] is False and not c.get('foto')
