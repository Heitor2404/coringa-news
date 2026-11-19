"""Garimpo visual reaproveita Commons/visão existentes e não aceita prova cega."""
import io

from PIL import Image

from src.v4.formatos.garimpo_visual import _licenca, procurar, coletar


def _imagem():
    im = Image.new('RGB', (900, 900), '#789abc')
    out = io.BytesIO()
    im.save(out, 'JPEG')
    return out.getvalue()


def _cands(_):
    return [{'url': 'https://example.org/origem.jpg',
             'w': 900, 'h': 900, 'titulo': 'chip físico',
             'credito': 'Fotógrafo X (CC BY 4.0), Wikimedia Commons'}]


def _escolher(cands, deve, usados, consultas):
    return cands[0], {'prova': 'PROVADO', 'motivo': 'objeto central aparece',
                      'local_confere': True, 'objeto_confere': True,
                      'roi': [0.1, 0.1, 0.8, 0.8]}


def _brief():
    return {'id': 'b1', 'consultas_en': ['silicon integrated circuit closeup'],
            'deve_mostrar': 'chip real com circuitos visíveis'}


def test_recusa_midias_sem_licenca_simples():
    assert _licenca('Autor (CC BY-NC 4.0)') is None
    assert _licenca('Autor (CC BY-SA 4.0)') is None
    assert _licenca('Autor (CC BY 4.0)') == 'CC BY 4.0'


def test_pesquisa_escolhe_por_visao_e_hash_sem_inventar():
    o, status = procurar(_brief(), set(), _cands, _escolher, lambda _: _imagem())
    assert status['estado'] == 'CANDIDATO_VERIFICADO'
    assert len(o[0]['sha256_origem']) == 64
    assert o[0]['uso_provisorio_previa'] is True


def test_visao_indisponivel_nao_vira_aprovacao():
    o, status = procurar(_brief(), set(), _cands, lambda *_: (None, {'prova': 'INCERTO'}),
                        lambda _: _imagem())
    assert o is None and status['estado'] == 'SEM_MIDIA'


def test_coleta_provisoria_gera_manifesto_e_contato(tmp_path):
    r = coletar([_brief()], tmp_path, _cands, _escolher, lambda _: _imagem())
    assert len(r['itens']) == 1
    assert (tmp_path / 'contato.jpg').exists()
    assert (tmp_path / 'catalogo.json').exists()
    import hashlib
    item = r['itens'][0]
    originais = list((tmp_path / 'originais').glob(item['sha256_origem'] + '.*'))
    assert len(originais) == 1
    assert hashlib.sha256(originais[0].read_bytes()).hexdigest() == item['sha256_origem']
