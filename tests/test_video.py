"""VÍDEO EM MOVIMENTO (v35): clipes entram no acervo, o editor escolhe foto ou vídeo, o clipe deitado vai na moldura."""
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]


def _jpg(arq: Path, w: int = 960, h: int = 540, cor=(90, 120, 160)) -> Path:
    from PIL import Image
    Image.new('RGB', (w, h), cor).save(arq, 'JPEG')
    return arq


def test_clipes_pequenos_ou_curtos_ficam_fora(monkeypatch):
    """Só entra clipe nítido no celular: deitado com 720+ linhas, em pé com 1280+, e com pelo menos 3 s."""
    from src import acervo, midia
    def clipe(nome, w, h, dur):
        return {'tipo': 'video', 'url': f'https://x/{nome}.mp4', 'thumb': f'https://x/{nome}.jpg', 'descricao': nome,
                'credito': '', 'w': w, 'h': h, 'dur': dur}
    monkeypatch.setattr(midia, 'candidatos_arquivo', lambda q: [clipe('bom', 1920, 1080, 12), clipe('pequeno', 640, 360, 12)])
    monkeypatch.setattr(midia, 'candidatos_pixabay', lambda q: [clipe('curto', 1920, 1080, 2), clipe('empe', 1080, 1920, 8),
                                                                clipe('empe_baixo', 720, 1280 - 2, 8)])
    nomes = [x['titulo'] for x in acervo.f_videos(['Coober Pedy'])]
    assert sorted(nomes) == ['bom', 'empe']
    x = next(c for c in acervo.f_videos(['Coober Pedy']) if c['titulo'] == 'bom')
    assert x['url'].endswith('.jpg') and x['video']['url'].endswith('.mp4')     # baixa só a miniatura no acervo


def test_cada_video_entra_em_uma_ideia_so(monkeypatch):
    """Foto e vídeo: cada um em UMA ideia só (11/11: a mesma molécula apareceu 3 vezes)."""
    from src import acervo, gemini
    acv = [{'id': 'a0', 'mostra': 'deserto visto do alto', 'mini': b'', 'video': {'url': 'u', 'w': 1920, 'h': 1080}},
           {'id': 'a1', 'mostra': 'placa da cidade', 'mini': b''}]
    v = {'cenas': [{'tipo': 'historia', 'fala': f'frase {k}'} for k in range(4)]}
    monkeypatch.setattr(gemini, 'json_visao', lambda *a, **k: {'escolhas': [
        {'ideia': 0, 'foto': 'a0'}, {'ideia': 1, 'foto': 'a1'}, {'ideia': 2, 'foto': 'a0'}, {'ideia': 3, 'foto': 'a1'}]})
    acervo.casar(v, acv)
    assert [c.get('foto') for c in v['cenas']] == ['a0', 'a1', None, None]


def test_texto_do_acervo_marca_video():
    from src import acervo
    t = acervo.texto([{'id': 'a0', 'mostra': 'mina de opala'}, {'id': 'a1', 'mostra': 'deserto', 'video': {'url': 'u'}}])
    assert 'a1: [VÍDEO EM MOVIMENTO] deserto' in t and '[VÍDEO' not in t.splitlines()[0]


def test_video_deitado_ganha_moldura_e_etiqueta(tmp_path):
    import main
    f = _jpg(tmp_path / 'f_0001.jpg')
    cenas = [{'tipo': 'historia', 'start': 0, 'end': 4, 'img': str(f), 'video': {'dir': str(tmp_path), 'n': 1},
              'video_moldura': True, 'ano_foto': 2019}]
    main._acabamento(cenas)
    c = cenas[0]
    assert c['moldura'] and c['foto_wh'] == [960, 540]
    assert c['etiqueta'] == '▶ VÍDEO · 2019'
    assert Path(c['img_fundo']).exists()


def test_video_em_pe_continua_tela_cheia(tmp_path):
    import main
    f = _jpg(tmp_path / 'f_0001.jpg', 720, 1280)
    cenas = [{'tipo': 'historia', 'start': 0, 'end': 4, 'img': str(f), 'video': {'dir': str(tmp_path), 'n': 1},
              'video_moldura': False}]
    main._acabamento(cenas)
    assert not cenas[0].get('moldura') and not cenas[0].get('etiqueta')


@pytest.mark.skipif(not shutil.which('ffmpeg'), reason='sem ffmpeg')
def test_quadros_da_moldura_nao_cortam_o_video(tmp_path):
    """Na moldura o quadro guarda a proporção do clipe (largura 960), em vez do corte vertical 720x1280."""
    from PIL import Image
    from src import midia
    clipe = tmp_path / 'c.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc=size=1280x720:rate=30:duration=3',
                    '-pix_fmt', 'yuv420p', str(clipe)], check=True)
    n = midia.quadros(clipe, 1.0, tmp_path / 'm', moldura=True)
    assert n >= 30
    assert Image.open(tmp_path / 'm' / 'f_0001.jpg').size == (960, 540)
    midia.quadros(clipe, 1.0, tmp_path / 'v')
    assert Image.open(tmp_path / 'v' / 'f_0001.jpg').size == (720, 1280)


def test_template_troca_quadros_dentro_da_moldura():
    html = (RAIZ / 'src' / 'render' / 'template.html').read_text(encoding='utf-8')
    assert "sc.video&&sc.moldura" in html and 'class="foto vid"' in html


def test_baixar_cria_a_pasta(tmp_path, monkeypatch):
    """O clipe escolhido é salvo em tmp/<vídeo>/midia, que ainda não existe quando o acervo é usado (bug de 10/11:
    'No such file or directory' e o vídeo em movimento caía para foto vizinha)."""
    from src import midia
    class R:
        content = b'video'
        def raise_for_status(self):
            pass
    monkeypatch.setattr(midia.requests, 'get', lambda *a, **k: R())
    destino = tmp_path / 'nao' / 'existe' / 'v_a5.mp4'
    assert midia._baixar('https://x/v.mp4', destino).read_bytes() == b'video'


@pytest.mark.parametrize('titulo,estilo', [
    ('O fungo que transforma formigas em zumbis', 'estudio'), ('A tempestade de estrelas cadentes de 1833', 'ceu'),
    ('Por que a Lua se afasta da Terra', 'ceu'), ('astronautas na ISS', 'ceu'), ('A lua de mel mais cara', 'estudio'),
    ('O solo mais fértil do mundo', 'estudio'), ('Coober Pedy: a cidade embaixo da terra', 'estudio'),
])
def test_fundo_escolhido_pelo_tema(titulo, estilo):
    from src.midia import estilo_fundo
    assert estilo_fundo(titulo) == estilo


@pytest.mark.parametrize('estilo', ['estudio', 'ceu'])
def test_fundo_escuro_sem_mancha(tmp_path, estilo):
    """A (estúdio) e B (céu): escuros nas bordas, luz no meio, 540x960; nada do borrão bege de antes."""
    from PIL import Image, ImageStat
    from src.midia import fundo
    f = Image.open(fundo(_jpg(tmp_path / 'g.jpg', 800, 600, (150, 150, 150)), estilo))
    assert f.size == (540, 960)
    borda = ImageStat.Stat(f.crop((0, 880, 540, 960))).mean
    meio = ImageStat.Stat(f.crop((200, 350, 340, 450))).mean
    assert max(borda) < 40 and sum(meio) > sum(borda) + 30


def test_etiqueta_sem_traco_sobrando():
    from src.midia import _legenda
    assert _legenda('Leonids-, 1844', 1844) == 'Leonids, 1844'


def test_foto_generica_que_nao_e_exata_sai(monkeypatch):
    """11/11: vaso qualquer numa frase sobre múmias — foto genérica e não exata não entra."""
    from src import acervo, gemini
    acv = [{'id': 'a0', 'mostra': 'vaso de vidro', 'mini': b'', 'generica': True},
           {'id': 'a1', 'mostra': 'lago vermelho', 'mini': b''}]
    v = {'cenas': [{'tipo': 'historia', 'fala': 'os egípcios mumificavam'}, {'tipo': 'historia', 'fala': 'o lago'}]}
    monkeypatch.setattr(gemini, 'json_visao', lambda *a, **k: {'escolhas': [
        {'ideia': 0, 'foto': 'a0', 'exata': False}, {'ideia': 1, 'foto': 'a1', 'exata': True}]})
    acervo.casar(v, acv)
    assert [c.get('foto') for c in v['cenas']] == [None, 'a1']


def test_buraco_pega_reserva_video_primeiro():
    """11/11 (tardígrados): 7 frases sem imagem com 8 reservas sobrando."""
    from src import acervo
    acv = [{'id': 'a0', 'mostra': 'x'}, {'id': 'a1', 'mostra': 'foto', 'nota': 9},
           {'id': 'a2', 'mostra': 'clipe', 'video': {'url': 'u'}, 'generica': True}, {'id': 'a3', 'mostra': 'ruim', 'util': False}]
    v = {'cenas': [{'tipo': 'historia', 'fala': 'f0', 'foto': 'a0'}, {'tipo': 'historia', 'fala': 'f1'},
                   {'tipo': 'historia', 'fala': 'f2'}, {'tipo': 'historia', 'fala': 'f3'}]}
    acervo.preencher(v, acv)
    assert [c.get('foto') for c in v['cenas']] == ['a0', 'a2', 'a1', None]
