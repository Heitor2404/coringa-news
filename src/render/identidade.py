"""IDENTIDADE VISUAL do Coringa Explica (plano-mestre, etapa F — 12/11/2026): os tokens de design num lugar só.

Os valores são os que o template já usava (nenhuma mudança visual por trocar o número de lugar); o template declara os
mesmos tokens em :root e um teste confere que os dois continuam iguais. Uma identidade Coringa; o que varia é o
CONTEÚDO (qual componente explica a frase), não o estilo por cena.

Prioridade visual (de quem cede espaço): legenda < rótulo/etiqueta < gráfico/cartão. A legenda nunca disputa com eles: o
fiscal da tela (f4796c9) desce a legenda e esconde a etiqueta no trecho em conflito.
Cada componente responde a UMA pergunta (ver FUNCAO); componente sem função não entra (src/recursos.py confere).
"""
TOKENS = {
    'cor': {'destaque': '#FFD21F', 'alerta': '#ff4d4d', 'ok': '#3ddc84', 'info': '#5b9bff', 'fundo': '#05080f',
            'cartao': 'rgba(13,19,32,.88)', 'linha': 'rgba(255,255,255,.12)', 'apagado': '#9aa6bb'},
    'fonte': {'texto': 'Mont', 'dado': 'JBM'},
    'tamanho': {'titulo': 96, 'secao': 58, 'legenda': 76, 'rotulo': 26, 'etiqueta': 24, 'aviso': 24},
    'zona': {'topo': 270, 'base': 1480, 'direita': 930, 'margem': 50},
    'legivel_min': 24,              # px no quadro 1080×1920 (≈ 8,7 px de CSS num celular de 390 px)
}
FUNCAO = {
    'mapa': 'onde, distância, trajetória ou deslocamento',
    'numero': 'um número grande que é o centro da frase (com fonte nos fatos)',
    'comparacao': 'comparar quantidades (mesma unidade, valores dos fatos)',
    'escala': 'posicionar um valor numa escala conhecida',
    'linha_tempo': 'sequência de datas que conta a história (não lista disfarçada)',
    'lista': 'itens paralelos que a narração enumera',
    'cards': 'dois ou três fatos paralelos lado a lado',
    'citacao': 'frase real de alguém (só se estiver nos fatos)',
    'revelacao': 'a resposta da pergunta central (payoff)',
    'documento': 'evidência real, com procedência e tempo de leitura',
    'diagrama': 'mecanismo, processo ou causalidade',
    'foto': 'mostrar evento, pessoa, objeto, lugar ou prova',
}


def css_vars() -> dict[str, str]:
    """Os tokens como variáveis CSS (os nomes que o template declara em :root)."""
    t = TOKENS
    return {'--y': t['cor']['destaque'], '--r': t['cor']['alerta'], '--g': t['cor']['ok'], '--b': t['cor']['info'],
            '--bg': t['cor']['fundo'], '--card': t['cor']['cartao'], '--line': t['cor']['linha'], '--mut': t['cor']['apagado'],
            **{f'--fs-{k}': f'{v}px' for k, v in t['tamanho'].items()},
            **{f'--zona-{k}': f'{v}px' for k, v in t['zona'].items()}}
