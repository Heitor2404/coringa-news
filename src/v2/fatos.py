"""PRECISÃO FACTUAL V2: número na tela só com contexto, natureza, moeda original e fonte listada.

O caso que motivou (Panamá, execução 43435732255): a tela dizia "R$ 27 milhões pagos por um navio para atravessar".
Na verdade era ~US$ 5,3 milhões pagos EM LEILÃO por uma VAGA de travessia (SK Gas, navio G. Spirit, 1º/09/2026) —
valor excepcional, não a tarifa; o pedágio é cobrado à parte; e a fonte exibida ("O GLOBO") nem estava na lista.

Regras (bloqueiam a cena; não são aviso):
  F1 dinheiro precisa de moeda ORIGINAL (o valor como a fonte publicou);
  F2 conversão de moeda só com taxa, DATA e fonte do câmbio; sem isso, mostra só a moeda original;
  F3 todo número precisa de fonte, e a fonte precisa estar na lista de fontes do vídeo;
  F4 natureza obrigatória para dinheiro e recordes: 'tipico' (média/tarifa), 'excepcional' (recorde, leilão, pico),
     'estimativa', 'historico'; valor excepcional não pode ser rotulado como típico nem aparecer sem a palavra que o
     qualifica (recorde/leilão/pico/máximo) no rótulo ou na nota;
  F5 o rótulo não pode afirmar mais que o contexto ("para atravessar" quando o contexto é "vaga em leilão").
"""
from __future__ import annotations

import re
import unicodedata

NATUREZAS = {'tipico': 'VALOR TÍPICO', 'excepcional': 'VALOR EXCEPCIONAL', 'estimativa': 'ESTIMATIVA', 'historico': 'VALOR HISTÓRICO'}
QUALIFICA_EXC = ('recorde', 'leilao', 'leilão', 'pico', 'maximo', 'máximo', 'excepcional', 'extraordin')
MOEDAS = {'USD': 'US$', 'BRL': 'R$', 'EUR': '€', 'GBP': '£', 'JPY': '¥', 'CNY': 'CN¥', 'PAB': 'B/.'}


def _n(s) -> str:
    s = unicodedata.normalize('NFKD', str(s or '').lower())
    return ''.join(c for c in s if not unicodedata.combining(c))


def validar(valor: dict, fontes_video: list[str]) -> list[str]:
    """`valor` = {valor, unidade?, moeda?, natureza?, contexto, rotulo, nota?, fonte, conversao?: {moeda, valor, taxa,
    data, fonte}}. Devolve a lista de violações (vazia = pode ir para a tela)."""
    erros = []
    eh_dinheiro = bool(valor.get('moeda')) or bool(re.search(r'(R\$|US\$|€|£|d[oó]lar|reais|euro)', f"{valor.get('rotulo', '')} {valor.get('unidade', '')} {valor.get('prefixo', '')}", re.I))
    if eh_dinheiro and not valor.get('moeda'):
        erros.append('F1: dinheiro sem moeda original declarada')
    if valor.get('moeda') and valor['moeda'] not in MOEDAS:
        erros.append(f"F1: moeda desconhecida {valor['moeda']!r} (use código ISO: USD, BRL…)")
    cv = valor.get('conversao')
    if cv:
        faltam = [k for k in ('moeda', 'valor', 'taxa', 'data', 'fonte') if not cv.get(k)]
        if faltam:
            erros.append(f"F2: conversão sem {', '.join(faltam)}")
        elif cv.get('fonte') and not _listada(cv['fonte'], fontes_video):
            erros.append(f"F2: fonte do câmbio {cv['fonte']!r} fora da lista de fontes")
        else:
            esperado = float(valor['valor']) * float(cv['taxa'])
            if abs(esperado - float(cv['valor'])) > max(0.02 * esperado, 0.01):
                erros.append(f"F2: conversão não confere ({valor['valor']} × {cv['taxa']} = {esperado:.2f}, não {cv['valor']})")
    if not valor.get('fonte'):
        erros.append('F3: número sem fonte')
    elif not _listada(valor['fonte'], fontes_video):
        erros.append(f"F3: fonte {valor['fonte']!r} não está na lista de fontes do vídeo")
    nat = valor.get('natureza')
    if (eh_dinheiro or any(q in _n(valor.get('contexto')) for q in QUALIFICA_EXC)) and not nat:
        erros.append('F4: natureza do valor não declarada (típico, excepcional, estimativa, histórico)')
    if nat and nat not in NATUREZAS:
        erros.append(f'F4: natureza inválida {nat!r}')
    ctx = _n(valor.get('contexto'))
    if any(q in ctx for q in QUALIFICA_EXC) and nat == 'tipico':
        erros.append('F4: contexto diz recorde/leilão/pico, mas a natureza está como típica')
    if nat == 'excepcional' and not any(q in _n(f"{valor.get('rotulo', '')} {valor.get('nota', '')} {valor.get('natureza_txt', '')}") for q in QUALIFICA_EXC):
        erros.append('F4: valor excepcional sem a palavra que o qualifica (recorde/leilão/pico) na tela')
    rot = _n(valor.get('rotulo'))
    if ('leilao' in ctx or 'vaga' in ctx) and re.search(r'\b(atravessar|travessia|passar|pedagio|tarifa)\b', rot) and not re.search(r'leilao|vaga', rot):
        erros.append('F5: rótulo apresenta lance de leilão por vaga como preço da travessia')
    return erros


def _listada(fonte: str, fontes: list[str]) -> bool:
    f = _n(fonte)
    return any(f in _n(x) or _n(x) in f for x in fontes if x)


def para_tela(valor: dict) -> dict:
    """Parâmetros de numero.animado a partir de um valor VALIDADO (moeda original em destaque; conversão em letra menor)."""
    p = {'rotulo': valor.get('rotulo', ''), 'valor': valor['valor'], 'casas': valor.get('casas', 0),
         'prefixo': MOEDAS.get(valor.get('moeda', ''), ''), 'unidade': valor.get('unidade', ''),
         'natureza': valor.get('natureza_txt') or NATUREZAS.get(valor.get('natureza', ''), ''),
         'contexto': valor.get('contexto', ''), 'fonte': valor.get('fonte', '')}
    cv = valor.get('conversao')
    if cv:
        p['conversao'] = f"≈ {MOEDAS.get(cv['moeda'], cv['moeda'])} {_fmt(cv['valor'])} {valor.get('unidade', '')} · câmbio de {cv['data']} ({cv['fonte']})".strip()
    if valor.get('equivalencia'):
        p['equivalencia'] = valor['equivalencia']
    else:   # V2.1: equivalência só por conversão exata de unidade (src/v2/unidades.py); sem unidade de volume, nenhuma
        from src.v2 import unidades
        eq = unidades.equivalencia(valor['valor'], valor.get('unidade', ''))
        if eq:
            p['equivalencia'] = eq
    return p


def _fmt(x) -> str:
    x = float(x)
    return f'{x:,.1f}'.replace(',', 'X').replace('.', ',').replace('X', '.').rstrip('0').rstrip(',')


# O CASO DO PANAMÁ, como deveria ter sido (dados da tabela de problemas; câmbio deixado sem conversão de propósito:
# a data/fonte do câmbio não estava nos fatos, então a tela mostra só a moeda original).
PANAMA_LEILAO = {'valor': 5.3, 'casas': 1, 'moeda': 'USD', 'unidade': 'milhões', 'natureza': 'excepcional', 'natureza_txt': 'LANCE RECORDE EM LEILÃO',
                 'rotulo': 'Leilão de uma vaga para cruzar', 'contexto': 'Lance em leilão por uma vaga (SK Gas, navio G. Spirit, 1º/09/2026); o pedágio é cobrado à parte.',
                 'fonte': 'Revista Oeste'}
PANAMA_ERRADO = {'valor': 27, 'unidade': 'milhões', 'prefixo': 'R$ ', 'rotulo': 'pagos por um navio para atravessar', 'nota': 'recorde com El Niño',
                 'contexto': 'lance em leilão por vaga', 'fonte': 'O GLOBO'}
