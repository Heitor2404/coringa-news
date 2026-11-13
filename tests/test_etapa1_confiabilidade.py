"""Etapa 1 da auditoria estrutural (13/11/2026): confiabilidade. Casos tirados do vídeo real do polvo. Sem IA paga.
1 JSON do Claude recuperado com segurança (1º objeto válido + esquema) e resposta bruta guardada;
2 gancho subordinado à promessa; 3 desvio do assunto central; 4 narração extra (causa) e áudio masterizado."""
import copy
import json
import subprocess
from pathlib import Path

import pytest

from src import claude, editorial as ed, fiscal, gemini, roteiro, voz
from src.render import render

ROT = {'titulo': 'POLVO', 'cenas': [{'tipo': 'gancho', 'fala': 'a'}, {'tipo': 'historia', 'fala': 'b'},
                                    {'tipo': 'historia', 'fala': 'c'}, {'tipo': 'fechamento', 'fala': 'd'}]}


# ───────── 1. JSON ─────────
def test_roteiro_com_texto_depois_do_json_e_recuperado():
    """O caso do polvo: "Extra data" — havia algo depois do JSON e a busca gulosa jogava a resposta paga fora."""
    txt = json.dumps(ROT, ensure_ascii=False) + '\n\nObservação: mantive 12 cenas {ver acima}.'
    assert gemini.extrair_json(txt, roteiro.e_roteiro) == ROT
    assert 'ignorei 0 caractere(s) antes' in gemini.AVISOS_JSON[-1]


def test_dois_blocos_e_cercas_de_codigo():
    txt = '```json\n' + json.dumps(ROT) + '\n```\n```json\n{"outro": 1}\n```'
    assert gemini.extrair_json(txt, roteiro.e_roteiro) == ROT
    assert gemini.extrair_json('Aqui está:\n' + json.dumps(ROT) + ' fim', roteiro.e_roteiro) == ROT


def test_nao_aceita_pedaco_nem_formato_errado():
    quebrado = '{"titulo": "X", "cenas": [{"tipo": "gancho", "fala": "a"}, {"tipo": "historia", "fala": "b"'   # cortado
    with pytest.raises(ValueError):
        gemini.extrair_json(quebrado, roteiro.e_roteiro)        # não devolve uma CENA solta no lugar do roteiro
    with pytest.raises(ValueError):
        gemini.extrair_json(quebrado)                          # sem esquema: só o 1º objeto, e ele está quebrado
    with pytest.raises(ValueError, match='formato esperado'):
        gemini.extrair_json('{"notas": {}}', roteiro.e_roteiro)
    assert gemini.extrair_json('lixo {"aprovado": true} {"x": 2}', roteiro.e_critica) == {'aprovado': True}


def test_cascata_aproveita_a_resposta_paga_do_claude(monkeypatch):
    monkeypatch.setattr(claude, 'disponivel', lambda: True)
    monkeypatch.setattr(claude, 'pedir', lambda p, leve=False: json.dumps(ROT) + '\nFim do roteiro.')
    gem = []
    r = gemini._em_cascata(lambda m: gem.append(m) or {}, 'PEDIDO', True, False, roteiro.e_roteiro)
    assert r == ROT and gem == []                                  # o Gemini nem foi chamado


def test_resposta_fora_do_esquema_cai_para_a_reserva(monkeypatch, capsys):
    monkeypatch.setattr(claude, 'disponivel', lambda: True)
    monkeypatch.setattr(claude, 'pedir', lambda p, leve=False: '{"notas": {"gancho": 7}}')
    monkeypatch.setattr(gemini, '_tentar', lambda f, modelos=None: copy.deepcopy(ROT))
    assert gemini._em_cascata(lambda m: None, 'P', True, False, roteiro.e_roteiro) == ROT
    assert 'formato esperado' in capsys.readouterr().out


def test_resposta_bruta_guardada_so_no_coringa(monkeypatch, tmp_path):
    monkeypatch.setattr(claude, 'PASTA_BRUTAS', tmp_path / 'brutas')
    monkeypatch.setattr(claude, '_no_coringa', lambda: False)
    claude.guardar_bruta('NTC')
    assert not (tmp_path / 'brutas').exists()                      # NTC: nada muda
    monkeypatch.setattr(claude, '_no_coringa', lambda: True)
    claude.guardar_bruta('{"cenas": []} resto')
    claude.guardar_bruta('segunda')
    arqs = sorted((tmp_path / 'brutas').glob('*.txt'))
    assert len(arqs) == 2 and arqs[0].read_text() == '{"cenas": []} resto'


# ───────── 2. gancho e promessa ─────────
PLANO = {'origem': 'roteirista', 'assunto': 'como o polvo muda de cor', 'promessa': 'como o polvo muda de cor em frações de segundo',
         'angulo': {'tipo': 'mecanismo', 'pergunta': 'como a cor do polvo muda tão rápido?'},
         'intencao': 'entender cromatóforos, nervos e células refletoras',
         'estrategia': {'progressao': ['cromatóforos são sacos de pigmento', 'músculos esticam', 'nervos ligados ao cérebro'],
                        'payoff': 'impulso direto do cérebro'},
         'evidencias': [{'afirmacao': 'cromatóforos têm pigmento', 'fonte': 'Wikipédia'}]}


def _v():
    return ed.preparar({'titulo': 'POLVO', 'plano': copy.deepcopy(PLANO), 'cenas': [
        {'tipo': 'gancho', 'fala': 'O polvo muda de cor em frações de segundo.'},
        {'tipo': 'historia', 'fala': 'A pele tem células, os cromatóforos.'},
        {'tipo': 'historia', 'fala': 'Mamíferos e aves não têm cromatóforos, só melanócitos.'},
        {'tipo': 'historia', 'fala': 'Em janeiro de 2026, uma pele sintética imitou cor e textura em segundos.'},
        {'tipo': 'historia', 'fala': 'Dormindo, ele revive padrões de cor.'},
        {'tipo': 'fechamento', 'fala': 'Segue.'}]})


def _ganchos(monkeypatch, opcoes, escolha=0):
    vistos = []
    monkeypatch.setattr(gemini, 'json_', lambda p, leve=False, validar=None: vistos.append(p) or {'opcoes': opcoes, 'escolha': escolha})
    from src import orcamento
    monkeypatch.setattr(orcamento, 'sobra', lambda: 999)
    v = roteiro.escolher_gancho(_v(), 'FATOS')
    return v, vistos[0]


def test_gancho_do_polvo_fora_da_promessa_e_trocado(monkeypatch, capsys):
    v, pedido = _ganchos(monkeypatch, [{'fala': 'Ele tem *nove cérebros* e três corações.', 'titulo': 'O ANIMAL DE *9 CÉREBROS*'},
                                       {'fala': 'Um *polvo* dormindo continua mudando de cor.', 'titulo': 'O POLVO QUE *MUDA* DE COR'}])
    assert v['cenas'][0]['fala'].startswith('Um *polvo* dormindo')
    assert 'fugia da promessa' in capsys.readouterr().out
    assert 'como o polvo muda de cor em frações de segundo' in pedido or 'promessa' in pedido.lower()


def test_sem_opcao_dentro_da_promessa_fica_o_gancho_original(monkeypatch):
    v, _ = _ganchos(monkeypatch, [{'fala': 'Ele tem *nove cérebros* e três corações.'}])
    assert v['cenas'][0]['fala'] == 'O polvo muda de cor em frações de segundo.'


def test_roteiro_sem_plano_nao_confere_promessa(monkeypatch):
    assert roteiro.na_promessa({'fala': 'qualquer coisa'}, {'titulo': 'T', 'cenas': [{'fala': 'x'}]})


# ───────── 3. desvio do assunto central ─────────
def test_pele_sintetica_de_2026_e_desvio(monkeypatch):
    d = ed.desvios(_v())
    assert len(d) == 1 and 'cena 4' in d[0] and '2026' in d[0]
    assert any('desvio' in x for x in ed.avaliar_roteiro(_v())['problemas'])
    assert 'desvio' in ed.para_critica(_v())                      # vai para a crítica que já é chamada


def test_bloco_seguido_fora_do_assunto_e_desvio():
    v = _v()
    v['cenas'][2:4] = [{'tipo': 'historia', 'fala': 'O Japão lançou um trem bala novo.'},
                       {'tipo': 'historia', 'fala': 'Ele atinge velocidade recorde nos trilhos.'}]
    assert any('cenas 3–4' in x for x in ed.desvios(v))


def test_os_tres_casos_bons_nao_tem_desvio():
    casos = json.loads((Path(__file__).parent / 'editorial_casos.json').read_text(encoding='utf-8'))
    for nome, c in casos.items():
        v = ed.preparar(copy.deepcopy(c['roteiro']))
        assert ed.desvios(v) == [], nome


def test_desvio_vira_alerta_p1_do_fiscal_sombra():
    v = _v()
    v['fatos'] = '- fatos'
    al = fiscal.alertas(v, [], [], [])
    assert any(a['nivel'] == 'P1' and 'desvio' in a['evidencia'] for a in al)


# ───────── 4. narração extra e áudio ─────────
def test_causa_da_narracao_extra_e_a_instrucao_lida_em_voz_alta():
    """16 s cortados no polvo ≈ o pedido inteiro ao TTS (instrução + estilo antigo do config.json ≈ 37 palavras ≈ 16 s
    a ~2,4 palavras/s). O diagnóstico agora diz o que foi falado; o estilo do Coringa ficou curto (o do NTC não mudou)."""
    antigo = ('narrador de documentário brasileiro, voz grave, séria e envolvente, ritmo natural e firme (nem rápido nem '
              'lento), pequena pausa entre as frases para criar suspense')
    ouvido = 'Narre em português do Brasil narrador de documentário brasileiro voz grave séria e envolvente'.split()
    assert 'leu a INSTRUÇÃO' in voz.diagnostico_extra(ouvido, antigo)
    assert 'não é instrução' in voz.diagnostico_extra('o polvo o polvo o polvo'.split(), antigo)
    instrucao = f'Narre em português do Brasil ({antigo}). Leia SOMENTE o texto abaixo da linha.'
    assert 14 <= len(instrucao.split()) / 2.4 <= 18                  # a duração bate com os 16 s cortados
    cfg = json.loads((Path(__file__).parent.parent / 'config.json').read_text(encoding='utf-8'))
    assert len(cfg['estilo_gemini'].split()) <= 8
    from src import fabula
    assert 'debochado' in fabula.VOZ['estilo_gemini']                # NTC com o estilo dele, intocado


def _sinal(tmp, nome, expr, d=8):
    arq = tmp / f'{nome}.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f"aevalsrc='{expr}':s=96000:d={d}", str(arq)], check=True)
    return arq


def _em_mp4(tmp, wav):
    mp4 = tmp / (wav.stem + '.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'color=c=black:s=64x64:d=8', '-i', str(wav),
                    '-c:v', 'libx264', '-c:a', 'aac', '-b:a', '160k', '-ar', '48000', '-shortest', str(mp4)], check=True)
    return mp4


@pytest.mark.parametrize('nome,expr', [
    ('quente', '0.99*sin(2*PI*220*t)+0.4*(random(0)*2-1)'),                     # acima de 0 dBTP (como o polvo: +0,9)
    ('baixo', '0.9*sin(2*PI*180*t)*(0.15+0.85*gt(mod(t\\,2)\\,1.6))'),          # picos com fala baixa no meio
    ('fraco', '0.05*sin(2*PI*200*t)')])                                        # baixo demais (−29 LUFS)
def test_master_fica_no_alvo_com_pico_seguro_depois_do_aac(tmp_path, nome, expr):
    w = _sinal(tmp_path, nome, expr)
    r = render.masterizar(w, tmp_path / f'{nome}-m.wav')
    m = fiscal.medir_audio(_em_mp4(tmp_path, tmp_path / f'{nome}-m.wav'))
    assert m['taxa_hz'] == 48000 and m['pico'] <= -1.0, (r, m)
    assert -15.0 <= m['lufs'] <= -13.0, (r, m)


def test_master_de_silencio_nao_quebra(tmp_path):
    w = _sinal(tmp_path, 'mudo', '0')
    render.masterizar(w, tmp_path / 'mudo-m.wav')
    assert (tmp_path / 'mudo-m.wav').exists()
