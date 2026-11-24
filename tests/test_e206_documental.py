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


def test_e208_diagnostico_de_rejeicao():
    d = []
    out, falhas = G.candidatos_documentais(['nature'], False,
        lambda q, video: [_page('CC BY-SA 4.0'), _page()], d)
    assert len(out) == 1 and not falhas
    assert d[0]['retornados_api'] == 2 and d[0]['recusados']['licenca_ou_autor'] == 1


def test_e208_fonte_institucional_sem_homologar(tmp_path):
    fonte = {'url': 'https://www.fws.gov/sites/default/files/images/fixture.jpg',
             'pagina': 'https://www.fws.gov/media/fixture', 'autor': 'Fixture',
             'titulo': 'Fixture', 'mostra': 'Fixture', 'licenca': 'PUBLIC DOMAIN',
             'evidencia_licenca': 'Fixture de teste, não licença real'}
    f = io.BytesIO()
    Image.new('RGB',(800,800),'blue').save(f,'JPEG')
    raw = f.getvalue()
    n = {'id': 'r', 'modalidade_proposta': 'registro_real',
         'pesquisa': {'consultas': ['nature']}, 'estado': 'PESQUISAR_MIDIA'}
    r = G.pesquisar_triagem([n], tmp_path, lambda q,video: [], lambda url: raw,
                            fontes_institucionais={'r':[fonte]})
    assert len(r['adquiridos']) == 1 and r['adquiridos'][0]['provedor'] == 'FWS'
    assert not r['adquiridos'][0]['direitos_revisados']
    import pytest
    with pytest.raises(ValueError,match='E208-FONTE'):
        G.candidato_institucional({**fonte, 'url':'https://example.com/x.jpg'})


def test_e207_narracao_nao_omite_modalidade():
    from src.v4.formatos import ciclo_e202 as C
    p={'cenas':[{'modalidade':m,'beats':[{'fala':m}]} for m in
       ('registro_real','mapa_atlas','cena_declarativa')]}
    assert C._falas(p)==['registro_real','mapa_atlas','cena_declarativa']


def test_e207_audio_hash_tempo_privado_e_cobertura(tmp_path):
    import wave, pytest
    from src.v4.formatos import diretor_visual_e202 as D
    folder=tmp_path/'e202'
    folder.mkdir()
    wav=folder/'voz.wav'
    with wave.open(str(wav),'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(8000); w.writeframes(bytes(2)*16000)
    sha=hashlib.sha256(wav.read_bytes()).hexdigest()
    # bytes de fixture são silêncio: o teste verifica contrato, não fala.
    target=folder/(sha+'.wav')
    wav.rename(target)
    asset='e202/'+sha+'.wav'
    p={'preview':True,'private_review_only':True,'duracao':2.,
       'shots':[{'id':'r','type':'photo','start':0.,'end':1.},
                {'id':'m','type':'atlas_map','start':1.,'end':2.}]}
    gs=[{'start':.1,'end':.9,'words':[{'w':'a','hl':True}]},
        {'start':1.1,'end':1.9,'words':[{'w':'b','hl':True}]}]
    r=D.anexar_audio_documental(p,asset,gs,tmp_path,'FRASES_MEDIDAS_LAB')
    assert r['scene_narration_asset']==asset
    with pytest.raises(ValueError,match='E207-CENA-SEM-LEGENDA'):
        D.anexar_audio_documental(p,asset,gs[:1],tmp_path,'FRASES_MEDIDAS_LAB')
    with pytest.raises(ValueError,match='E207-PRIVADO'):
        D.anexar_audio_documental({**p,'private_review_only':False},asset,gs,tmp_path,'FRASES_MEDIDAS_LAB')
    with pytest.raises(ValueError,match='E207-HASH'):
        D.anexar_audio_documental(p,'e202/'+'0'*64+'.wav',gs,tmp_path,'FRASES_MEDIDAS_LAB')


def test_e209_retimar_sem_esticar_video_ou_mapa(tmp_path):
    import json,pytest
    from src.v4.formatos import diretor_visual_e202 as D
    proof=tmp_path/'proof.json';proof.write_text(json.dumps({'duracao_s':3.0}))
    p={'cenas':[{'id':'r','modalidade':'registro_real','beats':[{}]},
                {'id':'a','modalidade':'cena_declarativa','beats':[{}]},
                {'id':'m','modalidade':'mapa_atlas','beats':[{}]}]}
    d={'shots':[{'id':'r','type':'video','asset':'v','start':0.,'end':3.,'source_in_seconds':1.,'cues':[{'at':.5}]},
                {'id':'m','type':'atlas_map','asset':'m','start':3.,'end':6.}],
       'media':{'v':{'duration_s':5.},'m':{'atlas_proof':str(proof)}},'duracao':6.}
    r=D.retimar_documental(p,d,[2.,4.,3.])
    assert r['duracao']==5. and r['shots'][1]['start']==2.
    assert r['shots'][0]['source_in_seconds']==1. and r['shots'][0]['cues']==d['shots'][0]['cues']
    assert d['duracao']==6.
    with pytest.raises(ValueError,match='E209-VIDEO-CURTO'):
        D.retimar_documental(p,d,[5.,4.,3.])
    with pytest.raises(ValueError,match='E209-ATLAS-RETIMAR'):
        D.retimar_documental(p,d,[2.,4.,5.])
