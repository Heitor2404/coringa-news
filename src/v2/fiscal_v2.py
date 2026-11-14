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
    D12 (V2.2) foto de arquivo sem resolução/proporção para ser protagonista (vira faixa fina ou exige ampliação
        destrutiva; acervo_v2.adequacao_historica) — bloqueio: buscar o original ou outra foto autêntica
  SEMÂNTICO — o que a tela mostra contradiz ou não cumpre o que a fala diz. Pode BLOQUEAR.
    S1 acontecimento crítico sem representação (capacidades → limitação)        (antigo B1)
    S2 fala promete mecanismo/processo e a cena mostra foto ou texto             (antigo B2)
    S3 eclusa animada no sentido contrário ao da fala (sobe × desce)
    S4 dados insuficientes para o que a fala sugere (gráfico/número recusado) — aviso
    S5 (V2.2) acontecimento DECLARADO pelo roteiro (contrato) × o que foi selecionado × o que a composição é capaz de
       mostrar × se a cena existe/foi renderizada; substituição genérica de acontecimento crítico — bloqueio
    S6 (V2.2) cena narrativa sem acontecimento declarado e que os padrões não reconheceram: a seleção não tem como
       saber se havia algo a mostrar → REVISÃO HUMANA obrigatória (gravidade 'revisao': impede a aprovação automática)
  ESTÉTICO — NÃO bloqueia nem vira nota. Sinais medidos (mesma composição em sequência, imagem repetida, foto
    parada) entram como observação, e as perguntas abertas ficam para o Heitor.

Cada achado: {categoria, codigo, gravidade (bloqueio|revisao|aviso|observacao), cena, comp, instante, problema, evidencia, solucao}.
`aprovacao_automatica` só é verdadeira sem bloqueio E sem revisão pendente.
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
    'D11': 'dividir o plano / normalizar o áudio',
    'D12': 'usar o original em resolução maior (ou outra foto autêntica do mesmo fato); nunca inventar resolução nem ampliar além de 1,5×', 'S1': 'fornecer os dados que a composição exige ou reescrever a fala',
    'S2': 'trocar a foto pela composição de mecanismo', 'S3': 'inverter o sentido da animação para bater com a fala',
    'S4': 'conseguir os valores com fonte ou deixar a fala sem promessa de comparação',
    'S5': 'fornecer os dados exigidos pela composição capaz (ver evidência) ou criar a composição que falta; nunca trocar por foto',
    'S6': 'o roteiro deve declarar o acontecimento da cena (contrato: tipo, mostrar, dados); até lá, um humano confere a cena',
    'E': 'avaliação humana',
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


COMPS_FOTO = ('foto.documental', 'foto.historica', 'lower_third', 'banner.discreto')
FOTO_REAL = ('foto.documental', 'foto.historica', 'video.documental', 'abertura.pergunta', 'lower_third', 'banner.discreto')
TECNICO = re.compile(r'BLOQUEAD|SEM VERIFICA|SEM ACERVO|PENDENTE|TODO\b|FIXME|\bundefined\b|\bNaN\b|\bnull\b|\bNone\b|placeholder', re.I)
CODIGO = re.compile(r'(?:[FSDAP]\d{1,2}\s*[;,]?\s*)+')


def _textos(x) -> list[str]:
    """Todos os textos de um dicionário de parâmetros (o que pode aparecer na tela)."""
    if isinstance(x, str):
        return [x] if not x.startswith(('file:', '/', 'http')) and not re.fullmatch(r'[#\w.-]+\.(jpg|png|webp|mp4)', x) else []
    if isinstance(x, dict):
        return [t for k, v in x.items() if k not in ('img', 'video', 'recorte', 'cor', 'icone', 'variante', 'tipo', 'sentido', 'modo', 'representacao')
                for t in _textos(v)]
    if isinstance(x, (list, tuple)):
        return [t for v in x for t in _textos(v)]
    return []


def _quadro_vazio(arq) -> bool:
    """Quadro escuro e uniforme fora do cabeçalho e da faixa de legenda: tela preta com só a legenda."""
    try:
        from PIL import Image
        import numpy as np
        with Image.open(arq) as im:
            g = np.asarray(im.convert('L').resize((108, 192)), float)
        area = np.concatenate([g[25:120], g[150:]])
        return area.mean() < 28 and area.std() < 10
    except Exception:
        return False


def _adequada(sc: dict, d: dict, ac: dict, renderizadas, k) -> str:
    """'sim' (representa), 'declarada' (imagem pedida; crítico → revisão humana), 'render' (não apareceu) ou 'nao'."""
    from src.v2 import contrato as ct
    comp = sc['comp']
    rep = ac.get('representacao') if isinstance(ac.get('representacao'), dict) else {}
    tem_img = bool((sc.get('fundo') or {}).get('img') or (sc.get('params') or {}).get('img'))
    if renderizadas is not None and k not in renderizadas:
        return 'render'
    if comp in ct.capazes(ac['tipo']) and not (comp in ct.GENERICAS and ac['tipo'] not in ('pessoa', 'lugar', 'ambiente')):
        return 'sim'
    if rep.get('modo') == 'composicao' and comp == rep.get('comp'):
        return 'sim'
    if rep.get('modo') == 'foto_direta' and comp in FOTO_REAL and tem_img:
        return 'sim'
    if rep.get('modo') == 'editorial' and comp in ('revelacao.surpresa', 'abertura.pergunta', 'encerramento.editorial', 'numero.animado'):
        return 'sim'
    if rep.get('modo') == 'foto_declarada' and comp in FOTO_REAL and tem_img:
        return 'declarada'
    return 'nao'


def avaliar(dados_v2: dict, direcao: list[dict], geometria: list[dict] | None = None, dados_v1: dict | None = None,
            audio: dict | None = None, catalogo: dict | None = None, conflitos_legenda: list | None = None,
            renderizadas: list | None = None, quadros: dict | None = None) -> dict:
    """`catalogo`: {id: meta} (para limites de texto); `conflitos_legenda`: V2.conflitosLegenda do palco;
    `renderizadas`: índices das cenas V2 que tiveram conteúdo visível no palco (None = não verificado)."""
    from src.v2 import geo as geomod
    A = []
    cenas = dados_v2['scenes']
    direcao = list(direcao) + [{}] * (len(cenas) - len(direcao))
    for k, (sc, d) in enumerate(zip(cenas, direcao)):
        ini, comp, p = round(sc['start'], 2), sc['comp'], sc.get('params') or {}
        if d.get('aviso'):
            A.append(_achado('semantico', 'S4', 'aviso', k, comp, ini, 'dados insuficientes para o que a fala sugere', d['aviso']))
        # D9
        if d.get('bloqueio'):
            A.append(_achado('deterministico', 'D9', 'bloqueio', k, comp, ini, 'número sem validação', '; '.join(d['bloqueio'])))
        for a in d.get('avisos', []):
            A.append(_achado('estetico', 'E-rep' if 'repetida' in a else 'E-ritmo', 'observacao', k, comp, ini, a, a))
        # D13 (correção do piloto): cena sem conteúdo visual — composição de foto sem imagem (tela preta com só a legenda)
        if comp in COMPS_FOTO and not ((sc.get('fundo') or {}).get('img') or p.get('img')):
            A.append(_achado('deterministico', 'D13', 'bloqueio', k, comp, ini, 'cena sem conteúdo visual', f"{comp} sem imagem por {sc['end'] - sc['start']:.1f} s"))
        if quadros and k in quadros and _quadro_vazio(quadros[k]):
            A.append(_achado('deterministico', 'D13', 'bloqueio', k, comp, ini, 'cena sem conteúdo visual', f'quadro {Path(quadros[k]).name}: tela escura e uniforme fora da legenda'))
        # D14 (correção do piloto): texto técnico/interno na tela ("NÚMERO BLOQUEADO", "SEM ACERVO", códigos F3…)
        tecnico = [t for t in _textos(p) if TECNICO.search(t) or CODIGO.fullmatch(t.strip())]
        if tecnico:
            A.append(_achado('deterministico', 'D14', 'bloqueio', k, comp, ini, 'mensagem interna/técnica na tela', '; '.join(tecnico)[:120]))
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
        # D12 foto de arquivo protagonista
        if comp == 'foto.historica' and p.get('img') and Path(str(p['img'])).exists():
            from PIL import Image
            from src.v2 import acervo_v2
            with Image.open(p['img']) as im:
                wh = im.size
            rc = p['recorte'] if isinstance(p.get('recorte'), list) else acervo_v2.recorte_conteudo(p['img'])
            ad = acervo_v2.adequacao_historica(wh, rc)
            if ad['modo'] == 'insuficiente':
                A.append(_achado('deterministico', 'D12', 'bloqueio', k, comp, ini, 'foto de arquivo sem resolução para ser protagonista',
                                 f"{Path(str(p['img'])).name}: {ad['motivo']}"))
        # D12 também para a foto de FUNDO (foto.documental e cenas sobre foto): panorâmica em moldura sem altura possível
        fu = sc.get('fundo') or {}
        arq_f = str(fu.get('img') or '').replace('file://', '')
        if comp != 'foto.historica' and arq_f and Path(arq_f).exists() and (fu.get('modo') in ('moldura', 'arquivo')):
            from PIL import Image
            from src.v2 import acervo_v2
            with Image.open(arq_f) as im:
                wh = im.size
            ad = acervo_v2.adequacao_historica(wh)
            if ad['modo'] == 'insuficiente':
                A.append(_achado('deterministico', 'D12', 'bloqueio', k, comp, ini, 'foto sem resolução para ser protagonista',
                                 f"{Path(arq_f).name}: {ad['motivo']}"))
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
    # S1/S2/S5/S7 por ACONTECIMENTO (correção do piloto): os fragmentos de uma fala dividida são avaliados juntos, a
    # mesma causa conta uma vez, e foto real que mostra o fato (conferida pelo preparo no catálogo) é representação válida
    from src.v2 import contrato as ct
    prep = ((dados_v1 or {}).get('meta') or {}).get('preparo') or {}
    faltam_prep = {b['evento']: b['faltam'] for b in prep.get('bloqueios') or []}
    eventos, ordem_ev = {}, []

    def _ev(eid, ac, crit):
        if eid not in eventos:
            eventos[eid] = {'ac': ac, 'critico': crit, 'v2': [], 'v1': []}
            ordem_ev.append(eid)
        return eventos[eid]
    if dados_v1:
        for i1, s1 in enumerate(dados_v1['scenes']):
            ac = ct.declarado(s1)
            if not ac:
                continue
            ev = _ev(ac.get('id') or s1.get('evento') or f'v1:{i1}', ac, ct.critico(ac))
            ev['v1'].append(i1)
            ev['v2'] += [k for k, sc in enumerate(cenas) if i1 in sc.get('origem', []) and k not in ev['v2']]
    else:
        for k, d in enumerate(direcao):
            ac = d.get('acontecimento')
            if ac and ac.get('tipo'):
                _ev(ac.get('id') or f'v2:{k}', ac, ct.critico(ac))['v2'].append(k)
    for eid in ordem_ev:
        ev = eventos[eid]
        ac, ks = ev['ac'], sorted(ev['v2'])
        if not ev['critico']:
            continue
        rot = f"{ac['tipo']} — {ac.get('mostrar') or ac.get('acao') or eid}"
        if not ks:
            A.append(_achado('semantico', 'S5', 'bloqueio', None, None, None, 'acontecimento crítico declarado sem cena no vídeo', f'{eid}: {rot}'))
            continue
        modos = [_adequada(cenas[k], direcao[k] if k < len(direcao) else {}, ac, renderizadas, k) for k in ks]
        if 'sim' in modos:
            continue
        na_tela = ', '.join(dict.fromkeys(cenas[k]['comp'] for k in ks))
        if 'declarada' in modos:
            A.append(_achado('semantico', 'S7', 'revisao', ks[0], na_tela, cenas[ks[0]]['start'],
                             'acontecimento crítico mostrado pela imagem pedida, sem prova do estado narrado',
                             f"{eid} ({rot}); cenas {ks}: um humano confere se a imagem explica o fato"))
            continue
        falta = faltam_prep.get(eid) or next((direcao[k].get('faltam') for k in ks if k < len(direcao) and direcao[k].get('faltam')), None) \
            or [x for k in ks if k < len(direcao) for x in [direcao[k].get('limitacao') or direcao[k].get('substituicao')] if x]
        A.append(_achado('semantico', 'S5', 'bloqueio', ks[0], na_tela, cenas[ks[0]]['start'],
                         'cena do acontecimento crítico sem conteúdo visível no render' if 'render' in modos else 'acontecimento crítico sem representação adequada',
                         f"{eid}: declarado {rot}; capazes: {', '.join(ct.capazes(ac['tipo'])) or 'nenhuma'}; na tela: {na_tela} (cenas {ks})"
                         + (f"; falta: {' | '.join(map(str, falta))[:220]}" if falta else '')))
    for r in prep.get('revisoes') or []:
        if not any(a['codigo'] == 'S7' and a['evidencia'].startswith(f"{r['evento']} ") for a in A):
            ks = sorted({k for i1 in r.get('cenas') or [] for k, sc in enumerate(cenas) if i1 in sc.get('origem', [])})
            A.append(_achado('semantico', 'S7', 'revisao', ks[0] if ks else None, None, cenas[ks[0]]['start'] if ks else None,
                             r['problema'], f"{r['evento']} {r['evidencia']}"))
    # formato antigo (sem contrato): S1/S2/substituição/S6 continuam, agrupados pela ideia (um achado por causa)
    com_contrato = {i1 for ev in eventos.values() for i1 in ev['v1']}
    vistos = set()
    if dados_v1:
        for i1, s1 in enumerate(dados_v1['scenes']):
            if i1 in com_contrato or s1.get('tipo') not in ('historia', 'imagem'):
                continue
            achados = [a for a in capacidades.detectar(s1) if a['critica'] and a['por_texto']]
            mec = (s1.get('bloco') or {}).get('funcao') == 'mecanismo' or any(a['capacidade'] in ('agua_subindo', 'agua_descendo', 'elevacao_vertical', 'manobra_eclusa', 'processo', 'forca', 'explosao', 'maquina') for a in achados)
            k = next((k for k, sc in enumerate(cenas) if i1 in sc.get('origem', [])), None)
            chave = ('S2', s1.get('evento') or s1.get('grupo') or i1)
            if mec and k is not None and cenas[k]['comp'] not in MECANISMOS and chave not in vistos:
                vistos.add(chave)
                A.append(_achado('semantico', 'S2', 'bloqueio', k, cenas[k]['comp'], s1['start'], 'fala descreve mecanismo e a tela não mostra',
                                 f'"{re.sub(r"[*]", "", s1.get("fala", ""))[:60]}" → {cenas[k]["comp"]}'))
    for k, d in enumerate(direcao):
        if k >= len(cenas) or any(i1 in com_contrato for i1 in cenas[k].get('origem', [])):
            continue
        if d.get('limitacao') and (d.get('critica') or cenas[k].get('limitacao')) and d.get('comp') is None:
            A.append(_achado('semantico', 'S1', 'bloqueio', k, cenas[k]['comp'], round(cenas[k]['start'], 2), 'acontecimento crítico sem representação', d['limitacao']))
        if d.get('substituicao') and d.get('critica'):
            A.append(_achado('semantico', 'S5', 'bloqueio', k, cenas[k]['comp'], cenas[k]['start'], 'substituição genérica de acontecimento crítico', d['substituicao']))
        if d.get('sem_contrato'):
            A.append(_achado('semantico', 'S6', 'revisao', k, cenas[k]['comp'], cenas[k]['start'],
                             'cena sem acontecimento declarado e não reconhecida pelos padrões', f"\"{str(d.get('fala', ''))[:70]}\" → {cenas[k]['comp']}"))
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
        A.append(_achado('deterministico', 'A1', 'bloqueio', None, None, 0, 'loudness fora da meta', f"{audio['lufs']:.1f} LUFS (meta −14 ± 1)"))
    if audio and audio.get('pico_dbtp') is not None and audio['pico_dbtp'] > -1.0:
        A.append(_achado('deterministico', 'A1', 'bloqueio', None, None, 0, 'pico verdadeiro acima de −1 dBTP', f"{audio['pico_dbtp']:.1f} dBTP"))
    # mesma causa contínua (tela vazia em cenas seguidas) é UM problema: junta os achados D13 consecutivos
    juntos = []
    for a in A:
        ant = juntos[-1] if juntos else None
        if a['codigo'] == 'D13' and ant and ant['codigo'] == 'D13' and a['cena'] is not None and ant.get('_ate', ant['cena']) is not None \
                and a['cena'] == ant.get('_ate', ant['cena']) + 1:
            ant['_ate'] = a['cena']
            ant['evidencia'] = f"cenas {ant['cena']}–{a['cena']}: " + re.sub(r'^cenas \d+–\d+: ', '', ant['evidencia'])
            continue
        juntos.append(a)
    A = [{k: v for k, v in a.items() if k != '_ate'} for a in juntos]
    for q in PERGUNTAS:
        A.append(_achado('estetico', 'E-pergunta', 'observacao', None, None, None, q, 'sem medida automática'))

    bloq = [a for a in A if a['gravidade'] == 'bloqueio']
    revisao = [a for a in A if a['gravidade'] == 'revisao']
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
    return {'aprovado_tecnicamente': not bloq, 'aprovacao_automatica': not bloq and not revisao, 'revisao_humana': len(revisao), 'achados': A,
            'por_categoria': {c: {'bloqueios': sum(1 for a in A if a['categoria'] == c and a['gravidade'] == 'bloqueio'),
                                  'revisoes': sum(1 for a in A if a['categoria'] == c and a['gravidade'] == 'revisao'),
                                  'avisos': sum(1 for a in A if a['categoria'] == c and a['gravidade'] == 'aviso'),
                                  'observacoes': sum(1 for a in A if a['categoria'] == c and a['gravidade'] == 'observacao')}
                              for c in ('deterministico', 'semantico', 'estetico')},
            'bloqueios': [compat(a) for a in bloq], 'avisos': [compat(a) for a in A if a['gravidade'] == 'aviso'],
            'deterministico': det,
            'subjetivo': {'estado': 'pendente de avaliação humana (sem nota automática)', 'perguntas': PERGUNTAS}}


def texto(r: dict) -> str:
    linhas = [f"FISCAL V2.2 — {'sem bloqueio' if r['aprovado_tecnicamente'] else str(len(r['bloqueios'])) + ' bloqueio(s)'}"
              f" · aprovação automática: {'sim' if r['aprovacao_automatica'] else 'NÃO'}" + (f" ({r['revisao_humana']} cena(s) para revisão humana)" if r['revisao_humana'] else '')]
    for c, n in r['por_categoria'].items():
        linhas.append(f"  {c}: {n['bloqueios']} bloqueio(s), {n['revisoes']} revisão(ões), {n['avisos']} aviso(s), {n['observacoes']} observação(ões)")
    for a in r['achados']:
        if a['codigo'] == 'E-pergunta':
            continue
        marca = {'bloqueio': '✘', 'revisao': '?', 'aviso': '!', 'observacao': '·'}[a['gravidade']]
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
