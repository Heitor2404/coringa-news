"""Acervo V4 com as fontes do acervo herdado substituídas (sem rede): chama as fontes com as consultas, escolhe com
licença, baixa e preenche o asset; sem candidato registra 'sem_midia' sem quebrar (erro da execução 43954670866)."""
from pathlib import Path

from PIL import Image

from src import acervo
from src.v4 import acervo_v4


def test_acervo_chama_fontes_com_consultas_e_monta(tmp_path, monkeypatch):
    vistos = []
    img = tmp_path / 'src.jpg'
    Image.new('RGB', (1600, 1200), (90, 100, 110)).save(img)

    def commons(q):
        vistos.append(('commons', tuple(q)))
        return [{'titulo': 'Miraflores', 'desc': 'navio na eclusa', 'ano': 2010, 'url': 'http://x/a.jpg', 'w': 1600, 'h': 1200,
                 'credito': '"Miraflores" — Fulano (CC BY-SA 4.0), via Wikimedia Commons'}]

    def videos(q):
        vistos.append(('videos', tuple(q)))
        return []

    monkeypatch.setattr(acervo, 'f_commons', commons)
    monkeypatch.setattr(acervo, 'f_videos', videos)
    monkeypatch.setattr(acervo, '_baixar_item', lambda x, arq: dict(x, arq=str(img)))
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    ep = {'cenas': [{'id': 'c1', 'params': {'asset': 'auto'}, 'busca': {'tipo': 'foto', 'consultas_en': ['Miraflores Locks ship']}},
                    {'id': 'c2', 'params': {'asset': 'auto'}, 'busca': {'tipo': 'video', 'consultas_en': ['Panama locks video']}}]}
    acv, reg = acervo_v4.montar(ep, tmp_path / 'acervo')
    assert ('commons', ('Miraflores Locks ship',)) in vistos and ('videos', ('Panama locks video',)) in vistos
    assert ep['cenas'][0]['params']['asset'] == 'a1' and acv['a1']['licenca'] == 'CC BY-SA 4.0'
    assert ep['cenas'][1]['params']['asset'] is None and reg[1]['estado'] == 'sem_midia'
    assert (tmp_path / 'acervo' / 'acervo.json').exists()
