"""Fonte NASA: original + hash medido; sem transformar a descrição em fato visual."""
import copy
import hashlib
import json
from pathlib import Path

import pytest
from src.v4.formatos import prospeccao_video_nasa as N

ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/'docs/v4/formatos/CANDIDATOS_ACAO_NASA_SVS_20261120.json'


def item():
    return json.loads(FILE.read_text())['itens'][0]


def test_fonte_oficial_e_exemplo_independente_do_catalogo_anterior():
    x=item()
    N.validar_origem(x)
    assert x['provedor']=='nasa_svs'
    assert x['aprovacao_editorial'] is False
    assert x['expected_sha256'] is None
    assert 'curiosity' in x['id']


def test_arquivo_so_e_verificado_apos_bytes_serem_lidos(tmp_path):
    x=item()
    data=b'a'*250000
    proof=N.baixar(x,tmp_path/'original.mp4',fetch=lambda url:data)
    assert proof['sha256']==hashlib.sha256(data).hexdigest()
    assert proof['integridade']=='BAIXADO_E_MEDIDO_SEM_HASH_PUBLICADO'
    assert (tmp_path/'original.mp4').read_bytes()==data


def test_nova_versao_com_hash_diferente_e_recusada(tmp_path):
    x=item()
    x['expected_sha256']='a'*64
    with pytest.raises(ValueError,match='N-SHA'):
        N.baixar(x,tmp_path/'no.mp4',fetch=lambda _:b'a'*250000)
    assert not (tmp_path/'no.mp4').exists()


@pytest.mark.parametrize('url',[
    'http://svs.gsfc.nasa.gov/vis/file.mp4',
    'https://evil.example.org/vis/file.mp4',
    'https://svs.gsfc.nasa.gov.evil.net/vis/file.mp4',
    'https://svs.gsfc.nasa.gov/vis/a.mp4?auth=1',
    'https://svs.gsfc.nasa.gov/other/file.mp4',
])
def test_download_somente_na_origem_institucional(url):
    x=item()
    x['download']=url
    with pytest.raises(ValueError,match='N-URL'):
        N.validar_origem(x)


def test_direitos_privados_nunca_sao_promovidos_para_publicacao():
    x=item()
    x['aprovacao_editorial']=True
    with pytest.raises(ValueError,match='N-GATE'):
        N.validar_origem(x)


def test_licenca_nao_e_inferida_pela_fala_ou_pelo_titulo():
    x=item()
    assert x['credito']=='NASA/JPL-Caltech'
    assert x['aprovacao_editorial'] is False
    assert x.get('acao_observada_comprovada') is not True
    assert x.get('publicar') is not True
