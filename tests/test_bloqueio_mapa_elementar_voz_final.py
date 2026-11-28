"""Regressão que proíbe o novo mapa elementar e o Edge em edição final."""
import json
from pathlib import Path

from src.v4.formatos import filme_editorial as filme
from src.v4.formatos import direcao_eventos
from src.v4.formatos import plano as atlas

ROOT=Path(__file__).resolve().parents[1]


def exemplo():
    return json.loads((ROOT/'docs/v4/formatos/filme_taiwan_prova.json').read_text(encoding='utf-8'))


def codigos(p):
    return {f['codigo'] for f in filme.avaliar(p)['bloqueios']}


def test_mapa_prototipo_nao_existe_mais_em_codigo_ou_fluxos():
    assert not (ROOT/'motor4/remotion/src/formatos/NarrativeMapStage.tsx').exists()
    assert not (ROOT/'docs/v4/formatos/qa_mapas_eventos_tres_temas.json').exists()
    assert not (ROOT/'.github/workflows/qa-mapa-rotulos-r2.yml').exists()
    assert not (ROOT/'.github/workflows/qa-mapas-r2-telegram.yml').exists()
    fonte=(ROOT/'motor4/remotion/src/formatos/FilmeEditorial.tsx').read_text(encoding='utf-8')
    assert 'NarrativeMapStage' not in fonte
    assert "type: 'photo' | 'video' | 'comparison' | 'mechanism' | 'atlas_map';" in fonte
    assert "type: 'photo' | 'video' | 'comparison' | 'mechanism' | 'map'" not in fonte
    assert 'ATLAS/Formato/PalcoMapa' in (ROOT/'src/v4/formatos/ponte_mapa_atlas.py').read_text(encoding='utf-8')
    assert 'data-testid="filme-progresso-global"' in fonte


def test_filme_bloqueia_mapa_elementar_mesmo_com_pins_ou_rota():
    p=exemplo()
    p['shots'][0]['type']='map'
    p['shots'][0]['map']={'kind':'route','points':[{'label':'PIN','lonlat':[1,1]}],
                            'route':{'coords':[[1,1],[2,2]]}}
    assert {'F-MAPA-PROIBIDO','F-TIPO'} <= codigos(p)


def test_diretor_roteia_localizacao_e_trajeto_ao_sistema_atlas():
    for intent in ('localizar','trajeto'):
        x=direcao_eventos.verificar([{
          'id':'beat','type':'photo',
          'direcao_evento':{'intencao':intent,'fato_id':'fato-1',
                            'aprendizado':'localização geográfica realmente identificada'},
        }])
        assert 'D-EXIGE-CARTOGRAFIA-ATLAS' in {e['codigo'] for e in x}


def test_motores_cartograficos_anteriores_preservados():
    a=(ROOT/'motor4/remotion/src/formatos/Palco.tsx').read_text(encoding='utf-8')
    b=(ROOT/'motor4/remotion/src/MapaRota.tsx').read_text(encoding='utf-8')
    assert 'PalcoMapa' in a and 'rasters' in a and 'maplibre-gl' in a
    assert 'MapLibre' in b or 'maplibre-gl' in b
    assert (ROOT/'motor4/formatos/dados/raster/s2_panama_canal.webp').is_file()
    assert (ROOT/'motor4/formatos/dados/raster/ne2_istmo_panama.jpg').is_file()


def test_preset_oficial_charon_nao_alterado():
    n=atlas.canal('coringa')['narrador']
    assert n['motor']=='gemini' and n['voz']=='Charon' and n['fallback']=='bloquear'


def test_narracao_edge_testada_nao_pode_ser_voz_do_video_final():
    p=exemplo()
    p['tipo']='PRODUCAO'
    p['narrador']={'motor':'edge','voz':'pt-BR-AntonioNeural',
                   'fallback':'bloquear','sha256_voz':'a'*64,'aprovacao_humana':True}
    assert 'F-VOZ-TESTE-EM-PRODUCAO' in codigos(p)


def test_sem_revisao_humana_e_fallback_sao_bloqueadores():
    p=exemplo()
    p['tipo']='PRODUCAO'
    p['narrador']={'motor':'gemini','voz':'Charon',
                   'fallback':'edge','sha256_voz':'a'*64,'aprovacao_humana':False}
    assert {'F-VOZ-TESTE-EM-PRODUCAO','F-VOZ-SEM-APROVACAO'} <= codigos(p)


def test_voz_oficial_com_prova_e_revisao_pode_passar_sem_auto_publicar():
    p=exemplo()
    p['tipo']='PRODUCAO'
    p['narrador']={'motor':'gemini','voz':'Charon','fallback':'bloquear',
                   'sha256_voz':'a'*64,'aprovacao_humana':True}
    assert 'F-VOZ-TESTE-EM-PRODUCAO' not in codigos(p)
    assert 'F-VOZ-SEM-APROVACAO' not in codigos(p)
