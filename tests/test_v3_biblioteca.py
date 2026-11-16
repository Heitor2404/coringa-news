"""V3.1 — Biblioteca Coringa: ids estáveis, deduplicação (sha e pHash), reuso de regiões entre vídeos, licença, IA,
manifesto portátil, recuperação verificada por hash e limpeza segura."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from PIL import Image

from src.v3 import biblioteca as B

IMG = Path(__file__).parent / 'piloto_ever_given' / 'img'


def _bib(tmp_path, nome='b'):
    return B.Biblioteca(tmp_path / f'{nome}.sqlite3', tmp_path / f'{nome}_arm')


META = {'titulo': 'Ever Given container ship', 'desc': 'ship in the canal', 'mostra': 'navio porta-contêineres no Canal de Suez',
        'ano': 2021, 'url': 'https://upload.wikimedia.org/x.jpg', 'credito': '"Ever Given" — Fulano (CC BY-SA 2.0), via Wikimedia Commons',
        'lugar': 'Canal de Suez', 'tipo_img': 'foto'}


def test_migracao_idempotente_e_id_estavel(tmp_path):
    b = _bib(tmp_path)
    assert b.versao() == len(B.MIGRACOES)
    b.migrar()
    r = b.ingerir(IMG / 'a23-g.jpg', META, video='v1', alias='a10')
    assert r['id'].startswith('cm-') and r['id'] == f"cm-{r['sha256'][:12]}" and r['reuso'] is None
    d = b.obter(r['id'])
    assert d['uso_comercial'] == 'sim' and d['licenca'] == 'CC BY-SA' and d['autor'] == 'Fulano' and d['largura'] > 0


def test_mesmo_arquivo_em_outro_video_reusa_registro_e_regioes(tmp_path):
    b = _bib(tmp_path)
    r1 = b.ingerir(IMG / 'a23-g.jpg', META, video='video-1', alias='a10')
    chamadas = []

    def visao(prompt, imgs):
        chamadas.append(prompt)
        return {'foco': {'box_2d': [100, 100, 900, 900]}, 'objetos': [{'objeto': 'navio', 'visivel': True, 'box_2d': [300, 200, 700, 800], 'confianca': 'alta'}]}
    f1 = b.localizar(IMG / 'a23-g.jpg', ['navio'], visao)
    assert f1['objetos']['navio']['ancoravel'] and len(chamadas) == 1
    r2 = b.ingerir(IMG / 'a23-g.jpg', {**META, 'titulo': ''}, video='video-2', alias='a3')     # outro vídeo, outro alias
    assert r2['id'] == r1['id'] and r2['reuso'] == 'sha'
    f2 = b.localizar(IMG / 'a23-g.jpg', ['navio'], visao)                                   # NENHUMA chamada nova
    assert len(chamadas) == 1 and f2['objetos']['navio']['caixa'] == f1['objetos']['navio']['caixa']
    assert b.estat['regioes_reusadas'] == 1
    assert {u['video'] for u in b.usos(r1['id'])} == {'video-1', 'video-2'}
    assert b.con.execute('SELECT COUNT(*) FROM midia').fetchone()[0] == 1


def test_quase_igual_vira_variante(tmp_path):
    b = _bib(tmp_path)
    r1 = b.ingerir(IMG / 'a23-g.jpg', META)
    menor = tmp_path / 'menor.jpg'
    Image.open(IMG / 'a23-g.jpg').resize((540, 360)).save(menor, quality=70)
    r2 = b.ingerir(menor, META)
    assert r2['reuso'] == 'quase' and b.obter(r2['id'])['variante_de'] == r1['id']


def test_ia_e_licenca_fora_da_busca(tmp_path):
    b = _bib(tmp_path)
    b.ingerir(IMG / 'a23-g.jpg', META)
    b.ingerir(IMG / 'a1-g.jpg', {**META, 'desc': 'ship ai generated image', 'credito': 'Pixabay (CC0)'})
    b.ingerir(IMG / 'a6-g.jpg', {**META, 'credito': 'Fulano (CC BY-NC 2.0)'})
    b.ingerir(IMG / 'a27-g.jpg', {**META, 'credito': 'Fulano'})                               # licença não identificada
    achou = b.buscar('navio Canal de Suez')
    assert len(achou) == 1 and achou[0]['uso_comercial'] == 'sim' and not achou[0]['ia']
    todos = {d['uso_comercial'] for d in b.buscar('navio Canal de Suez', so_comercial=False, excluir_ia=False)}
    assert todos == {'sim', 'nao', 'indefinido'}


def test_manifesto_reconstroi_em_outra_maquina(tmp_path):
    b = _bib(tmp_path)
    r = b.ingerir(IMG / 'a23-g.jpg', META, video='v1', alias='a10', tema='Ever Given')
    b.gravar_regioes(r['sha256'], {'objetos': {'navio': {'caixa': [.1, .1, .5, .5], 'visivel': True, 'ancoravel': True, 'origem': 'visao'}}})
    man = tmp_path / 'manifesto.jsonl'
    assert b.exportar_manifesto(man) == 1
    assert '/home/' not in man.read_text() and str(tmp_path) not in man.read_text()          # sem caminhos locais
    c = _bib(tmp_path, 'c')
    assert c.importar_manifesto(man) == 1
    d = c.obter(r['id'])
    assert d['sha256'] == r['sha256'] and c.regioes(r['sha256'])['objetos']['navio']['ancoravel']
    assert c.usos(r['id'])[0]['alias'] == 'a10' and c.buscar('ever given')


def test_recuperar_confere_hash_e_rebaixa_da_origem(tmp_path):
    b = _bib(tmp_path)
    r = b.ingerir(IMG / 'a23-g.jpg', META)
    p = Path(r['arquivo'])
    p.write_bytes(b'corrompido')                                                               # armazém estragou
    baixados = []
    def baixar(url, dest):
        baixados.append(url)
        shutil.copy(IMG / 'a23-g.jpg', dest)
    assert b.recuperar(r['id'], baixar) == p and baixados == [META['url']]
    p.unlink()
    def errado(url, dest):
        shutil.copy(IMG / 'a1-g.jpg', dest)                                                  # a origem devolve outro arquivo
    assert b.recuperar(r['id'], errado) is None and not p.exists()


def test_limpeza_so_remove_orfaos(tmp_path):
    b = _bib(tmp_path)
    r = b.ingerir(IMG / 'a23-g.jpg', META)
    orfao = b.armazem / 'zz' / 'lixo.jpg'
    orfao.parent.mkdir(parents=True)
    orfao.write_bytes(b'x')
    lista = b.limpar()
    assert lista['orfaos'] == ['zz/lixo.jpg'] and orfao.exists()
    b.limpar(aplicar=True)
    assert not orfao.exists() and Path(r['arquivo']).exists()
    v = b.verificar()
    assert v['ok'] == 1 and not v['faltam'] and not v['corrompidos']


def test_backup_consistente(tmp_path):
    b = _bib(tmp_path)
    b.ingerir(IMG / 'a23-g.jpg', META)
    out = b.backup(tmp_path / 'bk')
    assert out['midias'] == 1 and (tmp_path / 'bk' / 'coringa.sqlite3').exists()
    assert json.loads((tmp_path / 'bk' / 'manifesto.jsonl').read_text().splitlines()[0])['_manifesto'] == 'biblioteca-coringa'
