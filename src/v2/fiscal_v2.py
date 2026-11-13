"""FISCAL V2.1: três categorias separadas, cada achado com evidência e solução.

Antes (V2) o fiscal misturava bloqueio e gosto. Agora:

  DETERMINÍSTICO — medido, sem interpretação. Pode BLOQUEAR.
    D1 texto sobre texto / fora do quadro, persistente (≥ 0,75 s)              (antigo B4)
    D2 texto na zona da interface da plataforma (aviso)
    D3 letra abaixo do mínimo do token (V2.T.fs.min = 26 px) (aviso)
    D4 legenda sem posição livre na cena (conflito registrado pelo palco)
    D5 arquivo referenciado (imagem, vídeo, mascote) que não existe              — bloqueia
    D6 texto acima do limite declarado pela composição (meta.limites)           — aviso
    D7 coordenada inválida (fora do globo / fora do país declarado)              — bloqueia
    D8 rota marítima que atravessa continente (geo.validar_rota)                 — bloqueia
    D9 número que não passou em fatos.validar()                                  (antigo B3) — bloqueia
    D10 revelação mostrada antes de ser dita ou > 0,4 s depois                   (antigo B5) — bloqueia
    D11 plano longo fora de mecanismo (> 8 s), loudness fora de −14 ± 1 LUFS    — aviso
  SEMÂNTICO — o que a tela mostra contradiz ou não cumpre o que a fala diz. Pode BLOQUEAR.
    S1 acontecimento crítico sem representação (capacidades → limitação)        (antigo B1)
    S2 fala promete mecanismo/processo e a cena mostra foto ou texto             (antigo B2)
    S3 eclusa animada no sentido contrário ao da fala (sobe × desce)
    S4 dados insuficientes para o que a fala sugere (gráfico/número recusado) — aviso
  ESTÉTICO — NÃO bloqueia nem vira nota. Sinais medidos (mesma composição em sequência, imagem repetida, foto
    parada) entram como observação, e as perguntas abertas ficam para o Heitor.

Cada achado: {categoria, codigo, gravidade (bloqueio|aviso|observacao), cena, comp, instante, problema, evidencia, solucao}.
As chaves antigas `bloqueios`/`avisos` continuam (mesmos códigos antigos B1–B5 entre parênteses em `codigo_v2`).
"""
from __future__ import annotations

import re
from pathlib import Path

from src.v2 import capacidades

MECANISMOS = {'mecanismo.eclusa', 'mecanismo.nivel', 'processo.etapas', 'diagrama.explicativo', 'forcas.vetores', 'astronomia.orbita', 'evento.impacto'}
PERGUNTAS = ['A abertura faz querer ver o resto (sem depender da legenda)?', 'O mecanismo ficou claro só olhando a tela, sem som?',
             'Algum gráfico/mapa ficou bonito mas não explicou nada?', 'Alguma foto parece de banco de imagens, sem relação com a fala?',
             'O ritmo cansa em algum trecho (anotar o segundo)?', 'O encerramento tem cara de marca (mascote, marca, fontes legíveis)?']
ANTIGO = {'D1': 'B4', 'D9': 'B3', 'D10': 'B5', 'S1': 'B1', 'S2': 'B2'}
SOLUCAO = {
    'D1': 'mover/encolher o elemento ou mudar a posição da legenda na cena', 'D2': 'trazer o texto para dentro da área segura (V2.Z)',
    'D3': 'subir para ≥ 26 px (token fs.min)', 'D4': 'a composição deve liberar uma faixa (1240–1455 ou 360) ou declarar legenda integrada',
    'D5': 'trocar pelo arquivo correto ou remover a referência', 'D6': 'encurtar o texto (o limite vem do catálogo da composição)',
    'D7': 'corrigir lon/lat a partir da fonte', 'D8': 'redesenhar a rota pelo mar (pontos intermediários) ou marcar tipo correto',
    'D9': 'usar o valor e o contexto exatos da fonte (fatos.validar)', 'D10': 'ajustar a virada para o instante em que a palavra é dita',
    'D11': 'dividir o plano / normalizar o áudio', 'S1': 'fornecer os dados que a composição exige ou reescrever a fala',
    'S2': 'trocar a foto pela composição de mecanismo', 'S3': 'inverter o sentido da animação para bater com a fala',
    'S4': 'conseguir os valores com fonte ou deixar a fala sem promessa de comparação', 'E': 'avaliação humana',
}
_SOBE = re.compile(r'\b(sob[ea]\w*|subi\w*|ench\w*|elev\w*|ergu\w*)')
_DESCE = re.compile(r'\b(desc[ei]\w*|esvazi\w*|baix\w*|escoa\w*)')


def _persistentes(geo: list[dict], passo: float = .25, minimo: float = .75) -> list[dict]:
    grupos = {}
    for p in sorted(geo, key=lambda x: x['t']):
        k = (p['tipo'], p['txt'])
        g = grupos.setdefault(k, [])
        if g and p['t'] - g[-1]['fim'] <= passo * 1.5:
            g[-1]['fim'] = p['t']
        else:
            g.append({**p, 'ini': p['t'], 'fim': p['t']})
    return [x for g in grupos.values() for x in g if x['fim'] - x['ini'] + passo >= minimo]


def _achado(cat, cod, grav, cena, comp, t, problema, evidencia, solucao=None):
    return {'categoria': cat, 'codigo': cod, 'codigo_v2': ANTIGO.get(cod, ''), 'gravidade': grav, 'cena': cena, 'comp': comp,
            'instante': None if t is None else round(float(t), 2), 'problema': problema, 'evidencia': evidencia,
            'solucao': solucao or SOLUCAO.get(cod, SOLUCAO['E'])}


def _arquivos(x, pref=''):
    """Caminhos de arquivo citados nos params (img, video, pose de mascote, fundo…)."""
    if isinstance(x, dict):
        for k, v in x.items():
            yield from _arquivos(v, k)
    elif isinstance(x, list):
        for v in x:
            yield from _arquivos(v, pref)
    elif isinstance(x, str) and pref in ('img', 'imagem', 'video', 'arq', 'antes', 'depois', 'foto') and (x.startswith('/') or re.search(r'\.(jpe?g|png|webp|mp4|mov|webm)$', x, re.I)):
        yield x


def _cena_de(cenas, t):
    return next((k for k, sc in enumerate(cenas) if sc['start'] <= t < sc['end']), None)


def avaliar(dados_v2: dict, direcao: list[dict], geometria: list[dict] | None = None, dados_v1: dict | None = None,
            audio: dict | None = None, catalogo: dict | None = None, conflitos_legenda: list | None = None) -> dict:
    """`catalogo`: {id: meta} (para limites de texto); `conflitos_legenda`: V2.conflitosLegenda do palco."""
    from src.v2 import geo as geomod
    A = []
    cenas = dados_v2['scenes']
    direcao = list(direcao) + [{}] * (len(cenas) - len(direcao))
    for k, (sc, d) in enumerate(zip(cenas, direcao)):
        ini, comp, p = round(sc['start'], 2), sc['comp'], sc.get('params') or {}
        # S1
        if d.get('limitacao') and (d.get('critica') or sc.get('limitacao')) and d.get('comp') is None:
            A.append(_achado('semantico', 'S1', 'bloqueio', k, comp, ini, 'acontecimento crítico sem representação', d['limitacao']))
        if d.get('aviso'):
            A.append(_achado('semantico', 'S4', 'aviso', k, comp, ini, 'dados insuficientes para o que a fala sugere', d['aviso']))
        # D9
        if d.get('bloqueio'):
            A.append(_achado('deterministico', 'D9', 'bloqueio', k, comp, ini, 'número sem validação', '; '.join(d['bloqueio'])))
        for a in d.get('avisos', []):
            A.append(_achado('estetico', 'E-rep' if 'repetida' in a else 'E-ritmo', 'observacao', k, comp, ini, a, a))
        # D5 arquivos
        for arq in set(_arquivos({'params': p, 'fundo': sc.get('fundo') or {}})):
            if not Path(arq).exists():
                A.append(_achado('deterministico', 'D5', 'bloqueio', k, comp, ini, 'arquivo referenciado não existe', arq))
        # D6 limites
        lim = ((catalogo or {}).get(comp) or {}).get('limites') or {}
        for campo, mx in lim.items():
            v = p.get(campo)
            if isinstance(v, str) and isinstance(mx, (int, float)) and len(v.replace('*', '')) > mx:
                A.append(_achado('deterministico', 'D6', 'aviso', k, comp, ini, f'texto "{campo}" acima do limite', f'{len(v.replace("*", ""))} > {mx} caracteres: "{v[:50]}"'))
        # D7 / D8 mapas
        if comp.startswith('mapa.'):
            pts = list(p.get('pontos') or [])
            for e in geomod.coordenadas_validas(pts):
                A.append(_achado('deterministico', 'D7', 'bloqueio', k, comp, ini, 'coordenada inválida', e))
            rotas = [(r.get('nome', f'rota {i}'), r.get('rota') or [[x['lon'], x['lat']] for x in r.get('pontos') or []]) for i, r in enumerate(p.get('rotas') or [])]
            if p.get('rota'):
                rotas.append(('rota', p['rota']))
            tipo = p.get('tipo', 'maritima' if comp == 'mapa.rota' else '')
            for nome, r in rotas:
                if len(r) >= 2 and tipo == 'maritima':
                    v = geomod.validar_rota(r, 'maritima')
                    if not v['ok']:
                        A.append(_achado('deterministico', 'D8', 'bloqueio', k, comp, ini, f'rota marítima "{nome}" atravessa terra',
                                         f"{v['em_terra'] * 100:.1f}% do traçado sobre {', '.join(v['paises'])}"))
        # S3 eclusa × fala
        if comp == 'mecanismo.eclusa':
            fala = capacidades._n(sc.get('fala', ''))
            diz = 'descer' if _DESCE.search(fala) and not _SOBE.search(fala) else 'subir' if _SOBE.search(fala) and not _DESCE.search(fala) else None
            mostra = p.get('sentido', 'subir')
            if diz and diz != mostra:
                A.append(_achado('semantico', 'S3', 'bloqueio', k, comp, ini, 'eclusa no sentido contrário ao da fala', f'fala: "{sc.get("fala", "")[:60]}" ({diz}); animação: {mostra}'))
        # D11 plano
        dur = sc['end'] - sc['start']
        if dur > 8 and comp not in MECANISMOS | {'linha_tempo.historica'}:
            A.append(_achado('deterministico', 'D11', 'aviso', k, comp, ini, 'plano longo', f'{dur:.1f} s'))
        if k and comp == cenas[k - 1]['comp'] and p == cenas[k - 1].get('params') and (sc.get('fundo') or {}).get('img') == (cenas[k - 1].get('fundo') or {}).get('img'):
            A.append(_achado('estetico', 'E-cont', 'observacao', k, comp, ini, 'mesma composição e mesmos dados da cena anterior', comp))
    # S2
    if dados_v1:
        for i, s in enumerate(dados_v1['scenes']):
            if s.get('tipo') not in ('historia', 'imagem'):
                continue
            achados = [a for a in capacidades.detectar(s) if a['critica'] and a['por_texto']]
            mec = (s.get('bloco') or {}).get('funcao') == 'mecanismo' or any(a['capacidade'] in ('agua_subindo', 'agua_descendo', 'elevacao_vertical', 'manobra_eclusa', 'processo', 'forca', 'explosao', 'maquina') for a in achados)
            if not mec:
                continue
            k = next((k for k, sc in enumerate(cenas) if i in sc.get('origem', [])), None)
            if k is not None and cenas[k]['comp'] not in MECANISMOS:
                A.append(_achado('semantico', 'S2', 'bloqueio', k, cenas[k]['comp'], s['start'], 'fala descreve mecanismo e a tela não mostra',
                                 f'"{re.sub(r"[*]", "", s.get("fala", ""))[:60]}" → {cenas[k]["comp"]}'))
    # D1–D3 geometria (amostrada pelo palco)
    for g in _persistentes(geometria or []):
        k = _cena_de(cenas, g['ini'])
        if g.get('grave'):
            A.append(_achado('deterministico', 'D1', 'bloqueio', k, g.get('cena'), g['ini'], f"{g['tipo']} persistente", f"{g['txt']} ({g['ini']:.1f}–{g['fim']:.1f} s)"))
        else:
            cod = 'D3' if g['tipo'] == 'pequeno' else 'D2' if g['tipo'] == 'zona' else 'D1'
            A.append(_achado('deterministico', cod, 'aviso', k, g.get('cena'), g['ini'], g['tipo'], f"{g['txt']} ({g['ini']:.1f}–{g['fim']:.1f} s)"))
    for c in conflitos_legenda or []:
        A.append(_achado('deterministico', 'D4', 'aviso', c.get('cena'), c.get('comp'), c.get('t'), 'legenda sem posição livre', str(c)))
    # D10
    for k, sc in enumerate(cenas):
        if sc['comp'] != 'revelacao.surpresa':
            continue
        alvo = {w.lower() for w in re.findall(r'\w{3,}', str(sc['params'].get('resposta', '')))}
        dito = next((w.get('s', c['start']) for c in dados_v2.get('captions', []) for w in c['words']
                     if sc['start'] <= w.get('s', c['start']) <= sc['end'] and re.sub(r'\W', '', w['w'].lower()) in alvo), None)
        if dito is not None:
            mostra = sc['start'] + float(sc['params'].get('virada', 1.0))
            if mostra < dito - .4 or mostra > dito + .4:
                A.append(_achado('deterministico', 'D10', 'bloqueio', k, sc['comp'], mostra, 'revelação fora de sincronia', f'aparece em {mostra:.2f} s, é dita em {dito:.2f} s'))
    if audio and audio.get('lufs') is not None and abs(audio['lufs'] + 14) > 1:
        A.append(_achado('deterministico', 'D11', 'aviso', None, None, 0, 'loudness fora da meta', f"{audio['lufs']:.1f} LUFS (meta −14 ± 1)"))
    for q in PERGUNTAS:
        A.append(_achado('estetico', 'E-pergunta', 'observacao', None, None, None, q, 'sem medida automática'))

    bloq = [a for a in A if a['gravidade'] == 'bloqueio']
    criticas = [d for d in direcao if d.get('critica')]
    det = {
        'cenas': len(cenas), 'acontecimentos_criticos': len(criticas), 'criticos_representados': sum(1 for d in criticas if d.get('comp')),
        'mecanismos_na_tela': sum(1 for sc in cenas if sc['comp'] in MECANISMOS),
        'numeros_bloqueados': sum(1 for d in direcao if d.get('bloqueio')),
        'problemas_geometricos_graves': sum(1 for b in bloq if b['codigo'] == 'D1'),
        'imagens_repetidas': sum(1 for a in A if a['codigo'] == 'E-rep'),
        'maior_plano_s': round(max((sc['end'] - sc['start'] for sc in cenas), default=0), 1),
        'composicoes_distintas': len({sc['comp'] for sc in cenas}),
    }
    compat = lambda a: {'codigo': a['codigo_v2'] or a['codigo'], 'cena': a['cena'], 'inicio': a['instante'], 'texto': f"{a['problema']}: {a['evidencia']}"}
    return {'aprovado_tecnicamente': not bloq, 'achados': A,
            'por_categoria': {c: {'bloqueios': sum(1 for a in A if a['categoria'] == c and a['gravidade'] == 'bloqueio'),
                                  'avisos': sum(1 for a in A if a['categoria'] == c and a['gravidade'] == 'aviso'),
                                  'observacoes': sum(1 for a in A if a['categoria'] == c and a['gravidade'] == 'observacao')}
                              for c in ('deterministico', 'semantico', 'estetico')},
            'bloqueios': [compat(a) for a in bloq], 'avisos': [compat(a) for a in A if a['gravidade'] == 'aviso'],
            'deterministico': det,
            'subjetivo': {'estado': 'pendente de avaliação humana (sem nota automática)', 'perguntas': PERGUNTAS}}


def texto(r: dict) -> str:
    linhas = [f"FISCAL V2.1 — {'sem bloqueio' if r['aprovado_tecnicamente'] else str(len(r['bloqueios'])) + ' bloqueio(s)'}"]
    for c, n in r['por_categoria'].items():
        linhas.append(f"  {c}: {n['bloqueios']} bloqueio(s), {n['avisos']} aviso(s), {n['observacoes']} observação(ões)")
    for a in r['achados']:
        if a['codigo'] == 'E-pergunta':
            continue
        marca = {'bloqueio': '✘', 'aviso': '!', 'observacao': '·'}[a['gravidade']]
        t = '' if a['instante'] is None else f"{a['instante']:.2f}s "
        linhas.append(f"  {marca} {a['codigo']} cena {a['cena']} {t}{a['problema']} — {a['evidencia'][:110]} → {a['solucao']}")
    linhas.append('  medidas: ' + ', '.join(f'{k}={v}' for k, v in r['deterministico'].items()))
    linhas.append('  estética: ' + r['subjetivo']['estado'])
    return '\n'.join(linhas)


def tabela_md(r: dict) -> str:
    """Relatório em tabela (cena | instante | problema | evidência | gravidade | solução)."""
    out = ['| categoria | código | cena | instante | problema | evidência | gravidade | solução |', '|---|---|---|---|---|---|---|---|']
    for a in r['achados']:
        if a['codigo'] == 'E-pergunta':
            continue
        ev = str(a['evidencia']).replace('|', '/')[:120]
        out.append(f"| {a['categoria']} | {a['codigo']} | {'' if a['cena'] is None else a['cena']} | {'' if a['instante'] is None else a['instante']} | {a['problema']} | {ev} | {a['gravidade']} | {a['solucao']} |")
    return '\n'.join(out)
