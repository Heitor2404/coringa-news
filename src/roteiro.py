"""Escolhe as pautas do dia e escreve o roteiro em cenas com o Gemini."""
import json, os, re
from pathlib import Path
from . import gemini
from src import cofre

TIPOS = {'gancho', 'numero', 'cards', 'citacao', 'escala', 'lista', 'mapa', 'imagem', 'historia', 'revelacao', 'fechamento',
         'linha_tempo', 'comparacao'}
# tipos de cena que são infográfico (desenhado no próprio vídeo, sobre a imagem do plano escurecida)
INFOGRAFICOS = {'numero', 'cards', 'escala', 'lista', 'mapa', 'linha_tempo', 'comparacao', 'citacao', 'revelacao'}
CLIMAS = ('misterioso', 'tenso', 'epico', 'leve')

PROMPT_ESCOLHA = cofre.prompt('PROMPT_ESCOLHA')

PROMPT_PESQUISA = cofre.prompt('PROMPT_PESQUISA')

PROMPT_ROTEIRO = cofre.prompt('PROMPT_ROTEIRO')


LIMITE_PALAVRAS = 160      # ≈ 55–60 s de narração: mais que isso o vídeo fica longo e a retenção cai


def _gerar_roteiro(prompt: str, tentativas: int = 3, serie: bool = False) -> dict:
    """Pede o roteiro e confere; se vier incompleto, pede de novo (até 3 vezes) em vez de desistir do vídeo.
    Em série (parte 1), exige o plano em 2 ou 3 partes: a parte 1 conta só o 1º capítulo e chama para a parte 2."""
    erro, melhor = None, None
    for k in range(tentativas):
        try:
            v = _validar(gemini.json_(prompt))
            if melhor is None or len(v['cenas']) > len(melhor['cenas']):
                melhor = v
            palavras = sum(len(c['fala'].split()) for c in v['cenas'])
            if palavras > LIMITE_PALAVRAS:
                prompt += (f'\n\nATENÇÃO: a versão anterior tinha {palavras} palavras (≈ {palavras // 2.6:.0f} s). '
                           f'O MÁXIMO é {LIMITE_PALAVRAS - 10} palavras (≈ 55 s). Corte o que não for essencial.')
                raise ValueError(f'roteiro longo demais ({palavras} palavras)')
            ideias = [c for c in v['cenas'] if c['tipo'] != 'fechamento']
            longas = [c['fala'] for c in ideias if len(c['fala'].split()) > 16]
            if len(ideias) < 11 or len(longas) >= 3:
                prompt += (f'\n\nATENÇÃO: a versão anterior tinha {len(ideias)} cenas' + (f' e frases longas demais ("{longas[0][:60]}...")' if longas else '')
                           + '. São OBRIGATÓRIAS 12 a 18 cenas, UMA frase de no máximo 12 palavras por cena.')
                raise ValueError(f'{len(ideias)} cenas, {len(longas)} frase(s) longa(s)')
            if serie and len(v.get('arco') or []) < 2:
                prompt += ('\n\nATENÇÃO: o "arco" PRECISA ter 2 ou 3 partes. Conte nesta PARTE 1 só o primeiro capítulo, '
                           'com detalhe, e termine em suspense. NÃO conte a história inteira.')
                raise ValueError('a IA contou a história inteira em uma parte só')
            return v
        except ValueError as e:
            erro = e
            print(f'  [roteiro] tentativa {k + 1} veio incompleta ({str(e)[:140]}); peço de novo')
    # 3 tentativas fora do formato: se a melhor tiver pelo menos 8 cenas, segue (as frases longas viram 2 planos) em vez de perder o dia
    if melhor and len([c for c in melhor['cenas'] if c['tipo'] != 'fechamento']) >= 8 and not str(erro).startswith(('roteiro longo', 'a IA contou')):
        print('  [roteiro] sigo com a melhor das tentativas')
        return melhor
    raise ValueError(f'roteiro incompleto depois de {tentativas} tentativas: {erro}')


_CHAMADA = re.compile(r'\b(segu[ea]|comenta|comente|parte \d|inscrev|curt[ae]|compartilh)', re.I)


def arrumar_final(v: dict, parte: int = 0) -> dict:
    """O fechamento é só a chamada final. Se o roteirista colocou história nele, essa parte vira cenas de verdade
    (com imagem) antes do fechamento. Em série, garante o convite para a próxima parte."""
    cenas = v['cenas']
    fech = cenas[-1] if cenas and cenas[-1]['tipo'] == 'fechamento' else None
    if fech is None:
        fech = {'tipo': 'fechamento', 'fala': ''}
        cenas.append(fech)
    frases = [f.strip() for f in re.split(r'(?<=[.!?])\s+', fech.get('fala', '')) if f.strip()]
    historia = [f for f in frases if not _CHAMADA.search(f)]
    chamada = [f for f in frases if _CHAMADA.search(f)]
    if historia and len(fech.get('fala', '').split()) > 12:
        base = next((c for c in reversed(cenas[:-1]) if c.get('cenario') or c.get('busca')), {})
        novas = [{'tipo': 'historia', 'fala': f, 'cenario': base.get('cenario', ''), 'busca': '', 'midia': ''} for f in historia]
        cenas[-1:-1] = novas
        print(f'  [final] {len(novas)} frase(s) de história saíram do fechamento e viraram cenas com imagem')
    else:
        chamada = frases
    arco = v.get('arco') or []
    prox = (parte or 1) + 1
    if len(arco) > 1 and (parte or 1) < len(arco):
        fech['titulo'] = f'Quer a *parte {prox}*?'
        fech['proxima'] = prox
        if not any(f'parte {prox}' in f.lower() for f in chamada) or len(' '.join(chamada).split()) > 9:
            chamada = [f'Parte {prox} amanhã. Segue pra não perder.']
    else:
        fech['titulo'] = 'Segue o *@coringa.explica*'
        fech.pop('proxima', None)
        if not chamada or len(' '.join(chamada).split()) > 6 or re.search(r'parte \d', ' '.join(chamada), re.I):
            chamada = ['Segue o *Coringa Explica*.']        # final curto: o vídeo recomeça logo (revisão conta no algoritmo)
    fech['fala'] = ' '.join(chamada)
    fech.pop('fala_tts', None)
    v['cenas'] = cenas
    return _validar(v)


PROMPT_ESCOLHER_VERSAO = cofre.prompt('PROMPT_ESCOLHER_VERSAO')


def _melhor_de_dois(prompt: str, serie: bool = False) -> dict:
    """O roteirista escreve duas versões diferentes e o editor-chefe escolhe a melhor."""
    a = _gerar_roteiro(prompt, serie=serie)
    from .orcamento import sobra
    # 11/11: 2ª versão + comparação custavam 2 pedidos ao Claude por vídeo e quase nunca mudavam o resultado
    # (a crítica e os 3 ganchos já melhoram o roteiro). Ligar de novo com DUAS_VERSOES=1.
    if os.environ.get('DUAS_VERSOES', '0') != '1':
        return a
    if sobra() < 75:
        print('  [roteiro] tempo apertado: fico com uma versão só')
        return a
    try:
        b = _gerar_roteiro(serie=serie, prompt=prompt + '\n\nIMPORTANTE: escreva uma versão DIFERENTE da mais óbvia — outro gancho de abertura, '
                                    'outro fio condutor ou outra ordem de revelação, com a mesma qualidade e as mesmas regras.')
    except Exception as e:
        print(f'  [roteiro] 2ª versão não saiu ({str(e)[:80]}); sigo com a 1ª')
        return a
    try:
        enx = lambda v: json.dumps({'titulo': v.get('titulo'), 'falas': [c['fala'] for c in v['cenas']]}, ensure_ascii=False)
        r = gemini.json_(PROMPT_ESCOLHER_VERSAO.format(a=enx(a), b=enx(b)))
        if isinstance(r, list):
            r = r[0] if r else {}
        esc = str(r.get('escolha', 'A')).strip().upper()[:1]
        print(f"  [roteiro] editor escolheu a versão {esc}: {str(r.get('motivo', ''))[:100]}")
        return b if esc == 'B' else a
    except Exception as e:
        print(f'  [roteiro] não consegui comparar as versões ({str(e)[:80]}); fico com a 1ª')
        return a


def escolher(pautas: list[dict], n: int) -> list[dict]:
    lista = '\n'.join(f"{p['id']} · {p['topico']} · {p['titulo']} · {p['fonte']}" for p in pautas)
    escolha = gemini.json_(PROMPT_ESCOLHA.format(lista=lista, n=n), leve=True)
    por_id = {p['id']: p for p in pautas}
    out = []
    for e in escolha:
        p = por_id.get(int(e.get('id', -1)))
        if p and p not in out:
            out.append({**p, 'categoria': e.get('categoria', p['topico']), 'angulo': e.get('angulo', ''),
                        'viral': float(e.get('viral', 0) or 0)})
    return out[:n]


def _normalizar(v) -> dict:
    """Modelos menores às vezes mudam nomes de campos ou embrulham o JSON: arruma antes de validar."""
    if isinstance(v, list):
        v = next((x for x in v if isinstance(x, dict) and (x.get('cenas') or x.get('scenes'))), v[0] if v else {})
    if not isinstance(v, dict):
        return {}
    if isinstance(v.get('roteiro'), dict) and not v.get('cenas'):
        v = {**v, **v['roteiro']}
    cenas = v.get('cenas') or v.get('scenes') or []
    out = []
    for c in cenas if isinstance(cenas, list) else []:
        if not isinstance(c, dict):
            continue
        c = dict(c)
        c['tipo'] = str(c.get('tipo') or c.get('type') or '').strip().lower()
        c['fala'] = c.get('fala') or c.get('narracao') or c.get('narração') or c.get('texto') or c.get('text') or ''
        if c['tipo'] not in TIPOS:
            c['tipo'] = 'historia' if c.get('cenario') else 'imagem'
        out.append(c)
    v['cenas'] = out
    return v


def _validar(v: dict) -> dict:
    v = _normalizar(v)
    cenas = [c for c in v.get('cenas', []) if c.get('tipo') in TIPOS and c.get('fala')]
    if len(cenas) < 3:
        raise ValueError(f'roteiro com poucas cenas ({len(cenas)}; chaves recebidas: {list(v)[:8]})')
    if cenas[0]['tipo'] != 'gancho':
        cenas[0]['tipo'] = 'gancho'
        cenas[0].setdefault('titulo', v.get('titulo', '').upper())
    if cenas[-1]['tipo'] != 'fechamento':
        cenas.append({'tipo': 'fechamento', 'fala': 'Segue o Coringa Explica pra mais histórias assim.'})
    for c in cenas:   # cards com 1 item só ficam vazios: viram um destaque visual
        if c['tipo'] == 'cards' and len(c.get('itens') or []) < 2:
            it = (c.get('itens') or [{}])[0]
            c['tipo'] = 'imagem'
            c['rotulo'] = c.get('titulo') or f"{it.get('rotulo', '')}: *{it.get('valor', '')}*"
            c['icone'] = it.get('icone') or c.get('icone')
    for c in cenas:   # "numero" precisa de um número de verdade; texto vira um destaque na cena
        if c['tipo'] == 'numero':
            try:
                bruto = str(c.get('valor', '')).strip()
                val = float(bruto.replace('.', '') if re.fullmatch(r'\d{1,3}(\.\d{3})+', bruto) else bruto.replace(',', '.'))
                if abs(val) < 10:            # "1 suspeito" não é infográfico: número pequeno vira cena com foto
                    c['tipo'] = 'historia'
            except ValueError:
                c['tipo'] = 'historia'
                c['destaque'] = c.get('destaque') or f"*{c.get('valor', '')}*"[:40]
    for c in cenas:   # linha do tempo e comparação precisam de pelo menos 2 itens válidos; senão viram cena com imagem
        if c['tipo'] == 'linha_tempo':
            c['itens'] = [i for i in (c.get('itens') or []) if isinstance(i, dict) and i.get('ano') and i.get('texto')][:4]
            if len(c['itens']) < 2:
                c['tipo'] = 'historia'
        if c['tipo'] == 'comparacao':
            ok = []
            for i in c.get('itens') or []:
                try:
                    ok.append({**i, 'valor': float(str(i.get('valor')).replace(',', '.'))})
                except (TypeError, ValueError, AttributeError):
                    pass
            c['itens'] = ok[:3]
            if len(ok) < 2 or max(x['valor'] for x in ok) <= 0:
                c['tipo'] = 'historia'
    for c in cenas:   # mapa sem nenhum lugar não mostra nada: vira um destaque visual
        if c['tipo'] == 'mapa' and len(c.get('pontos') or []) < 1:
            c['tipo'] = 'imagem'
            c.setdefault('rotulo', c.get('rotulo') or '')
            c.setdefault('icone', '📍')
        if c.get('fala_tts'):
            c['fala_tts'] = c['fala_tts'].replace('*', '')
    imgs = [i for i in (v.get('imagens') or []) if not str(i.get('id', '')).startswith('c')]
    vistos = set()
    for k, c in enumerate(cenas):          # cada IDEIA (frase original) ganha a sua imagem; os pedaços dela usam a mesma
        if (c.get('cenario') or c.get('busca')) and c['tipo'] != 'fechamento':
            iid = f"c{c['grupo']}" if c.get('grupo') is not None else f'c{k}'
            if iid not in vistos:
                vistos.add(iid)
                imgs.append({'id': iid, 'prompt': c.get('prompt_imagem') or c.get('cenario') or c.get('busca'),
                             'personagem': bool(c.get('usa_personagem'))})
            c['imagem'] = iid
    imgs = imgs[:32]
    v['imagens'] = imgs
    ids = {i.get('id') for i in imgs}
    lista_ids = [i['id'] for i in imgs]
    for k, c in enumerate(cenas):          # cena sem imagem válida reaproveita uma das imagens do vídeo
        if c.get('imagem') not in ids:
            c['imagem'] = lista_ids[k % len(lista_ids)] if (lista_ids and c['tipo'] != 'fechamento') else None
    v['cenas'] = cenas
    return v


PROMPT_FATOS_RSS = cofre.prompt('PROMPT_FATOS_RSS')


def _fatos(pauta: dict) -> str:
    try:
        return gemini.pesquisar(PROMPT_PESQUISA.format(**pauta))
    except Exception as e:
        print(f'  [pesquisa] sem busca no Google ({str(e)[:80]}); usando a cobertura do Google News')
        from . import pautas
        cov = pautas.cobertura(pauta['titulo'])
        return gemini.texto(PROMPT_FATOS_RSS.format(cobertura=cov or '(sem cobertura extra)', **pauta), leve=True)


def escrever(pauta: dict, produtos: list[dict]) -> dict:
    fatos = _fatos(pauta)
    prods = '\n'.join(f"- {p['id']}: {p['nome']} (temas: {', '.join(p.get('temas', []))})" for p in produtos) or '(nenhum)'
    v = _melhor_de_dois(PROMPT_ROTEIRO.format(fatos=fatos, produtos=prods, **pauta))
    v = revisar(v, fatos)
    v.setdefault('estilo_visual', 'cinematic photorealistic news illustration, dramatic lighting, shallow depth of field')
    v.pop('arco', None)                    # notícia não é série: nunca chama para "parte 2"
    v = escolher_gancho(v, fatos)
    v = dividir(geocodificar(dirigir(arrumar_final(v))))
    from .orcamento import marca
    marca('roteiro pronto')
    v['fatos'] = fatos
    prod = next((p for p in produtos if p['id'] == v.get('produto')), None)
    v['produto'] = prod
    return v


# ───────────────────────── Coringa Explica (curiosidades) ─────────────────────────
PROMPT_TEMAS_EXPLICA = cofre.prompt('PROMPT_TEMAS_EXPLICA')

PROMPT_ROTEIRO_EXPLICA = cofre.prompt('PROMPT_ROTEIRO_EXPLICA')

BLOCO_PARTE1 = """SÉRIE EM CAPÍTULOS — esta é a PARTE 1 de {n}.
- OBRIGATÓRIO: planeje em "arco" a história completa em EXATAMENTE {n} partes (1 frase por parte), cortando nos suspenses naturais.
- Esta PARTE 1 conta SÓ o primeiro capítulo do arco, com calma e detalhe (não resuma a história toda).
  A última cena de "historia" termina num GANCHO DE SUSPENSE (o momento em que tudo vai mudar, sem contar o que acontece).
  O "fechamento" tem "titulo": "Quer a *parte 2*?" e fala do tipo "A parte 2 sai amanhã. Segue pra não perder."
  A "revelacao" desta parte é uma revelação do capítulo (nunca entregue o final da série)."""

BLOCO_PARTE_N = cofre.prompt('BLOCO_PARTE_N')


UNICO = 'VÍDEO ÚNICO: conte a curiosidade completa neste vídeo, sem partes ("arco" com 1 item). O "fechamento" convida a seguir o perfil.'


def bloco_partes(parte: int, serie: dict | None, n: int = 2) -> str:
    if parte <= 1 or not serie:
        return BLOCO_PARTE1.format(n=max(2, min(3, n)))
    arco = serie.get('arco') or []
    ultima = parte >= len(arco)
    fim = ('Esta é a ÚLTIMA parte: feche a história com a grande revelação e um "fechamento" que agradeça quem acompanhou a série.'
           if ultima else f'Ainda haverá parte {parte + 1}: termine em suspense e o "fechamento" com "titulo": "Quer a *parte {parte + 1}*?" '
                          f'avisando que a parte {parte + 1} sai amanhã.')
    partes = serie.get('partes', [])
    anteriores = '\n'.join(f"Parte {p['parte']}: {p['resumo']}" for p in partes)
    ant = next((p for p in partes if p.get('parte') == parte - 1), partes[-1] if partes else {})
    return BLOCO_PARTE_N.format(parte=parte, anterior=parte - 1, pergunta_serie=serie.get('pergunta', ''),
                                arco=' | '.join(f'Parte {i + 1}: {a}' for i, a in enumerate(arco)) or '(livre)',
                                anteriores=anteriores or '(sem registro)', fim=fim,
                                suspense=ant.get('suspense') or '(ver o fim do resumo acima)')


PROMPT_TEMA_LIVRE = cofre.prompt('PROMPT_TEMA_LIVRE')


def tema_livre(pedido: str) -> dict:
    t = gemini.json_(PROMPT_TEMA_LIVRE.format(pedido=pedido), leve=True)
    if isinstance(t, list):
        t = t[0]
    t.setdefault('pergunta', pedido)
    t.setdefault('termos', [pedido])
    t['pedido'] = pedido
    return t


def temas_explica(pautas_: list[dict], n: int, usados: list[str]) -> list[dict]:
    lista = '\n'.join(f"{p['id']} · {p['topico']} · {p['titulo']}" for p in pautas_[:60])
    temas = gemini.json_(PROMPT_TEMAS_EXPLICA.format(lista=lista, n=n, usados='\n'.join(usados[-80:]) or '(nenhum)'), leve=True)
    por_id = {p['id']: p for p in pautas_}
    out = []
    for t in temas if isinstance(temas, list) else []:
        if t.get('pergunta') and t.get('termos'):
            t['noticia'] = por_id.get(t.get('noticia_id'), {}).get('titulo', '')
            out.append(t)
    return out[:n]


def escrever_explica(tema: dict, parte: int = 1, serie: dict | None = None, capitulos: bool = True) -> dict:
    """ORDEM DE DOCUMENTÁRIO: pesquisa → ACERVO de fotos reais (antes de escrever!) → roteiro em cima do acervo →
    revisão → gancho → casamento frase × foto (conferido olhando as fotos) → só então a montagem."""
    from . import acervo as acervo_mod, fontes as fontes_mod
    from .orcamento import marca
    gemini.RESERVAS_USADAS.clear()
    fatos, fontes, link, dossie = fontes_mod.coletar(tema, tema.get('pedido', ''), parte)
    if parte <= 1:                                # série só quando o tema merece (o padrão é vídeo único)
        n = int(tema.get('partes') or 0) or decidir_partes(tema, fatos)
        capitulos = capitulos and n > 1
    else:
        n = len((serie or {}).get('arco') or []) or 2
    pasta = Path(__file__).resolve().parent.parent / 'tmp' / ('acervo-' + re.sub(r'[^a-z0-9]+', '-', tema['pergunta'].lower())[:40])
    acervo = acervo_mod.coletar(tema, dossie, pasta)        # sem fotos reais suficientes: ValueError → próximo tema
    marca('acervo pronto')
    v = _melhor_de_dois(serie=capitulos and parte <= 1, prompt=PROMPT_ROTEIRO_EXPLICA.format(
        pergunta=tema['pergunta'], formato=tema.get('formato', 'explica'), noticia=tema.get('noticia', ''), fatos=fatos,
        partes=bloco_partes(parte, serie, n) if capitulos else UNICO,
        categoria=tema.get('categoria', 'CIÊNCIA'), acervo=acervo_mod.texto(acervo)))
    v['arco'] = (v.get('arco') or []) if capitulos else (v.get('arco') or [])[:1]
    if capitulos and parte <= 1 and len(v['arco']) > n:
        v['arco'] = v['arco'][:n]
    prot = dossie.get('protagonista') if isinstance(dossie.get('protagonista'), dict) else {}
    if not v.get('personagem') and prot.get('visual'):
        v['personagem'] = prot['visual']
    arco = (serie or {}).get('arco') or v['arco']
    escopo = ''
    if capitulos and len(arco) > 1 and parte <= len(arco):
        depois = '; '.join(arco[parte:])
        escopo = (f'esta é a PARTE {parte} de {len(arco)} e deve contar SÓ este capítulo: "{arco[parte - 1]}". '
                  + (f'NÃO pode contar nada destes capítulos seguintes: "{depois}" — termina em suspense antes deles.' if depois else ''))
        print(f'  [série] parte {parte}/{len(arco)}: {arco[parte - 1][:90]}')
    escopo += '\nFOTOS DO ACERVO (o vídeo é montado com elas; cada frase deve poder ser mostrada por uma delas):\n' + acervo_mod.texto(acervo)
    v = revisar(v, fatos, escopo=escopo)
    v = escolher_gancho(v, fatos, parte=parte, serie=serie, acervo=acervo)
    epoca = ' · '.join(x for x in [str(dossie.get('epoca') or ''), ', '.join(dossie.get('lugares') or [])] if x)
    if serie and serie.get('arco'):
        v['arco'] = serie['arco']             # a série segue o plano da parte 1 (a parte 2 sabe se ainda vem a 3)
    v = arrumar_final(v, parte if (parte > 1 or len(v.get('arco') or []) > 1) else 0)
    v = dividir(geocodificar(v))
    v = acervo_mod.casar(v, acervo)
    # 2ª busca: para cada frase ainda sem foto, procura imagem real do ASSUNTO DA FRASE (Loki, Templários, o bombardeiro...)
    acervo = acervo_mod.complementar(v, acervo, pasta)
    v = acervo_mod.casar(v, acervo)
    v = acervo_mod.preencher(v, acervo)          # buraco = reserva do acervo (vídeo primeiro), antes de 2D ou repetir
    v['acervo'] = acervo
    v = _planos_sem_foto(v, epoca)
    v['_reserva'] = list(gemini.RESERVAS_USADAS)   # vai como aviso na prévia de aprovação
    marca('roteiro pronto')
    v['produto'] = None
    v['fontes'] = fontes
    v['serie'] = 'CORINGA EXPLICA'
    v['parte'] = parte if (parte > 1 or len(v.get('arco') or []) > 1) else 0
    v['link'] = link
    v['resumo'] = ' '.join(c['fala'].replace('*', '') for c in v['cenas'] if c['tipo'] != 'fechamento')
    hist = [c['fala'].replace('*', '') for c in v['cenas'] if c['tipo'] not in ('fechamento',)]
    v['suspense'] = hist[-1] if hist else ''
    return v


MAX_IA = 4          # ilustrações 2D por vídeo (só para frases sem foto real boa; 11/11: 2D em vez de foto falsa de IA)
MAX_VIZINHA = 2     # frases que reaproveitam a foto vizinha
MIN_COBERTURA = 0.35  # 11/11: com a ilustração 2D cobrindo buracos, basta ~1/3 das frases com foto real (antes 1/2)

PROMPT_PARTES = cofre.prompt('PROMPT_PARTES')


def decidir_partes(tema: dict, fatos: str) -> int:
    try:
        r = gemini.json_(PROMPT_PARTES.format(tema=tema.get('pedido') or tema.get('pergunta', ''), fatos=str(fatos)[:6000]), leve=True)
        if isinstance(r, list):
            r = r[0] if r else {}
        n = max(1, min(3, int(r.get('partes') or 1)))
        print(f"  [série] {'vídeo único' if n == 1 else f'{n} partes'}: {str(r.get('motivo', ''))[:100]}")
        return n
    except Exception:
        return 1


def _planos_sem_foto(v: dict, epoca: str) -> dict:
    """Ideias que ficaram sem foto do acervo: vídeo de clima (se o roteirista pediu, até 2), imagem de IA com a época
    travada (até 6) e, no máximo, 2 ideias reaproveitando a foto real vizinha.
    PORTEIRO: se menos da metade das ideias tem foto real do próprio assunto, o tema não tem material visual → próximo tema
    (foi o caso do sangue de dinossauro: 4 de 12 ideias com foto certa)."""
    ideias = [c for c in v['cenas'] if c['tipo'] not in ('fechamento', 'mapa') and not c.get('sub')]
    com_foto = sum(1 for c in ideias if c.get('foto'))
    # ciência "por dentro" (cérebro, células, sabor, espaço profundo): não existe foto real de quase nada disso; a imagem
    # certa é a ilustração científica 3D. Aí basta 1/4 das frases com foto real e a IA pode cobrir até 8.
    estilo = str(v.get('estilo_visual') or '').lower()
    ciencia = any(k in estilo for k in ('scientific', '3d', 'medical', 'microscop', 'space'))
    minimo, max_ia = (0.25, 8) if ciencia else (MIN_COBERTURA, MAX_IA)
    if ideias and com_foto / len(ideias) < minimo:
        raise ValueError(f'pouco material visual: só {com_foto} de {len(ideias)} frases têm foto real do assunto; pulo para o próximo tema')
    n_ia, n_clima, n_viz = 0, 0, 0
    trava = (f'Set in {epoca}. ' if epoca else '') + 'Period-accurate clothing, objects and architecture; no modern objects, no smartphones, no cars unless period-correct'
    trava += '. Flat 2D illustration (not a photo)'
    for k, c in enumerate(ideias):
        if c.get('foto'):
            continue
        if k == 0:                                 # GANCHO nunca é imagem de IA: o 1º quadro é o que vende o vídeo
            c['midia'] = 'vizinha'; n_viz += 1
            continue
        vis = str(c.get('visual') or '').strip()
        base = c.get('cenario') or (f"Scene showing {c['busca']}" if c.get('busca') else '')
        if vis.lower().startswith('clima') and n_clima < 2:
            c['midia'], c['busca'] = 'video', vis.split(':', 1)[-1].strip() or 'old city street'
            n_clima += 1
        elif n_viz < MAX_VIZINHA and not base:
            c['midia'] = 'vizinha'; n_viz += 1
        elif n_ia < max_ia and base:
            c['midia'] = 'ia'
            c['prompt_imagem'] = f"{base}. {trava}."
            n_ia += 1
        else:
            c['midia'] = 'vizinha'; n_viz += 1
    if n_viz > MAX_VIZINHA:
        raise ValueError(f'pouco material visual: {n_viz} frases sem imagem própria; pulo para o próximo tema')
    for c in v['cenas']:                       # pedaços da mesma ideia seguem a ideia
        if c.get('sub'):
            pai = next((x for x in v['cenas'] if x.get('grupo') == c.get('grupo') and not x.get('sub')), None)
            if pai:
                for k in ('midia', 'busca', 'prompt_imagem'):
                    if pai.get(k):
                        c[k] = pai[k]
    print(f'  [acervo] sem foto: {n_clima} vídeo(s) de clima · {n_ia} imagem(ns) de IA · {n_viz} reaproveitam a foto vizinha')
    return _validar(v)


# ───────────────────────── editor-chefe: critica e reescreve ─────────────────────────
PROMPT_CRITICA = cofre.prompt('PROMPT_CRITICA')


def revisar(v: dict, fatos: str, rodadas: int = 1, escopo: str = '') -> dict:   # 11/11: 1 rodada (economia de cota)
    """O editor-chefe dá nota e reescreve até aprovar (no máximo 'rodadas' vezes)."""
    from .orcamento import sobra
    for rodada in range(rodadas):
        if rodada and sobra() < 60:
            print('  [editor] tempo apertado: paro as revisões aqui')
            return v
        try:
            base = {k: val for k, val in v.items() if k not in ('fatos', 'produto', 'resumo', 'imagens', 'dossie')}
            r = gemini.json_(PROMPT_CRITICA.format(fatos=str(fatos)[:14000], roteiro=json.dumps(base, ensure_ascii=False),
                                                   escopo=(f'- escopo: {escopo} Se contar algo além disso (ou "spoilar" as próximas partes), nota 0.\n' if escopo else '')))
            if isinstance(r, list):
                r = r[0]
            print(f"  [editor] rodada {rodada + 1}: notas {r.get('notas')} · {'aprovado' if r.get('aprovado') else 'reescrito'}")
            for prob in (r.get('problemas') or [])[:4]:
                print(f'     - {str(prob)[:120]}')
            novo = r.get('roteiro')
            if r.get('aprovado') or not (isinstance(novo, dict) and novo.get('cenas')):
                return v
            for k in ('serie', 'parte', 'link', 'fatos', 'produto', 'categoria', 'fontes', 'arco', 'personagem', 'estilo_visual', 'dossie',
                      'clima', 'legenda_post', 'hashtags', 'titulo_youtube', 'legenda_tiktok'):
                if k in v and k not in novo:
                    novo[k] = v[k]
            novo = _validar(novo)
            ideias = [c for c in novo['cenas'] if c['tipo'] != 'fechamento']
            palavras = sum(len(c['fala'].split()) for c in novo['cenas'])
            if len(ideias) < 11 or palavras > LIMITE_PALAVRAS or any(len(c['fala'].split()) > 16 for c in ideias):
                print(f'  [editor] a reescrita saiu fora do formato ({len(ideias)} cenas, {palavras} palavras); fico com a anterior')
                return v
            v = novo
        except Exception as e:
            print(f'  [editor] não consegui revisar ({str(e)[:100]}); sigo com o roteiro atual')
            return v
    return v


# ───────────────────────── 3 ganchos: o editor escolhe o melhor ─────────────────────────
PROMPT_GANCHOS = cofre.prompt('PROMPT_GANCHOS')


# palavras em inglês que já apareceram em gancho/título ("Blower *truck* ruge", "BLASTER NO DESERTO", 10/11/2026)
INGLES = {'the', 'and', 'of', 'in', 'on', 'with', 'truck', 'trucks', 'blower', 'blaster', 'dugout', 'dugouts', 'boom', 'city',
          'town', 'mine', 'mines', 'miner', 'miners', 'desert', 'underground', 'house', 'houses', 'home', 'wow', 'opal',
          'opals', 'life', 'world', 'secret', 'hidden', 'heat', 'down', 'under'}


def tem_ingles(*textos: str) -> bool:
    import re as _re
    ws = {w.lower() for t in textos for w in _re.findall(r"[A-Za-zÀ-ÿ']+", str(t or '').replace('*', ''))}
    return bool(ws & INGLES)


def escolher_gancho(v: dict, fatos: str, parte: int = 1, serie: dict | None = None, acervo: list | None = None) -> dict:
    """O editor escreve 3 ganchos e fica com o melhor (o gancho é o que mais pesa na retenção)."""
    from .orcamento import sobra
    if sobra() < 60 or not v.get('cenas'):
        return v
    regra = ''
    if parte > 1 and serie:
        ant = next((p for p in serie.get('partes', []) if p.get('parte') == parte - 1), {})
        regra = (f'ESTA É A PARTE {parte}: o gancho RETOMA o suspense da parte {parte - 1} ("{ant.get("suspense", "")}") e o '
                 f'"titulo" inclui "PARTE {parte}".')
    try:
        falas = '\n'.join(f"{k}. [{c['tipo']}] {c['fala']}" for k, c in enumerate(v['cenas']))
        # 11/11: o gancho só promete o que as fotos mostram ("o lago que vira PEDRA" sem nenhum animal petrificado)
        from . import acervo as acervo_mod
        fotos = acervo_mod.texto(acervo) if acervo else '(sem lista de fotos)'
        r = gemini.json_(PROMPT_GANCHOS.format(regra=regra, falas=falas, fatos=str(fatos)[:9000], fotos=fotos))
        if isinstance(r, list):
            r = {'opcoes': r, 'escolha': 0}
        ops = [o for o in (r.get('opcoes') or []) if isinstance(o, dict) and o.get('fala') and len(str(o['fala']).split()) <= 18]
        if not ops:
            return v
        try:
            e = int(r.get('escolha') or 0)
        except (TypeError, ValueError):
            e = 0
        o = ops[e if 0 <= e < len(ops) else 0]
        if tem_ingles(o.get('fala'), o.get('titulo'), o.get('subtitulo')):     # gancho em inglês: o espectador não entende
            limpos = [x for x in ops if not tem_ingles(x.get('fala'), x.get('titulo'), x.get('subtitulo'))]
            if limpos:
                print('  [gancho] escolhido tinha palavra em inglês; fico com outra opção')
                o = limpos[0]
            elif not tem_ingles(v['cenas'][0].get('fala'), v['cenas'][0].get('titulo')):
                print('  [gancho] todas as opções tinham palavra em inglês; fico com o gancho original')
                return v
        g = v['cenas'][0]
        for k, o2 in enumerate(ops):
            print(f"  [gancho] {'→' if o2 is o else ' '} {o2['fala'][:90]}")
        g['fala'] = o['fala']
        g['titulo'] = o.get('titulo') or g.get('titulo')
        g['subtitulo'] = o.get('subtitulo') or g.get('subtitulo', '')
        if o.get('fala_tts'):
            g['fala_tts'] = str(o['fala_tts']).replace('*', '')
        else:
            g.pop('fala_tts', None)
        print(f"  [gancho] editor escolheu: {str(r.get('motivo', ''))[:100]}")
    except Exception as e:
        print(f'  [gancho] não consegui comparar ganchos ({str(e)[:80]}); fico com o original')
    return v


# ───────────────────────── diretor de arte: uma imagem por ideia, mídia real primeiro ─────────────────────────
PROMPT_DIRETOR = cofre.prompt('PROMPT_DIRETOR')


def dirigir(v: dict, epoca: str = '') -> dict:
    """Escolhe a mídia de cada ideia (foto real, filmagem, vídeo, mapa ou IA), câmera e transição."""
    planos = [(k, c) for k, c in enumerate(v['cenas']) if c['tipo'] != 'fechamento']
    if not planos:
        return v
    linhas = '\n'.join(f"{k} · {c['tipo']} · {c['fala'].replace('*', '')} · {c.get('cenario', '')}" for k, c in planos)
    try:
        r = gemini.json_(PROMPT_DIRETOR.format(titulo=v.get('titulo', ''), estilo=v.get('estilo_visual') or 'photorealistic',
                                               personagem=v.get('personagem') or '(nenhum)', epoca=epoca or '(ver narração)',
                                               planos=linhas))
        if isinstance(r, list):
            r = {'planos': r}
        paleta = (r.get('paleta') or '').strip()
        if r.get('personagem'):
            v['personagem'] = r['personagem']
        cont = {}
        for p in r.get('planos') or []:
            try:
                c = v['cenas'][int(p.get('i'))]
            except (TypeError, ValueError, IndexError):
                continue
            if c['tipo'] == 'fechamento':
                continue
            midia = str(p.get('midia') or 'ia').lower()
            if midia == 'mapa' and c['tipo'] in ('historia', 'imagem') and p.get('pontos'):
                c['tipo'], c['pontos'] = 'mapa', p['pontos'][:5]
                c['rotulo'] = c.get('rotulo') or p.get('rotulo') or c.get('destaque') or ''
            elif midia == 'mapa' and c['tipo'] != 'mapa':
                midia = 'video' if p.get('busca') else 'ia'
            elif midia not in ('foto', 'arquivo', 'video', 'ia', 'mapa'):
                midia = 'ia'
            c['midia'] = c.get('midia') or midia
            c['busca'] = p.get('busca') or ''
            if p.get('ano'):
                c['ano_max'] = p['ano']
            if p.get('prompt'):
                c['prompt_imagem'] = p['prompt'] + (f', color palette: {paleta}' if paleta else '')
                c['cenario'] = c.get('cenario') or p['prompt']
            c['usa_personagem'] = bool(p.get('usa_personagem'))
            for campo in ('camera', 'transicao'):
                if p.get(campo):
                    c[campo] = p[campo]
            cont[midia] = cont.get(midia, 0) + 1
        print(f'  [diretor] planos: {cont} · paleta: {paleta}')
        v = _validar(v)
    except Exception as e:
        print(f'  [diretor] não consegui escolher as mídias ({str(e)[:100]}); uso imagens de IA')
    return v


# ───────────────────────── mapas: coordenadas reais (OpenStreetMap), não chute da IA ─────────────────────────
_GEO: dict[str, tuple[float, float] | None] = {}


def _geocodificar(q: str):
    """Nominatim (OpenStreetMap): grátis, sem chave, no máximo 1 pedido por segundo."""
    q = re.sub(r'\s+', ' ', str(q or '')).strip()
    if not q:
        return None
    if q.lower() in _GEO:
        return _GEO[q.lower()]
    import time, requests
    res = None
    try:
        r = requests.get('https://nominatim.openstreetmap.org/search', timeout=20,
                         params={'q': q, 'format': 'json', 'limit': 1, 'accept-language': 'en'},
                         headers={'User-Agent': 'CoringaExplicaBot/1.0 (https://github.com/Heitor2404/coringa-news; educational short videos)'})
        r.raise_for_status()
        j = r.json()
        if j:
            res = (float(j[0]['lat']), float(j[0]['lon']))
    except Exception as e:
        print(f'  [mapa] não achei "{q}" no OpenStreetMap ({str(e)[:60]})')
    time.sleep(1.1)
    _GEO[q.lower()] = res
    return res


def geocodificar(v: dict) -> dict:
    """Troca as coordenadas que a IA chutou pelas do OpenStreetMap. Ponto que não é achado sai do mapa;
    mapa sem nenhum ponto confirmado vira cena com imagem (melhor nenhum mapa do que um mapa errado)."""
    for c in v['cenas']:
        if c.get('tipo') != 'mapa':
            continue
        bons = []
        for p in c.get('pontos') or []:
            if not isinstance(p, dict):
                continue
            achou = _geocodificar(p.get('local')) or _geocodificar(p.get('nome'))
            if not achou:
                continue
            try:
                ia = (float(p.get('lat')), float(p.get('lon')))
                if abs(ia[0] - achou[0]) + abs(ia[1] - achou[1]) > 3:
                    print(f"  [mapa] {p.get('nome')}: IA disse {ia[0]:.1f},{ia[1]:.1f}; OpenStreetMap diz {achou[0]:.1f},{achou[1]:.1f} (fico com o OSM)")
            except (TypeError, ValueError):
                pass
            bons.append({**p, 'lat': achou[0], 'lon': achou[1]})
        perto = len(bons) > 1 and max(abs(a['lat'] - b['lat']) + abs(a['lon'] - b['lon']) for a in bons for b in bons) < 0.6
        if perto:
            print(f"  [mapa] lugares na mesma cidade ({', '.join(str(p.get('nome')) for p in bons)}): mapa não mostra nada → cena com foto")
        if bons and not perto:
            c['pontos'] = bons
        else:
            print(f"  [mapa] nenhum lugar confirmado em: {c['fala'][:60]} → vira cena com imagem")
            c['tipo'] = 'historia'
            c.pop('pontos', None)
            if c.get('midia') == 'mapa':
                c['midia'] = 'video' if c.get('busca') else 'ia'
    return _validar(v)


# ───────────────────────── ritmo: frase longa vira dois planos DA MESMA IMAGEM ─────────────────────────
MAX_PALAVRAS = 11    # ≈ 3 a 4 segundos de narração: mais que isso a imagem fica parada tempo demais
MAX_INFOGRAFICO = 18 # infográfico/mapa é animado: aguenta uma frase mais longa sem cortar


def _cortar(fala: str, limite: int = MAX_PALAVRAS) -> tuple[str, str] | None:
    """Divide a frase em duas: de preferência na pontuação perto do meio; senão, no meio, sem quebrar um *destaque*."""
    pal = fala.split()
    if len(pal) <= limite:
        return None
    dentro, candidatos = False, []
    for i, w in enumerate(pal[:-2]):
        dentro ^= w.count('*') % 2 == 1
        if i < 2 or dentro:
            continue
        nota = 3 if w.endswith(('.', '!', '?', ';', ':')) else 2 if w.endswith((',', '—', '–')) else \
            1 if pal[i + 1].lower().strip('*') in ('e', 'mas', 'que', 'quando', 'porque', 'enquanto', 'onde', 'até', 'depois') else 0.2
        candidatos.append((nota * 10 - abs(i + 1 - len(pal) / 2) * 1.5, i + 1))
    for _, corte in sorted(candidatos, reverse=True):
        a, b = ' '.join(pal[:corte]), ' '.join(pal[corte:])
        if not (a.count('*') % 2 or b.count('*') % 2):
            return a, b
    return None


def _pedacos(fala: str, limite: int = MAX_PALAVRAS) -> list[str]:
    partes = _cortar(fala, limite)
    if not partes:
        return [fala]
    return _pedacos(partes[0], limite) + _pedacos(partes[1], limite)


CAMERAS_SUB = ['aproxima', 'esquerda', 'afasta', 'direita', 'sobe', 'desce']


def dividir(v: dict) -> dict:
    """Ritmo de 2–4 s por plano SEM trocar de assunto: uma frase longa vira 2 planos da MESMA imagem (mesma ideia),
    com outro enquadramento e outro movimento de câmera — nunca uma imagem nova para um pedaço de frase.
    Infográficos e mapas são animados e ficam inteiros (até 18 palavras)."""
    novas = []
    for g, c in enumerate(v['cenas']):
        c['grupo'] = g
        if c['tipo'] == 'fechamento':
            novas.append(c)
            continue
        limite = 9 if c['tipo'] == 'gancho' else MAX_INFOGRAFICO if c['tipo'] in INFOGRAFICOS else MAX_PALAVRAS
        ped = _pedacos(c['fala'], limite)
        if len(ped) == 1:
            novas.append(c)
            continue
        cam0 = c.get('camera') or CAMERAS_SUB[g % len(CAMERAS_SUB)]
        for k, p in enumerate(ped):
            if k == 0:
                novas.append({**c, 'fala': p, 'fala_tts': None, 'sub': 0, 'n_sub': len(ped), 'fala_ideia': c['fala']})
            else:
                cam = CAMERAS_SUB[(CAMERAS_SUB.index(cam0) + 2 * k) % len(CAMERAS_SUB)] if cam0 in CAMERAS_SUB else 'aproxima'
                novas.append({key: val for key, val in c.items()
                              if key in ('cenario', 'busca', 'midia', 'prompt_imagem', 'usa_personagem', 'ano_max', 'grupo')}
                             | {'tipo': 'historia', 'fala': p, 'sub': k, 'n_sub': len(ped), 'camera': cam,
                                'transicao': 'corte', 'fala_ideia': c['fala']})
    for c in novas:
        if not c.get('fala_tts'):
            c.pop('fala_tts', None)
    if len(novas) != len(v['cenas']):
        print(f"  [ritmo] {len(v['cenas'])} ideias → {len(novas)} planos (mesma imagem com outro enquadramento)")
    v['cenas'] = novas
    return _validar(v)


def engenhar_3d(v: dict) -> dict:
    """Desligado: as simulações 3D/animadas não tinham qualidade. A ação é mostrada com foto, filmagem ou infográfico."""
    return v
