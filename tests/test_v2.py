"""Testes do sistema audiovisual V2 (ramo visual-v2). Sem IA, sem rede (os mapas precisam do Natural Earth baixado
por scripts/v2_natural_earth.py; sem ele, os testes de mapa são pulados com aviso).

Teste automático NÃO é aprovação visual: a aprovação é do Heitor, pela galeria (python -m src.v2.galeria).
"""
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw

from src.v2 import acervo_v2, capacidades, fatos, fiscal_v2, galeria, montagem, palco, regressao

RAIZ = Path(__file__).resolve().parents[1]
TEM_NE = (RAIZ / 'src' / 'render' / 'v2' / 'dados' / 'ne' / 'paises10.json').exists()
TEM_CHROME = shutil.which('ffmpeg') is not None
try:
    from src.v2 import manim_cenas
    TEM_MANIM = manim_cenas.disponivel()
except Exception:
    TEM_MANIM = False


def _pula(mid):
    return (mid.startswith('mapa.') and not TEM_NE) or (mid == 'animacao.quadros' and not TEM_MANIM)
OBRIGATORIAS = ['abertura.pergunta', 'abertura.revelacao', 'banner.discreto', 'banner.importante', 'lower_third', 'numero.animado',
                'comparacao.grandezas', 'comparacao.antes_depois', 'mapa.localizacao', 'mapa.rota', 'mapa.territorio', 'linha_tempo.historica',
                'foto.historica', 'foto.sequencia', 'grafico.barras', 'grafico.temporal', 'diagrama.explicativo', 'mecanismo.eclusa',
                'processo.etapas', 'revelacao.surpresa', 'fonte.evidencia', 'encerramento.editorial']
CAMPOS = ['id', 'nome', 'objetivo', 'params', 'layout', 'paleta', 'animacao', 'duracao', 'limites', 'area_segura', 'legibilidade', 'rejeicao', 'exemplo', 'legenda', 'tratamento']


@pytest.fixture(scope='module')
def catalogo(tmp_path_factory):
    return galeria.catalogo(tmp_path_factory.mktemp('cat'))


# ---------------- catálogo ----------------
def test_catalogo_tem_as_22_obrigatorias_e_mais_de_20(catalogo):
    ids = {m['id'] for m in catalogo}
    assert len(ids) >= 20
    assert not set(OBRIGATORIAS) - ids, set(OBRIGATORIAS) - ids


def test_cada_composicao_declara_tudo_que_a_ordem_pede(catalogo):
    for m in catalogo:
        faltam = [c for c in CAMPOS if not m.get(c)]
        assert not faltam, f"{m['id']}: faltam {faltam}"
        assert len(m['duracao']) == 3 and m['duracao'][0] <= m['duracao'][1] <= m['duracao'][2], m['id']
        assert m['legenda'] in ('livre', 'integrada', 'normal', 'oculta'), m['id']


def test_tratamentos_variados_nao_so_cartao_escuro(catalogo):
    trat = {m['tratamento'] for m in catalogo}
    assert {'documental', 'dado', 'mapa', 'ciencia', 'arquivo'} <= trat
    assert sum(1 for m in catalogo if m.get('tom') == 'claro') >= 4          # infográficos em papel claro


# ---------------- render de cada composição (exemplo da galeria) ----------------
def _render_ok(meta, tmp):
    regressao._midia_repo()
    d = galeria.dados_exemplo(meta)
    with palco.abrir(palco.preparar(d), tmp / meta['id']) as pg:
        geo = palco.medir(pg, d['duration'], 0.25)
        erros = pg.erros + pg.evaluate('V2.avisos')
    return geo, erros


def test_exemplos_sem_erro_e_sem_texto_sobre_texto(catalogo, tmp_path):
    falhas = []
    for m in catalogo:
        if _pula(m['id']):
            continue
        geo, erros = _render_ok(m, tmp_path)
        graves = fiscal_v2._persistentes([g for g in geo if g.get('grave')])
        if erros or graves:
            falhas.append((m['id'], erros[:2], [g['txt'] for g in graves][:3]))
    assert not falhas, falhas


# ---------------- regressão visual ----------------
def test_regressao_visual_contra_referencias(catalogo, tmp_path):
    metas = [m for m in catalogo if not _pula(m['id'])]
    res = regressao.verificar(metas, tmp_path)
    falhas = [r for r in res if not r['ok']]
    assert not falhas, falhas


def test_regressao_detecta_mudanca_real(catalogo, tmp_path):
    """O detector precisa pegar uma mudança visual de verdade (outro valor no número → outra imagem)."""
    m = json.loads(json.dumps(next(x for x in catalogo if x['id'] == 'numero.animado')))
    m['exemplo']['params']['valor'] = 9876
    m['exemplo']['params']['unidade'] = 'toneladas'
    t, im = next(iter(regressao.quadros(m, tmp_path).items()))
    ref = Image.open(regressao.arquivo('numero.animado', t)).convert('RGB')
    assert not regressao.comparar(im, ref)['ok']


# ---------------- legenda contextual ----------------
def test_legenda_some_so_quando_redundante(tmp_path):
    def estado(fala):
        d = {'duration': 3, 'meta': {}, 'scenes': [{'comp': 'abertura.pergunta', 'start': 0, 'end': 3, 'params': {'kicker': 'X', 'pergunta': 'Quem levanta este *navio*?', 'contexto': ''}}],
             'captions': galeria.legendas_sinteticas(fala, 0, 3, por_bloco=8)}
        with palco.abrir(palco.preparar(d), tmp_path / str(abs(hash(fala)))) as pg:
            pg.evaluate('seek(1.5)')
            return pg.evaluate('estadoV2(1.5)')
    assert estado('Quem levanta este navio?')['legenda'] is False             # repete a pergunta da tela
    e = estado('Ninguém empurra, mas ele sobe vinte e seis metros')
    assert e['legenda'] is True, e                                            # informação nova: legenda fica


# ---------------- direção por acontecimento ----------------
@pytest.mark.parametrize('fala,comp', [
    ('Então a câmara *enche* e o navio sobe junto com a água.', 'mecanismo.eclusa'),
    ('O navio entra numa câmara e a comporta de trás fecha.', 'mecanismo.eclusa'),
    ('A maré sobe 16 metros.', 'mecanismo.nivel'),
    ('A Terra gira em torno do Sol.', 'astronomia.orbita'),
])
def test_acontecimento_escolhe_composicao_que_mostra(fala, comp):
    ctx = 'canal eclusa navio' if comp == 'mecanismo.eclusa' else ''
    assert capacidades.escolher({'fala': fala}, {}, ctx)['comp'] == comp


def test_acontecimento_critico_sem_dados_vira_limitacao_explicita():
    r = capacidades.escolher({'fala': 'A explosão derrubou as árvores'}, {})
    assert r['comp'] is None and r['critica'] and 'evento.impacto' in r['limitacao']
    r = capacidades.escolher({'fala': 'A explosão derrubou as árvores'}, {'aneis': [{'raio_km': 10, 'rotulo': 'x'}]})
    assert r['comp'] == 'evento.impacto'


def test_lugar_comum_continua_foto_real():
    assert capacidades.escolher({'fala': 'No meio do caminho há um lago,', 'acontecimento': {'recurso': 'lugar'}}, {})['comp'] == 'foto.documental'


def test_escala_usa_referencias_conhecidas_na_mesma_unidade():
    p = capacidades.escala_com_referencias(26)
    assert p['unidade'] == 'm' and any(x['valor'] == 26 for x in p['itens']) and len(p['itens']) >= 3
    assert all(26 / 14 <= x['valor'] <= 26 * 1.6 for x in p['itens'])


# ---------------- precisão factual ----------------
FONTES = ['Wikipédia', 'Wikipedia (inglês)', 'Revista Oeste', 'Wikimedia Commons']


def test_o_erro_do_panama_e_bloqueado():
    e = ' | '.join(fatos.validar(fatos.PANAMA_ERRADO, FONTES))
    for cod in ('F1', 'F3', 'F4', 'F5'):
        assert cod in e, e


def test_o_valor_correto_passa_e_mostra_moeda_original():
    assert fatos.validar(fatos.PANAMA_LEILAO, FONTES) == []
    p = fatos.para_tela(fatos.PANAMA_LEILAO)
    assert p['prefixo'] == 'US$' and 'LEILÃO' in p['natureza'] and 'conversao' not in p


def test_conversao_exige_data_e_confere_a_conta():
    v = dict(fatos.PANAMA_LEILAO, conversao={'moeda': 'BRL', 'valor': 28.6, 'taxa': 5.4, 'fonte': 'Revista Oeste'})
    assert any('data' in e for e in fatos.validar(v, FONTES))
    v['conversao']['data'] = '01/09/2026'
    assert fatos.validar(v, FONTES) == []
    v['conversao']['valor'] = 27
    assert any('não confere' in e for e in fatos.validar(v, FONTES))


# ---------------- acervo ----------------
def _cartao(tmp, nome='cartao.jpg'):
    """Foto (com textura) colada num cartão preto liso com etiqueta branca — o caso da foto de 1913."""
    rng = np.random.default_rng(1)
    im = Image.new('RGB', (1200, 1000), (12, 12, 12))
    foto = Image.fromarray((rng.random((120, 1000, 3)) * 255).astype('uint8'))
    im.paste(foto, (100, 450))
    ImageDraw.Draw(im).rectangle((480, 700, 720, 760), fill=(240, 240, 240))
    p = tmp / nome
    im.save(p, quality=92)
    return p


def test_recorte_tira_cartao_do_scanner(tmp_path):
    r = acervo_v2.recorte_conteudo(_cartao(tmp_path))
    assert abs(r[0] - 100 / 1200) < .03 and abs(r[2] - 1100 / 1200) < .03 and abs(r[1] - .45) < .03 and abs(r[3] - .57) < .03, r
    assert acervo_v2.enquadramento(_cartao(tmp_path))['modo'] == 'historica'


def test_foto_comum_nao_e_recortada():
    assert acervo_v2.recorte_conteudo(RAIZ / 'tests' / 'img' / 'fundo_b.jpg') == [0.0, 0.0, 1.0, 1.0]


def test_hash_perceptual_pega_copia_redimensionada(tmp_path):
    a = RAIZ / 'tests' / 'img' / 'fundo_b.jpg'
    b = tmp_path / 'b.jpg'
    Image.open(a).resize((540, 450)).save(b, quality=70)
    assert acervo_v2.distancia(acervo_v2.phash(a), acervo_v2.phash(b)) <= 6
    assert acervo_v2.distancia(acervo_v2.phash(a), acervo_v2.phash(RAIZ / 'tests' / 'img' / 'fundo_d.jpg')) > 10


def test_licenca_nc_e_nd_fora():
    assert not acervo_v2.licenca({'credito': 'foto (CC BY-NC 2.0) via Flickr'})['ok']
    assert acervo_v2.licenca({'credito': '"x" — fulano (CC BY-SA 4.0), via Wikimedia Commons'})['ok']


def test_relevancia_rebaixa_generica_para_cena_especifica():
    cena = {'fala': 'O SS Ancon fez a primeira travessia', 'acontecimento': {'quem': 'navio SS Ancon', 'onde': 'Miraflores', 'quando': '1914', 'recurso': 'foto'}}
    certa = {'titulo': 'SS Ancon at Miraflores locks', 'ano': 1914, 'w': 1800, 'h': 1200}
    generica = {'titulo': 'container ship', 'mostra': 'navio cargueiro moderno', 'ano': 2019, 'generica': True, 'w': 1800, 'h': 1200}
    assert acervo_v2.relevancia(certa, cena)['nota'] > acervo_v2.LIMIAR > acervo_v2.relevancia(generica, cena)['nota']


# ---------------- montagem e fiscal ----------------
def _panama_min():
    falas = [('gancho', 'Ninguém empurra este navio, mas ele sobe *26 metros*.'), ('historia', 'O navio entra numa câmara e a *comporta* de trás fecha.'),
             ('historia', 'Então a câmara *enche*'), ('historia', 'e o navio sobe junto com a água.'), ('historia', 'Quando o nível iguala, a *comporta da frente* se abre.'),
             ('numero', 'Um navio chegou a pagar *R$ 27 milhões* para passar.'), ('fechamento', 'Segue o *Coringa Explica*.')]
    sc, t = [], 0.0
    for tp, f in falas:
        s = {'tipo': tp, 'fala': f, 'start': t, 'end': t + 3, 'bloco': {'funcao': 'mecanismo' if tp == 'historia' else ''}}
        if tp == 'gancho':
            s.update(titulo='QUEM LEVANTA ESTE *NAVIO*?', subtitulo='Canal do Panamá, 26 metros')
        if tp == 'numero':
            s.update(valor='27', prefixo='R$ ', sufixo=' milhões', rotulo='pagos por um navio para atravessar', nota='recorde com El Niño')
        sc.append(s)
        t += 3
    return {'duration': t, 'meta': {'titulo': 'Como um navio sobe 26 metros sem bomba?', 'categoria': 'MUNDO', 'fontes': FONTES}, 'scenes': sc, 'captions': []}


def test_montagem_junta_o_mecanismo_numa_composicao_com_etapas():
    v2, dr = montagem.converter(_panama_min())
    mec = [s for s in v2['scenes'] if s['comp'] == 'mecanismo.eclusa']
    assert len(mec) == 1 and mec[0]['origem'] == [1, 2, 3, 4]
    t = mec[0]['params']['tempos']
    assert t[0] == 0 and t[1] == 3.0 and t[2] == 9.0 and mec[0]['params']['desnivel_m'] == 26


def test_montagem_bloqueia_numero_sem_verificacao_e_aceita_correcao():
    v2, dr = montagem.converter(_panama_min())
    assert any(d.get('bloqueio') for d in dr)
    v2, dr = montagem.converter(_panama_min(), fatos_corrigidos={5: fatos.PANAMA_LEILAO})
    assert not any(d.get('bloqueio') for d in dr)
    assert any(s['comp'] == 'numero.animado' and s['params']['prefixo'] == 'US$' for s in v2['scenes'])


def test_fiscal_v2_reprova_mecanismo_trocado_por_foto_e_aprova_o_v2():
    d = _panama_min()
    antigo = {'scenes': [{**s, 'comp': 'foto.documental', 'origem': [i], 'params': {}} for i, s in enumerate(d['scenes'])], 'captions': []}
    r = fiscal_v2.avaliar(antigo, [{'comp': 'foto.documental'} for _ in d['scenes']], [], d)
    assert sum(1 for b in r['bloqueios'] if b['codigo'] == 'B2') == 4 and not r['aprovado_tecnicamente']
    v2, dr = montagem.converter(d, fatos_corrigidos={5: fatos.PANAMA_LEILAO})
    r = fiscal_v2.avaliar(v2, dr, [], d)
    assert not [b for b in r['bloqueios'] if b['codigo'] == 'B2']
    assert 'sem nota automática' in r['subjetivo']['estado']


def test_montagem_converte_todos_os_tipos_do_roteiro_para_composicoes_que_existem(catalogo):
    ids = {m['id'] for m in catalogo}
    tipos = [{'tipo': 'lista', 'titulo': 'X', 'itens': ['a', 'b']}, {'tipo': 'cards', 'itens': [{'rotulo': 'a', 'valor': '1'}]},
             {'tipo': 'linha_tempo', 'itens': [{'ano': 1900, 'texto': 'a'}, {'ano': 1950, 'texto': 'b'}]}, {'tipo': 'citacao', 'texto': 'x', 'autor': 'y'},
             {'tipo': 'comparacao', 'itens': [{'rotulo': 'a', 'valor': 1}, {'rotulo': 'b', 'valor': 2}], 'fonte': 'Wikipédia'},
             {'tipo': 'revelacao', 'pergunta': 'p?', 'resposta': 'R'}, {'tipo': 'mapa', 'pontos': [{'nome': 'a', 'lon': 1, 'lat': 2}]}]
    d = {'duration': 30, 'meta': {'fontes': FONTES}, 'captions': [], 'scenes': [{**s, 'fala': 'x', 'start': i * 3, 'end': i * 3 + 3} for i, s in enumerate(tipos)]}
    v2, _ = montagem.converter(d)
    assert all(s['comp'] in ids for s in v2['scenes']), [s['comp'] for s in v2['scenes']]


# ---------------- integração com o render (vídeo curto, sem IA) ----------------
@pytest.mark.skipif(not TEM_CHROME, reason='sem ffmpeg')
def test_render_v2_gera_video_pelo_mesmo_pipeline(tmp_path):
    from src.render import render
    audio = tmp_path / 'a.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=mono', '-t', '2', str(audio)], check=True)
    d = {'duration': 2.0, 'meta': {'motor': 'v2'}, 'captions': [],
         'scenes': [{'comp': 'titulo.capitulo', 'start': 0, 'end': 2, 'params': {'numero': '01', 'titulo': 'Teste', 'subtitulo': 'render v2'}}]}
    saida = render.renderizar(d, audio, tmp_path / 'v.mp4', tmp_path / 'tr', workers=1)
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=width,height', '-of', 'json', str(saida)], capture_output=True, text=True).stdout
    j = json.loads(out)
    assert abs(float(j['format']['duration']) - 2.0) < .2 and j['streams'][0]['width'] == 1080


def test_ntc_intocado():
    r = subprocess.run(['git', 'diff', '--name-only', 'origin/main...HEAD'], cwd=RAIZ, capture_output=True, text=True)
    mudou = r.stdout.split() + subprocess.run(['git', 'status', '--porcelain'], cwd=RAIZ, capture_output=True, text=True).stdout.split()
    assert not [x for x in mudou if 'ntc' in x.lower() and not x.startswith('tests/v2_referencias')]
