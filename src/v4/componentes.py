"""Componentes do motor V4: o que o diretor pode escolher, por MODALIDADE (a modalidade vem antes de câmera/efeito).

Cada componente declara backend, modalidades que serve, parâmetros (com tipos e exemplo) e o que precisa de acervo.
O catálogo HyperFrames inteiro (457 itens) também fica acessível via `hf.registro` + `buscar_registro()`.
"""
from __future__ import annotations

import re

from src.v4.backends import hyperframes as HF

MODALIDADES = {
    'registro_foto': 'foto real do fato/lugar/objeto (com licença, autoria e ano)',
    'registro_video': 'vídeo real (com licença); trecho com duração suficiente',
    'documento': 'documento/planta/arquivo histórico mostrado inteiro e legível',
    'mapa': 'mapa que ensina: localização, rota/propagação com geometria de fonte, escala, rótulos legíveis',
    'esquema_2d': 'mecanismo/processo desenhado: sujeito, estado inicial, ação física, estado final, causa→efeito',
    'composicao_25d': 'camadas a partir de foto real (recorte rembg) para passar do registro ao esquema',
    'cena_3d': 'profundidade que melhora a explicação (corte 3D simples, sem fotorrealismo)',
    'comparacao': 'antes/depois ou A×B com a mesma escala',
    'dados': 'número/gráfico com escala e referência; valores com fonte',
    'tipografia': 'frase-chave curta (uma ideia por tela), pontual',
}
# modalidades que DEMONSTRAM ação física (mecanismo, processo, movimento)
DEMONSTRAM_ACAO = {'esquema_2d', 'cena_3d', 'composicao_25d', 'registro_video', 'mapa'}
SELO = {'registro_foto': 'registro', 'registro_video': 'registro', 'documento': 'documento', 'mapa': 'mapa', 'esquema_2d': 'esquema',
        'composicao_25d': 'reconstrucao', 'cena_3d': 'reconstrucao', 'comparacao': 'dados', 'dados': 'dados', 'tipografia': None}

COMPONENTES = {
    'registro.foto': {'backend': 'legacy', 'modalidades': ['registro_foto', 'documento'], 'acervo': 'foto',
                      'params': {'asset': 'id do acervo', 'enquadramento': 'objeto|contexto|geral (fixo)', 'layout': 'auto|editorial'},
                      'exemplo': {'asset': 'a3', 'enquadramento': 'objeto'}},
    'registro.video': {'backend': 'ffmpeg', 'modalidades': ['registro_video'], 'acervo': 'video',
                       'params': {'asset': 'id do acervo (vídeo)', 'inicio': 'segundo de início no clipe'}, 'exemplo': {'asset': 'v1', 'inicio': 2.0}},
    'mapa.rota': {'backend': 'remotion:MapaRota', 'modalidades': ['mapa'], 'acervo': 'geo',
                  'params': {'regiao': '[oeste,sul,leste,norte] graus', 'camera': '[{t, centro:[lon,lat], zoom}] — 1 item = FIXA',
                             'rota_osm': '{"tags": {"waterway": "canal"}, "nome": "regex"} ou null — geometria real do OpenStreetMap',
                             'rota': '{de, ate, rotulo_distancia} segundos locais', 'pontos': '[{nome, lonlat, t, tipo, lado}]',
                             'areas': '[{nome, lonlat, t, estilo: oceano|lago|pais}]', 'localizador': '{lonlat, t} globo D3'},
                  'exemplo': {'regiao': [-80.4, 8.6, -79.2, 9.7], 'camera': [{'t': 0, 'centro': [-79.75, 9.15], 'zoom': 8.7}],
                              'rota_osm': {'tags': {'waterway': 'canal'}, 'nome': 'Panam'}, 'rota': {'de': .8, 'ate': 4.5, 'rotulo_distancia': '≈ 80 km'},
                              'pontos': [{'nome': 'Colón', 'lonlat': [-79.9, 9.36], 't': .3}], 'areas': [{'nome': 'Oceano Pacífico', 'lonlat': [-79.6, 8.75], 't': 0, 'estilo': 'oceano'}]}},
    'mecanismo.nivel_vasos': {'backend': 'revideo', 'modalidades': ['esquema_2d'], 'acervo': None,
                              'params': {'titulo': 'texto curto', 'desnivel_m': 'número com fonte', 'nomes': '{baixo, alto, objeto}',
                                         'passos': 'lista de 5 frases curtas (entra, fecha, válvula abre, sobe, abre)',
                                         'tempos': '{entra, fecha, valvula, enche, abre, sai} em segundos (somam ≤ duração)'},
                              'exemplo': {'titulo': 'COMO A ECLUSA LEVANTA O NAVIO', 'desnivel_m': 9, 'nomes': {'baixo': 'mar', 'alto': 'lago', 'objeto': 'navio'}}},
    'camadas.recorte': {'backend': 'hyperframes:camadas+rembg', 'modalidades': ['composicao_25d'], 'acervo': 'foto',
                        'params': {'asset': 'foto com o assunto inteiro e separável do fundo', 'foco': '[x,y] normalizado',
                                   'acao': '{tipo: subir|nenhuma, de, ate, sobe_px, metros, y_agua_px}', 'rotulo': '{texto, t, x, y}'},
                        'exemplo': {'asset': 'a2', 'foco': [.5, .55], 'acao': {'tipo': 'subir', 'de': 1.2, 'ate': 4.0, 'sobe_px': 420, 'metros': 26}}},
    'tresd.camara': {'backend': 'remotion:Camara3D', 'modalidades': ['cena_3d'], 'acervo': None,
                     'params': {'nivel_baixo_m': 'número', 'nivel_alto_m': 'número', 'encher': '{de, ate}', 'comprimento_m': 'número',
                                'largura_m': 'número', 'rotulos': '[{texto, t, ancora: agua|lago|comporta|navio}] ({nivel} = metros atuais)',
                                'rotulo_selo': 'texto'},
                     'exemplo': {'nivel_baixo_m': 0, 'nivel_alto_m': 9, 'encher': {'de': .6, 'ate': 4.0}}},
    'dados.escala': {'backend': 'manim:EscalaAltura', 'modalidades': ['dados', 'comparacao'], 'acervo': None,
                     'params': {'titulo': 'texto', 'alvo': '{nome, altura_m}', 'referencias': '[{nome, altura_m, andares, fonte}]', 'passo_m': 'número'},
                     'exemplo': {'alvo': {'nome': 'eclusas', 'altura_m': 26}, 'referencias': [{'nome': 'prédio ~9 andares', 'altura_m': 27, 'andares': 9}]}},
    'tipo.lottie': {'backend': 'remotion:TipoLottie', 'modalidades': ['tipografia'], 'acervo': None,
                    'params': {'linhas': '[{texto ≤ 18 caracteres, t, destaque}]', 'lottie': 'lottie/gota.json (original do canal)'},
                    'exemplo': {'linhas': [{'texto': 'Sem bombas.', 't': .2}, {'texto': 'Só gravidade.', 't': .8, 'destaque': True}], 'lottie': 'lottie/gota.json'}},
    'hf.registro': {'backend': 'hyperframes:registro', 'modalidades': ['tipografia', 'dados', 'comparacao', 'esquema_2d'], 'acervo': None,
                    'params': {'item': 'nome do catálogo HyperFrames (só retrato/responsivo em tela cheia)', 'variaveis': 'variáveis tipadas do item'},
                    'exemplo': {'item': 'flowchart-vertical', 'variaveis': {}}},
}


def buscar_registro(consulta: str, n: int = 12, so_tela_cheia: bool = True) -> list[dict]:
    """busca local no catálogo HyperFrames inteiro (palavras em inglês), devolve entradas resumidas para o diretor"""
    termos = [t for t in re.findall(r'[a-z0-9]+', consulta.lower()) if len(t) > 2]
    out = []
    for it in HF.CATALOGO['itens']:
        if so_tela_cheia and (it['tipo'] != 'block' or it['compat_9x16'] == 'recompor'):
            continue
        alvo = ' '.join([it['nome'], it['titulo'] or '', it['descricao'] or '', ' '.join(it['tags'])]).lower()
        nota = sum(alvo.count(t) for t in termos)
        if nota:
            out.append((nota, it))
    out.sort(key=lambda x: -x[0])
    return [{'item': i['nome'], 'titulo': i['titulo'], 'orientacao': i['orientacao'], 'duracao': i['duracao'],
             'variaveis': [v['id'] for v in i['parametros']], 'funcoes': i['funcoes_coringa']} for _, i in out[:n]]


def resumo_prompt() -> str:
    linhas = ['COMPONENTES (escolha a MODALIDADE primeiro; depois o componente que a serve):']
    for nome, c in COMPONENTES.items():
        linhas.append(f"- {nome} [{', '.join(c['modalidades'])}] backend={c['backend']} params={c['params']}")
    r = HF.CATALOGO['resumo']
    linhas.append(f"\nCatálogo HyperFrames acessível: {r['total']} itens (blocos {r['por_tipo'].get('block')}, componentes "
                  f"{r['por_tipo'].get('component')}); em tela cheia 9:16 só retrato/responsivo. Use hf.registro com o nome exato.")
    return '\n'.join(linhas)
