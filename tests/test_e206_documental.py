"""E206: tests offline, no claim of real acquisition or license review."""
import io
import hashlib
from PIL import Image
from src.v4.formatos import garimpo_visual as G


def _page(lic='CC BY 4.0', size=100, url='https://upload.wikimedia.org/wikipedia/commons/a/a1/Nature.jpg'):
    return {'title': 'File:Nature landscape.jpg', 'imageinfo': [{
        'url': url, 'descriptionurl': 'https://commons.wikimedia.org/wiki/File:Nature.jpg',
        'size': size, 'width': 800, 'height': 800, 'mime': 'image/jpeg',
        'extmetadata': {'LicenseShortName': {'value': lic}, 'Artist': {'value': 'Fixture author'}}}]}


def test_licenca_exata_e_origem():
    def search(q, video):
        return [_page('CC BY-SA 4.0'), _page('CC BY-NC 4.0'),
                _page(url='https://example.com/Nature.jpg'), _page()]
    out, erros = G.candidatos_documentais(['nature'], False, search)
    assert len(out) == 1 and not erros and out[0]['licenca'] == 'CC BY 4.0'
    assert out[0]['estado'] == 'CANDIDATO_SEM_INSPECAO'


def test_aquisicao_foto_preserva_bytes_sem_homologar(tmp_path):
    f = io.BytesIO()
    Image.new('RGB', (800, 800), 'blue').save(f, 'JPEG')
    raw = f.getvalue()
    def search(q, video):
        return [] if video else [_page(size=len(raw))]
    n = {'id': 'r', 'modalidade_proposta': 'registro_real',
         'pesquisa': {'consultas': ['nature']}, 'estado': 'PESQUISAR_MIDIA'}
    m = {'id': 'm', 'modalidade_proposta': 'mapa_atlas', 'estado': 'SOLICITAR_ATLAS'}
    r = G.pesquisar_triagem([n, m], tmp_path, search, lambda url: raw)
    a = r['adquiridos'][0]
    assert a['sha256_origem'] == hashlib.sha256(raw).hexdigest()
    assert (tmp_path / 'originais' / a['arquivo']).read_bytes() == raw
    assert not a['identidade_e_acao_confirmadas'] and not a['direitos_revisados'] and not a['publicar']
    assert [x['estado'] for x in r['resultados']] == ['REVISAO_MIDIA_PENDENTE', 'SOLICITAR_ATLAS']


def test_falha_na_origem_nao_vira_animacao(tmp_path):
    n = {'id': 'r', 'modalidade_proposta': 'registro_real',
         'pesquisa': {'consultas': ['nature']}, 'estado': 'PESQUISAR_MIDIA'}
    r = G.pesquisar_triagem([n], tmp_path,
                            lambda q, video: [] if video else [_page()],
                            lambda url: b'errado')
    assert not r['adquiridos']
    assert r['resultados'][0]['estado'] == 'PESQUISA_SEM_BYTES'
    assert r['resultados'][0]['falhas']
