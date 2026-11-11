"""Casos para o FISCAL DA TELA: reproduzem vídeos que já saíram com texto em cima de texto.

Cada caso devolve `dados` no formato do template (meta, scenes, captions, duration), com imagens geradas na hora.
Usado pelo pytest (tests/test_tela.py) e para conferir à mão:  python -m tests.caso_tela  (mostra o que o fiscal achou).
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def _foto(pasta: Path, nome: str, w: int, h: int, cor: tuple) -> str:
    from PIL import Image, ImageDraw
    arq = pasta / f'{nome}.jpg'
    im = Image.new('RGB', (w, h), cor)
    d = ImageDraw.Draw(im)
    for k in range(0, w, 40):                    # textura, para o desfoque do fundo ter o que mostrar
        d.line([(k, 0), (k + h // 2, h)], fill=tuple(min(255, c + 40) for c in cor), width=6)
    im.save(arq, 'JPEG', quality=85)
    return str(arq)


def _clipe(pasta: Path, n: int = 130) -> dict:
    """Quadros de um 'vídeo' deitado 960x540 (uma faixa clara andando), sem precisar de ffmpeg."""
    from PIL import Image, ImageDraw
    pasta.mkdir(parents=True, exist_ok=True)
    for k in range(1, n + 1):
        im = Image.new('RGB', (960, 540), (40, 70, 110))
        x = (k * 20) % 960
        ImageDraw.Draw(im).rectangle([x, 0, x + 120, 540], fill=(230, 200, 120))
        im.save(pasta / f'f_{k:04d}.jpg', 'JPEG', quality=80)
    return {'dir': str(pasta), 'n': n}


def _inserir(dados: dict, antes_de: str, cena: dict, dur: float, fala: str) -> dict:
    """Põe `cena` antes da 1ª cena do tipo `antes_de`, empurrando o resto (cenas e legendas) `dur` segundos."""
    k = next(i for i, c in enumerate(dados['scenes']) if c['tipo'] == antes_de)
    t0 = dados['scenes'][k]['start']
    for c in dados['scenes'][k:]:
        c['start'] += dur; c['end'] += dur
    for c in dados['captions']:
        if c['start'] >= t0:
            c['start'] += dur; c['end'] += dur
            for w in c['words']:
                w['s'] += dur
    dados['scenes'].insert(k, dict(cena, start=t0, end=t0 + dur))
    dados['captions'] += _legendas([(t0, t0 + dur, fala)])
    dados['captions'].sort(key=lambda c: c['start'])
    dados['duration'] += dur
    return dados


def _legendas(falas: list[tuple[float, float, str]]) -> list[dict]:
    """[(início, fim, 'texto da frase')] → legendas palavra a palavra, em blocos de até 3 palavras (como a voz faz)."""
    caps = []
    for a, b, txt in falas:
        ws = txt.split()
        passo = (b - a) / len(ws)
        for k in range(0, len(ws), 3):
            bloco = ws[k:k + 3]
            s0 = a + k * passo
            caps.append({'start': round(s0, 3), 'end': round(s0 + len(bloco) * passo, 3),
                         'words': [{'w': w.strip('*'), 's': round(s0 + j * passo, 3), 'hl': w.startswith('*')}
                                   for j, w in enumerate(bloco)]})
    return caps


def coober_pedy(pasta: Path, com_mapa: bool = True) -> dict:
    """O vídeo de 10/11/2026: título + legenda no gancho, 'picos de 50°C' com cartão por cima, linha do tempo
    encostando na legenda, 'COOBER PEDY · 1915' em cima da etiqueta da foto e o cartão final repetido na legenda."""
    pasta.mkdir(parents=True, exist_ok=True)
    f1 = _foto(pasta, 'cidade', 1024, 683, (150, 120, 90))
    f2 = _foto(pasta, 'museu', 800, 600, (170, 140, 100))
    f3 = _foto(pasta, 'passaro', 1600, 1200, (60, 90, 150))
    f4 = _foto(pasta, 'igreja', 900, 600, (120, 60, 40))
    f5 = _foto(pasta, 'rua', 1200, 800, (160, 110, 80))
    moldura = lambda f, wh, et: {'img': f, 'real': True, 'moldura': True, 'foto_wh': list(wh), 'etiqueta': et,
                                 'img_fundo': f}
    cenas = [
        {'tipo': 'gancho', 'start': 0.0, 'end': 3.0, 'titulo': 'Opalas *subterrâneas*: riqueza escondida',
         'subtitulo': 'Deserto escaldado', 'moldura_gancho': True, **moldura(f1, (1024, 683), 'FOTO · 2005')},
        {'tipo': 'historia', 'start': 3.0, 'end': 7.5, 'lugar': 'Coober Pedy · 1915', 'fala': 'Em *1915* a descoberta',
         **moldura(f2, (800, 600), 'FOTO · 2002')},
        {'tipo': 'numero', 'start': 7.5, 'end': 12.5, 'img': f3, 'rotulo': 'Temperatura no deserto', 'valor': 50,
         'prefixo': 'picos de', 'sufixo': '°C', 'nota': 'Calor extremo no verão',
         'comparacao': 'Calor sufocante no deserto australiano'},
        {'tipo': 'historia', 'start': 12.5, 'end': 17.0, 'destaque': 'Igrejas e *bares*', 'real': True,
         'fala': 'Escavaram igrejas', **moldura(f4, (900, 600), 'FOTO · 2003')},
        {'tipo': 'linha_tempo', 'start': 17.0, 'end': 23.0, 'img': f5, 'titulo': 'Evolução da cidade',
         'itens': [{'ano': '1915', 'texto': 'Descoberta de opalas'}, {'ano': '1920', 'texto': 'Nome Coober Pedy'},
                   {'ano': '1987', 'texto': 'Eleições do governo local'}]},
        {'tipo': 'revelacao', 'start': 23.0, 'end': 28.0, 'img': f5, 'pergunta': 'Cidade subterrânea?',
         'resposta': 'VERDADE', 'detalhe': 'Escavada para fugir dos 50°C no deserto'},
        {'tipo': 'fechamento', 'start': 28.0, 'end': 32.0, 'img': f5},
    ]
    if com_mapa:
        cenas.insert(3, {'tipo': 'mapa', 'start': 12.5, 'end': 12.5, 'rotulo': '846 km de distância', 'pais': 'Australia',
                         'pontos': [{'nome': 'Coober Pedy', 'lon': 134.75, 'lat': -29.01},
                                    {'nome': 'Adelaide', 'lon': 138.6, 'lat': -34.93}]})
        cenas[3]['end'] = 15.0                       # o mapa entra antes das igrejas: empurra o resto 2,5 s
        for c in cenas[4:]:
            c['start'] += 2.5; c['end'] += 2.5
    falas = [(0.3, 3.0, 'Opalas reluzentes sob 50°C de deserto'), (3.0, 7.5, 'Em *1915* a descoberta de opalas preciosas mudou a região'),
             (7.5, 12.5, 'No verão o deserto atinge picos sufocantes de *50°C*')]
    off = 2.5 if com_mapa else 0.0
    if com_mapa:
        falas.append((12.5, 15.0, 'Essa cidade fica a *846* quilômetros da capital Adelaide'))
    falas += [(12.5 + off, 17.0 + off, 'Debaixo da terra escavaram *igrejas* hotéis lojas e até bares'),
              (17.0 + off, 23.0 + off, 'A partir dos anos *1960* a opala rendeu milhões de dólares e a população superou 3 mil no deserto australiano'),
              (23.0 + off, 28.0 + off, 'O refúgio subterrâneo virou uma atração turística mundial'),
              (28.0 + off, 32.0 + off, 'Segue o Coringa Explica')]
    dados = {'duration': 32.0 + off,
             'meta': {'titulo': 'Coober Pedy: a cidade embaixo da terra', 'categoria': 'CIÊNCIA', 'marca': '@coringa.explica',
                      'pergunta': '', 'fontes': ['Wikipédia (português)', 'Wikipédia (inglês)']},
             'scenes': cenas, 'captions': _legendas(falas)}
    # 3º vídeo de 10/11: "MAIS DE … MORADORES" (prefixo e sufixo longos juntados com reticências)
    dados = _inserir(dados, 'linha_tempo', {'tipo': 'numero', 'img': f5, 'rotulo': 'Habitantes subterrâneos', 'valor': 3000,
                                            'prefixo': 'Mais de', 'sufixo': 'moradores', 'nota': 'metade vive em dugouts',
                                            'comparacao': 'Quase todos debaixo da terra'},
                     4.0, 'Mais de *3.000* moradores vivem debaixo da terra')
    # v35: VÍDEO EM MOVIMENTO deitado, dentro da moldura, com a etiqueta ▶ VÍDEO e um lugar escrito em cima
    clipe = _clipe(pasta / 'clipe')
    f0 = str(Path(clipe['dir']) / 'f_0001.jpg')
    return _inserir(dados, 'linha_tempo', {'tipo': 'historia', 'video': clipe, 'img': f0, 'img_fundo': f0, 'moldura': True,
                                           'foto_wh': [960, 540], 'etiqueta': '▶ VÍDEO · 2019', 'lugar': 'Deserto australiano'},
                    4.0, 'Do alto o deserto em volta da cidade parece outro planeta')


def exemplo(nome: str, trab: Path) -> dict:
    """Um roteiro de tests/exemplo_*.json montado pelo MESMO caminho da produção (main._montar_cenas), com a duração
    de cada fala estimada (0,36 s por palavra) em vez de voz de verdade — para o fiscal da tela, basta."""
    import json
    import main
    from src import voz
    v = json.loads((RAIZ / 'tests' / nome).read_text(encoding='utf-8'))
    imgs = {i['id']: RAIZ / i['arquivo'] for i in v.get('imagens', []) if i.get('arquivo') and not i.get('video')}
    reais = {i['id']: {'tipo': 'video' if i.get('video') else 'foto', 'arq': RAIZ / i['arquivo']}
             for i in v.get('imagens', []) if i.get('arquivo') and (i.get('video') or i.get('real'))}
    t, tempos, caps = voz.INICIO, [], []
    for c in v['cenas']:
        limpo = c['fala'].replace('*', '')
        dur = 0.36 * len(limpo.split()) + 0.3
        pal = voz.alinhar(voz._estimar(limpo, dur), c['fala'])
        for p in pal:
            p['start'] += t; p['end'] += t
        caps += voz.legendas(pal, voz.destaques(c['fala']))
        tempos.append((t, t + dur + voz.PAUSA))
        t += dur + voz.PAUSA
    cenas = main._montar_cenas(v, reais, imgs, tempos, trab)
    return {'duration': round(t + 0.5, 3), 'scenes': cenas, 'captions': caps,
            'meta': {'titulo': v['titulo'], 'categoria': v.get('categoria', ''), 'marca': '@coringa.explica',
                     'serie': v.get('serie', ''), 'parte': v.get('parte', 0), 'pergunta': main._pergunta_fixa(v),
                     'fontes': v.get('fontes', [])[:3]}}


def tem_mapa() -> bool:
    return (RAIZ / 'node_modules' / 'd3-geo' / 'dist' / 'd3-geo.min.js').exists()


if __name__ == '__main__':
    import tempfile
    from src.render.render import fiscal_tela, preparar
    with tempfile.TemporaryDirectory() as tmp:
        d = preparar(coober_pedy(Path(tmp) / 'img', com_mapa=tem_mapa()))
        erros = fiscal_tela(d, Path(tmp))
        print('cap_baixo:', d['cap_baixo'])
        print('ERROS:', erros or 'nenhum')
