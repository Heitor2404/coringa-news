"""Direção de cena por ACONTECIMENTO, não por título ou nome do tema.

O roteiro explicita objetivo, fato, evidência. O diretor escolhe tipo de cena
compatível com o que consegue provar, sem fazer mapa estático representar ação,
ou foto de outro episódio virar vídeo do evento. Regras genéricas para qualquer
assunto; o tipo semântico nunca contém nomes de países/guerras.
"""
from __future__ import annotations

INTENCOES={
    'localizar':(),
    'trajeto':(),
    'mostrar_registro':('photo','video'),
    'demonstrar_acao':('video','mechanism'),
    'comparar':('comparison',),
    'explicar_contexto':('photo','video'),
    'concluir':('video','comparison','photo','mechanism'),
}


def verificar(cenas: list[dict]) -> list[dict]:
    falhas=[]
    vistos=set()
    for c in cenas:
        d=c.get('direcao_evento')
        if d is None:
            continue  # legado preservado: migrar planos conscientemente
        cid=c.get('id') or '?'
        if not isinstance(d,dict) or d.get('intencao') not in INTENCOES:
            falhas.append({'codigo':'D-INTENCAO','cena':cid,
                           'motivo':'intenção visual não reconhecida'})
            continue
        intencao=d['intencao']
        fato=d.get('fato_id')
        if not isinstance(fato,str) or not fato.strip():
            falhas.append({'codigo':'D-SEM-FATO','cena':cid,
                           'motivo':'cada plano precisa de fato distinto do roteiro'})
        elif fato in vistos and not d.get('revisita_justificada'):
            falhas.append({'codigo':'D-FATO-REPETIDO','cena':cid,
                           'motivo':'mesma promessa visual repetida sem nova informação'})
        vistos.add(fato)
        if c.get('type') not in INTENCOES[intencao]:
            falhas.append({'codigo':'D-RECURSO-INCOMPATIVEL','cena':cid,
                           'motivo':f"{intencao} não pode ser demonstrado por {c.get('type')}"})
        if intencao in ('localizar','trajeto'):
            falhas.append({'codigo':'D-EXIGE-CARTOGRAFIA-ATLAS','cena':cid,
                           'motivo':'mapa exige PalcoMapa MapLibre com raster licenciado; recuso render alternativo simplificado'})
        if intencao=='mostrar_registro' and c.get('evidence')!='literal':
            falhas.append({'codigo':'D-REGISTRO-SEM-PROVA','cena':cid,
                           'motivo':'imagem genérica não pode comprovar evento específico'})
        if intencao=='demonstrar_acao' and c.get('type')=='video':
            if not d.get('acao_capturada'):
                falhas.append({'codigo':'D-ACAO-NAO-VERIFICADA','cena':cid,
                               'motivo':'vídeo só representa ação após checagem por frames reais'})
        if not isinstance(d.get('aprendizado'),str) or len(d['aprendizado'].strip())<10:
            falhas.append({'codigo':'D-SEM-APRENDIZADO','cena':cid,
                           'motivo':'resultado visível esperado não definido'})
    return falhas
