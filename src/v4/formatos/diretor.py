"""DIRETOR ORIENTADO POR FORMATO: o modelo NÃO inventa estilo nem animação — escolhe beats e PREENCHE primitivas aprovadas
em slots fixos, com mídia que já existe (biblioteca comprovada) e fatos verificados. A saída passa por `plano.validar`
(colisão, texto que não cabe, progressão, repetição, modalidades) e pelo preflight; erro volta UMA vez como correção.

Uso: `pedir(fatos, formato, narracao_palavras|None, chamar)`; `chamar(prompt) -> str` é injetado (Claude/Gemini do V4),
então o módulo é testável sem gastar cota.
"""
from __future__ import annotations

import json

from src.v4.formatos import plano as P

ESQUEMA = {
    'atlas.provaVisual': "{asset (FOTO REAL comprovada), meta: 'AUTOR · LICENÇA' (crédito obrigatório), enquadramento?: 'conter'|'cobrir', rotulo? (curto)} — usar composição atlas.prova, slot prova; imagem PRINCIPAL, não pino/card",
    'atlas.geoPin': "{tipo: 'local'|'foto', lonlat: [lon, lat] (DENTRO do roi do beat), rotulo, t_ativo?, lado?: 'direita'|'esquerda', asset?+meta (foto real com crédito), papel: 'protagonista'|'secundario' (posição, raio e deslocamento calculados pelo motor; NÃO escrever)} — slot 'geo': o pino segue a câmera",
    'editorial.statCard': "{valor (número ou texto curto), unidade, prefixo ('≈ '), rotulo, titulo, estilo: 'cartao'|'pilula'|'dial'|'cedula'|'selo' (cedula: cabecalho, rubrica, rubrica_dir, linhas [{texto, t?, marca_t?, dir?}]; selo: valor; dial: partes [{rotulo, fracao, cor}]); contagem?: bool}",
    'editorial.peopleCard': '{asset (retrato da biblioteca), nome, papel}',
    'editorial.hierarchy': "{niveis: [{rotulo, valor?}], ativo: [{i, t0}], alturas?: [0–1] (perfil), legenda_base?, legenda_t?}",
    'editorial.timeline': "{marcos: [{data, texto ≤ 22, t}]}",
    'dossie.documentCard': "{asset, cabecalho, cabecalho_dir (data), meta: ['DESCRIÇÃO · DATA', 'AUTOR · LICENÇA'], estilo: 'registro'|'documento', zoom?: {t0, escala ≥ 1.5, foco:[x,y]}}",
    'dossie.evidenceHighlight': "{tipo: 'carimbo'|'sublinhado'|'circulo', texto?, alvo: id de camada, parte?: 'cabecalho_dir'}",
    'editorial.comparison': '{itens: [{rotulo, valor, t?}], unidade}',
    'editorial.flowConnections': '{nos: [{rotulo ≤ 16, sub?, t, seta?}], fluxo: bool}',
    'editorial.cta': "inserido pelo MOTOR no último beat quando cabe (não use)",
    'editorial.titleOrPayoff': "{linhas: [{texto ≤ 16, t, destaque?}]} (≤ 3 linhas; nunca slide longo)",
}


def fichas_do_v3(contexto: dict | None) -> list[dict]:
    """Reusa a ficha V3 (acontecimento + forma + prova), sem criar outro classificador ATLAS.

    O chamador que já produziu roteiro e eventos V3 passa {roteiro, acervo,
    fatos, eventos}. Nenhum efeito se não houver contexto explicitamente fornecido.
    """
    if not contexto:
        return []
    from src.v3 import plano_av
    return plano_av.fichas(contexto['roteiro'], contexto.get('acervo') or {},
                          contexto.get('fatos') or [], contexto['eventos'])


def prompt(fatos: list[dict], formato: str, palavras: list[dict] | None, inventario: str | None, correcoes: list[dict] | None = None, anterior: str = '', contexto_v3: dict | None = None) -> str:
    if formato == 'atlas' and inventario is None:
        from src.v4.formatos import ponte_biblioteca
        inventario = ponte_biblioteca.inventario_para_diretor(fatos)
    F = P.CFG['formatos'][formato]
    comp = {k: v for k, v in P.COMP.items() if v.get('formato') == formato}
    slots = ('COMPOSIÇÕES (cada beat escolhe UMA em "composicao"; mapa exige "roi": [oeste, sul, leste, norte]; a câmera é calculada '
             'do roi e do movimento medido na referência; camadas usam os slots DA composição):\n' +
             '\n'.join(f"- {k}: {v.get('uso')} · movimento {v.get('movimento', '-')} · slots {', '.join(v['slots'])}" + (' · aceita pinos (slot geo)' if v.get('pinos') else '')
                       for k, v in comp.items())) if comp else '\n'.join(f'- {k}: x={v[0]} y={v[1]} w={v[2]} h={v[3]}' for k, v in P.SLOTS.items())
    comps = '\n'.join(f'- {c}: {ESQUEMA[c]}' for c in F['componentes'])
    fala = (' '.join(w['w'] for w in palavras) if palavras else '(escreva a narração em "narracao.texto", 60–90 s, só com os fatos)')
    instrucao_saida = (\
        'Responda SÓ um JSON válido, sem texto extra. ATLAS: "camera":"roi"; NÃO escreva "palco" (o motor gera). '\
        'Campos do plano: "formato", "canal", "video_id", "titulo", "duracao", "camera", "abertura_tipo", "rasters" (nomes reais), '\
        '"destaques", "rotas", "rotulos", "clipes", "explicacoes" e "beats". '\
        'Cada beat: "id", "composicao" da lista, "t" de início, "roi" numérico [oeste,sul,leste,norte], '\
        '"movimento" (aproxima/fixo/recua), "prova", "fatos", "camadas". '\
        'atlas.tecnica exige "funcao":"mecanismo" ou "estrutura". '\
        'Cada camada: "id", "componente", "slot", "t0", "t1", "p". '\
        'Se falta mídia real do inventário, NÃO substitua por algo diferente: reporte a ausência.'\
        if formato == 'atlas' else\
        'Responda SÓ o JSON válido do DOSSIÊ, com formato, canal, vídeo, título, duração, beats com composição e camadas.'\
    )
    direcao_atlas = """DIREÇÃO NARRATIVA REUTILIZÁVEL DO ATLAS (a identidade vem dos tokens do canal):
- Padrão aprovado V1: abertura_tipo:"mapa", beat 0 atlas.abertura, mapa hero desde o 1º quadro;
  nenhum clipe nos primeiros 3 segundos.
- Opcional V2, só com prova autenticamente identificada: abertura_tipo:"prova_real". FOTO: beat 0
  atlas.prova, atlas.provaVisual desde 0 até ao menos 2,5s, com origem e crédito. VÍDEO: beat 0
  atlas.abertura, clipe registro.video desde 0 até ao menos 2,5s, com fonte e hash verificável.
  Nunca fingir registro documental usando mecanismo técnico ou imagem genérica.
- Primeiro classifique a necessidade visual de cada trecho: geografia, fato real, funcionamento,
  comparação, revelação. Escolha mídia por pertinência e comprovação, sem cota de animações.
- Imagem real do objeto/fábrica/evento pode ocupar o plano principal com atlas.provaVisual em atlas.prova.
- Vídeo documental REAL comprovado usa clipes: [{t0,t1,componente:"registro.video",params:{asset:"ID DA BIBLIOTECA",inicio:0}}].
  O MP4 tem movimento próprio (sem câmera artificial), ocupa o intervalo todo e traz crédito do acervo;
  não atribua a ele uma ação que o arquivo não comprova, nem use vídeos genéricos como prova específica.
  Em abertura_tipo:"mapa", vídeo entra apenas após 3s. Em abertura_tipo:"prova_real", o
  vídeo autenticado pode iniciar em 0s; mapa aparece depois como consequência geográfica.
  Não sobrepor camadas ao intervalo de vídeo, pois ficariam invisíveis.
  Se não existir vídeo comprovado com duração/qualidade suficiente, reporte pendência, NÃO invente um arquivo.
- Animação técnica só quando mostra um processo que a mídia real não explica adequadamente.
- Se a narração continua explicando o MESMO processo, preserve a demonstração durante todo o
  intervalo, focando as peças e os fluxos citados. Não substitua o mecanismo por cards soltos.
- Declare todo clipe técnico em "explicacoes": [{id, tipo:"mecanismo", t0, t1, recurso}],
  onde recurso é o nome do componente aprovado, t0/t1 seguem as palavras da fala,
  e o clipe cobre integralmente o intervalo. O validador reprova se faltarem contratos.
- Focos físicos são selecionados por "focos": [{t, alvo, rotulo}], com alvos
  SEMÂNTICOS permitidos no catálogo do componente e tempo sincronizado com a fala.
  O componente calcula a câmera e a posição do rótulo: nunca invente coordenadas.
- Mostre UMA informação protagonista por vez. Máximo de 2 camadas editoriais
  simultâneas; rótulos de mecanismo curtos e legíveis, sem excesso de etiquetas.
- Dado final deve entrar na fala correspondente e encerrar sem repetir uma cena por decoração.
- Não corte narração para reduzir duração. Na dúvida sobre a cobertura visual, reporte pendência.
"""
    if formato != 'atlas':
        direcao_atlas = ''
    else:
        catalogo = F.get('alvos_componentes') or {}
        direcao_atlas += ("\nCATÁLOGO DE ALVOS FÍSICOS APROVADOS (não invente):\n" +
                         "\n".join(f"- {nome}: {', '.join(alvos)}" for nome, alvos in catalogo.items()))
    base = f"""Você preenche o formato {formato.upper()} do Coringa Explica. NÃO invente estilo, efeito nem animação: use SÓ as
primitivas e slots abaixo; posições são fixas. {F['descricao']}
REGRAS: cada beat prova visualmente a fala (diga a prova em "prova"); nova informação no conteúdo a cada ≤ {P.REGRAS['progressao_max_s']} s;
nada de duas camadas no mesmo slot ao mesmo tempo; mídia SÓ da lista comprovada (nunca invente registro); fotos licenciadas de pessoas reais, inclusive figuras públicas, SÃO PERMITIDAS quando a história exige uma pessoa; se o inventário não contiver a pessoa necessária, sinalize BLOQUEIO DE MÍDIA (não a substitua por um prédio); número com unidade;
no máximo {F['max_componentes_distintos']} primitivas distintas; tempos ancorados na fala ("@palavra", "@2:palavra+0.3", "@fim").
PALCOS: {', '.join(F['palcos'])} (troca de palco só quando a explicação muda de nível). CLIPES APROVADOS: {', '.join(F['clipes']) or 'nenhum'}.
IDENTIDADE É DO MOTOR: não escreva tamanho, raio, largura, cor, ajuste, transição, zoom_max nem deslocamento manual — o motor aplica
os tokens do canal. Mapa geográfico SEMPRE sobre base cartográfica da lista "rasters" que cubra o roi; diagrama técnico só em beat
com "funcao": "mecanismo" ou "estrutura".
SLOTS:\n{slots}\nPRIMITIVAS:\n{comps}\nMÍDIA COMPROVADA:\n{inventario}\nFATOS (use os ids):\n""" + \
        '\n'.join(f"- {f['id']}: {f['texto']}" for f in fatos) + f"""\n{direcao_atlas}

NARRAÇÃO:\n{fala}\n
{instrucao_saida}"""
    if formato == 'atlas' and contexto_v3:
        from src.v3 import plano_av
        fichas = fichas_do_v3(contexto_v3)
        base += ('\n\nFICHAS AUDIOVISUAIS DA V3 (contrato existente, não inferência livre):\n'
                 + plano_av.texto_prompt(fichas)
                 + '\nPara cada acontecimento crítico, escreva o id na chave evento_id do beat que o demonstra. '
                 'Sem mídia/componente ATLAS viável, sinalize bloqueio; nunca use card/mapa como substituto da ação.')
    if correcoes:
        base += '\n\nSEU PLANO VIOLOU REGRAS VERIFICADAS EM CÓDIGO; corrija só isto e devolva o JSON inteiro:\n' + \
                '\n'.join(f"- [{v['regra']}] {v['onde']}: {v['texto']}" for v in correcoes) + '\nANTERIOR:\n' + anterior[:20000]
    return base


def pedir(fatos: list[dict], formato: str, palavras: list[dict] | None, inventario: str | None, chamar, contexto_v3: dict | None = None) -> tuple[dict, list[dict]]:
    """→ (plano, violações restantes). No máximo UMA correção dirigida (cota é recurso escasso)."""
    from src.gemini import extrair_json
    bruto = chamar(prompt(fatos, formato, palavras, inventario, contexto_v3=contexto_v3))
    pl = extrair_json(bruto)
    viol = _violacoes(pl, palavras, contexto_v3)
    if viol:
        bruto = chamar(prompt(fatos, formato, palavras, inventario, viol, json.dumps(pl, ensure_ascii=False),
                              contexto_v3=contexto_v3))
        pl = extrair_json(bruto)
        viol = _violacoes(pl, palavras, contexto_v3)
    return pl, viol


def _violacoes(pl: dict, palavras: list[dict] | None, contexto_v3: dict | None = None) -> list[dict]:
    try:
        r = P.resolver_tempos(pl, palavras or [])
    except (ValueError, KeyError) as e:
        return [{'gravidade': 'erro', 'regra': 'F-ANCORA', 'onde': '-', 'texto': str(e)}]
    if isinstance(r.get('duracao'), str) or not r.get('duracao'):
        r['duracao'] = (palavras[-1]['e'] + .6) if palavras else 0
    violacoes = [v for v in P.validar(r) if v['gravidade'] == 'erro']
    if r.get('formato') == 'atlas' and contexto_v3:
        aprovadas = set(P.CFG['formatos']['atlas']['componentes'] + P.CFG['formatos']['atlas']['clipes'])
        beats = r.get('beats') or []
        for ficha in fichas_do_v3(contexto_v3):
            if not ficha.get('critico'):
                continue
            fid = ficha['evento_id']
            if not any(b.get('evento_id') == fid for b in beats):
                violacoes.append({'gravidade': 'erro', 'regra': 'F-EVENTO-SEM-BEAT',
                                  'onde': fid, 'texto': 'acontecimento crítico da V3 não possui beat correspondente'})
            if ficha.get('status') == 'indisponivel':
                violacoes.append({'gravidade': 'erro', 'regra': 'F-PROVA-INDISPONIVEL',
                                  'onde': fid, 'texto': ficha['representacao_necessaria']})
            if ficha.get('forma_visual') == 'esquema' and not (set(ficha.get('composicoes_viaveis') or []) & aprovadas):
                violacoes.append({'gravidade': 'erro', 'regra': 'F-MECANISMO-FORA-ATLAS',
                                  'onde': fid, 'texto': 'V3 prevê mecanismo, mas nenhum componente está homologado no ATLAS'})
    return violacoes
