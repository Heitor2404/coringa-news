"""VIABILIDADE VISUAL ANTES DAS CHAMADAS CARAS (12/11/2026, depois do teste do polvo).

O teste do polvo gastou ≈ US$ 0,49 (pesquisa, 2 roteiros, crítica, ganchos) e só DEPOIS o porteiro de imagem barrou o tema
(4 de 13 frases com foto real). O acervo já estava pronto ANTES do roteiro: dava para decidir ali, sem chamada nova.

Tipo de conteúdo (pela pergunta, pelos fatos e pelo dossiê — código, sem IA):
  - mecanismo: como algo funciona por dentro (célula, pele, luz, cérebro...). O que explica é ESQUEMA correto; foto real do
    assunto é âncora e contexto. Exigir foto do processo invisível é exigir o impossível.
  - historico: pessoas, datas e lugares do passado. O que mostra é foto/documento real do próprio fato.
  - natureza / geral: o resto.
O porteiro (roteiro._planos_sem_foto) usa o MESMO tipo, com regra própria e sem afrouxar: em mecanismo, cada frase precisa
de foto real OU esquema explicativo OU infográfico, e precisa haver fotos reais do assunto como âncora.
"""
import re
import unicodedata

MECANISMO = re.compile(r'\b(celul|pele|cerebr|neuron|molecul|atomo|luz|cor(es)?\b|pigment|gene|dna|proteina|enzima|hormon|'
                       r'muscul|virus|bacteria|imun|quimic|fisic|gravidade|energia|onda|som\b|visao|olho|sangue|coracao|'
                       r'digest|fotossintese|cromatoforo|camufl|reflet|eletric|magnet|calor|temperatura|pressao|'
                       r'metabol|sono|memoria|dor\b|celular|tecido|orgao|nervo|sinal)', re.I)
PERGUNTA_COMO = re.compile(r'\b(como|por que|porque|o que acontece|de onde vem|para que serve)\b', re.I)
HISTORIA = re.compile(r'\b(seculo|imperio|rei|rainha|guerra|golpe|revolucao|batalha|presidente|papa|faraó|farao|historia|'
                      r'descobri|invent|assassin|crime|naufrag|expedi)', re.I)
ANO_ANTIGO = re.compile(r'\b(1[0-8][0-9]{2}|19[0-8][0-9])\b')
NATUREZA = re.compile(r'\b(animal|especie|polvo|peixe|ave|inseto|planta|arvore|floresta|oceano|mar|vulcao|deserto|ilha|'
                      r'montanha|rio|lago|caverna|planeta|estrela|galaxia)', re.I)

# o que o acervo precisa ter ANTES do roteiro (≈ o que o porteiro vai exigir depois, para 13 frases)
MINIMOS = {'historico': {'especificas': 5, 'uteis': 5},
           'natureza': {'especificas': 3, 'uteis': 5},
           'geral': {'especificas': 3, 'uteis': 5},
           'mecanismo': {'especificas': 2, 'uteis': 3}}


def _n(s) -> str:
    return unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().lower()


def classificar(tema: dict, fatos: str = '', dossie: dict | None = None) -> str:
    pergunta = _n(tema.get('pergunta'))
    epoca = _n((dossie or {}).get('epoca'))
    if PERGUNTA_COMO.search(pergunta) and MECANISMO.search(pergunta):
        return 'mecanismo'
    if HISTORIA.search(pergunta) or ANO_ANTIGO.search(f'{pergunta} {epoca}'):
        return 'historico'
    if MECANISMO.search(pergunta) and len(MECANISMO.findall(_n(fatos))) >= 6:
        return 'mecanismo'
    if NATUREZA.search(pergunta):
        return 'natureza'
    return 'geral'


def avaliar(acervo: list[dict], tipo: str) -> dict:
    uteis = [x for x in acervo if x.get('util', True)]
    esp = [x for x in uteis if not x.get('generica')]
    m = MINIMOS.get(tipo, MINIMOS['geral'])
    r = {'tipo': tipo, 'uteis': len(uteis), 'especificas': len(esp), 'videos': sum(1 for x in uteis if x.get('video')),
         'minimo': m, 'ok': len(esp) >= m['especificas'] and len(uteis) >= m['uteis'], 'motivo': ''}
    if not r['ok']:
        r['motivo'] = (f"pouco material visual ANTES do roteiro ({tipo}): {len(esp)} imagem(ns) específica(s) e {len(uteis)} útil(eis); "
                       f"mínimo {m['especificas']} e {m['uteis']}")
    return r
