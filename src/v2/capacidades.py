"""DIREÇÃO VISUAL POR ACONTECIMENTO (V2).

Pergunta que este módulo responde para cada trecho narrado: O QUE está acontecendo, e qual composição MOSTRA isso?
Não é busca por palavra solta: cada capacidade descreve um acontecimento por padrões de (sujeito/objeto + verbo de
ação/estado) em português, mais os sinais estruturados que o roteiro já manda (bloco.funcao, acontecimento.recurso).

Regras:
  - acontecimento CRÍTICO (mecanismo físico, movimento, rota, explosão, transformação, escala) exige composição que
    o represente; foto genérica ou texto NÃO servem;
  - se a composição exige dados que a cena não tem (coordenadas, duas imagens, valores), a cena recebe uma LIMITAÇÃO
    explícita e o fiscal_v2 reprova a cena — em vez de "fingir que explicou";
  - acontecimento não crítico (lugar, pessoa, ambiente) pode ser foto real.
Catálogo extensível: nova capacidade = nova entrada em CAPACIDADES + composição registrada em src/render/v2/comp.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field


def _n(s) -> str:
    s = unicodedata.normalize('NFKD', str(s or '').lower().replace('*', ''))
    return ''.join(c for c in s if not unicodedata.combining(c))


# verbos/estados em várias flexões (radicais) — o texto já vem sem acento
AGUA = r'(agua|nivel|camara|mare|rio|lago|represa|reservatorio|mar|enchente|inundacao|liquido)'
SOBE = r'(sob[ea]|subi\w*|ench\w*|elev\w*|inund\w*|transbord\w*|cheia)'
DESCE = r'(desc[ei]\w*|esvazi\w*|escoa\w*|baix[oa]\w*|drena\w*|recua\w*)'
OBJ_MOVEL = r'(navio|barco|embarcacao|objeto|carro|aviao|foguete|elevador|bloco|pedra)'


@dataclass
class Capacidade:
    id: str
    descricao: str
    padroes: list[str]                     # expressões regulares (texto normalizado, sem acento)
    comps: list[str]                       # composições capazes, em ordem de preferência
    critica: bool
    requisitos: dict = field(default_factory=dict)   # comp -> lista de campos necessários na cena
    sinais: dict = field(default_factory=dict)       # campos estruturados que também disparam (bloco.funcao, recurso)


CAPACIDADES: list[Capacidade] = [
    Capacidade('agua_subindo', 'água/nível subindo, enchendo uma câmara/recipiente/região',
               [rf'{AGUA}.{{0,40}}{SOBE}', rf'{SOBE}.{{0,25}}{AGUA}'], ['mecanismo.eclusa', 'mecanismo.nivel'], True,
               {'mecanismo.eclusa': ['contexto:eclusa|comporta'], 'mecanismo.nivel': []}),
    Capacidade('elevacao_vertical', 'objeto sendo erguido/elevado (movimento vertical)',
               [rf'{OBJ_MOVEL}.{{0,40}}(sob[ea]|subi\w*|e erguid\w*|e elevad\w*|levant\w*|ergu\w*)', rf'(ergu\w*|levant\w*|elev\w*).{{0,30}}{OBJ_MOVEL}'],
               ['mecanismo.eclusa', 'forcas.vetores'], True, {'mecanismo.eclusa': ['contexto:eclusa|comporta'], 'forcas.vetores': []}),
    Capacidade('agua_descendo', 'água descendo/escoando, por gravidade ou esvaziando',
               [rf'{AGUA}.{{0,40}}{DESCE}', r'por gravidade', rf'{DESCE}.{{0,25}}{AGUA}'], ['mecanismo.eclusa', 'mecanismo.nivel', 'diagrama.explicativo'], True,
               {'mecanismo.eclusa': ['contexto:eclusa|comporta'], 'mecanismo.nivel': [], 'diagrama.explicativo': ['nos']}),
    Capacidade('manobra_eclusa', 'navio entrando/saindo de câmara, comporta fechando/abrindo (mecanismo de eclusa)',
               [r'(comporta|camara|eclusa)\w*.{0,40}(fech\w*|abr\w*|entr\w*|iguala\w*)', r'(entr\w*|sai\w*) (numa|na|da) (camara|eclusa)', r'nivel iguala'],
               ['mecanismo.eclusa'], True, {'mecanismo.eclusa': []}),
    Capacidade('explosao', 'explosão, impacto, erupção, onda de choque',
               [r'explod\w*|explos\w*|onda de choque|cratera|erup\w*|detona\w*|impacto (de|do|da)'], ['evento.impacto'], True,
               {'evento.impacto': ['aneis']}),
    Capacidade('rota', 'trajeto, ligação ou deslocamento entre lugares',
               [r'\bliga\w* .{0,30}\b(a|ao|com)\b', r'\b(de|do|da) [a-z]+.{0,30}\b(ate|ao|a) [a-z]+', r'atravess\w*|naveg\w*|percorr\w*|viaj\w*|rota|trajeto|caminho entre'],
               ['mapa.rota'], True, {'mapa.rota': ['pontos>=2']}),
    Capacidade('localizacao', 'onde fica um lugar',
               [r'\bfica (em|no|na)\b|localizad\w*|\bonde fica|situad\w*'], ['mapa.localizacao'], False, {'mapa.localizacao': ['pontos>=1']},
               {'tipo': ['mapa']}),
    Capacidade('territorio', 'país/território/fronteira como assunto',
               [r'\b(pais|territorio|fronteira|regiao) (estreit|grande|pequen|cortad|dividid)\w*', r'faz fronteira'], ['mapa.territorio'], False, {'mapa.territorio': ['pais']}),
    Capacidade('escala', 'comparação de tamanho/altura/escala física',
               [r'(do tamanho de|altura de|da altura|mais alto que|tao (grande|alto)|equivale a|o mesmo que) ', r'\d+ metros (de altura|acima)|sobe \d+ metros'],
               ['comparacao.grandezas'], True, {'comparacao.grandezas': ['itens>=2']}),
    Capacidade('comparacao_numerica', 'comparação entre quantidades',
               [r'\b(mais|menos) (do )?que\b.{0,30}\d', r'\d+ vezes (mais|menos|maior|menor)', r'\bdobro|metade|triplo'], ['grafico.barras'], False, {'grafico.barras': ['itens>=2']}),
    Capacidade('serie_temporal', 'algo que muda ao longo do tempo (subiu, caiu, desde…)',
               [r'(cresc|caiu|cai |aument|diminu|despenc|disparo)\w*.{0,40}(desde|ao longo|por ano|em \d{4}|decada)', r'desde \d{4}'],
               ['grafico.temporal'], False, {'grafico.temporal': ['serie>=4']}),
    Capacidade('sequencia_historica', 'sequência de datas/fatos históricos',
               [r'\b1[5-9]\d\d\b.{3,80}\b(1[5-9]\d\d|20\d\d)\b|\b20\d\d\b.{3,80}\b20\d\d\b'], ['linha_tempo.historica'], False,
               {'linha_tempo.historica': ['eventos>=2']}, {'tipo': ['linha_tempo']}),
    Capacidade('transformacao', 'transformação de um estado em outro (antes × depois)',
               [r'(vir[ao]u?|transform\w*|se torn\w*|antes .{0,40} (hoje|depois|agora))'], ['comparacao.antes_depois', 'processo.etapas'], True,
               {'comparacao.antes_depois': ['img_antes', 'img_depois'], 'processo.etapas': ['etapas>=2']}),
    Capacidade('proporcao', 'porcentagem / fração de um todo', [r'\d+ ?(%|por cento)'], ['proporcao'], False, {'proporcao': ['pct']}),
    Capacidade('numero', 'um número grande no centro da frase', [r'\b\d{2,}[\d.,]*\s*(mil|milho\w*|bilho\w*|litros|km|metros|toneladas|anos)'], ['numero.animado'], False,
               {'numero.animado': ['valor', 'fonte']}, {'tipo': ['numero']}),
    Capacidade('processo', 'processo em etapas / mecanismo explicado passo a passo',
               [r'\b(primeiro|em seguida|depois|entao|por fim)\b.{0,80}\b(depois|entao|em seguida|por fim)\b'], ['processo.etapas', 'diagrama.explicativo'], True,
               {'processo.etapas': ['etapas>=2'], 'diagrama.explicativo': ['nos']}, {'bloco.funcao': ['mecanismo'], 'recurso': ['esquema']}),
    Capacidade('forca', 'forças físicas (empuxo, peso, atrito, pressão), flutuar/afundar',
               [r'empuxo|\bpeso\b|atrito|pressao|flutu\w*|afund\w*|forca (da|de|do)'], ['forcas.vetores'], True, {'forcas.vetores': ['forcas']}),
    Capacidade('orbita', 'movimento celeste (órbita, translação, rotação)',
               [r'orbit\w*|gir\w* em torno|volta (ao redor|em torno)|translac\w*|ano-luz|anos-luz'], ['astronomia.orbita'], True, {'astronomia.orbita': []}),
    Capacidade('citacao', 'fala literal de alguém', [r'["“].{10,}["”]'], ['citacao'], False, {'citacao': ['texto', 'autor']}),
    Capacidade('fonte', 'informação atribuída a uma fonte (estudo, jornal, documento)',
               [r'\b(segundo|de acordo com) (o|a|um|uma)?\s*(estudo|pesquisa|jornal|relatorio|documento|reportagem)'], ['fonte.evidencia'], False, {'fonte.evidencia': ['veiculo', 'trecho']}),
    Capacidade('pessoa', 'identificar uma pessoa', [], ['lower_third'], False, {'lower_third': ['nome']}, {'recurso': ['retrato']}),
    Capacidade('lugar', 'mostrar um lugar', [], ['foto.documental'], False, {}, {'recurso': ['lugar', 'foto', 'video', 'ambiente']}),
]
POR_ID = {c.id: c for c in CAPACIDADES}


def _sinal(cap: Capacidade, cena: dict) -> bool:
    for campo, vals in cap.sinais.items():
        v = (cena.get('bloco') or {}).get('funcao') if campo == 'bloco.funcao' else (cena.get('acontecimento') or {}).get('recurso') if campo == 'recurso' else cena.get(campo)
        if v in vals:
            return True
    return False


def detectar(cena: dict) -> list[dict]:
    """Acontecimentos que a cena descreve, do mais específico ao mais geral. Usa a fala E o que o roteiro disse que
    a cena deve mostrar (campo `mostrar`), além dos sinais estruturados."""
    txt = _n(f"{cena.get('fala', '')} || {cena.get('mostrar', '')}")
    achados = []
    for cap in CAPACIDADES:
        m = next((re.search(p, txt) for p in cap.padroes if re.search(p, txt)), None)
        if m or _sinal(cap, cena):
            achados.append({'capacidade': cap.id, 'critica': cap.critica, 'trecho': m.group(0) if m else '(sinal do roteiro)', 'por_texto': bool(m)})
    # prioridade: críticas detectadas pelo texto > não críticas; dentro do grupo, ordem do catálogo
    achados.sort(key=lambda a: (not (a['critica'] and a['por_texto']), not a['critica'], [c.id for c in CAPACIDADES].index(a['capacidade'])))
    return achados


def _tem(req: str, params: dict, contexto: str) -> bool:
    if req.startswith('contexto:'):
        return re.search(req.split(':', 1)[1], contexto) is not None
    m = re.match(r'(\w+)>=(\d+)', req)
    if m:
        return len(params.get(m.group(1)) or []) >= int(m.group(2))
    return params.get(req) not in (None, '', [], {})


def escolher(cena: dict, params: dict | None = None, contexto: str = '') -> dict:
    """Decide a composição para a cena. `params` = dados disponíveis para montar (pontos, itens, imagens…);
    `contexto` = palavras do tema/vídeo (ex.: 'canal eclusa navio'). Retorna {comp, capacidade, critica, motivo} ou,
    sem composição viável, {comp: None, limitacao, critica}."""
    params = params or {}
    ctx = _n(contexto + ' ' + cena.get('fala', '') + ' ' + cena.get('mostrar', ''))
    achados = detectar(cena)
    falhas = []
    for a in achados:
        cap = POR_ID[a['capacidade']]
        for comp in cap.comps:
            reqs = cap.requisitos.get(comp, [])
            faltam = [r for r in reqs if not _tem(r, params, ctx)]
            if not faltam:
                return {'comp': comp, 'capacidade': cap.id, 'critica': cap.critica, 'trecho': a['trecho'],
                        'motivo': f'"{a["trecho"]}" → {cap.descricao}'}
            falhas.append(f'{comp} precisa de {", ".join(faltam)}')
        if cap.critica and a['por_texto']:
            return {'comp': None, 'capacidade': cap.id, 'critica': True, 'trecho': a['trecho'],
                    'limitacao': f'acontecimento "{a["trecho"]}" ({cap.descricao}) sem composição viável: ' + '; '.join(falhas)}
    return {'comp': 'foto.documental', 'capacidade': 'lugar', 'critica': False, 'trecho': '', 'motivo': 'nenhum acontecimento específico: foto real do assunto'}


# Referências de altura conhecidas (Wikipédia), para a escala sem inventar números
REFERENCIAS_M = [('Pessoa', 1.75, 'pessoa'), ('Girafa', 5.5, 'arvore'), ('Prédio 3 andares', 9, 'predio'), ('Prédio 8 andares', 24, 'predio'),
                 ('Cristo Redentor', 38, 'torre'), ('Est. Liberdade', 93, 'torre'), ('Torre Eiffel', 330, 'torre')]


def escala_com_referencias(valor_m: float, rotulo: str = 'Desnível') -> dict:
    """Parâmetros de comparacao.grandezas: o valor narrado + até 3 referências entre 1/12 e 1,6× dele (mesma escala)."""
    refs = [r for r in REFERENCIAS_M if valor_m / 14 <= r[1] <= valor_m * 1.6]
    refs = sorted(refs, key=lambda r: abs(r[1] - valor_m))[:3]
    itens = [{'rotulo': n, 'valor': v, 'forma': f} for n, v, f in refs] + [{'rotulo': rotulo[:16], 'valor': valor_m, 'forma': 'agua'}]
    itens.sort(key=lambda x: x['valor'])
    fmt = ('%g' % valor_m).replace('.', ',')
    return {'titulo': f'Quanto são *{fmt} metros*?', 'unidade': 'm', 'itens': itens,
            'destaque': next(k for k, x in enumerate(itens) if x['forma'] == 'agua'), 'fonte': 'Wikipédia · estátuas com pedestal; prédios ≈ 3 m/andar'}
