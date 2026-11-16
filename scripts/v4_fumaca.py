"""Teste TÉCNICO de integração do motor V4 (não é vídeo de avaliação estética, não é entregue): passa UMA cena curta por
cada componente/backend, pela composição, camada de identidade/legendas, som e métricas. Dublês só para o que depende
de rede/chaves (IA do diretor, acervo, voz). uso: python scripts/v4_fumaca.py <foto.jpg> <video.mp4> <saida>"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.v4 import acervo_v4, diretor, episodio  # noqa: E402

foto, video, saida = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
D = 2.4
CENAS = [
    ('registro_foto', 'registro.foto', {'asset': 'auto'}, {'tipo': 'foto'}),
    ('registro_video', 'registro.video', {'asset': 'auto', 'inicio': 0}, {'tipo': 'video'}),
    ('mapa', 'mapa.rota', {'regiao': [-80.15, 8.85, -79.45, 9.45], 'camera': [{'t': 0, 'centro': [-79.75, 9.15], 'zoom': 8.6}],
                           'rota_osm': {'tags': {'waterway': '~canal|fairway'}, 'nome': 'Panam'}, 'rota': {'de': .1, 'ate': .9, 'rotulo_distancia': '≈ 80 km'},
                           'pontos': [{'nome': 'Colón', 'lonlat': [-79.9, 9.36], 't': .1}], 'areas': [{'nome': 'Oceano Pacífico', 'lonlat': [-79.6, 8.9], 't': 0, 'estilo': 'oceano'}],
                           'localizador': {'lonlat': [-79.7, 9.1], 't': 0}}, None),
    ('esquema_2d', 'mecanismo.nivel_vasos', {'desnivel_m': 9, 'tempos': {'entra': .1, 'fecha': .05, 'valvula': .1, 'enche': .45, 'abre': .1, 'sai': .15}}, None),
    ('composicao_25d', 'camadas.recorte', {'asset': 'auto', 'foco': [.5, .55], 'acao': {'tipo': 'subir', 'de': .3, 'ate': .9, 'sobe_px': 300, 'metros': 26}}, {'tipo': 'foto'}),
    ('cena_3d', 'tresd.camara', {'nivel_baixo_m': 0, 'nivel_alto_m': 9, 'encher': {'de': .1, 'ate': .9}, 'rotulos': [{'texto': '+{nivel} m', 't': 0, 'ancora': 'agua'}]}, None),
    ('dados', 'dados.escala', {'alvo': {'nome': 'eclusas', 'altura_m': 26}, 'referencias': [{'nome': 'prédio ~9 andares', 'altura_m': 27, 'andares': 9}]}, None),
    ('tipografia', 'tipo.lottie', {'linhas': [{'texto': 'Só gravidade.', 't': .1, 'destaque': True}]}, None),
    ('tipografia', 'hf.registro', {'item': 'notes-reveal', 'variaveis': {}}, None),
]
rot = {'titulo': 'fumaça', 'cenas': [{'id': f'c{i + 1}', 'fala': 'palavra ' * 6, 'objetivo': 'teste técnico', 'o_que_precisa_aparecer': 'teste',
                                      'modalidade': m, 'componente': c, 'params': p, 'busca': b, 'camera': {'tipo': 'fixa'},
                                      'transicao': {'tipo': 'dissolve', 'justificativa': 'teste do compositor'} if i == 3 else {'tipo': 'corte'},
                                      'sfx': [{'id': 'comporta', 'em': .5, 'justificativa': 'teste'}] if i == 3 else []}
                                     for i, (m, c, p, b) in enumerate(CENAS)]}
diretor.pedir = lambda *a, **k: json.loads(json.dumps(rot))


def acv_falso(ep, pasta):
    acv, n = {}, 0
    for c in ep['cenas']:
        if c.get('busca'):
            n += 1
            aid = f'a{n}'
            ehv = c['busca']['tipo'] == 'video'
            acv[aid] = {'id': aid, 'arq': str(video if ehv else foto), 'wh': [1080, 1920] if ehv else [1920, 867], 'titulo': 'teste', 'desc': 'teste', 'ano': 1913,
                        'credito': '"teste" — autor (CC BY 4.0), via Wikimedia Commons', 'licenca': 'CC BY 4.0', 'video': {'dur': 6} if ehv else None, 'roi': None}
            c['params']['asset'] = aid
    return acv, []


acervo_v4.montar = acv_falso
from src import voz  # noqa: E402


def voz_falsa(cenas, pasta, **k):
    pasta.mkdir(parents=True, exist_ok=True)
    dur = D * len(cenas)
    wav = pasta / 'voz.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'sine=f=220:d={dur}', '-af', 'volume=0.2', '-ar', '48000', str(wav)], check=True)
    tempos = [(i * D, (i + 1) * D) for i in range(len(cenas))]
    caps = [{'start': i * D, 'end': (i + 1) * D, 'words': [{'w': f'PALAVRA{k}', 's': i * D + k * .5, 'hl': k == 1} for k in range(4)]} for i in range(len(cenas))]
    return wav, tempos, caps, dur


voz.narrar = voz_falsa
pedido = {'video_id': 'fumaca-v4', 'pergunta': 'teste', 'alvo_duracao': [20, 25], 'fatos': [{'id': 'f1', 'texto': 't', 'fonte': 'x'}]}
res = episodio.produzir(pedido, saida, saida / '_trabalho')
print(json.dumps({'estado': res['estado'], 'bloqueios': res['bloqueios'], 'mp4': res.get('mp4'), 'segundos': res.get('segundos'),
                  'resumo': res.get('metricas_resumo'), 'audio': res.get('audio')}, ensure_ascii=False, indent=1))
