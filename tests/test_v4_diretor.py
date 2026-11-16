import json

from src.v4 import diretor


def test_claude_falha_cai_para_gemini_uma_vez(monkeypatch):
    from src import claude, gemini
    monkeypatch.setattr(claude, 'disponivel', lambda: True)
    def falha(p, leve=False):
        raise RuntimeError("Claude (sonnet): You've hit your 5-hour limit")
    monkeypatch.setattr(claude, 'pedir', falha)
    chamadas = []
    monkeypatch.setattr(gemini, 'texto', lambda p, leve=False: chamadas.append(1) or json.dumps({'titulo': 't', 'cenas': []}))
    r = diretor.pedir({'pergunta': 'x', 'fatos': [], 'alvo_duracao': [75, 90]})
    assert chamadas == [1] and r['_origem'] == 'gemini (queda)'


def test_reproducao_do_roteiro_cifrado(tmp_path, monkeypatch):
    from src.v3 import material
    monkeypatch.setenv('CHECKPOINT_KEY', 'segredo-de-teste')
    pub = material.publica(material._segredo())
    arq = tmp_path / 'r.bin'
    arq.write_bytes(material.cifrar(pub, json.dumps({'titulo': 'ok', 'cenas': [{'id': 'c1'}]}).encode()))
    r = diretor.pedir({'roteiro_ia_cifrado': str(arq), 'roteiro_ia_origem': 'execução X'})
    assert r['cenas'] == [{'id': 'c1'}] and 'execução X' in r['_origem']
