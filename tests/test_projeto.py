"""Testes rápidos: não usam internet nem chaves de API. Rodar com:  pytest"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
EXEMPLOS = sorted((RAIZ / 'tests').glob('exemplo_*.json'))
CAMPOS = {'titulo', 'categoria', 'legenda_post', 'hashtags', 'fontes', 'imagens', 'cenas'}


def test_codigo_importa():
    """Pega erro de sintaxe ou import quebrado em qualquer módulo."""
    import main  # noqa: F401
    from src import fontes, gemini, imagens, pautas, roteiro, voz, wiki  # noqa: F401
    from src.render import render  # noqa: F401


def test_slug():
    import main
    assert main.slug('O Irã vai fazer a bomba?') == 'o-ira-vai-fazer-a-bomba'
    assert len(main.slug('a' * 200)) <= 50


@pytest.mark.parametrize('arq', EXEMPLOS, ids=lambda p: p.name)
def test_exemplo_tem_formato_esperado(arq):
    v = json.loads(arq.read_text(encoding='utf-8'))
    assert CAMPOS <= set(v), f'faltam campos: {CAMPOS - set(v)}'
    ids = {im['id'] for im in v['imagens']}
    for c in v['cenas']:
        assert c['fala'].strip()
        assert c.get('imagem') is None or c['imagem'] in ids or c['tipo'] != 'imagem'
    for im in v['imagens']:
        if im.get('arquivo'):
            assert (RAIZ / im['arquivo']).exists(), f'imagem não existe: {im["arquivo"]}'


def test_assets_existem():
    assert (RAIZ / 'assets' / 'mascote.svg').exists()
    assert list((RAIZ / 'assets' / 'musica').rglob('*.mp3')), 'nenhuma música em assets/musica'
    assert list((RAIZ / 'assets' / 'img').iterdir()), 'assets/img vazia'


def test_jsons_de_dados_sao_validos():
    for arq in [RAIZ / 'config.json', *(RAIZ / 'data').rglob('*.json')]:
        json.loads(arq.read_text(encoding='utf-8'))


def test_historico_descarta_pautas_com_mais_de_10_dias(tmp_path, monkeypatch):
    from src import pautas
    monkeypatch.setattr(pautas, 'HIST', tmp_path / 'historico.json')
    agora = datetime.now(timezone.utc)
    pautas.salvar_historico({
        'recente': (agora - timedelta(days=2)).isoformat(),
        'antiga': (agora - timedelta(days=11)).isoformat(),
    })
    assert set(pautas.carregar_historico()) == {'recente'}


def test_etiqueta_de_musica_normaliza_valores():
    from src.etiquetar_musicas import validar
    assert validar({'clima': 'Tenso', 'energia': 'media', 'descricao': 'x'}) == {'clima': 'tenso', 'energia': 'média', 'descricao': 'x'}
    assert validar({'clima': 'SERIO', 'energia': 'ALTA', 'descricao': ''})['clima'] == 'sério'


def test_etiqueta_invalida_nao_descarta_a_musica():
    from src.etiquetar_musicas import validar
    r = validar({'clima': 'triste', 'energia': 'altíssima', 'descricao': 'piano'})
    assert (r['clima'], r['energia']) == ('neutro', 'média')
    assert r['descricao'].startswith('revisar:')


def test_env_example_lista_as_variaveis_usadas_no_codigo():
    import re
    usadas = set()
    for arq in [RAIZ / 'main.py', *(RAIZ / 'src').rglob('*.py')]:
        usadas |= set(re.findall(r"(?:getenv|environ(?:\.get)?)[(\[]\s*'([A-Z][A-Z0-9_]+)'", arq.read_text(encoding='utf-8')))
    doc = (RAIZ / '.env.example').read_text(encoding='utf-8')
    faltam = {v for v in usadas if not re.search(rf'^#?\s*{v}=', doc, re.M)}
    assert not faltam, f'variáveis usadas no código e ausentes do .env.example: {sorted(faltam)}'


def test_musicas_json_cobre_as_musicas_da_pasta():
    """Só vale depois de rodar src.etiquetar_musicas; antes disso o arquivo não existe e o teste é ignorado."""
    from src.etiquetar_musicas import ARQ, PASTA, validar
    if not ARQ.exists():
        pytest.skip('musicas.json ainda não foi gerado')
    tags = json.loads(ARQ.read_text(encoding='utf-8'))
    assert set(tags) == {m.name for m in PASTA.glob('*.mp3')}, 'musicas.json fora de sincronia com a pasta'
    for t in tags.values():
        validar(t)
