"""Motor cinematic visual-first isolado: valida cenas e preserva origem sem green estético."""
import io
import json
from pathlib import Path
from PIL import Image
import pytest

from src.v4.formatos.filme_editorial import avaliar, preparar

ROOT = Path(__file__).resolve().parents[1]
PROVA = ROOT / 'docs/v4/formatos/filme_taiwan_prova.json'


def _plano():
    return json.loads(PROVA.read_text(encoding='utf-8'))


def test_plano_piloto_tem_seis_assuntos_reais_sem_cartao_mapa_global():
    plano = _plano()
    qa = avaliar(plano)
    assert qa['pronto'], qa['bloqueios']
    assert qa['medias_unicas'] >= 5
    assert qa['visual_approval'] == 'NAO_FOI_AVALIADO'
    assert all(s['type'] in ('photo','video','comparison') for s in plano['shots'])


def test_proibe_imagem_representativa_parecendo_registro_exato():
    plano = _plano()
    plano['shots'][0]['literal_identity'] = 'Foto supostamente de fábrica TSMC'
    x = avaliar(plano)
    assert 'F-REPRESENTATIVA-ROTULADA-LITERAL' in [e['codigo'] for e in x['bloqueios']]


def test_proibe_historia_com_duas_fotos_e_seis_cenas_repetidas():
    plano = _plano()
    for cena in plano['shots']:
        cena['asset'] = 'chip-macro'
        if cena['type'] == 'comparison':
            cena['assetB'] = 'fab-tsmc'
    x = avaliar(plano)
    assert not x['pronto']
    assert 'F-POUCO-ACERVO' in [e['codigo'] for e in x['bloqueios']]


def test_proibe_repeticao_sem_evento_intermediario():
    plano = _plano()
    plano['shots'][2]['cues'] = []
    plano['shots'][3]['end'] += 2
    qa = avaliar(plano)
    assert {'F-SEM-REVELACAO','F-PLANO-SEM-DIRECAO','F-LACUNA'} <= {
        e['codigo'] for e in qa['bloqueios']}


def test_prepara_midia_original_bit_a_bit_e_propriedades(tmp_path):
    plano = _plano()
    fontes = list(plano['media'])
    imagens={}
    for i,k in enumerate(fontes):
        im=Image.new('RGB',(820,820),(35+i*29,46+i*17,62+i*9))
        b=io.BytesIO()
        im.save(b,'JPEG',quality=95)
        imagens[plano['media'][k]['url']]=b.getvalue()
    r=preparar(plano,tmp_path/'saida',tmp_path/'public',
               downloader=lambda url: imagens[url])
    assert r['pronto'] and r['shots']==6 and r['midias']==len(fontes)
    props=json.loads((tmp_path/'saida'/'props.json').read_text())
    assert props['shots'][0]['asset'].startswith('film_editorial/')
    assert 'IMAGEM ILUSTRATIVA' not in props['shots'][1]['headline']
    assert props['shots'][1]['evidence'] == 'literal'
    assert all((tmp_path/'public'/s['asset']).is_file() for s in props['shots'])


def test_nao_assume_licenca_ou_host_publico_de_video():
    plano=_plano()
    plano['media']['fab-tsmc']['url']='https://random.site.invalid/imagem.jpg'
    plano['media']['fab-tsmc']['license']='???'
    qa=avaliar(plano)
    errs={e['codigo'] for e in qa['bloqueios']}
    assert 'F-LICENCA' in errs and 'F-ORIGEM-INSEGURA' in errs


def test_filme_final_exige_contrato_integral_mesmo_com_shots_tecnicamente_validos():
    p=_plano()
    p["tipo"]="FILME_FINAL"
    q=avaliar(p)
    codigos={x["codigo"] for x in q["bloqueios"]}
    assert "F-PORTAO-INTEGRAL-AUSENTE" in codigos
    assert not q["pronto"]


def test_filme_final_nao_aceita_contrato_de_outro_storyboard():
    p=_plano()
    p["tipo"]="FILME_FINAL"
    contrato=(ROOT/"docs/v4/formatos/CONTRATO_PILOTO_TAIWAN_INTEGRAL_20261119.json")
    p["contrato_integral"]=json.loads(contrato.read_text(encoding="utf8"))
    q=avaliar(p)
    codigos={x["codigo"] for x in q["bloqueios"]}
    assert "F-PORTAO-CONTRATO-DIVERGENTE" in codigos
    assert "F-PORTAO-INTEGRAL-BLOQUEADO" in codigos
    assert not q["pronto"]


def test_filme_final_nao_aceita_contrato_com_fontes_trocadas():
    p=_plano()
    p["tipo"]="FILME_FINAL"
    p["contrato_integral"]={
        "versao":1,"formato":"filme_editorial","tipo":"PRE_PRODUCAO_PRIVADA",
        "politica":{"publicar":False},
        "cenas":[{
            "id":s["id"],"inicio":s["start"],"fim":s["end"],
            "midia":{"tipo":"comparison" if s["type"]=="comparison" else "foto",
                     "asset_id":"fonte-externa"},
        } for s in p["shots"]]
    }
    q=avaliar(p)
    assert "F-PORTAO-FONTE-DIVERGENTE" in {x["codigo"] for x in q["bloqueios"]}
    assert not q["pronto"]
