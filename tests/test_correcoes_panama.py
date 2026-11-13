"""13/11/2026 — correções pontuais depois do teste do Canal do Panamá (sem IA, sem rede, sem custo):
1) execução única (curiosidade pedida à mão / teste) gera no máximo UM vídeo, mesmo reprovado;
2) payoff e fechamento não herdam a mesma foto até passar de 11 s seguidos (o que barrou o vídeo);
3) o TTS do Coringa nunca recebe a instrução de tom dentro do texto falado."""
import contextlib

import main
from src import voz


# ───────────── 1) execução única ─────────────
def test_execucao_unica_gera_um_video_e_nao_promete_outro_tema(monkeypatch, tmp_path):
    from src import orcamento_video, roteiro
    chamadas, msgs = [], []
    monkeypatch.setattr(orcamento_video, 'video', lambda *a, **k: contextlib.nullcontext())
    from src import custo
    monkeypatch.setattr(custo, 'tentativa', lambda *a, **k: None)
    monkeypatch.setattr(main, '_arquivo_serie', lambda *a: tmp_path / 'serie.json')
    monkeypatch.setattr(roteiro, 'tema_livre', lambda p: {'pergunta': 'Como?', 'tema': p})
    monkeypatch.setattr(roteiro, 'escrever_explica', lambda t, parte, serie: {'titulo': 'T', 'resumo': '', 'cenas': []})

    def montar(v, pasta, nome):
        chamadas.append(nome)
        v['_bloqueado'] = 'a mesma imagem ficou 13s na tela'
        return tmp_path / 'x.mp4'
    monkeypatch.setattr(main, 'montar_video', montar)
    monkeypatch.setattr(main, '_tg', lambda metodo, dados: msgs.append(dados['text']))
    r = main.fazer_curiosidade('Canal do Panamá', 1, tmp_path, unico=True)
    assert len(chamadas) == 1 and r == 'pular'
    assert 'nenhum outro tema' in msgs[0] and 'Vou tentar outro tema' not in msgs[0]


def test_linha_de_comando_da_curiosidade_e_execucao_unica_e_o_diario_nao_muda():
    import inspect
    fonte = inspect.getsource(main.main)
    assert 'fazer_curiosidade(a.curiosidade.strip(), a.parte, pasta, unico=True)' in fonte
    assert 'unico' not in inspect.getsource(main._diario)          # produção (diário) continua tentando outras pautas


# ───────────── 2) repetição de mídia no final ─────────────
def _cena(tipo, ini, fim, img=None, **kw):
    return {'tipo': tipo, 'start': ini, 'end': fim, 'img': img, 'fala': 'A eclusa enche com *água* do lago.', **kw}


def _final_do_panama():
    return [_cena('gancho', 0, 6, 'a0.jpg', real=True, grupo=0),
            _cena('historia', 6, 14, 'a4.jpg', real=True, grupo=1),
            _cena('historia', 14, 22, 'a22.jpg', real=True, grupo=2),
            _cena('historia', 22, 30, 'a14.jpg', real=True, grupo=3),
            _cena('historia', 30, 38, 'a10.jpg', real=True, grupo=4),
            _cena('historia', 38, 46, 'a6.jpg', real=True, grupo=5),
            _cena('historia', 46, 56, 'a2.jpg', real=True, grupo=6),
            _cena('historia', 56, 63, 'a2.jpg', repetida=True, real=True, grupo=7),       # payoff herdou a foto anterior
            _cena('fechamento', 63, 69, 'a2.jpg', _fundo_fechamento=True, grupo=8)]       # fundo = "última foto"


def test_payoff_e_fechamento_nao_esticam_a_mesma_foto():
    cenas = _final_do_panama()
    assert any('mesma imagem' in e for e in main.erros_basicos(cenas, []))            # o caso que barrou o vídeo
    avisos = main._sem_repeticao_longa(cenas)
    assert not any('mesma imagem' in e for e in main.erros_basicos(cenas, []))
    payoff = cenas[7]
    assert payoff['img'] != 'a2.jpg' and payoff['real']                               # outra foto REAL de cena anterior
    usada_antes = next(c for c in cenas[:7] if c['img'] == payoff['img'])
    assert payoff['start'] - usada_antes['end'] >= main.SEPARACAO_MIN                 # com separação visual
    assert avisos == []


def test_sem_alternativa_vira_pendencia_avisada_antes_do_render():
    cenas = [_cena('gancho', 0, 5, 'a0.jpg', real=True, grupo=0),                     # única outra foto: saiu há < 4 s
             _cena('historia', 5, 8, 'a2.jpg', real=True, grupo=1),
             _cena('historia', 8, 16, 'a2.jpg', repetida=True, grupo=2),
             _cena('fechamento', 16, 22, 'a2.jpg', _fundo_fechamento=True, grupo=3)]
    avisos = main._sem_repeticao_longa(cenas)
    assert cenas[2].get('img') is None and cenas[2]['pendente'] == 'repeticao'
    assert cenas[2]['hf']['nome'] == 'vox-annotate'                                   # frase narrada, nada inventado
    assert avisos and 'cena 2' in avisos[0]
    assert not any('mesma imagem' in e for e in main.erros_basicos(cenas, []))


def test_foto_propria_longa_nao_e_trocada():
    cenas = [_cena('historia', 0, 6, 'a1.jpg', real=True, grupo=0),
             _cena('historia', 6, 12, 'a2.jpg', real=True, grupo=1),
             _cena('historia', 12, 18, 'a2.jpg', real=True, grupo=1, sub=1)]               # mesma ideia: detalhe da foto
    antes = [c['img'] for c in cenas]
    main._sem_repeticao_longa(cenas)
    assert [c['img'] for c in cenas] == antes


# ───────────── 3) TTS sem instrução no texto falado ─────────────
ROTEIRO = 'Um navio gigante sobe 26 metros sem guindaste algum.'


def _gravar(monkeypatch, falhas=0):
    """Força o caminho REST (o SDK falha) e grava o que seria enviado à API."""
    from src import gemini as g
    enviados = []
    monkeypatch.setattr(g, 'cliente', lambda: (_ for _ in ()).throw(RuntimeError('sem sdk')))
    monkeypatch.setattr(g, 'CHAVES', ['k'])
    monkeypatch.setattr(voz.time, 'sleep', lambda s: None)

    def rest(modelo, texto, vz, formato, chave='', sistema=None):
        enviados.append({'texto': texto, 'sistema': sistema})
        if sistema and len([e for e in enviados if e['sistema']]) <= falhas:
            raise RuntimeError('400 INVALID_ARGUMENT: system_instruction is not supported')
        return b'\x00\x00' * 2400
    monkeypatch.setattr(voz, '_rest_tts', rest)
    return enviados


def test_coringa_texto_falado_e_so_o_roteiro(monkeypatch, tmp_path):
    enviados = _gravar(monkeypatch)
    voz.gemini_tts(ROTEIRO, tmp_path / 'v.wav', 'Charon', 'narrador de documentário, voz grave e firme', estilo_separado=True)
    falado = enviados[-1]['texto']
    assert falado == voz.pronuncia(ROTEIRO)
    for proibido in ('Narre', 'Leia', 'narrador', 'linha', '---'):
        assert proibido not in falado
    assert 'voz grave' in enviados[-1]['sistema']                                     # o tom vai FORA do texto


def test_modelo_sem_instrucao_de_sistema_repete_so_com_o_roteiro(monkeypatch, tmp_path):
    enviados = _gravar(monkeypatch, falhas=1)
    voz.gemini_tts(ROTEIRO, tmp_path / 'v.wav', 'Charon', 'voz grave', estilo_separado=True)
    assert enviados[0]['sistema'] and enviados[-1]['sistema'] is None
    assert all(e['texto'] == voz.pronuncia(ROTEIRO) for e in enviados)                # nunca a instrução no texto


def test_coringa_usa_estilo_separado_e_ntc_continua_igual(monkeypatch, tmp_path):
    vistos = []
    monkeypatch.setenv('GEMINI_API_KEY', 'x')
    monkeypatch.setattr(voz, '_narrar_gemini', lambda cenas, pasta, cfg: vistos.append(cfg['_estilo_separado']) or ('w', [], [], 1))
    voz.narrar([{'fala': ROTEIRO}], tmp_path)                       # Coringa (sem cfg)
    voz.narrar([{'fala': ROTEIRO}], tmp_path, cfg={'voz_gemini': 'Kore'})   # NTC (cfg próprio)
    assert vistos == [True, False]
    texto, sistema = voz.pedido_tts(ROTEIRO, 'tom', separado=False)
    assert texto.startswith('Narre em português') and sistema is None         # pedido do NTC inalterado
