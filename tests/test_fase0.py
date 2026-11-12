"""Fase 0 da auditoria do Coringa (12/11/2026): livro-caixa de custo, detector de trechos estáticos e fiscal sombra.
Nenhuma chamada real de IA: o Claude Code e o Gemini são falsos."""
import json
import subprocess
import types
from pathlib import Path

import pytest

from src import claude, custo, estaticos, fiscal


@pytest.fixture(autouse=True)
def limpo():
    custo.zerar()
    yield
    custo.zerar()


def _claude_falso(monkeypatch, respostas):
    """Cada chamada do `claude -p` devolve o próximo JSON da lista."""
    fila = list(respostas)
    monkeypatch.setattr(claude.shutil, 'which', lambda _: '/bin/claude')
    monkeypatch.setenv('CLAUDE_CODE_OAUTH_TOKEN', 'x')
    monkeypatch.setattr(claude, '_falhas', 0)

    def run(cmd, **kw):
        return types.SimpleNamespace(stdout=json.dumps(fila.pop(0)), stderr='', returncode=0)
    monkeypatch.setattr(claude.subprocess, 'run', run)


def _resp(usd, entrada=1000, saida=300, erro=False):
    return {'type': 'result', 'is_error': erro, 'result': '' if erro else '{"ok": 1}', 'total_cost_usd': usd,
            'usage': {'input_tokens': entrada, 'cache_creation_input_tokens': 9000, 'cache_read_input_tokens': 0,
                      'output_tokens': saida}}


# ───────── livro-caixa ─────────
def revisar():          # mesmo nome da função da crítica no roteiro: o livro descobre a etapa pelo nome de quem pediu
    return claude.pedir('p')


def escolher_gancho():
    return claude.pedir('p')


def test_livro_registra_etapa_tokens_e_custo(monkeypatch):
    _claude_falso(monkeypatch, [_resp(0.05), _resp(0.02, saida=50)])
    revisar()
    escolher_gancho()
    a, b = custo.LIVRO
    assert (a['etapa'], a['usd'], a['entrada'], a['cache_escrita'], a['saida']) == ('crítica', 0.05, 1000, 9000, 300)
    assert b['etapa'] == 'ganchos' and custo.claude_usd() == 0.07
    assert custo.por_etapa()['crítica']['chamadas'] == 1


def test_tentativas_de_tema_e_descartado_aparece(monkeypatch):
    _claude_falso(monkeypatch, [_resp(0.04), _resp(0.10), _resp(0.06)])
    with custo.etapa('pauta'):
        claude.pedir('p')                      # antes de qualquer tema
    custo.tentativa('tema A')
    revisar()                                  # tema A (descartado)
    custo.tentativa('tema B')
    revisar()
    assert [x['tentativa'] for x in custo.LIVRO] == [0, 1, 2]
    linha = custo.linha_telegram()
    assert '≈USD 0.20 estimado' in linha and 'cobrança em dinheiro: USD 0' in linha and 'descartado(s) USD 0.10' in linha and 'maior etapa: crítica' in linha


def test_chamada_que_falha_tambem_entra_no_livro(monkeypatch):
    _claude_falso(monkeypatch, [_resp(0.03, erro=True)])
    with pytest.raises(RuntimeError):
        revisar()
    assert custo.LIVRO[0]['ok'] is False and custo.claude_usd() == 0.03


def test_gemini_conta_separado_e_gratis(monkeypatch):
    from src import gemini
    monkeypatch.setattr(gemini, 'CHAVES', ['x'])
    monkeypatch.setattr(gemini.time, 'sleep', lambda s: None)
    gemini._tentar(lambda m: {'ok': 1}, ['gemini-teste'])
    assert custo.LIVRO[0]['ia'] == 'gemini' and custo.LIVRO[0]['usd'] == 0 and custo.claude_usd() == 0
    assert 'Gemini (grátis) 1 chamada' in custo.linha_telegram()


def test_tabela_e_arquivo(tmp_path, monkeypatch):
    _claude_falso(monkeypatch, [_resp(0.05)])
    revisar()
    assert 'TOTAL Claude USD 0.0500' in custo.tabela()
    custo.salvar(tmp_path / 'c.json')
    d = json.loads((tmp_path / 'c.json').read_text())
    assert d['claude_usd_estimado'] == 0.05 and d['cobranca_efetiva_usd'] == 0 and d['chamadas'][0]['etapa'] == 'crítica'


# ───────── trechos estáticos ─────────
def _cenas(*planos):
    out, t = [], 0.0
    for img, dur, tipo in planos:
        out.append({'imagem': img, 'img': img, 'start': t, 'end': t + dur, 'tipo': tipo})
        t += dur
    return out


def test_mesma_imagem_reenquadrada_conta_como_parada():
    # a mesma foto em 3 planos seguidos (reenquadrada) = 7,5 s parada; depois troca a cada 2 s
    c = _cenas(('a', 2.5, 'historia'), ('a', 2.5, 'historia'), ('a', 2.5, 'historia'), ('b', 2, 'historia'), ('c', 2, 'historia'))
    m = estaticos.medir_cenas(c)
    assert m['estaticos'] == [(0.0, 7.5, 7.5)] and m['imagens'] == 3


def test_infografico_conta_como_mudanca():
    c = _cenas(('a', 3, 'historia'), ('a', 3, 'numero'), ('a', 3, 'historia'))
    assert estaticos.medir_cenas(c)['estaticos'] == []


def _video(tmp_path, cores):
    """Vídeo sintético: uma cor por trecho (cor, segundos)."""
    partes = []
    for k, (cor, dur) in enumerate(cores):
        arq = tmp_path / f'p{k}.mp4'
        fonte = f'{cor}=s=216x384:d={dur}:r=10' if cor in ('testsrc', 'smptebars') else f'color=c={cor}:s=216x384:d={dur}:r=10'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', fonte,
                        '-pix_fmt', 'yuv420p', str(arq)], check=True)
        partes.append(arq)
    lista = tmp_path / 'l.txt'
    lista.write_text(''.join(f"file '{p}'\n" for p in partes))
    out = tmp_path / 'v.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(lista), '-c', 'copy', str(out)], check=True)
    return out


def test_detector_no_arquivo_acha_o_trecho_parado(tmp_path):
    v = _video(tmp_path, [('red', 6), ('smptebars', 2), ('testsrc', 2)])
    m = estaticos.medir(v)
    assert m['imagens'] == 3 and len(m['estaticos']) == 1 and m['estaticos'][0][2] >= 5.5


# ───────── fiscal sombra ─────────
V = {'titulo': 'Ötzi', 'fatos': 'Em 2013 acharam 19 parentes vivos.',
     'cenas': [{'tipo': 'gancho', 'fala': 'Um assassinato de 5.300 anos'},
               {'tipo': 'historia', 'fala': 'A vítima tem descendentes.'},
               {'tipo': 'fechamento', 'fala': 'Segue'}]}


def _pedir(resposta):
    return lambda prompt: resposta


BASE = 'fatos: {fatos} | frases: {frases} | título: {titulo}'


def test_sombra_pesos_bloqueador_separado_e_nao_decide():
    resp = {'fatos': {'nota': 17, 'problemas': [{'frase': 2, 'tipo': 'erro_grave', 'explicacao': 'são parentes, não descendentes'}]},
            'narrativa': {'nota': 12}, 'recursos': {'faltou': []}}
    cenas = _cenas(('a', 3, 'gancho'), ('b', 3, 'historia'))
    r = fiscal.sombra(V, cenas, None, nota_imagem=6, pedir=_pedir(resp), prompt_base=BASE)
    assert r['partes']['imagem'] == 12 and r['partes']['fatos'] == 17 and r['partes']['recursos'] == 5
    assert r['bloqueadores'] == ['frase 2: são parentes, não descendentes']       # fora da média, separado
    assert 'audio' in r['nao_medido']                                              # sem vídeo: não medido, sem chute
    medidos = {k: p for k, p in r['partes'].items() if p is not None}
    assert r['nota'] == round(10 * sum(medidos.values()) / sum(fiscal.PESOS[k] for k in medidos), 1)
    assert any('bloqueador' in x for x in fiscal.linhas_telegram(r))


def test_sombra_recurso_so_tira_ponto_quando_era_necessario():
    resp = {'fatos': {'nota': 25}, 'narrativa': {'nota': 15},
            'recursos': {'faltou': [{'frase': 1, 'recurso': 'mapa', 'necessario': False},
                                    {'frase': 2, 'recurso': 'mapa', 'necessario': True, 'por_que': 'fronteira'}]}}
    r = fiscal.sombra(V, _cenas(('a', 3, 'gancho')), None, nota_imagem=None, pedir=_pedir(resp), prompt_base=BASE)
    assert r['partes']['recursos'] == 3.5


def test_sombra_sem_prompt_no_cofre_nao_inventa(monkeypatch):
    from src import cofre
    monkeypatch.setattr(cofre, 'prompt', lambda nome: f'[{nome}: texto guardado no cofre privado]')
    r = fiscal.sombra(V, _cenas(('a', 3, 'gancho')), None, nota_imagem=8)
    assert set(r['nao_medido']) >= {'fatos', 'narrativa', 'recursos'} and r['nota'] is not None


def test_sombra_ritmo_cai_com_imagem_parada_e_repeticao():
    boa = _cenas(('a', 2, 'historia'), ('b', 2, 'historia'), ('c', 2, 'historia'))
    ruim = _cenas(('a', 8, 'historia'), ('b', 2, 'historia'), ('a', 2, 'historia'))
    assert fiscal.nota_ritmo(boa)[0] == 15 and fiscal.nota_ritmo(ruim)[0] < 8


def test_pode_postar_continua_o_mesmo():
    """O fiscal sombra não mexe na decisão: _qualidade continua só com a nota antiga."""
    import main
    q = main._qualidade({'cenas': [{'tipo': 'historia', 'fala': 'a b'}]}, [{'tipo': 'historia', 'imagem': 'i'}],
                        {'i': {'tipo': 'foto'}}, 6.0, 60)
    assert q['motivos'] == []


# ───────── condições do Heitor para subir (12/11) ─────────
def test_sem_chamada_duplicada(monkeypatch):
    """Uma linha por chamada real: 3 pedidos (1 falha) = 3 linhas; falha do Claude + Gemini de reserva = 2 chamadas reais."""
    _claude_falso(monkeypatch, [_resp(0.01), _resp(0.01, erro=True), _resp(0.01)])
    revisar()
    with pytest.raises(RuntimeError):
        revisar()
    revisar()
    assert len(custo.LIVRO) == 3 and [x['ok'] for x in custo.LIVRO] == [True, False, True]
    assert claude.GASTO['pedidos'] >= 2


def test_livro_caixa_nunca_quebra_a_producao(monkeypatch):
    monkeypatch.setattr(custo, '_registrar', lambda *a, **k: 1 / 0)
    custo.registrar('claude', 'sonnet', 0.1)            # não levanta


def test_sombra_desiste_no_limite_de_tempo_sem_segurar(monkeypatch):
    import time as _t
    monkeypatch.setattr(fiscal, 'LIMITE_TEXTO_S', 0.3)
    t0 = _t.time()
    r = fiscal.sombra(V, _cenas(('a', 3, 'gancho')), None, nota_imagem=8,
                      pedir=lambda p: _t.sleep(5), prompt_base=BASE)
    assert _t.time() - t0 < 2 and 'fatos' in r['nao_medido'] and r['nota'] is not None
    assert any('falhou' in o for o in r['obs'].get('texto', []))


def test_sombra_nao_roda_com_pouco_tempo_na_rodada(monkeypatch):
    from src import orcamento
    monkeypatch.setattr(orcamento, 'sobra', lambda: 5)
    r = fiscal.sombra(V, _cenas(('a', 3, 'gancho')), None, nota_imagem=8, pedir=lambda p: 1 / 0, prompt_base=BASE)
    assert r['nota'] is None and fiscal.linhas_telegram(r) == []
