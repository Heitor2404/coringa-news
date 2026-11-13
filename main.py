"""Coringa Explica (@coringa.explica) — gera o vídeo do dia.

    python main.py --diario         # produção: 1 curiosidade por dia (série em partes ou próximo tema do banco)
    python main.py --curiosidade "tema" --parte 1   # curiosidade escolhida
    python main.py --qtd 1          # notícia (só manual)
    python main.py --teste          # gera 1 vídeo do roteiro de exemplo, sem internet
"""
import argparse, io, json, os, re, shutil, subprocess, time, unicodedata
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

from src import voz
from src.render.render import renderizar, renderizar_capa
from src import cofre

RAIZ = Path(__file__).parent
BRT = timezone(timedelta(hours=-3))


def slug(s: str) -> str:
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')[:50]


def produtos() -> list[dict]:
    p = RAIZ / 'data' / 'produtos.json'
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else []


INFOGRAFICOS = {'numero', 'cards', 'escala', 'lista', 'linha_tempo', 'comparacao', 'citacao', 'revelacao'}
# trilha pelo clima da história (arquivos em assets/musica; CC0)
CLIMA_MUSICA = {'misterioso': ['hidden-truth', 'mysterious-lights'],
                'leve': ['asking-questions', 'think-about-it', 'fensters-explanation', 'inventing-flight'],
                'epico': ['the-story', 'infinite-wonder'],
                'tenso': ['beginning-of-conflict', 'driving-concern', 'desert-fox-underscore']}


def escolher_musica(v: dict, nome: str) -> Path | None:
    pasta = RAIZ / 'assets' / 'musica'
    todas = {p.stem: p for p in pasta.rglob('*.mp3')}
    clima = str(v.get('clima') or '').lower().replace('é', 'e')
    lista = [todas[n] for n in CLIMA_MUSICA.get(clima, []) if n in todas]
    if not lista:
        lista = sorted((pasta / ('explica' if v.get('serie') else 'noticia')).glob('*.mp3')) or sorted(todas.values())
    if not lista:
        return None
    m = lista[sum(map(ord, nome)) % len(lista)]
    print(f'  [música] clima {clima or "?"} → {m.stem}')
    return m


def _montar_cenas(v, reais, imgs, tempos, trab, ia_ids=frozenset()) -> list[dict]:
    from src import midia
    cenas, usado_video = [], {}
    for k, (c, (a, b)) in enumerate(zip(v['cenas'], tempos)):
        c = {key: val for key, val in c.items() if key not in ('fala_tts', 'prompt_imagem', 'cenario', 'fala_ideia')}
        c.update(start=round(a, 3), end=round(b, 3), img=None)
        iid = c.get('imagem')
        m = reais.get(iid)
        if c['tipo'] == 'mapa':
            pass                                   # o mapa é desenhado no próprio vídeo
        elif m and m['tipo'] == 'video':
            try:
                pasta_q = trab / 'quadros' / f'{k:02d}'
                desloc = usado_video.get(iid, 0.0)  # 2º plano da mesma ideia continua o vídeo de onde o 1º parou
                # vídeo deitado em cena de foto (história/imagem) vai na MOLDURA, inteiro; o resto ocupa a tela toda
                # clipe Full HD (ou em pé) vai em TELA CHEIA; só clipe deitado de resolução baixa fica na moldura
                # 11/11: TODO clipe em tela cheia (moldura pequena com fundo borrado foi o que mais incomodou)
                na_moldura = False
                n = len(list(pasta_q.glob('f_*.jpg'))) or midia.quadros(m['arq'], b - a + 0.4, pasta_q, desloc=desloc,
                                                                         moldura=na_moldura)
                usado_video[iid] = desloc + (b - a)
                c['video'] = {'dir': str(pasta_q), 'n': n}
                c['img'] = str(pasta_q / 'f_0001.jpg')
                c['video_moldura'] = na_moldura
                c['ano_foto'] = m.get('ano')
            except Exception as e:
                print(f'  [mídia] não consegui preparar o vídeo da cena {k}: {str(e)[:100]}')
        elif m and m['tipo'] == 'img':
            c['img'] = str(m['arq'])
        elif m:
            c['img'], c['real'] = str(m['arq']), True
            c['ano_foto'], c['tipo_img'] = m.get('ano'), m.get('tipo_img', 'foto')
            if m.get('legenda'):
                c['legenda_foto'] = m['legenda']      # etiqueta tirada do próprio arquivo (título/ano no Commons)
        elif imgs.get(iid):
            c['img'] = str(imgs[iid])
            c['ia'] = iid in ia_ids
        if c['tipo'] == 'fechamento' and v.get('produto'):
            c['produto'] = {'nome': v['produto']['nome'], 'chamada': v['produto'].get('chamada', 'link na bio')}
        cenas.append(c)
    # plano sem imagem própria: reaproveita a foto real mais próxima (mesma parte da história) com OUTRO enquadramento.
    # Nunca tela vazia; de preferência foto real, senão qualquer imagem vizinha.
    # Alterna entre as fotos reais do vídeo (a mais próxima que NÃO seja a mesma da cena anterior), para nenhuma foto
    # ficar muitos segundos seguidos na tela.
    reais_k = [k for k, c in enumerate(cenas) if c.get('real') and c.get('img')]
    com_img = reais_k or [k for k, c in enumerate(cenas) if c.get('img') and not c.get('video')]
    # Ideia sem imagem própria (no máximo 2 por vídeo, pelo porteiro do roteiro). Plano-mestre G: a imagem certa é a da
    # cena ANTERIOR, continuando (é contexto, e o storyboard registra isso) — nunca antecipar a imagem da PRÓXIMA ideia
    # (ela apareceria antes da hora) nem voltar a uma que já saiu da tela (A-B-A). Só o GANCHO, que não tem anterior,
    # pode abrir com a imagem da cena seguinte (é a abertura do assunto).
    for k, c in enumerate(cenas):
        if c.get('pendente'):                         # Etapa 2: cena pendente não ganha foto emprestada (não finge
            continue                                  # estar resolvida); fica sem mídia e marcada
        if not c.get('img') and c['tipo'] not in ('mapa', 'fechamento') and com_img:
            if k and cenas[k - 1].get('img') and not cenas[k - 1].get('video'):
                viz = cenas[k - 1]
            elif k == 0:
                viz = next((x for x in cenas[1:] if x.get('img') and not x.get('video')), None)
            else:
                viz = None
            if viz is None:
                continue
            c['img'], c['repetida'] = viz['img'], True
            c['sub'] = (viz.get('sub') or 0) + 1          # outro recorte/movimento da mesma foto
            if viz.get('real'):
                c['real'] = True
                for key in ('legenda_foto', 'ano_foto', 'tipo_img'):
                    c[key] = viz.get(key)
    cenas = _quebrar_longos(cenas)
    estilo = midia.estilo_fundo(v.get('titulo'), (v.get('_pauta') or {}).get('tema'), v.get('pergunta'), v.get('resumo'))
    print(f"  [fundo] {'B · céu' if estilo == 'ceu' else 'A · estúdio escuro'} atrás das fotos")
    _acabamento(cenas, estilo)
    # revelação: continua na imagem da cena anterior com outro enquadramento (11/11 noite: voltar à imagem do gancho no fim
    # parecia repetição — o logo da Força Aérea apareceu 3x no vídeo do supercomputador)
    for k, c in enumerate(cenas):
        if c['tipo'] == 'revelacao':
            ant = next((x for x in reversed(cenas[:k]) if x.get('img') and not x.get('video')), None)
            if ant:
                c['img'], c['real'], c['sub'] = ant['img'], ant.get('real', False), (ant.get('sub') or 0) + 1
                c.pop('video', None)
    from src import storyboard
    storyboard.registrar_tempos(cenas)             # plano-mestre D: span da narração e motivo da transição (registro)
    _transicoes(cenas)                             # plano-mestre G: a transição segue o motivo (sem tela preta automática)
    # fundo do fechamento: a última foto do vídeo (escurecida atrás do Coringa), não a da abertura
    fundo = next((c['img'] for c in reversed(cenas[:-1]) if c.get('img') and not c.get('video')), None)
    if cenas and cenas[-1]['tipo'] == 'fechamento' and fundo:
        cenas[-1]['img'] = fundo
    return cenas


PLANO_MAX = 3.5         # plano mais longo que isso PODE ganhar um detalhe da mesma foto (se a resolução deixar)
DETALHE_MIN = 1.3       # zoom mínimo para o detalhe ser outra vista de verdade (menos que isso é Ken Burns, não conta)
DETALHE_MAX = 1.6
AMPLIA_MAX = 2.0        # quanto a foto pode ser ampliada no total (cobrir a tela × detalhe) sem ficar borrada
PLANO_MIN = 1.6         # nenhum pedaço de plano mais curto que isso (corte nervoso)


def _zoom_detalhe(img: str) -> float:
    """Até quanto dá para aproximar desta foto em tela cheia sem borrar (0 = não dá)."""
    w, h = _tamanho(img)
    if not w or not h:
        return 0.0
    z = min(DETALHE_MAX, AMPLIA_MAX / max(1080 / w, 1920 / h))
    return round(z, 2) if z >= DETALHE_MIN else 0.0


def _quebrar_longos(cenas: list[dict]) -> list[dict]:
    """Plano-mestre G: ritmo não é quantidade de cortes. Plano longo (> PLANO_MAX) ganha UM detalhe da mesma foto só se
    a resolução deixar um zoom de verdade (≥ DETALHE_MIN) e cada pedaço ficar com pelo menos PLANO_MIN; senão fica
    inteiro (cena longa que mostra o fato é melhor que corte para outra coisa). Nunca entra a foto de outra ideia aqui
    (antecipava a próxima ou voltava a uma que já saiu: A-B-A). Documento: o detalhe só depois de dar tempo de ler."""
    out = []
    for c in cenas:
        dur = c['end'] - c['start']
        if not c.get('img') or c.get('video') or c['tipo'] not in ('historia', 'imagem') or dur <= PLANO_MAX:
            out.append(c)
            continue
        papel = str(c.get('tipo_img') or '').lower() in ('documento', 'jornal', 'manuscrito', 'carta') or \
            (c.get('sb') or {}).get('midia_preferida') == 'documento'
        z = _zoom_detalhe(c['img'])
        corte = round(c['start'] + max(PLANO_MIN, dur * (0.6 if papel else 0.5)), 3)
        if not z or c['end'] - corte < PLANO_MIN:
            out.append(c)                                # inteiro: sem resolução para um detalhe de verdade
            continue
        out.append(dict(c, end=corte))
        d = dict(c, start=corte, sub=(c.get('sub') or 0) + 1, zoom_detalhe=z)
        d.pop('soco', None)
        out.append(d)
    return out


def _transicoes(cenas: list[dict]):
    """Transição pelo motivo registrado no storyboard: pedaço da mesma ideia ou continuação do mesmo acontecimento →
    corte seco; mudança de lugar/tempo → zoom curto; contraste → chicote. Nada de tela preta automática. Sem motivo (ou
    roteiro antigo), fica a transição de sempre do template. Transição já escolhida não muda."""
    MOTIVO = {'continuidade': 'corte', 'mudanca_de_lugar_ou_tempo': 'zoom', 'contraste': 'chicote'}
    ant = None
    for c in cenas:
        sb = c.get('sb')
        if sb and not c.get('transicao') and c['tipo'] in ('historia', 'imagem'):
            if ant is not None and ant.get('sb') is sb:
                c['transicao'] = 'corte'
            elif MOTIVO.get(sb.get('transicao')):
                c['transicao'] = MOTIVO[sb['transicao']]
        ant = c


SEM_SOCO = {'mapa', 'fechamento', 'gancho', 'revelacao', 'numero', 'linha_tempo', 'comparacao', 'cards', 'lista', 'escala', 'citacao'}


def _tamanho(img: str) -> tuple[int, int]:
    try:
        from PIL import Image
        if str(img).startswith('file:'):          # o render troca os caminhos por endereços file://
            from urllib.parse import unquote, urlparse
            img = unquote(urlparse(str(img)).path)
        with Image.open(img) as im:
            return im.size
    except Exception:
        return (0, 0)




def _acabamento(cenas: list[dict], estilo: str = 'estudio'):
    """Edição: (1) tudo em tela cheia; (2) etiqueta "FOTO · ano" só em foto histórica; (3) plano com mais de 2,6 s
    ganha um "soco" no meio."""
    from src import midia
    for c in cenas:
        for k in ('img_fundo', 'moldura_gancho', 'etiqueta', 'moldura', 'foto_wh', 'soco'):   # plano copiado traz os da outra foto
            c.pop(k, None)
        if c.get('video') and c.get('video_moldura'):     # vídeo deitado: moldura + etiqueta ▶ VÍDEO + fundo desfocado
            c['foto_wh'] = list(_tamanho(c['img']))
            c['moldura'] = True
            c['etiqueta'] = '▶ VÍDEO' + (f" · {c['ano_foto']}" if c.get('ano_foto') else '')
            c['img_fundo'] = str(midia.fundo(Path(c['img']), estilo))
        elif c.get('img') and c.get('real') and not c.get('video'):
            w, h = _tamanho(c['img'])
            c['foto_wh'] = [w, h]
            ano, tipo = c.get('ano_foto'), c.get('tipo_img') or 'foto'
            # 11/11: TODA cena em tela cheia (a câmera passeia pela foto). Moldura pequena sobre fundo borrado saiu de vez.
            # Foto pequena demais já fica de fora no acervo (MIN_LADO). Etiqueta com ano só em FOTO histórica de verdade
            # (antes molécula/desenho/vaso ganhavam "ARQUIVO · 2009" ou "FOTO · 1500").
            c['moldura'] = False
            if tipo == 'foto' and ano and 1826 <= ano < 1990:
                c['etiqueta'] = 'FOTO · ' + (str(c['legenda_foto']) if c.get('legenda_foto') else str(ano))
        dur = c['end'] - c['start']
        if c.get('img') and c['tipo'] not in SEM_SOCO and dur > 2.6:
            c['soco'] = round(c['start'] + dur / 2, 3)


def erros_basicos(cenas: list[dict], caps: list[dict]) -> list[str]:
    """Fiscal automático do que NUNCA pode sair errado (vai para o resumo do Telegram)."""
    import datetime
    erros = []
    # imagem parada: um plano sozinho com mais de 6.5 s, ou a mesma imagem (mesmo com reenquadramento) por mais de 11 s
    fim = max((c.get('end', 0) for c in cenas), default=0)
    for c in cenas:
        d = c.get('end', 0) - c.get('start', 0)
        if c.get('img') and not c.get('video') and c.get('tipo') in ('historia', 'imagem', 'gancho') and d > 6.5:
            erros.append(f'imagem parada {d:.0f}s num plano só (a partir de {c["start"]:.0f}s)')
            break
    ini, atual = 0.0, None
    for c in cenas + [{'img': '__fim__', 'start': fim, 'end': fim}]:
        img = c.get('img') or f"__{c.get('tipo')}{c.get('start')}"
        if img != atual:
            if atual and not str(atual).startswith('__') and not str(atual).endswith('f_0001.jpg') and c['start'] - ini > 11:
                erros.append(f'a mesma imagem ficou {c["start"] - ini:.0f}s na tela (a partir de {ini:.0f}s)')
                break
            atual, ini = img, c['start']
    ano = datetime.date.today().year
    if any(str(ano) in str(c.get('etiqueta', '')) for c in cenas):
        erros.append('etiqueta de foto com o ano atual (data errada)')
    longas = [w['w'] for cp in caps for w in cp['words'] if len(str(w['w'])) > 21]
    if longas:
        erros.append(f'palavra longa demais na legenda: {longas[0]}')
    import re as _re
    vazias = [c['fala'] for c in cenas if c['tipo'] in ('historia', 'imagem') and not c.get('sub')
              and not _re.search(r'\d|\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+', c['fala'][1:].replace('*', ''))]
    if len(vazias) >= 3:
        erros.append(f'{len(vazias)} frases sem nome/número/data (ex.: "{vazias[0][:50]}")')
    rep = sum(1 for c in cenas if c.get('repetida') and not c.get('sub'))
    if rep >= 3:
        erros.append(f'{rep} ideias sem imagem própria')
    return erros


def pacote_diagnostico(v: dict, dados: dict, pasta: Path, nome: str):
    """Guarda roteiro + cenas + imagens (reduzidas) do vídeo num zip, que vai junto nos arquivos da execução do GitHub.
    Com ele dá para remontar o MESMO vídeo, com as mesmas fotos reais, e testar uma correção no caso real."""
    import zipfile
    try:
        from PIL import Image
        from urllib.parse import unquote, urlparse
        arq = pasta / f'{nome}-diagnostico.zip'
        with zipfile.ZipFile(arq, 'w', zipfile.ZIP_DEFLATED) as z:
            base = {k: val for k, val in v.items() if k not in ('acervo', 'dossie', '_telegram')}
            z.writestr('roteiro.json', json.dumps(base, ensure_ascii=False, indent=1, default=str))
            z.writestr('acervo.json', json.dumps([{k: val for k, val in x.items() if k not in ('mini', 'arq')}
                                                  for x in v.get('acervo') or []], ensure_ascii=False, indent=1, default=str))
            dd = json.loads(json.dumps(dados, default=str))
            for sc in dd.get('scenes', []):
                for campo in ('img', 'img_fundo'):
                    u = sc.get(campo)
                    if not u:
                        continue
                    p = unquote(urlparse(u).path) if str(u).startswith('file:') else u
                    destino = f'img/{Path(p).name}'
                    if destino not in z.namelist() and Path(p).exists():
                        im = Image.open(p).convert('RGB')
                        im.thumbnail((1080, 1080))
                        b = io.BytesIO()
                        im.save(b, 'JPEG', quality=82)
                        z.writestr(destino, b.getvalue())
                    sc[campo] = destino
                sc.pop('video', None)
            dd.pop('world', None); dd.pop('mascote', None)
            z.writestr('dados.json', json.dumps(dd, ensure_ascii=False, default=str))
        print(f'  [diagnóstico] {arq.name} ({arq.stat().st_size / 1e6:.1f} MB)')
    except Exception as e:
        print(f'  [diagnóstico] não consegui salvar: {str(e)[:100]}')


def _pergunta_fixa(v: dict) -> str:
    """A pergunta que fica pequena no topo até a resposta: só se for uma pergunta de verdade ("E depois?" não diz nada)."""
    p = next((c.get('pergunta', '') for c in v['cenas'] if c['tipo'] == 'revelacao'), '').replace('*', '').strip()
    return p[:70] if len(p.split()) >= 4 else ''


def _contexto(v: dict) -> str:
    return f"{v.get('titulo', '')} — {(v.get('resumo') or ' '.join(c['fala'] for c in v['cenas']))[:400]}".replace('*', '')


def _cena_da_imagem(v: dict, iid: str) -> dict:
    return next((c for c in v['cenas'] if c.get('imagem') == iid), {})


def _fala_ideia(c: dict) -> str:
    return c.get('fala_ideia') or c.get('fala', '')


def conferir_ia(v: dict, imgs: dict, trab: Path, contexto: str, ids=None, rodada: int = 1) -> dict:
    """O fiscal (modelo principal) confere cada imagem de IA contra a IDEIA da frase; a reprovada é gerada de novo
    uma vez, com a correção, e conferida de novo. Se continuar errada, sai (o plano reaproveita a foto real vizinha)."""
    from src import imagens, midia
    from src.orcamento import sobra
    if sobra() < 40:
        print('  [fiscal] tempo apertado: pulo a conferência das imagens de IA')
        return imgs
    refazer, ruins = [], []
    for iid in list(ids if ids is not None else imgs):
        c = _cena_da_imagem(v, iid)
        if not c or iid not in imgs:
            continue
        try:
            mini = midia.miniatura_jpg(Path(imgs[iid]).read_bytes())
        except Exception:
            continue
        if midia.fiscal(_fala_ideia(c), contexto, c.get('cenario', ''), [mini]) is None:
            ruins.append(iid)
            base = next((i for i in v['imagens'] if i['id'] == iid), {'id': iid, 'prompt': c.get('cenario', '')})
            refazer.append({**base, 'prompt': f"{base['prompt']}. It must clearly show: {_fala_ideia(c).replace('*', '')}"})
    if not refazer:
        return imgs
    if rodada > 1:                         # já foi refeita uma vez e continua errada: tira
        for iid in ruins:
            imgs.pop(iid, None)
        print(f'  [fiscal] {len(ruins)} imagem(ns) continuam erradas: esses planos reaproveitam a foto real vizinha')
        return imgs
    print(f'  [fiscal] {len(refazer)} imagem(ns) de IA reprovada(s); gerando de novo')
    estilo = imagens.ESTILO_ANIM if v.get('serie') else v.get('estilo_visual', '')     # curiosidade: sempre 2D
    novas = imagens.gerar(refazer, trab / 'refeitas', estilo, v.get('personagem', ''))
    for iid in ruins:
        imgs.pop(iid, None)
    imgs.update(novas)
    return conferir_ia(v, imgs, trab, contexto, ids=list(novas), rodada=2)


PROMPT_FISCAL_FINAL = cofre.prompt('PROMPT_FISCAL_FINAL')


def fiscal_final(saida: Path, cenas: list[dict], v: dict) -> tuple[float | None, list[tuple[int, str]]]:
    """Assiste o vídeo pronto (um quadro por plano) e devolve (nota, planos com problema grave de imagem)."""
    from src.orcamento import sobra
    if not os.getenv('GEMINI_API_KEY') or sobra() < 25:
        if os.getenv('GEMINI_API_KEY'):
            print('  [fiscal final] tempo apertado: entrego sem a 2ª montagem')
        return None, []
    try:
        from src import gemini
        quadros, idx = [], []
        for k, c in enumerate(cenas):
            if c['tipo'] in ('fechamento', 'mapa') or not c.get('img') or c.get('repetida'):
                continue
            t = (c['start'] + c['end']) / 2
            r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.2f}', '-i', str(saida), '-frames:v', '1', '-vf',
                                'scale=360:-2', '-f', 'image2', '-c:v', 'mjpeg', '-'], capture_output=True)
            if r.stdout:
                quadros.append(r.stdout); idx.append(k)
        if not quadros:
            return None, []
        # k é a posição em `cenas` (já com os planos divididos), que tem MAIS itens que v['cenas']: a fala vem da própria
        # cena (antes buscava a frase pela posição na lista de ideias → "list index out of range" e o fiscal não rodava quando uma ideia virava 2 planos)
        falas = '\n'.join(f"plano {j}: {str(cenas[k].get('fala') or '').replace('*', '')}" for j, k in enumerate(idx))
        r = gemini.json_visao(PROMPT_FISCAL_FINAL.format(falas=falas), quadros[:24], leve=True)   # só a nota: modelo lite (economia de cota)
        if isinstance(r, list):
            r = r[0] if r else {}
        ruins = []
        for x in r.get('cenas_ruins') or []:
            try:
                ruins.append((idx[int(x.get('i'))], str(x.get('problema', ''))[:120]))
            except (TypeError, ValueError, IndexError):
                pass
        try:
            nota = float(r.get('nota_geral'))
        except (TypeError, ValueError):
            nota = None
        print(f"  [fiscal final] nota {nota} · {len(ruins)} plano(s) com problema")
        for k, pr in ruins:
            print(f'     - plano {k}: {pr}')
        return nota, ruins[:6]
    except Exception as e:
        print(f'  [fiscal final] indisponível ({str(e)[:80]})')
        return None, []


def _qualidade(v: dict, cenas: list[dict], reais: dict, nota, dur: float) -> dict:
    """Resumo para o Telegram: o editor decide em 5 segundos se posta."""
    ideias = {}
    for c in cenas:
        if c['tipo'] == 'fechamento':
            continue
        g = c.get('imagem') or f"x{c.get('grupo', id(c))}"
        if c['tipo'] == 'mapa':
            ideias[g] = 'mapa'
        elif c.get('repetida'):
            ideias.setdefault(g, 'foto repetida')
        else:
            m = reais.get(c.get('imagem'))
            ideias[g] = ('foto real' if m['tipo'] == 'foto' else 'vídeo' if m['tipo'] == 'video' else 'banco') if m else \
                ('ia' if c.get('ia') else 'banco')
            if c['tipo'] in INFOGRAFICOS:
                ideias[g] = 'infográfico'
    cont = {}
    for t in ideias.values():
        cont[t] = cont.get(t, 0) + 1
    total = max(1, len(ideias))
    palavras = sum(len(c['fala'].split()) for c in v['cenas'])
    motivos = []
    if nota is not None and nota < 6:
        motivos.append(f'nota do fiscal {nota:.0f}/10')
    if cont.get('foto repetida', 0) >= 4 or cont.get('foto repetida', 0) / total > 0.3:
        motivos.append(f"{cont['foto repetida']} ideia(s) sem imagem própria")
    if dur > 78:
        motivos.append(f'vídeo longo ({dur:.0f}s)')
    return {'nota': nota, 'cont': cont, 'ideias': total, 'dur': dur, 'palavras': palavras, 'motivos': motivos,
            'ia': any(c.get('ia') for c in cenas)}


def resumo_telegram(v: dict, q: dict) -> str:
    c = q['cont']
    tem_parte = re.search(r'parte\s*\d', v['titulo'], re.I)
    pauta = v.get('_pauta') or {}
    linhas = [f"🎬 {v['titulo']}" + (f" — PARTE {v['parte']}" if v.get('parte') and not tem_parte else ''),
              f"⏱ {q['dur']:.0f}s · {q['palavras']} palavras · {q['ideias']} ideias",
              f"⭐ fiscal: {q['nota']:.0f}/10"
              if q['nota'] is not None else '⭐ fiscal: não rodou',
              '🖼 ' + ' · '.join(f'{n} {t}' for t, n in sorted(c.items(), key=lambda x: -x[1]))]
    if q.get('erros'):
        linhas.append('🔧 Erros básicos: ' + '; '.join(q['erros']))
    if pauta.get('motivo'):
        linhas.append(f"🧭 Por que este tema: {pauta['motivo']}" + (f" ({pauta['contexto']})" if pauta.get('contexto') else ''))
    if q['motivos']:
        linhas.append('⚠️ NÃO RECOMENDO POSTAR: ' + '; '.join(q['motivos']))
    else:
        linhas.append('✅ pode postar')
    if q['ia']:
        linhas.append('🤖 Tem imagem de IA: no Instagram ative "Informações de IA" (Configurações avançadas → Rótulo de IA).')
    return '\n'.join(linhas)


def textos_post(v: dict, creditos: list[str]) -> dict:
    tags = [h.lstrip('#').replace(' ', '') for h in (v.get('hashtags') or []) if str(h).strip()][:5]
    if 'coringaexplica' not in [t.lower() for t in tags]:
        tags = tags[:4] + ['coringaexplica']
    hs = ' '.join('#' + h for h in tags)
    parte = f" (Parte {v['parte']})" if v.get('parte') and not re.search(r'parte\s*\d', v['titulo'], re.I) else ''
    ig = [v.get('legenda_post') or v['titulo'], '', hs]
    if v.get('produto'):
        ig += ['', f"#publi {v['produto']['nome']}: {v['produto']['link']}"]
    if v.get('fontes'):
        ig += ['', 'Fontes: ' + ', '.join(v['fontes'])]
    if creditos:      # fotos e filmagens reais: crédito exigido pelas licenças Creative Commons
        ig += ['', 'Imagens: ' + ' · '.join(dict.fromkeys(creditos))]
    yt_titulo = (v.get('titulo_youtube') or v['titulo'])[:90] + ('' if 'parte' in (v.get('titulo_youtube') or '').lower() else parte)
    yt = [yt_titulo[:100], '', (v.get('legenda_post') or '').split('\n')[0], '', hs + ' #shorts']
    tk = [f"{v.get('legenda_tiktok') or v['titulo']}{parte} {hs}"]
    return {'instagram': '\n'.join(ig).strip(), 'tiktok': '\n'.join(tk).strip(), 'youtube': '\n'.join(yt).strip()}


def _midia_de_item(x: dict, trab: Path) -> dict:
    """Prepara um item do acervo para a montagem. Vídeo: só agora baixa o clipe (o escolhido, não os candidatos)."""
    from src import midia
    if x.get('video'):
        url = x['video']['url']
        ext = '.' + url.split('?')[0].rsplit('.', 1)[-1][:5]
        clipe = midia._baixar(url, trab / 'midia' / f"v_{x['id']}{ext}", cab=midia.UA if 'wikimedia' in url else {})
        print(f"  [mídia] vídeo {x['id']}: {x.get('mostra', '')[:70]}")
        return {'tipo': 'video', 'arq': clipe, 'w': x['video']['w'], 'h': x['video']['h'], 'ano': x.get('ano'),
                'thumb': x.get('arq')}
    return {'tipo': 'foto', 'arq': midia.graduar(Path(x['arq'])), 'legenda': x.get('legenda', ''),
            'ano': x.get('ano'), 'tipo_img': x.get('tipo_img', 'foto')}


def _midia_do_acervo(v: dict, trab: Path):
    """Curiosidade: as fotos já vêm do acervo (casadas com cada frase). Aqui só entram os vídeos de clima e as poucas
    imagens de IA (com a época travada, conferidas pelo fiscal). O que sobrar reaproveita a foto vizinha na montagem."""
    from src import imagens, midia
    por_id = {x['id']: x for x in v['acervo']}
    reais, creditos = {}, []
    for c in v['cenas']:
        x = por_id.get(c.get('foto'))
        if x and c.get('imagem') and c['imagem'] not in reais:
            try:
                reais[c['imagem']] = _midia_de_item(x, trab)
                if x.get('credito'):
                    creditos.append(x['credito'])
            except Exception as e:     # vídeo que não baixou: a frase fica com a foto vizinha (nunca tela vazia)
                print(f"  [mídia] não consegui usar {x['id']} ({str(e)[:80]}); a frase usa a foto vizinha")
    contexto = _contexto(v)
    clima = [c for c in v['cenas'] if c.get('midia') == 'video' and c.get('imagem') and c['imagem'] not in reais]
    if clima:
        r2, _, cred = midia.obter(clima, trab / 'midia', contexto)
        reais.update(r2); creditos += cred
    pedir_ids = {c['imagem'] for c in v['cenas'] if c.get('midia') == 'ia' and c.get('imagem') and c['imagem'] not in reais}
    pedir = [i for i in v.get('imagens', []) if i['id'] in pedir_ids]
    # 11/11: frase sem foto boa ganha ILUSTRAÇÃO 2D (estilo único do canal), não foto falsa de IA — assim o tema não é
    # descartado por falta de imagem e ninguém confunde com foto real
    imgs = imagens.gerar(pedir, trab, imagens.ESTILO_ANIM, v.get('personagem', '')) if pedir else {}
    imgs = conferir_ia(v, imgs, trab, contexto, rodada=2)     # 1 conferência: reprovada sai (vira foto vizinha)
    imgs = {k: midia.graduar(Path(p)) for k, p in imgs.items()}
    print(f"  [mídia] {len(reais)} ideias com foto/vídeo real · {len(imgs)} com IA · o resto reaproveita a foto vizinha")
    return reais, imgs, creditos, set(imgs)


def montar_video(v: dict, pasta: Path, nome: str, teste=False) -> Path:
    trab = RAIZ / 'tmp' / nome
    if trab.exists():
        shutil.rmtree(trab)
    trab.mkdir(parents=True)
    t0 = time.time()

    imgs, reais, creditos, ia_ids = {}, {}, [], set()
    if v.get('acervo') is not None and not teste:
        reais, imgs, creditos, ia_ids = _midia_do_acervo(v, trab)
    elif v.get('imagens') and not teste:
        from src import imagens, midia
        contexto = _contexto(v)
        reais, falta, creditos = midia.obter(v['cenas'], trab / 'midia', contexto)   # fotos, filmagens e vídeos de verdade
        pedir = [i for i in v['imagens'] if i['id'] in falta]
        print(f'  [mídia] {len(reais)} ideias com mídia real · {len(pedir)} com imagem de IA')
        imgs = imagens.gerar(pedir, trab, v.get('estilo_visual', ''), v.get('personagem', '')) if pedir else {}
        imgs = conferir_ia(v, imgs, trab, contexto)
        ia_ids = set(imgs)
        sem = [i['id'] for i in pedir if i['id'] not in imgs]
        if sem:                              # IA não conseguiu: procura ilustração e foto em todas as fontes
            achadas, cred = midia.resgate(v['cenas'], sem, trab / 'midia', contexto)
            imgs.update(achadas); creditos += cred
        imgs = {k: midia.graduar(Path(p)) for k, p in imgs.items()}
        for m in reais.values():
            if m['tipo'] in ('foto', 'img'):
                m['arq'] = midia.graduar(Path(m['arq']))
    elif teste:
        imgs = {i['id']: RAIZ / i['arquivo'] for i in v.get('imagens', []) if i.get('arquivo') and not i.get('video')}
        reais = {i['id']: {'tipo': 'video' if i.get('video') else 'foto', 'arq': RAIZ / i['arquivo']}
                 for i in v.get('imagens', []) if i.get('arquivo') and (i.get('video') or i.get('real'))}

    from src.orcamento import marca, sobra
    marca('mídia e imagens prontas')
    # APROVAÇÃO: o roteiro e as imagens vão para o Telegram; NADA é montado sem o OK (voz e render vêm depois)
    if not teste and v.get('acervo') is not None and os.getenv('APROVACAO', '1') != '0':
        from src import aprovacao
        minutos = max(5.0, min(float(os.getenv('APROVACAO_MIN') or 40), sobra() - 22))
        r = aprovacao.aprovar(v, reais, imgs, lambda x: _midia_de_item(x, trab), minutos)
        v['_aprovacao'] = r
        if r == 'outro':
            raise ValueError('material recusado na aprovação (você pediu outro tema)')
        if r == 'sem_resposta':
            raise RuntimeError('sem aprovação no Telegram: o vídeo não foi montado')
        marca('aprovado' if r == 'ok' else 'sem aprovação (Telegram indisponível)')
    audio, tempos, caps, dur = voz.narrar(v['cenas'], trab, teste=teste)
    marca('narração pronta')
    musica = escolher_musica(v, nome)
    saida = pasta / f'{nome}.mp4'
    # UMA montagem só: as imagens já foram conferidas antes (acervo + casamento + fiscal da IA)
    cenas = _montar_cenas(v, reais, imgs, tempos, trab, ia_ids)
    dados = {'duration': dur,
             'meta': {'titulo': v['titulo'], 'categoria': v.get('categoria', ''), 'data': datetime.now(BRT).strftime('%d/%m'),
                      'serie': v.get('serie', ''), 'parte': v.get('parte', 0), 'marca': '@coringa.explica',
                      'pergunta': _pergunta_fixa(v),
                      'fontes': v.get('fontes', [])[:3] + (['Wikimedia Commons'] if creditos else [])},
             'scenes': cenas, 'captions': caps}
    renderizar(dados, audio, saida, trab, musica=musica)
    marca('vídeo montado')
    nota = None if teste else fiscal_final(saida, cenas, v)[0]     # só a nota do vídeo pronto (≈1 min), sem 2ª montagem

    # capa: título grande dentro do recorte 3:4 do perfil
    try:
        gancho = next((c for c in cenas if c['tipo'] == 'gancho'), {})
        num = next((c for c in cenas if c['tipo'] == 'numero'), None)
        capa = {'tipo': 'curiosidade' if v.get('serie') else 'noticia',
                'titulo': gancho.get('titulo') or v['titulo'], 'data': dados['meta']['data'],
                'categoria': v.get('categoria', ''), 'parte': v.get('parte', 0),
                'img': next((c['img'] for c in cenas if c.get('img') and not c.get('video')), None)
                       or gancho.get('img')}
        if gancho.get('img') and not gancho.get('video') and not gancho.get('moldura_gancho'):
            capa['img'] = gancho['img']
        else:                                # foto do gancho pequena: a capa usa a imagem de maior resolução do vídeo
            cands = {c['img'] for c in cenas if c.get('img') and not c.get('video') and c['tipo'] != 'fechamento'}
            if cands:
                capa['img'] = max(cands, key=lambda p: min(_tamanho(p)))
        if num:
            val = f"{num.get('prefixo', '')}{num.get('valor', '')}{num.get('sufixo', '')}".strip()
            if len(val) <= 9:
                capa['dado'] = {'valor': val, 'rotulo': num.get('rotulo', '')[:22]}
        renderizar_capa(capa, pasta / f'{nome}-capa.jpg', trab)
    except Exception as e:
        print('  [capa] falhou, usando um quadro do vídeo:', str(e)[:120])
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(min(2.2, dur / 3)), '-i', str(saida), '-frames:v', '1',
                        '-q:v', '2', str(pasta / f'{nome}-capa.jpg')], check=False)

    q = _qualidade(v, cenas, reais, nota, dur)
    q['erros'] = erros_basicos(cenas, caps)
    if any('parada' in e for e in q['erros']):          # frase de ligação sem número é normal: fica só no 🔧 (aviso)
        q['motivos'] = q['motivos'] + ['erro básico (ver 🔧)']
    # PORTEIRO FINAL: erro que não pode ir ao ar (imagem parada, data errada, vídeo longo demais) → o vídeo não é enviado
    graves = [e for e in q['erros'] if 'parada' in e or 'na tela' in e or 'ano atual' in e]
    tela = dados.get('problemas_tela') or []          # fiscal da tela: texto em cima de texto / saindo da tela
    if tela:
        q['erros'].append(f'texto em cima de texto em {len(tela)} ponto(s) (ex.: {tela[0]})')
        graves.append(f'texto em cima de texto ({len(tela)}x, ex.: {tela[0]})')
    if dur > 80:
        graves.append(f'vídeo com {dur:.0f}s (máximo 80)')
    v['_bloqueado'] = '; '.join(graves) if graves and not teste else ''
    tx = textos_post(v, creditos)
    resumo = resumo_telegram(v, q)
    from src import claude, custo
    if claude.GASTO['pedidos']:                       # quanto do crédito mensal do Claude Pro este vídeo usou
        print('  [claude] ' + claude.resumo_gasto())
    # 12/11: o diagnóstico (🧪 fiscal sombra + 💰 custo) vai numa MENSAGEM SEPARADA no Telegram, inteira; a legenda do vídeo
    # tem limite de ~1000 caracteres e cortava o 💰 e parte do 🧪. O resumo principal (acima) fica como era.
    diag = []
    if not teste:                                     # FISCAL NOVO em modo sombra (Fase 0): mostra, NÃO decide
        try:
            from src import fiscal
            sb = fiscal.sombra(v, cenas, saida, nota, dados.get('problemas_tela') or [])
            diag += fiscal.linhas_telegram(sb)
            fiscal.salvar(sb, pasta / f'{nome}-fiscal-sombra.json')
        except Exception as e:
            print(f'  [fiscal sombra] não rodou ({str(e)[:100]})')
    if custo.linha_telegram():                        # livro-caixa (Fase 0): por etapa e por tentativa, Claude × Gemini
        diag.append(custo.linha_telegram())
    from src import orcamento_video
    if orcamento_video.linha_telegram():              # Fase 1 (monitorar): o que o orçamento FARIA; não decide nada
        diag.append(orcamento_video.linha_telegram())
    try:                                              # plano-mestre I: métricas da rodada — só registro
        from src import metricas
        met = metricas.coletar(v, cenas)
        diag.append(metricas.linha_telegram(met))
        (pasta / f'{nome}-metricas.json').write_text(json.dumps(met, ensure_ascii=False, indent=1), encoding='utf-8')
    except Exception as e:
        print(f'  [métricas] não medi ({str(e)[:80]})')
    try:                                              # Etapa 2: resolução visual por cena
        from src import resolucao
        if resolucao.linha_telegram(cenas):
            diag.append(resolucao.linha_telegram(cenas))
    except Exception as e:
        print(f'  [resolução] não medi ({str(e)[:80]})')
    try:                                              # plano-mestre D: storyboard — só registro
        from src import storyboard
        if storyboard.linha_telegram(cenas):
            diag.append(storyboard.linha_telegram(cenas))
            (pasta / f'{nome}-storyboard.json').write_text(json.dumps(storyboard.resumo(cenas), ensure_ascii=False, indent=1),
                                                          encoding='utf-8')
    except Exception as e:
        print(f'  [storyboard] não medi ({str(e)[:80]})')
    try:                                              # plano-mestre F: recursos gráficos com função e dado dos fatos
        from src import recursos
        if v.get('fatos') and recursos.linha_telegram(v, str(v['fatos'])):
            diag.append(recursos.linha_telegram(v, str(v['fatos'])))
    except Exception as e:
        print(f'  [recursos] não medi ({str(e)[:80]})')
    if v.get('plano'):                                # plano-mestre B/C (12/11): plano editorial e função dos blocos — só registro
        try:
            from src import editorial
            if editorial.linha_telegram(v, str(v.get('fatos') or '')):
                diag.append(editorial.linha_telegram(v, str(v.get('fatos') or '')))
        except Exception as e:
            print(f'  [plano editorial] não medi ({str(e)[:80]})')
    try:                                              # Fase 3 (12/11): cobertura visual por acontecimento — só registro
        from src import acontecimentos
        cob = acontecimentos.cobertura(cenas)
        v['_cobertura'] = cob
        if acontecimentos.linha_telegram(cob):
            diag.append(acontecimentos.linha_telegram(cob))
        (pasta / f'{nome}-cobertura.json').write_text(json.dumps(cob, ensure_ascii=False, indent=1), encoding='utf-8')
    except Exception as e:
        print(f'  [cobertura] não medi ({str(e)[:80]})')
    print(custo.tabela())
    try:
        custo.salvar(pasta / f'{nome}-custos.json')
    except Exception as e:
        print(f'  [custo] não salvei o livro-caixa: {str(e)[:80]}')
    if v.get('_aprovacao') == 'indisponivel':
        resumo = '⚠️ Montado SEM a sua aprovação (o Telegram não respondeu à prévia)\n' + resumo
    txt = [resumo] + (['', '\n'.join(diag)] if diag else []) + \
          ['', '════ INSTAGRAM (Reels) ════', tx['instagram'], '', '════ TIKTOK ════', tx['tiktok'], '',
           '════ YOUTUBE SHORTS (título na 1ª linha) ════', tx['youtube']]
    if v.get('link'):   # só para a equipe conferir; não vai no post
        txt += ['', '———————————————', '🔎 PARA CONFERIR (não copiar para o post):', v['link']]
    (pasta / f'{nome}.txt').write_text('\n'.join(txt).strip() + '\n', encoding='utf-8')
    v['_telegram'] = {'resumo': resumo, 'textos': tx, 'diagnostico': '\n'.join(diag)}
    if not teste:
        pacote_diagnostico(v, dados, pasta, nome)
        shutil.rmtree(trab, ignore_errors=True)
        if v.get('acervo'):
            shutil.rmtree(Path(v['acervo'][0]['arq']).parent, ignore_errors=True)
    print(f'  ✔ {saida.name} ({dur:.0f}s de vídeo, {time.time() - t0:.0f}s para gerar)')
    print('  ' + resumo.replace('\n', '\n  '))
    if diag:
        print('  ' + '\n'.join(diag).replace('\n', '\n  '))
    return saida


def _versao_telegram(arq: Path) -> Path:
    """Bots do Telegram só aceitam vídeo até 50 MB. Se passar, manda uma cópia comprimida (o original, em qualidade
    máxima, continua nos arquivos da execução do GitHub)."""
    mb = arq.stat().st_size / 1e6
    if mb <= 48:
        return arq
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(arq)],
                               capture_output=True, text=True).stdout.strip() or 60)
    kbps = int(44 * 8000 / dur) - 160                 # cabe em ~44 MB com o áudio
    menor = arq.with_name(arq.stem + '-telegram.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(arq), '-c:v', 'libx264', '-preset', 'medium', '-b:v', f'{kbps}k',
                    '-maxrate', f'{int(kbps * 1.3)}k', '-bufsize', f'{kbps * 2}k', '-c:a', 'aac', '-b:a', '160k',
                    '-movflags', '+faststart', str(menor)], check=True)
    print(f'  [telegram] vídeo tinha {mb:.0f} MB (limite 50): mando cópia de {menor.stat().st_size / 1e6:.0f} MB')
    return menor


def _tg(metodo: str, data: dict, arquivo: tuple[str, Path] | None = None) -> bool:
    tok, chat = os.getenv('TELEGRAM_BOT_TOKEN'), os.getenv('TELEGRAM_CHAT_ID')
    if not (tok and chat):
        return False
    for tentativa in range(3):
        try:
            if arquivo:
                with open(arquivo[1], 'rb') as f:
                    r = requests.post(f'https://api.telegram.org/bot{tok}/{metodo}', data={'chat_id': chat, **data},
                                      files={arquivo[0]: f}, timeout=300)
            else:
                r = requests.post(f'https://api.telegram.org/bot{tok}/{metodo}', data={'chat_id': chat, **data}, timeout=60)
            if r.ok:
                return True
            print(f'  [telegram] {metodo} recusou ({r.status_code}): {r.text[:150]}')
            if r.status_code == 429:
                time.sleep(int((r.json().get('parameters') or {}).get('retry_after', 10)) + 1)
            else:
                time.sleep(5)
        except Exception as e:
            print(f'  [telegram] {metodo} falhou: {str(e)[:120]}')
            time.sleep(5)
    return False


LIMITE_LEGENDA = 1000      # legenda de vídeo no Telegram (o limite do Telegram é 1024)
LIMITE_MSG = 3900          # mensagem de texto (o limite do Telegram é 4096)


def _pedacos(texto: str, limite: int = LIMITE_MSG) -> list[str]:
    """Quebra um texto longo em mensagens inteiras (por linha), sem cortar nada."""
    out, atual = [], ''
    for linha in texto.split('\n'):
        while len(linha) > limite:                   # linha sozinha maior que o limite: quebra no meio
            if atual:
                out.append(atual); atual = ''
            out.append(linha[:limite]); linha = linha[limite:]
        if atual and len(atual) + 1 + len(linha) > limite:
            out.append(atual); atual = linha
        else:
            atual = f'{atual}\n{linha}' if atual else linha
    if atual:
        out.append(atual)
    return out


def _comparar_audio(arq: Path, envio: Path) -> str:
    """Fase 0: só MEDE o áudio do original e da versão do Telegram (não muda a normalização)."""
    try:
        from src.fiscal import medir_audio, texto_audio
        orig = texto_audio(medir_audio(arq))
        if envio != arq:
            linha = f'original: {orig} · versão do Telegram: {texto_audio(medir_audio(envio))}'
        else:
            linha = f'original: {orig} · versão do Telegram: o próprio original (não precisou comprimir)'
        print(f'  [áudio] {linha}')
        return '🔊 áudio — ' + linha
    except Exception as e:
        print(f'  [áudio] comparação não medida ({str(e)[:60]})')
        return f'🔊 áudio — comparação não medida ({str(e)[:60]})'


def telegram(arq: Path, legenda: str, v: dict | None = None):
    """Manda o vídeo (com o resumo de qualidade), o diagnóstico (🧪 + 💰 + 🔊) numa mensagem separada, a capa e os
    textos prontos de cada rede."""
    if not (os.getenv('TELEGRAM_BOT_TOKEN') and os.getenv('TELEGRAM_CHAT_ID')):
        return
    try:
        info = (v or {}).get('_telegram') or {}
        envio = _versao_telegram(arq) if arq.suffix == '.mp4' else arq
        audio = _comparar_audio(arq, envio) if arq.suffix == '.mp4' else ''
        resumo = info.get('resumo') or legenda
        cabe = len(resumo) <= LIMITE_LEGENDA
        legenda_video = resumo if cabe else resumo[:LIMITE_LEGENDA - 40].rsplit('\n', 1)[0] + '\n(resumo completo na mensagem seguinte)'
        if _tg('sendVideo', {'caption': legenda_video, 'supports_streaming': 'true'}, ('video', envio)):
            print('  [telegram] vídeo enviado')
            # marca o dia: se o agendamento das 09:13 chegar atrasado depois disto, ele não faz outro vídeo
            (RAIZ / 'data' / 'ultimo_video.txt').write_text(datetime.now(BRT).strftime('%Y-%m-%d'), encoding='utf-8')
            from src import acervo as _acv
            _acv.marcar_clipes((v or {}).get('_clipes') or [])
        if not cabe:
            for parte in _pedacos(resumo):
                _tg('sendMessage', {'text': parte})
        diagnostico = '\n'.join(x for x in (info.get('diagnostico') or '', audio) if x)
        if diagnostico and info:
            for parte in _pedacos('📋 DIAGNÓSTICO DO VÍDEO (teste da Fase 0, não decide nada)\n' + diagnostico):
                _tg('sendMessage', {'text': parte, 'disable_notification': 'true'})
        capa = arq.with_name(arq.stem + '-capa.jpg')
        if capa.exists():
            _tg('sendPhoto', {'caption': 'Capa (o título fica dentro do recorte do perfil)'}, ('photo', capa))
        for rede, rotulo in (('instagram', '📸 INSTAGRAM'), ('tiktok', '🎵 TIKTOK'), ('youtube', '▶️ YOUTUBE SHORTS')):
            t = (info.get('textos') or {}).get(rede)
            if t:
                _tg('sendMessage', {'text': f'{rotulo}\n\n{t}'[:4000]})
    except Exception as e:
        print('  [telegram] falhou:', e)


# ───────────────────────── Coringa Explica: uma parte de uma série ─────────────────────────
PASTA_SERIES = RAIZ / 'data' / 'series'


def _arquivo_serie(pedido: str, parte: int) -> Path:
    PASTA_SERIES.mkdir(parents=True, exist_ok=True)
    chave = slug(pedido)
    arq = PASTA_SERIES / f'{chave}.json'
    if parte > 1 and not arq.exists():       # aceita o pedido escrito um pouco diferente
        import difflib
        perto = difflib.get_close_matches(chave, [p.stem for p in PASTA_SERIES.glob('*.json')], n=1, cutoff=0.5)
        if perto:
            arq = PASTA_SERIES / f'{perto[0]}.json'
    return arq


_FALHAS: list = []   # por que cada tema do dia não virou vídeo (vai no aviso do Telegram)


def fazer_curiosidade(pedido: str, parte: int, pasta: Path, pauta: dict | None = None):
    """True = vídeo feito; 'pular' = o tema não rende (sem material/sensível); False = erro passageiro."""
    from src import orcamento_video          # Fase 1 (monitorar): orçamento do vídeo; no diário já vem aberto
    with orcamento_video.video(pedido):
        return _fazer_curiosidade(pedido, parte, pasta, pauta)


def _fazer_curiosidade(pedido: str, parte: int, pasta: Path, pauta: dict | None = None):
    from src import roteiro
    parte = max(1, parte)
    arq_serie = _arquivo_serie(pedido, parte)
    serie = json.loads(arq_serie.read_text(encoding='utf-8')) if arq_serie.exists() else None
    print(f'Curiosidade: {pedido} (parte {parte})')
    from src import custo
    custo.tentativa(pedido)                    # livro-caixa: tudo daqui para a frente conta para esta tentativa de tema
    if parte > 1 and not serie:
        print('  ✘ não achei a parte 1 dessa série. Escreva a curiosidade igual à da parte 1.')
        return False
    try:
        t = serie['tema'] if serie else roteiro.tema_livre(pedido)
        if pauta and not serie:
            t['partes'] = pauta.get('partes') or 0          # 0 = o editor decide depois de pesquisar
            t['noticia'] = pauta.get('contexto') or ''
        print(f'  pergunta: {t["pergunta"]}')
        v = roteiro.escrever_explica(t, parte, serie)
        v['_pauta'] = pauta or {}
        nome = f'explica-{slug(pedido)[:40]}' + (f'-parte{parte}' if v.get('parte') else '')
        arq = montar_video(v, pasta, nome)
        if v.get('_bloqueado'):
            print(f"  ✘ porteiro: não mando este vídeo ({v['_bloqueado']}); tento outro tema")
            _tg('sendMessage', {'text': f"⛔ Vídeo de \"{v['titulo']}\" barrado antes de chegar aqui: {v['_bloqueado']}. "
                                        'Vou tentar outro tema (se der tempo hoje). O arquivo ficou nos artefatos do GitHub.'[:4000]})
            raise ValueError(f"material ruim: {v['_bloqueado']}")
        serie = serie or {'pedido': pedido, 'tema': t, 'pergunta': t['pergunta'], 'arco': v.get('arco') or [], 'partes': []}
        serie['partes'] = [p for p in serie['partes'] if p['parte'] != parte] + \
                          [{'parte': parte, 'titulo': v['titulo'], 'resumo': v['resumo'], 'suspense': v.get('suspense', '')}]
        total = len(serie.get('arco') or [])
        serie['proxima'] = parte + 1 if total > 1 and parte < total else None    # a execução de amanhã faz a próxima parte
        serie['atualizado'] = datetime.now(BRT).strftime('%Y-%m-%d')
        serie.pop('adiada', None)
        arq_serie.write_text(json.dumps(serie, ensure_ascii=False, indent=1), encoding='utf-8')
        telegram(arq, (pasta / (arq.stem + '.txt')).read_text(encoding='utf-8'), v)
        return True
    except Exception as e:
        print('  ✘ não consegui fazer essa curiosidade:', str(e)[:300])
        msg = str(e).lower()
        _FALHAS.append(f'{pedido[:60]}: {str(e)[:160]}')
        if 'material ruim' in msg and parte > 1:
            return False                         # parte de série barrada: tenta a mesma parte amanhã (não encerra a série)
        return 'pular' if ('material' in msg or 'sensível' in msg or 'nenhuma fonte' in msg) else False


def _parte_pendente() -> tuple[str, int] | None:
    """Série com parte por fazer (a mais antiga primeiro), feita nos últimos 10 dias."""
    hoje = datetime.now(BRT).date()
    pend = []
    for p in PASTA_SERIES.glob('*.json'):
        try:
            s = json.loads(p.read_text(encoding='utf-8'))
            if s.get('proxima') and (hoje - datetime.strptime(s.get('atualizado', '2000-01-01'), '%Y-%m-%d').date()).days <= 10:
                pend.append((s['atualizado'], s['pedido'], int(s['proxima'])))
        except Exception:
            continue
    return min(pend)[1:] if pend else None


def diario(pasta: Path):
    """O vídeo do dia (1 por dia, automático). O caçador de pautas escolhe o tema com mais potencial de viralizar
    (data chegando, notícia em alta, estudo novo ou curiosidade da planilha/lista). Série em andamento continua no dia
    seguinte; só um tema urgente (data/notícia com momento ≥ 9) passa na frente, e no máximo por 1 dia."""
    from src import orcamento_video          # Fase 1 (monitorar): UM orçamento para o vídeo do dia, com todas as tentativas
    with orcamento_video.video('diário'):
        return _diario(pasta)


def _diario(pasta: Path):
    from src import cacador, temas
    from src.orcamento import sobra
    hoje = datetime.now(BRT).strftime('%Y-%m-%d')
    pend = _parte_pendente()
    pautas = cacador.cacar()
    if pend:
        arq = _arquivo_serie(pend[0], pend[1])
        serie = json.loads(arq.read_text(encoding='utf-8'))
        urgente = next((p for p in pautas[:3] if p.get('origem') in ('data', 'noticia') and float(p.get('momento') or 0) >= 9), None)
        if urgente and not serie.get('adiada'):
            print(f"[diário] tema urgente passa na frente da série (que sai amanhã): {urgente['tema']}")
            serie['adiada'] = hoje
            arq.write_text(json.dumps(serie, ensure_ascii=False, indent=1), encoding='utf-8')
            pautas = [urgente] + [p for p in pautas if p is not urgente]
        else:
            print(f'[diário] continuando a série: {pend[0]} → parte {pend[1]}')
            r = fazer_curiosidade(pend[0], pend[1], pasta)
            if r is True or r is False:     # feito, ou erro passageiro (tenta a mesma parte amanhã)
                if r is False:
                    _aviso_sem_video(f'a parte {pend[1]} da série não saiu (tento de novo amanhã)')
                return
            try:                            # a próxima parte não rende (sem material): encerra a série e segue
                serie['proxima'] = None
                arq.write_text(json.dumps(serie, ensure_ascii=False, indent=1), encoding='utf-8')
            except Exception:
                pass
    for p in pautas[:3]:
        if sobra() < 50:
            print('  [diário] sem tempo para tentar outro tema hoje')
            _aviso_sem_video('acabou o tempo da execução antes de achar um tema que desse certo'); return
        print(f"[diário] tema: {p['tema']} ({p.get('origem')}/{p.get('area') or '?'}) — {p.get('motivo', '')}")
        r = fazer_curiosidade(p['tema'], 1, pasta, pauta=p)
        if r is True or r == 'pular':
            temas.marcar_usado(p['tema'])
            if p.get('tema_original') and p['tema_original'] != p['tema']:
                temas.marcar_usado(p['tema_original'])
        if r is True:
            cacador.registrar(p)
            return
        if r is False:
            print('  [diário] erro passageiro: tento de novo amanhã')
            _aviso_sem_video('erro passageiro (tento de novo amanhã)'); return
    if not pautas:
        print('  ✘ nenhuma pauta hoje: adicione temas na planilha')
    _aviso_sem_video('nenhum dos temas do dia deu certo' if pautas else 'nenhuma pauta hoje: adicione temas na planilha')


def _aviso_sem_video(motivo: str):
    """Dia sem vídeo NUNCA passa em silêncio: manda no Telegram o motivo de cada tema que ficou de fora."""
    linhas = [f'⚠️ Hoje não saiu vídeo: {motivo}.']
    linhas += [f'• {f}' for f in _FALHAS[-4:]]
    from src import custo
    if custo.linha_telegram():                    # o que foi gasto mesmo sem vídeo (temas descartados)
        linhas.append(custo.linha_telegram())
        print(custo.tabela())
    from src import orcamento_video
    if orcamento_video.linha_telegram():
        linhas.append(orcamento_video.linha_telegram())
    linhas.append('Detalhes no log da execução no GitHub (Actions). Pode rodar de novo à mão se quiser.')
    try:
        _tg('sendMessage', {'text': '\n'.join(linhas)[:4000]})
    except Exception as e:
        print(f'  [telegram] aviso não enviado: {e}')


def _noticias(a, pasta: Path):
    """Lote de notícias: escolha (uma chamada para o lote) + um vídeo por notícia, cada um com o seu orçamento."""
    from src import pautas, roteiro
    escolhidas = []
    if a.tema.strip():
        lista = pautas.buscar_tema(a.tema.strip())
        print(f'{len(lista)} manchetes sobre "{a.tema.strip()}"')
        if not lista:
            print('  ✘ não achei notícias recentes sobre esse assunto'); return False   # main encerra, como antes
        escolhidas = roteiro.escolher(lista, 1)
    elif a.qtd > 0:
        lista = pautas.buscar()
        print(f'{len(lista)} manchetes novas')
        escolhidas = roteiro.escolher(lista, max(a.qtd, 4) if a.so_virais else a.qtd)
        if a.so_virais:
            from src.voz import config as _cfg
            lim = float(_cfg().get('nota_viral_minima', 8))
            for p in escolhidas:
                print(f"  nota viral {p.get('viral', 0):.0f}/10 · {p['titulo'][:80]}")
            escolhidas = [p for p in escolhidas if p.get('viral', 0) >= lim][:a.qtd]
            if not escolhidas:
                print(f'  nenhuma notícia com nota ≥ {lim:.0f} agora: sem vídeo de notícia nesta rodada')
    from src import orcamento_video
    orcamento_video.definir_rateio(len(escolhidas))       # a escolha é dividida entre os vídeos que vão ser feitos
    hist = pautas.carregar_historico()
    prods = produtos()
    for i, p in enumerate(escolhidas, 1):
        print(f'[{i}/{len(escolhidas)}] {p["titulo"]}')
        try:                                   # Fase 1 (monitorar): um orçamento por notícia
            with orcamento_video.video(p['titulo']):
                v = roteiro.escrever(p, prods)
                v['link'] = p['link']
                arq = montar_video(v, pasta, f'{i:02d}-{slug(v["titulo"])}')
                hist[p['chave']] = datetime.now(timezone.utc).isoformat()
                pautas.salvar_historico(hist)
                telegram(arq, (pasta / (arq.stem + '.txt')).read_text(encoding='utf-8'), v)
        except Exception as e:
            print('  ✘ pulei esta notícia:', str(e)[:300])


def main():
    from src.orcamento import vigia
    vigia()
    ap = argparse.ArgumentParser()
    ap.add_argument('--diario', action='store_true', help='o vídeo do dia: continua a série ou pega o próximo tema do banco')
    ap.add_argument('--qtd', type=int, default=int(os.getenv('QTD', 0)), help='quantos vídeos de notícia (manual)')
    ap.add_argument('--tema', default='', help='fazer 1 vídeo de notícia sobre um assunto específico')
    ap.add_argument('--explica', type=int, default=0, help='quantos vídeos de curiosidade do banco de temas')
    ap.add_argument('--curiosidade', default='', help='fazer 1 curiosidade sobre um assunto escolhido')
    ap.add_argument('--parte', type=int, default=1, help='parte da série de curiosidade (1, 2, 3...)')
    ap.add_argument('--so-virais', action='store_true', help='só faz notícia com nota de viralização alta')
    ap.add_argument('--mascote', default='', help='"gerar" = 4 versões do Coringa 3D; "1".."4" = gera as expressões da versão escolhida')
    ap.add_argument('--fabula', default=None, nargs='?', const='', help='vídeo do canal Ninguém Te Contou (tema opcional)')
    ap.add_argument('--teste', action='store_true', help='offline (voz de teste local)')
    ap.add_argument('--teste-edge', action='store_true', help='vídeo de exemplo com a voz real + amostras de vozes')
    a = ap.parse_args()
    hoje = datetime.now(BRT).strftime('%Y-%m-%d')
    pasta = RAIZ / 'saida' / hoje
    pasta.mkdir(parents=True, exist_ok=True)

    if a.fabula is not None:                          # canal 2: Ninguém Te Contou (animação da Valdirene)
        from src import fabula
        fabula.fazer(a.fabula.strip())
        return

    if a.teste:
        v = json.loads((RAIZ / 'tests' / os.getenv('EXEMPLO', 'exemplo_ira.json')).read_text(encoding='utf-8'))
        montar_video(v, pasta, '00-teste-' + slug(v['titulo']), teste=True)
        return

    if a.teste_edge:
        import asyncio
        frase = 'Oi, eu sou o Coringa! Em menos de um minuto, eu te conto uma história que pouca gente conhece.'
        amostras = [('1-antonio', 'pt-BR-AntonioNeural', '+0Hz', '+10%'),
                    ('2-antonio-grave', 'pt-BR-AntonioNeural', '-8Hz', '+6%'),
                    ('3-macerio', 'pt-BR-MacerioMultilingualNeural', '+0Hz', '+8%')]
        for nome, vz, tom, vel in amostras:
            try:
                asyncio.run(voz._edge(voz.pronuncia(frase), pasta / f'amostra-voz-{nome}.mp3', voz=vz, tom=tom, vel=vel))
            except Exception as e:
                print('  amostra falhou', vz, str(e)[:120])
        for nome, vz in [('6-gemini-charon', 'Charon'), ('7-gemini-orus', 'Orus'), ('8-gemini-iapetus', 'Iapetus')]:
            try:
                voz.gemini_tts(frase, pasta / f'amostra-voz-{nome}.wav', vz)
            except Exception as e:
                print('  amostra falhou', vz, str(e)[:160])
        voz.VOZ = os.getenv('VOZ', 'pt-BR-AntonioNeural')
        v = json.loads((RAIZ / 'tests' / os.getenv('EXEMPLO', 'exemplo_ira.json')).read_text(encoding='utf-8'))
        for im in v['imagens']:
            im.pop('arquivo', None)
            im['prompt'] = 'dark stormy sky over a desert mountain range at dusk, distant industrial facility lights'
        montar_video(v, pasta, '00-teste-' + slug(v['titulo']))
        return

    if a.mascote.strip():
        from src import mascote
        alvo = a.mascote.strip().lower()
        if alvo.isdigit():
            mascote.gerar_expressoes(int(alvo), pasta / 'mascote')
        else:
            mascote.gerar_versoes(pasta / 'mascote')
        return

    if a.diario:
        try:
            diario(pasta)
        except Exception as e:                # erro inesperado: avisa no Telegram em vez de sumir em silêncio
            import traceback
            traceback.print_exc()
            _aviso_sem_video(f'erro inesperado no sistema: {str(e)[:200]}')
        return
    if a.curiosidade.strip():
        fazer_curiosidade(a.curiosidade.strip(), a.parte, pasta)
        return

    from src import orcamento_video          # Fase 1 (monitorar): a escolha das notícias é custo do LOTE, rateado
    orcamento_video.abrir_lote('notícias')
    try:
        if _noticias(a, pasta) is False:
            return
    finally:
        orcamento_video.fechar_lote()

    if a.explica > 0:                        # curiosidades extras do banco de temas (manual)
        from src import temas
        for tema in temas.fila()[:a.explica]:
            fazer_curiosidade(tema, 1, pasta)
            temas.marcar_usado(tema)


if __name__ == '__main__':
    main()
