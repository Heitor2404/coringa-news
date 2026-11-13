"""Correções da Fase 0 depois do vídeo da Torre Eiffel (12/11/2026).
1 fatos chegam ao fiscal (Explica e Notícias) · 2 diagnóstico em mensagem separada · 3 arquivos da rodada guardados
4 ritmo (total, 3 maiores, acumulado, excedente, imagem repetida) · 5 áudio (LUFS, pico, taxa, canais).
E a regra de sempre: o fiscal sombra não muda aprovação, bloqueio nem publicação. Nenhuma chamada real de IA."""
import copy
import json
import subprocess
from pathlib import Path

import pytest
import yaml

import main
from src import custo, estaticos, fiscal, roteiro

SOMBRA_REAL = fiscal.sombra
BASE = 'FATOS:{fatos}|FRASES:{frases}|TITULO:{titulo}'
RAIZ = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def limpo():
    custo.zerar()
    yield
    custo.zerar()


# ───────── 1. fiscal factual ─────────
FATOS = 'FATOS (★ = mais surpreendentes):\n- ★ Em 1925 Victor Lustig vendeu a Torre Eiffel como ferro-velho (Wikipédia)'
CENAS = [{'tipo': 'gancho', 'fala': 'Ele vendeu a Torre Eiffel.'},
         {'tipo': 'historia', 'fala': 'Victor Lustig se passou por funcionário do governo.'},
         {'tipo': 'fechamento', 'fala': 'Segue.'}]


def _sem_rede(monkeypatch):
    from src import orcamento
    monkeypatch.setattr(orcamento, 'marca', lambda *a, **k: None)
    for f in ('revisar', 'escolher_gancho', 'arrumar_final', 'dividir', 'geocodificar'):
        monkeypatch.setattr(roteiro, f, lambda v, *a, **k: v)
    monkeypatch.setattr(roteiro, '_melhor_de_dois', lambda *a, **k: {'titulo': 'Torre', 'cenas': copy.deepcopy(CENAS)})


def test_caminho_explica_guarda_os_fatos_e_o_fiscal_recebe(monkeypatch):
    from src import acervo as acv, fontes
    _sem_rede(monkeypatch)
    monkeypatch.setattr(fontes, 'coletar', lambda *a, **k: (FATOS, ['Wikipédia'], 'https://x', {'epoca': '1925'}))
    monkeypatch.setattr(roteiro, 'decidir_partes', lambda *a, **k: 1)
    monkeypatch.setattr(acv, 'coletar', lambda *a, **k: [])
    monkeypatch.setattr(acv, 'texto', lambda *a, **k: '')
    monkeypatch.setattr(acv, 'casar', lambda v, *a, **k: v)
    monkeypatch.setattr(acv, 'preencher', lambda v, *a, **k: v)
    monkeypatch.setattr(acv, 'complementar', lambda v, acervo, *a, **k: acervo)
    monkeypatch.setattr(roteiro, '_planos_sem_foto', lambda v, *a, **k: v)
    v = roteiro.escrever_explica({'pergunta': 'Como vendeu a torre?', 'termos': ['Lustig']})
    assert v['fatos'] == FATOS
    enviados = []
    fiscal.avaliar_texto(v, prompt_base=BASE, pedir=lambda p: enviados.append(p) or {'fatos': {}})
    assert 'Lustig vendeu a Torre Eiffel como ferro-velho' in enviados[0]


def test_caminho_noticias_guarda_os_fatos_e_o_fiscal_recebe(monkeypatch):
    _sem_rede(monkeypatch)
    monkeypatch.setattr(roteiro, '_fatos', lambda pauta: 'FATO DA NOTÍCIA: a ponte fechou em 3 de março')
    monkeypatch.setattr(roteiro, 'PROMPT_ROTEIRO', '{fatos} {produtos} {titulo}')     # o texto real fica no cofre
    v = roteiro.escrever({'titulo': 'Ponte fecha', 'resumo': '', 'fonte': '', 'link': ''}, [])
    enviados = []
    fiscal.avaliar_texto(v, prompt_base=BASE, pedir=lambda p: enviados.append(p) or {'fatos': {}})
    assert 'a ponte fechou em 3 de março' in enviados[0]


def test_prompt_do_cofre_aceita_os_fatos():
    from src import cofre
    base = cofre.prompt('PROMPT_FISCAL_SOMBRA')
    if base.startswith('['):
        pytest.skip('cofre privado não disponível aqui')
    p = base.format(fatos='FATO-XYZ', frases='1. a', titulo='t')
    assert 'FATO-XYZ' in p and 'nao_conferivel' in p and '"status"' in p


def _resp_fatos(*status):
    return {'fatos': {'frases': [{'frase': k + 1, 'status': s, 'explicacao': f'e{k + 1}'} for k, s in enumerate(status)]},
            'narrativa': {'nota': 15}, 'recursos': {'faltou': []}}


def _v(n=4, fatos='FATO'):
    return {'titulo': 't', 'fatos': fatos, 'cenas': [{'tipo': 'historia', 'fala': f'frase {k}'} for k in range(n)]}


def _cenas(*planos):
    out, t = [], 0.0
    for img, dur, tipo in planos:
        out.append({'imagem': img, 'img': img, 'start': t, 'end': t + dur, 'tipo': tipo})
        t += dur
    return out


def test_fatos_vazios_viram_nao_medido_mesmo_com_resposta_boa():
    """Sem fatos pesquisados não há evidência: nada de nota (nem 1/25 como na Torre Eiffel, nem 25/25)."""
    tudo_certo = _resp_fatos('confere', 'confere', 'confere', 'confere')
    enviados = []
    r = SOMBRA_REAL(_v(fatos=''), _cenas(('a', 3, 'historia')), None, 8,
                    pedir=lambda p: enviados.append(p) or tudo_certo, prompt_base=BASE)
    assert r['partes']['fatos'] is None and 'fatos' in r['nao_medido']
    assert 'SEM FATOS PESQUISADOS' in enviados[0]
    assert any('não recebeu os fatos' in x for x in fiscal.linhas_telegram(r))
    # o caso real: 12 frases "sem fonte" com o bloco vazio → antes 1/25, agora não medido e sem bloqueador
    torre = _resp_fatos(*['sem_fonte'] * 12)
    r = SOMBRA_REAL(_v(12, fatos=''), _cenas(('a', 3, 'historia')), None, 5, pedir=lambda p: torre, prompt_base=BASE)
    assert r['partes']['fatos'] is None and r['bloqueadores'] == []


def test_incorreta_e_diferente_de_nao_conferivel():
    r = SOMBRA_REAL(_v(4), _cenas(('a', 3, 'historia')), None, 8,
                    pedir=lambda p: _resp_fatos('confere', 'confere', 'erro_grave', 'nao_conferivel'), prompt_base=BASE)
    f = r['fatos']
    assert f['contagem']['erro_grave'] == 1 and f['contagem']['nao_conferivel'] == 1
    assert r['bloqueadores'] == ['frase 3: e3']                     # só a incorreta vira bloqueador
    assert r['obs']['fatos'] == ['não conferível: frase 4: e4']     # a não conferível aparece à parte, sem ser erro
    assert r['partes']['fatos'] == 12.5                             # 2 conferidas de 4 afirmações (não conferível: 0)
    linhas = '\n'.join(fiscal.linhas_telegram(r))
    assert 'INCORRETA' in linhas and '1 não conferíveis' in linhas and '1 incorretas' in linhas


def test_sem_evidencia_suficiente_nao_ganha_nota_positiva():
    # 3 de 4 afirmações sem fonte: menos da metade conferível → não medido (não dá 25 nem nenhum ponto)
    r = fiscal.nota_fatos(_resp_fatos('confere', 'nao_conferivel', 'nao_conferivel', 'nao_conferivel')['fatos'], 4)
    assert r['nota'] is None and 'evidência insuficiente' in r['motivo']
    # frase não conferível nunca soma ponto: 2 conferidas + 2 não conferíveis = metade da nota
    r = fiscal.nota_fatos(_resp_fatos('confere', 'confere', 'nao_conferivel', 'nao_conferivel')['fatos'], 4)
    assert r['nota'] == 12.5
    # frase de ligação fica fora da conta
    r = fiscal.nota_fatos(_resp_fatos('confere', 'sem_afirmacao')['fatos'], 2)
    assert r['nota'] == 25 and r['afirmacoes'] == 1
    # resposta no formato antigo (só uma nota, sem frase a frase): não aceita a nota → não medido
    r = fiscal.nota_fatos({'nota': 25, 'problemas': []}, 4)
    assert r['nota'] is None


# ───────── o fiscal sombra não muda aprovação, bloqueio nem publicação ─────────
def _montar(monkeypatch, tmp, nota_antiga, resposta, sombra=True, erros=(), dur=60.0):
    cenas = [{'tipo': 'gancho', 'fala': 'Ele vendeu a torre', 'imagem': 'a', 'img': 'a.jpg', 'start': 0, 'end': 3},
             {'tipo': 'historia', 'fala': 'Lustig fugiu', 'imagem': 'b', 'img': 'b.jpg', 'start': 3, 'end': dur - 2},
             {'tipo': 'fechamento', 'fala': 'Segue', 'start': dur - 2, 'end': dur}]
    monkeypatch.setattr(main.voz, 'narrar', lambda *a, **k: (tmp / 'a.wav', [], [], dur))
    monkeypatch.setattr(main, 'escolher_musica', lambda *a, **k: None)
    monkeypatch.setattr(main, '_montar_cenas', lambda *a, **k: copy.deepcopy(cenas))
    monkeypatch.setattr(main, 'renderizar', lambda dados, audio, saida, trab, musica=None: saida.write_bytes(b''))
    monkeypatch.setattr(main, 'renderizar_capa', lambda *a, **k: None)
    monkeypatch.setattr(main, 'fiscal_final', lambda *a, **k: (nota_antiga, []))
    monkeypatch.setattr(main, 'pacote_diagnostico', lambda *a, **k: None)
    monkeypatch.setattr(main, 'erros_basicos', lambda *a, **k: list(erros))
    if sombra:
        monkeypatch.setattr(fiscal, 'sombra', lambda v, c, s, n, t: SOMBRA_REAL(v, c, None, n, t, pedir=lambda p: resposta,
                                                                              prompt_base=BASE))
    else:
        monkeypatch.setattr(fiscal, 'sombra', lambda *a, **k: 1 / 0)
    v = {'titulo': 'Torre', 'fatos': 'FATO', 'cenas': [{'tipo': 'gancho', 'fala': 'Ele vendeu a torre'},
                                                       {'tipo': 'historia', 'fala': 'Lustig fugiu'},
                                                       {'tipo': 'fechamento', 'fala': 'Segue'}]}
    tmp.mkdir(exist_ok=True)
    main.montar_video(v, tmp, 'torre')
    return v


PESSIMA = _resp_fatos('erro_grave', 'erro_grave') | {'narrativa': {'nota': 0},
                                                     'recursos': {'faltou': [{'frase': 1, 'recurso': 'mapa'}] * 4}}
PERFEITA = _resp_fatos('confere', 'confere')


@pytest.mark.parametrize('nota_antiga,resposta,erros,dur', [
    (9.0, PESSIMA, (), 60.0), (3.0, PERFEITA, (), 60.0), (5.0, PESSIMA, (), 60.0), (5.0, PERFEITA, (), 60.0),
    (9.0, PESSIMA, ('imagem parada 8s num plano só (a partir de 3s)',), 60.0),       # bloqueio do porteiro antigo
    (3.0, PERFEITA, (), 85.0)])                                                     # bloqueio por duração
def test_sombra_nao_muda_aprovacao_bloqueio_nem_publicacao(monkeypatch, tmp_path, nota_antiga, resposta, erros, dur):
    sem = _montar(monkeypatch, tmp_path / 'sem', nota_antiga, resposta, sombra=False, erros=erros, dur=dur)
    com = _montar(monkeypatch, tmp_path / 'com', nota_antiga, resposta, sombra=True, erros=erros, dur=dur)
    sb = json.loads((tmp_path / 'com' / 'torre-fiscal-sombra.json').read_text())
    assert sb['nota'] is not None and abs(sb['nota'] - nota_antiga) >= 1          # as duas notas discordam de verdade
    assert com['_telegram']['resumo'] == sem['_telegram']['resumo']               # ⭐, ⚠️/✅, 🔧 idênticos
    assert com['_bloqueado'] == sem['_bloqueado']                                 # porteiro = publicação idêntica
    assert '🧪' not in com['_telegram']['resumo'] and '🧪' in com['_telegram']['diagnostico']
    assert f'⭐ fiscal: {nota_antiga:.0f}/10' in com['_telegram']['resumo']           # a ⭐ é a nota ANTIGA
    assert bool(com['_bloqueado']) == bool(erros or dur > 80)                        # só o porteiro antigo bloqueia
    if not erros and dur <= 78:
        assert ('NÃO RECOMENDO POSTAR' in com['_telegram']['resumo']) == (nota_antiga < 6)


# ───────── 2. Telegram: diagnóstico separado e inteiro ─────────
def test_diagnostico_vai_separado_inteiro_e_o_resumo_fica_igual(monkeypatch, tmp_path):
    enviados = []
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'x')
    monkeypatch.setenv('TELEGRAM_CHAT_ID', 'y')
    monkeypatch.setattr(main, '_tg', lambda metodo, data, arquivo=None: enviados.append((metodo, data)) or False)
    monkeypatch.setattr(main, '_comparar_audio', lambda a, e: '🔊 áudio — original: X · versão do Telegram: Y')
    arq = tmp_path / 'v.mp4'
    arq.write_bytes(b'0')
    longo = '\n'.join(f'   • não conferível: frase {k}: ' + 'x' * 120 for k in range(80))      # ~11 mil caracteres
    resumo = '🎬 Torre\n⭐ fiscal: 5/10\n⚠️ NÃO RECOMENDO POSTAR: nota do fiscal 5/10'
    v = {'_telegram': {'resumo': resumo, 'textos': {}, 'diagnostico': '🧪 Fiscal novo\n' + longo + '\n💰 Claude ≈USD 0.37'}}
    main.telegram(arq, 'legenda', v)
    assert enviados[0] == ('sendVideo', {'caption': resumo, 'supports_streaming': 'true'})   # resumo principal intacto
    msgs = [d['text'] for m, d in enviados if m == 'sendMessage']
    assert all(len(t) <= 4096 for t in msgs) and len(msgs) >= 3
    junto = '\n'.join(msgs)
    assert longo in junto and '💰 Claude ≈USD 0.37' in junto and '🔊 áudio' in junto      # nada cortado


def test_resumo_maior_que_a_legenda_vai_inteiro_em_mensagem(monkeypatch, tmp_path):
    enviados = []
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'x')
    monkeypatch.setenv('TELEGRAM_CHAT_ID', 'y')
    monkeypatch.setattr(main, '_tg', lambda metodo, data, arquivo=None: enviados.append((metodo, data)) or True)
    monkeypatch.setattr(main, '_comparar_audio', lambda a, e: '')
    monkeypatch.setattr(main, 'RAIZ', tmp_path)
    (tmp_path / 'data').mkdir()
    arq = tmp_path / 'v.mp4'
    arq.write_bytes(b'0')
    resumo = '\n'.join(f'linha {k} ' + 'y' * 60 for k in range(30))
    main.telegram(arq, 'legenda', {'_telegram': {'resumo': resumo, 'textos': {}}})
    assert len(enviados[0][1]['caption']) <= 1024
    assert resumo in '\n'.join(d['text'] for m, d in enviados if m == 'sendMessage')


def test_pedacos_nao_perde_nada():
    texto = '\n'.join(['a' * 50] * 200 + ['b' * 9000])
    partes = main._pedacos(texto)
    assert all(len(p) <= main.LIMITE_MSG for p in partes) and ''.join(partes).replace('\n', '') == texto.replace('\n', '')


# ───────── 3. arquivos da rodada ─────────
def test_workflow_guarda_arquivos_criptografados_por_7_dias_sem_parar_a_producao():
    wf = yaml.safe_load((RAIZ / '.github/workflows/gerar-videos.yml').read_text(encoding='utf-8'))
    passos = wf['jobs']['gerar']['steps']
    nomes = [p.get('name') for p in passos]
    emp = passos[nomes.index('Empacotar arquivos da rodada do Coringa (criptografado)')]
    up = passos[nomes.index('Guardar arquivos da rodada do Coringa (7 dias)')]
    assert nomes.index('Gerar vídeos') < nomes.index(emp['name']) < nomes.index(up['name'])
    for p in (emp, up):
        assert p['continue-on-error'] is True and 'always()' in p['if']             # falha aqui não derruba nada
    assert "inputs.ntc == ''" in emp['if'] and 'agenda-ntc' in emp['if']            # rodada do NTC fica de fora
    assert '--symmetric' in emp['run'] and 'AES256' in emp['run'] and 'ARTEFATOS_SENHA' in emp['env']
    assert "pacotes_ntc" in emp['run'] and '-telegram.mp4' in emp['run']
    for tipo in ('*.json', '*-diagnostico.zip', '*.mp4'):
        assert tipo in emp['run']
    assert up['uses'].startswith('actions/upload-artifact@') and up['with']['retention-days'] == 7
    assert up['with']['path'] == 'coringa-rodada.tar.gpg'                          # só o arquivo criptografado sobe
    assert 'git add' not in emp['run']                                               # nada vai para o repositório


# ───────── 4. ritmo ─────────
@pytest.mark.parametrize('duracoes', [
    [3.7, 4.3, 6.7, 5.3, 2.4, 2.3, 4.7, 1.8, 1.7, 1.0, 2.7, 3.2, 1.7, 1.7, 6.2, 4.6, 3.2],   # a Torre, plano a plano
    [5.0, 5.0, 5.0, 5.0, 5.0], [2.0, 2.0, 2.0], [4.0, 4.1, 3.9, 12.0]])
def test_soma_dos_trechos_bate_com_o_percentual_exibido(duracoes):
    c = _cenas(*[(f'i{k}', d, 'historia') for k, d in enumerate(duracoes)])
    m = estaticos.medir_cenas(c)
    dur = sum(duracoes)
    soma = sum(b - a for a, b, _ in m['estaticos'])
    assert abs(m['parado_s'] - soma) < 0.01 and abs(m['frac_estatica'] - soma / dur) < 0.001
    assert abs(m['excedente_s'] - sum(b - a - 4 for a, b, _ in m['estaticos'])) < 0.01
    txt = estaticos.resumo(m)
    if m['estaticos']:
        assert f"{len(m['estaticos'])} trecho(s)" in txt and f'({round(100 * soma / dur)}% do vídeo)' in txt
        assert f"só o que passou de 4s: {m['excedente_s']:.1f}s".replace('.', ',') in txt
        assert txt.split('\n')[1].split(';')[0].count('–') == min(3, len(m['estaticos']))   # no máximo 3 listados
    else:
        assert 'nenhum trecho parado' in txt


def test_torre_eiffel_mostra_total_tres_maiores_e_as_duas_reguas():
    c = _cenas(*[(f'i{k}', d, 'historia') for k, d in enumerate(
        [3.7, 4.3, 6.7, 5.3, 2.4, 2.3, 4.7, 1.8, 1.7, 1.0, 2.7, 3.2, 1.7, 1.7, 6.2, 4.6, 3.2])])
    txt = estaticos.resumo(estaticos.medir_cenas(c))
    assert '6 trecho(s)' in txt and 'somando 31,8s (56% do vídeo)' in txt
    assert 'os 3 maiores: 8,0–14,7s (6,7s), 43,2–49,4s (6,2s), 14,7–20,0s (5,3s)' in txt
    assert 'só o que passou de 4s: 7,8s (14%)' in txt


def test_foto_da_vizinha_conta_como_a_mesma_imagem_e_como_volta():
    """O caso da Torre: o plano sem imagem própria reaproveita a foto de outra ideia (mesmo arquivo, outro id)."""
    c = _cenas(('torre', 3, 'historia'), ('caminhao', 3, 'historia'), ('x', 3, 'historia'))
    c[2]['img'] = 'torre'                              # id 'x' (da ideia), mas na tela está a foto da torre
    assert fiscal.nota_ritmo(c)[2][-1] == '1 imagem(ns) voltando depois de outras'
    c2 = _cenas(('torre', 3, 'historia'), ('x', 3, 'historia'))
    c2[1]['img'] = 'torre'
    assert estaticos.medir_cenas(c2)['estaticos'] == [(0.0, 6.0, 6.0)]       # 6 s da mesma foto = parado


def test_plano_longo_quebrado_com_outra_foto_e_mudanca():
    c = _cenas(('a', 3, 'historia'), ('a', 3, 'historia'))
    c[1]['img'] = 'outra-foto'                          # mesma ideia (id 'a'), outra foto na tela
    assert estaticos.medir_cenas(c)['estaticos'] == []


def test_mesma_foto_em_dois_arquivos_e_a_mesma_imagem(tmp_path):
    from PIL import Image, ImageDraw
    def foto(nome, desenho):
        im = Image.new('RGB', (120, 200), 'white')
        desenho(ImageDraw.Draw(im))
        im.save(tmp_path / nome)
        return str(tmp_path / nome)
    torre = foto('torre.jpg', lambda d: d.polygon([(60, 10), (20, 190), (100, 190)], fill='black'))
    copia = foto('torre_copia.png', lambda d: d.polygon([(60, 10), (20, 190), (100, 190)], fill='black'))
    outra = foto('ponte.jpg', lambda d: d.rectangle([0, 120, 120, 200], fill='black'))
    c = _cenas(('i1', 3, 'historia'), ('i2', 3, 'historia'), ('i3', 3, 'historia'))
    c[0]['img'], c[1]['img'], c[2]['img'] = torre, outra, 'file://' + copia
    k = estaticos.chaves_visuais(c)
    assert k[0] == k[2] != k[1]
    assert fiscal.nota_ritmo(c)[2][-1] == '1 imagem(ns) voltando depois de outras'


def test_video_continuando_no_plano_seguinte_e_o_mesmo_clipe():
    c = _cenas(('clipe', 3, 'historia'), ('clipe', 3, 'historia'))
    c[0]['img'], c[1]['img'] = 'q/00/f_0001.jpg', 'q/01/f_0001.jpg'
    for x in c:
        x['video'] = {'dir': 'q', 'n': 30}
    assert estaticos.medir_cenas(c)['estaticos'] == [(0.0, 6.0, 6.0)]


# ───────── 5. áudio ─────────
def _audio(tmp_path, nome, taxa, canais, extra=()):
    arq = tmp_path / nome
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'sine=f=440:d=3:r={taxa}', '-ac', str(canais),
                    *extra, '-c:a', 'aac', '-b:a', '128k', str(arq)], check=True)
    return arq


def test_medir_audio_traz_volume_pico_taxa_e_canais(tmp_path):
    a = fiscal.medir_audio(_audio(tmp_path, 'a.m4a', 48000, 2))
    assert a['taxa_hz'] == 48000 and a['canais'] == 2 and a['lufs'] < 0
    assert fiscal.texto_audio(a).endswith('48 kHz, estéreo') and 'LUFS' in fiscal.texto_audio(a) and 'dBTP' in fiscal.texto_audio(a)


def test_comparacao_de_audio_original_e_telegram(tmp_path):
    orig = _audio(tmp_path, 'o.mp4', 96000, 1)
    tg = _audio(tmp_path, 'o-telegram.mp4', 44100, 2)
    linha = main._comparar_audio(orig, tg)
    assert linha.startswith('🔊 áudio — original: ') and '96 kHz, mono' in linha and '44.1 kHz, estéreo' in linha
    assert 'o próprio original' in main._comparar_audio(orig, orig)
    assert 'não medida' in main._comparar_audio(tmp_path / 'nao-existe.mp4', tg)          # falha só avisa


def test_normalizacao_nao_mudou():
    """Esta etapa só MEDE: a cadeia de áudio da montagem continua a mesma (loudnorm −14 / −1,5)."""
    fonte = (RAIZ / 'src/render/render.py').read_text(encoding='utf-8')
    assert fonte.count('loudnorm=I=-14:TP=-1.5[a]') == 2 and 'aresample' not in fonte.split('def renderizar(')[-1]
