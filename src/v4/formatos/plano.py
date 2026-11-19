"""PLANO DE FORMATO: beats → camadas em slots fixos sobre um palco persistente (ATLAS / DOSSIÊ).

Tudo determinístico e sem IA:
- `resolver_tempos`: tempos podem ser números (s) ou âncoras na fala ("@1880", "@comporta+0.3") resolvidas pelas
  palavras sincronizadas da narração — a revelação acompanha a palavra que a pede.
- `validar`: componente/slot/palco permitidos pelo formato; COLISÃO = caixas de camadas simultâneas que se cruzam
  (posições são fixas, então a geometria é verificável antes do render); texto que não cabe no slot; PROGRESSÃO
  informativa (nenhum intervalo > 4 s sem nova informação, sem contar legenda/marca); mesma mídia duas vezes ao mesmo
  tempo (ERR-055); mídia usada demais; número de componentes distintos (excesso de modalidades).
- `props`: entrega à composição Remotion `Formato`.
"""
from __future__ import annotations

import copy
import json
import math
import re
import unicodedata
from pathlib import Path
from src.v4.formatos import layout

RAIZ = Path(__file__).resolve().parents[3]
CFG = json.loads((Path(__file__).with_name('formatos.json')).read_text(encoding='utf-8'))
SLOTS = CFG['slots']
COMP = {k: v for k, v in CFG.get('composicoes', {}).items() if not k.startswith('_')}


def _resolver_layout():
    """ATLAS: intenções de slot/quadro → pixels pela área segura das plataformas ativas (layout.py)"""
    from src.v4.formatos import layout
    for k, v in COMP.items():
        if v.get('formato') != 'atlas':
            continue
        v['slots'] = {n: layout.slot(s) for n, s in v['slots'].items()}
        if v.get('quadro'):
            q0 = v['quadro']
            v['centro_intencao'] = [q0[0] + q0[2] / 2, q0[1] + q0[3] / 2]   # a câmera mira o centro DESENHADO, não o recortado
        v['quadro'] = layout.quadro(v.get('quadro'))


_resolver_layout()
RASTER_DIR = RAIZ / 'motor4' / 'formatos' / 'dados' / 'raster'
REGRAS = CFG['regras']
SAI = 0.3


def canal(nome: str = 'coringa') -> dict:
    return json.loads((Path(__file__).parent / 'canais' / f'{nome}.json').read_text(encoding='utf-8'))


def _norm(t: str) -> str:
    return ''.join(ch for ch in unicodedata.normalize('NFD', str(t).lower()) if unicodedata.category(ch) != 'Mn')


def ancora(valor, palavras: list[dict], depois: float = 0.0) -> float:
    """'@palavra' / '@palavra+0.4' / '@2:palavra' (2ª ocorrência) → início da palavra na narração"""
    if isinstance(valor, (int, float)):
        return float(valor)
    m = re.fullmatch(r'@(?:(\d+):)?([^+\-]+)([+\-]\d+(?:\.\d+)?)?', str(valor).strip())
    if not m:
        raise ValueError(f'tempo inválido {valor!r}')
    n, alvo, desl = int(m.group(1) or 1), _norm(m.group(2)), float(m.group(3) or 0)
    if alvo == 'fim':                                   # fim da fala (+ respiro): fecho de camadas e duração
        if not palavras:
            raise ValueError('âncora @fim sem narração')
        return round(palavras[-1]['e'] + .6 + desl, 3)
    achados = [w['s'] for w in palavras if _norm(w['w']).strip('.,!?:;') == alvo]
    if len(achados) < n:
        raise ValueError(f'âncora {valor!r}: palavra não está na narração')
    return round(achados[n - 1] + desl, 3)


def resolver_tempos(plano: dict, palavras: list[dict], duracao_audio: float | None = None) -> dict:
    """Resolve falas no relogio real. Com duracao_audio, @fim e o FIM REAL do WAV.

    O modo sem duracao_audio preserva o comportamento legado (ultimo fonema+0,6).
    Preflight deve conhecer o audio antes de colocar CTA ou fechar as camadas.
    """
    p = copy.deepcopy(plano)
    p['_estilo_no_episodio'] = estilo_no_episodio(plano)

    def a(v):
        # Piso temporal reutilizável: respeita a sincronização com a fala sem
        # permitir que uma narração mais rápida encurte uma prova visual obrigatória.
        # Ex.: @max(2.5,@por-0.12) = maior valor entre 2,5s e a âncora real.
        if isinstance(v, str):
            piso = re.fullmatch(r'@max\(\s*(\d+(?:\.\d+)?)\s*,\s*(@[^()]+?)\s*\)', v.strip())
            if piso:
                return round(max(float(piso.group(1)), a(piso.group(2).strip())), 3)
        if duracao_audio is not None and isinstance(v, str):
            m = re.fullmatch(r'@fim([+\-]\d+(?:\.\d+)?)?', v.strip())
            if m:
                return round(float(duracao_audio) + float(m.group(1) or 0), 3)
        return ancora(v, palavras)
    for k in p.get('palco') or []:
        k['t'] = a(k['t'])
    for lst in ('destaques', 'rotulos'):
        for x in p.get(lst) or []:
            x['t0'] = a(x['t0'])
            if x.get('t1') is not None:
                x['t1'] = a(x['t1'])
    for r in p.get('rotas') or []:
        r['t0'], r['t1'] = a(r['t0']), a(r['t1'])
        if r.get('some') is not None:
            r['some'] = a(r['some'])
    for e in p.get('explicacoes') or []:
        e['t0'], e['t1'] = a(e['t0']), a(e['t1'])
    for c in p.get('clipes') or []:
        c['t0'], c['t1'] = a(c['t0']), a(c['t1'])
        c['params']['tempos'] = [round(a(x) - (0 if plano.get('_resolvido') else c['t0']), 2)
                                 for x in c['params'].get('tempos') or []]
        # Os destaques de peças são ancorados na fala em tempo absoluto no JSON
        # e convertidos em tempo LOCAL do clipe para o renderizador V2.
        for lista in ('focos', 'destaques_fluxo'):
            for marca in c['params'].get(lista) or []:
                # Plano bruto: âncoras da narração são ABSOLUTAS.
                # Fixture/segundo passe de plano resolvido: focos já estão no
                # relógio LOCAL do clipe — nunca subtrair c['t0'] novamente.
                marca['t'] = round(a(marca['t']) - (0 if plano.get('_resolvido') else c['t0']), 2)
    for b in p['beats']:
        if b.get('t') is not None:
            b['t'] = a(b['t'])
        for L in b['camadas']:
            L['t0'], L['t1'] = a(L['t0']), a(L['t1'])
            q = L.get('p') or {}
            if L.get('componente') == 'atlas.provaVisual':
                for nome in ('rotulo_t', 'rotulo2_t'):
                    if q.get(nome) is not None:
                        q[nome] = a(q[nome])
            for lista in ('marcos', 'nos', 'niveis', 'linhas', 'itens'):
                for x in q.get(lista) or []:
                    if isinstance(x, dict) and x.get('t') is not None:
                        x['t'] = a(x['t'])
            for at in q.get('ativo') or []:
                at['t0'] = a(at['t0'])
                if at.get('t1') is not None:
                    at['t1'] = a(at['t1'])
            if q.get('zoom'):
                q['zoom']['t0'] = a(q['zoom']['t0'])
            if q.get('legenda_t') is not None:
                q['legenda_t'] = a(q['legenda_t'])
            for k in ('t_marca', 't_total', 't_carimbo', 't_abre'):
                if q.get(k) is not None:
                    q[k] = a(q[k])
            if isinstance(q.get('carimbo'), dict) and q['carimbo'].get('t') is not None:
                q['carimbo']['t'] = a(q['carimbo']['t'])
            for lista in ('campos', 'marcas', 'etiquetas', 'ativos', 'partes'):
                for x in q.get(lista) or []:
                    if isinstance(x, dict) and x.get('t') is not None:
                        x['t'] = a(x['t'])
    if isinstance(p.get('duracao'), str):
        p['duracao'] = a(p['duracao'])
    if duracao_audio is not None and (isinstance(plano.get('duracao'), str) or not plano.get('duracao')):
        # Faz o CTA e as camadas finais caberem na narracao VERDADEIRA,
        # nao em uma estimativa de pausa apos a ultima palavra.
        p['duracao'] = round(float(duracao_audio), 3)
    aplicar_tokens(p)
    if p.get('camera') == 'roi':
        p['palco'] = palco_dos_beats(p)
        posicionar_pinos(p)
    inserir_cta(p)
    p['_resolvido'] = True
    return p


def aplicar_tokens(p: dict) -> None:
    """identidade vem do CANAL, não do episódio: corpo dos títulos por slot, espessura de rota/conexão"""
    can = canal(p.get('canal', 'coringa'))
    T = can.get('titulo') or {}
    for b in p.get('beats') or []:
        for L in b.get('camadas') or []:
            if L.get('componente') == 'editorial.titleOrPayoff':
                tk = T.get(L.get('slot')) or T.get('padrao') or {'normal': 84, 'destaque': 104}
                for l in (L.get('p') or {}).get('linhas') or []:
                    l['tamanho'] = tk['destaque'] if l.get('destaque') else tk['normal']
    M = (can.get('palco') or {}).get('mapa') or {}
    for r in p.get('rotas') or []:
        r['largura'] = M.get('conexao_px', 7) if r.get('arco') else M.get('rota_px', 9)


def estilo_no_episodio(plano_bruto: dict) -> list[str]:
    """chaves de IDENTIDADE escritas no arquivo do episódio (proibidas no ATLAS): tamanho, raio, espessura, ajuste de cor,
    transição/zoom da câmera… — o diretor não reinventa a estética por episódio"""
    if plano_bruto.get('formato') != 'atlas' or plano_bruto.get('_resolvido'):
        return list(plano_bruto.get('_estilo_no_episodio') or [])
    P_ = REGRAS.get('estilo_proibido_no_episodio') or {}
    out = []
    for b in plano_bruto.get('beats') or []:
        out += [f"beat {b.get('id')}: {k}" for k in P_.get('beat', []) if k in b]
        for L in b.get('camadas') or []:
            q = L.get('p') or {}
            out += [f"{L.get('id')}: {k}" for k in P_.get('camada', []) if k in q]
            out += [f"{L.get('id')}: linha com {k}" for l in q.get('linhas') or [] for k in P_.get('camada', []) if isinstance(l, dict) and k in l]
            if isinstance(q.get('desloc'), list):
                out.append(f"{L.get('id')}: desloc manual (use 'auto')")
    out += [f"rota: {k}" for r in plano_bruto.get('rotas') or [] for k in P_.get('rota', []) if k in r]
    out += [f"raster {r.get('nome')}: {k}" for r in plano_bruto.get('rasters') or [] for k in P_.get('raster', []) if k in r]
    return out


def inserir_cta(p: dict) -> None:
    """CTA do canal no fim, SÓ se couber: depois que a última revelação terminou (+0,8 s), por min_s–max_s, sem esticar o vídeo"""
    if p.get('cta') is False or any(L.get('componente') == 'editorial.cta' for b in p['beats'] for L in b['camadas']):
        return
    K = canal(p.get('canal', 'coringa')).get('cta') or {}
    ult = p['beats'][-1] if p.get('beats') else None
    comp = COMP.get((ult or {}).get('composicao') or '')
    if not K or not ult or not comp or 'cta' not in comp['slots']:
        p['cta_decisao'] = 'sem CTA: a composição final não tem lugar para ele'
        return
    dur = float(p['duracao'])
    rev = [L['t0'] for L in ult['camadas']] + [x['t'] for L in ult['camadas'] for x in (L.get('p') or {}).get('linhas') or [] if isinstance(x.get('t'), (int, float))]
    ini = max(max(rev, default=0) + .8, dur - K.get('max_s', 2.2))
    sobreposto = False
    if dur - .05 - ini < K.get('min_s', 1.2):
        if p.get('formato') == 'atlas' and K.get('pode_sobrepor_fecho') and dur >= K.get('min_s', 1.2) + .25:
            # A conclusão pode ocupar o último segundo da voz. O CTA usa o slot reservado abaixo do título:
            # aparece COM o fecho, sem cortar a narração nem esticar o vídeo.
            ini = dur - .05 - K.get('min_s', 1.2)
            sobreposto = True
        else:
            p['cta_decisao'] = f'sem CTA: só {dur - ini:.1f} s depois da revelação final (mín. {K.get("min_s", 1.2)} s)'
            return
    ult['camadas'].append({'id': 'cta', 'componente': 'editorial.cta', 'slot': 'cta', 't0': round(ini, 2), 't1': round(dur - .05, 2),
                           'p': {'texto': K.get('texto'), 'handle': K.get('handle')}})
    p['cta_decisao'] = (f'CTA sobreposto ao fecho em slot distinto de {ini:.1f} a {dur:.1f} s'
                       if sobreposto else f'CTA de {ini:.1f} a {dur:.1f} s')


# ---------------------------------------------------------------- câmera geográfica (mesma matemática do Palco.tsx)
def merc(lon: float, lat: float) -> tuple[float, float]:
    """Web Mercator normalizado 0–1 (MapLibre: mundo = 512·2^zoom px)"""
    s_ = math.sin(math.radians(max(-85.0, min(85.0, lat))))
    return (lon + 180) / 360, .5 - math.log((1 + s_) / (1 - s_)) / (4 * math.pi)


def camera_roi(roi, quadro, zmax: float | None = None, folga: float = .86, centro=None) -> dict:
    """enquadra o território (roi = oeste, sul, leste, norte) DENTRO do quadro livre da composição"""
    o, s_, l, n = roi
    (x0, y0), (x1, y1) = merc(o, n), merc(l, s_)
    qx, qy, qw, qh = quadro
    if centro:                     # centro desenhado ≠ centro do recorte: cabe na MENOR metade em volta dele
        qw = 2 * min(centro[0] - qx, qx + qw - centro[0])
        qh = 2 * min(centro[1] - qy, qy + qh - centro[1])
    z = math.log2(min(qw * folga / ((x1 - x0) * 512), qh * folga / ((y1 - y0) * 512)))
    if zmax is not None:
        z = min(z, zmax)
    z = max(z, Z_MIN)
    fx, fy = (x0 + x1) / 2, (y0 + y1) / 2
    lon = fx * 360 - 180
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * fy))))
    return {'foco': [round(lon, 6), round(lat, 6)], 'ancora': list(centro) if centro else [qx + qw / 2, qy + qh / 2], 'zoom': round(z, 3)}


Z_MIN = math.log2(1920 / 512)          # abaixo disso o mundo é mais baixo que a tela e o MapLibre trava/desloca a câmera


def _restringir(c: dict) -> dict:
    """MESMA restrição do MapLibre (e de Palco.cameraEm): zoom ≥ Z_MIN e centro vertical dentro do mundo — sem isso os
    pinos descolam no mapa-múndi (reuso China × EUA: 37–340 px)"""
    z = max(c['zoom'], Z_MIN)
    ws = 512 * 2 ** z
    cy = c['fy'] - (c['ancora'][1] - 960) / ws
    cy = min(max(cy, 960 / ws), 1 - 960 / ws)
    return {**c, 'zoom': z, 'fy': cy + (c['ancora'][1] - 960) / ws}


def _ease(t: float) -> float:
    return 4 * t * t * t if t < .5 else 1 - (-2 * t + 2) ** 3 / 2


def _cam(c: dict) -> dict:
    if 'foco' in c:
        return c
    return {'foco': c['centro'], 'ancora': [540, 960], 'zoom': c['zoom']}


def camera_em(palco: list[dict], t: float) -> dict | None:
    """câmera no instante t: transição com pan ponderado pela escala (zoom-in pana cedo) + deriva lenta no beat"""
    ks = [k for k in palco if k.get('camera')]
    if not ks:
        return None
    a = ks[0]
    for k in ks:
        if t >= k['t']:
            a = k
    i = ks.index(a)
    ca, d = _cam(a['camera']), a.get('dur_camera', 1.2)
    if i > 0 and d > 0 and t < a['t'] + d:
        cb = _cam(ks[i - 1]['camera'])
        e = _ease(max(0., min(1., (t - a['t']) / d)))
        z = cb['zoom'] + (ca['zoom'] - cb['zoom']) * e
        u = e if abs(ca['zoom'] - cb['zoom']) < 1e-3 else (2 ** -cb['zoom'] - 2 ** -z) / (2 ** -cb['zoom'] - 2 ** -ca['zoom'])
        (bx, by), (ax, ay) = merc(*cb['foco']), merc(*ca['foco'])
        fx, fy = bx + (ax - bx) * u, by + (ay - by) * u
        anc = [cb['ancora'][0] + (ca['ancora'][0] - cb['ancora'][0]) * e, cb['ancora'][1] + (ca['ancora'][1] - cb['ancora'][1]) * e]
        return _restringir({'fx': fx, 'fy': fy, 'ancora': anc, 'zoom': z})
    fx, fy = merc(*ca['foco'])
    dt = max(0., t - a['t'] - (max(0, d) if i > 0 else 0))     # 1º beat: sem voo de chegada, a deriva começa no quadro 0
    if a.get('dur_deriva'):                # recuo: mesma variação total, com aceleração e assentamento (seno)
        T_ = a['dur_deriva']
        dt = T_ * (1 - math.cos(math.pi * min(1., dt / T_))) / 2
    z = ca['zoom'] + a.get('deriva', 0) * dt
    if a.get('zoom_teto') is not None and a.get('deriva', 0) > 0:
        z = min(z, max(ca['zoom'], a['zoom_teto']))
    if a.get('ponto_fixo') and z != ca['zoom']:
        # a deriva converge para o protagonista (referência A: ponto fixo entre o centro do quadro e o retrato):
        # o ponto geográfico sob 'ponto_fixo' fica parado na tela enquanto o zoom muda
        S, anc, w0, w1 = a['ponto_fixo'], ca['ancora'], 512 * 2 ** ca['zoom'], 512 * 2 ** z
        gx, gy = fx + (S[0] - anc[0]) / w0, fy + (S[1] - anc[1]) / w0
        fx, fy = gx - (S[0] - anc[0]) / w1, gy - (S[1] - anc[1]) / w1
    return _restringir({'fx': fx, 'fy': fy, 'ancora': ca['ancora'], 'zoom': z})


def roi_tela(cam: dict, roi) -> dict:
    o, s_, l, n = roi
    ws = 512 * 2 ** cam['zoom']
    (x0, y0), (x1, y1) = merc(o, n), merc(l, s_)
    px = lambda x: cam['ancora'][0] + (x - cam['fx']) * ws
    py = lambda y: cam['ancora'][1] + (y - cam['fy']) * ws
    return {'x': px(x0), 'y': py(y0), 'w': px(x1) - px(x0), 'h': py(y1) - py(y0)}


def tokens_canal(can: dict) -> dict:
    """tokens do canal que o palco/primitivas usam — UMA lista (antes, três cópias esqueciam 'papel' e 'selo')"""
    return {k: can[k] for k in ('cores', 'fontes', 'tempo', 'palco', 'cartao', 'cartao_atlas', 'pino', 'cta', 'papel', 'selo', 'titulo') if k in can}


def estilo_legenda(pl: dict) -> dict:
    return (canal(pl.get('canal', 'coringa')).get('legenda') or {}).get(pl.get('formato')) or {}


def props_camada(pl: dict, meta: dict, imagens: dict | None = None) -> dict:
    """camada de legenda/marca — UMA fonte para render, quadros, trechos: estilo da legenda vem do CANAL por formato"""
    from src.v4.formatos import legenda_sync
    est = ((canal(pl.get('canal', 'coringa')).get('legenda') or {}).get(pl['formato']) or {})
    pal = meta['palavras']
    if est.get('caixa') == 'frase':
        pal = legenda_sync.caixa_frase(pal, *legenda_sync.nomes_do_plano(pl))
    if pl['formato'] == 'atlas' and est.get('destaque_estatico'):
        pal = legenda_sync.destacar_atlas(pal, pl, maximo=est.get('max_palavras', 3))
    marcas = sorted({0.0, pl['duracao']} | {x for c in pl.get('clipes') or [] for x in (c['t0'], c['t1'])})
    imagens = imagens or {}
    cenas = []
    for a, b in zip(marcas, marcas[1:]):
        clip = next((c for c in pl.get('clipes') or [] if c['t0'] <= a + .001 and c['t1'] >= b - .001), None)
        reg = imagens.get(((clip or {}).get('params') or {}).get('asset')) or {}
        video_real = bool(clip and clip.get('componente') == 'registro.video')
        cenas.append({'ini': a, 'fim': b,
                      'selo': ('REGISTRO' if video_real else 'ESQUEMA' if clip else None),
                      'credito': reg.get('credito') if video_real else None, 'legenda': True})
    out = {'duracao': pl['duracao'], 'palavras': pal, 'cenas': cenas, 'estilo': {k: v for k, v in est.items() if not k.startswith('_')}}
    if pl['formato'] == 'atlas':
        out['legenda_caixa'] = zonas('atlas')['legenda']
        out['credito_caixa'] = zonas('atlas')['creditos']
        out['marca_y'] = layout.faixa_inferior().get('marca_y')
        out['marca_visivel'] = layout.CFG['faixa_inferior'].get('marca_atlas', True)
    return out


def seguro(formato: str | None) -> dict | None:
    """área útil para o que o PALCO desenha sozinho (rótulos de mar/cidade): união das plataformas, sem a coluna de ícones"""
    if formato != 'atlas':
        return None
    u, fi = layout.uniao(), layout.faixa_inferior()
    return {'esq': max(u['esquerda'], 72), 'topo': fi['conteudo_topo'], 'base': fi['conteudo_base'],
            'direita': [{'de_y': d['de_y'], 'ate_y': d.get('ate_y', 1920), 'x': 1080 - d['largura']} for d in u['direita']], 'dir_max': 1080 - u['esquerda']}


def _creditos(plano: dict) -> dict | None:
    """créditos cartográficos (manifesto) e a faixa onde aparecem — separados das fontes factuais do roteiro.
    Estilo da referência: o crédito da FOTO de um pino também vai para esta faixa, enquanto o pino está na tela."""
    if plano.get('formato') != 'atlas':
        return None
    from src.v4.formatos import atlas_ref
    z = zonas('atlas').get('creditos', [72, 1174, 936, 46])
    ref = (canal().get('pino') or {}).get('estilo') == 'referencia'
    extras = [{'t0': L['t0'], 't1': L['t1'], 'txt': L['p']['meta']} for L in camadas(plano)
              if (L.get('p') or {}).get('meta') and
              (L['componente'] == 'atlas.provaVisual' or
               (ref and L['componente'] == 'atlas.geoPin' and (L.get('p') or {}).get('tipo') == 'foto'))]
    return {'extras': extras,'datasets': {k: v['atribuicao_exigida'] for k, v in atlas_ref.datasets().items() if v.get('atribuicao_exigida')},
            'obrigatorias': [k for k, v in atlas_ref.datasets().items() if v.get('obrigatoria')], 'caixa': z, 'px': 18, 'linha': 22}


def raster_info(nome: str) -> dict:
    m = json.loads((RASTER_DIR / f'{nome}.json').read_text(encoding='utf-8'))
    (o, n), (l, s_) = m['cantos'][0], m['cantos'][2]
    ppg = m.get('px_por_grau_fonte') or m['px'][0] / (l - o)   # resolução REAL da fonte (não a superamostrada)
    m['nitido_ate'] = round(math.log2(ppg * 360 / 512) + 1.0, 2)   # até 2× de ampliação ainda lê como relevo/imagem
    m['bbox'] = [o, s_, l, n]
    return m


def bases_do_plano(p: dict) -> list[dict]:
    return [raster_info(r['nome']) for r in p.get('rasters') or []]


def tela_lonlat(cam: dict) -> list[float]:
    """[oeste, sul, leste, norte] visíveis na tela 1080×1920 com esta câmera (longitude contínua em torno do foco)"""
    ws = 512 * 2 ** cam['zoom']
    x0 = cam['fx'] - cam['ancora'][0] / ws; x1 = cam['fx'] + (1080 - cam['ancora'][0]) / ws
    y0 = cam['fy'] - cam['ancora'][1] / ws; y1 = cam['fy'] + (1920 - cam['ancora'][1]) / ws
    lat = lambda y: math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y))))
    return [x0 * 360 - 180, max(-85.0, lat(min(y1, 1.0))), x1 * 360 - 180, min(85.0, lat(max(y0, 0.0)))]


def cobre(ri: dict, roi) -> bool:
    return ri['bbox'][0] <= roi[0] and ri['bbox'][1] <= roi[1] and ri['bbox'][2] >= roi[2] and ri['bbox'][3] >= roi[3]


def opacidade_raster(zoom: float, de=None, ate=None) -> float:
    """Espelha Palco.tsx/rampa: ter raster no manifesto não garante uma imagem visível no zoom atual."""
    def limitado(v: float) -> float:
        return max(0.0, min(1.0, v))
    return (1.0 if de is None else limitado((zoom - (de - .5)) / .8)) * \
           (1.0 if ate is None else limitado(((ate + .3) - zoom) / .8))


def teto_zoom(p: dict, roi) -> float | None:
    ns = [ri['nitido_ate'] for ri in bases_do_plano(p) if cobre(ri, roi)]
    return max(ns) if ns else None


def duracao_transicao(a: dict | None, b: dict | None) -> float:
    """preset de câmera do canal (canal.camera): voo mais longo quando muda mais de escala; o episódio não escolhe"""
    K = canal().get('camera') or {}
    if not a or not b:
        return K.get('transicao_min', .8)
    dz = abs(_cam(a)['zoom'] - _cam(b)['zoom'])
    d = K.get('transicao_base', .8) + K.get('transicao_por_zoom', .22) * dz
    return round(min(K.get('transicao_max', 1.8), max(K.get('transicao_min', .8), d)), 2)


def palco_dos_beats(p: dict) -> list[dict]:
    """cada beat → uma chave de palco: tipo da composição, câmera que enquadra o roi no quadro, véu da composição.
    Movimento medido na referência (atlas_ref.DERIVA): 'aproxima' (≈ +2,4 %/s enquanto camadas se revelam), 'fixo'
    (o dado muda, a câmera para) e 'recua' (fecho: começa mais perto e TERMINA no enquadramento do roi)."""
    from src.v4.formatos import atlas_ref
    beats = [b for b in p['beats'] if COMP.get(b.get('composicao') or '')]
    ini = [b.get('t', min((L['t0'] for L in b['camadas']), default=0.0)) for b in beats]
    out, ultima = [], None
    for i, b in enumerate(beats):
        c = COMP[b['composicao']]
        t = ini[i]
        fim = ini[i + 1] if i + 1 < len(beats) else p.get('duracao', t + 5)
        k = {'t': t, 'tipo': c['palco'], 'composicao': b['composicao'], 'veu': c.get('veu', 'nenhum')}
        if c['palco'] == 'mapa':
            mov = b.get('movimento') or c.get('movimento') or 'fixo'
            k['movimento'] = mov
            k['deriva'] = atlas_ref.deriva(mov)
            if b.get('roi'):
                # teto de zoom = nitidez da MELHOR base licenciada que cobre o território (nunca amplia imagem além dela)
                teto = teto_zoom(p, b['roi'])
                # aproximação: o território começa com folga para CRESCER o beat inteiro e terminar ~96 % do quadro
                # (referência A: +23 % em 8 s sem sair do enquadramento); fixo/recua: folga padrão
                folga = .86
                if mov == 'aproxima':
                    folga = max(.7, min(.86, .96 / 2 ** (atlas_ref.deriva(mov) * max(0, fim - t))))
                k['camera'] = camera_roi(b['roi'], c.get('quadro') or [0, 0, 1080, 1920], teto, folga, c.get('centro_intencao'))
                k['dur_camera'] = duracao_transicao(ultima, k['camera'])
                # a deriva de aproximação PARA na nitidez da base e quando o território encosta no quadro livre
                if c.get('quadro'):
                    (x0, y0), (x1, y1) = merc(b['roi'][0], b['roi'][3]), merc(b['roi'][2], b['roi'][1])
                    qx_, qy_, qw_, qh_ = c['quadro']
                    if c.get('centro_intencao'):
                        cx_, cy_ = c['centro_intencao']
                        qw_, qh_ = 2 * min(cx_ - qx_, qx_ + qw_ - cx_), 2 * min(cy_ - qy_, qy_ + qh_ - cy_)
                    z_fit = math.log2(min(qw_ / ((x1 - x0) * 512), qh_ / ((y1 - y0) * 512)))
                    teto = z_fit if teto is None else min(teto, z_fit)
                if teto is not None:
                    k['zoom_teto'] = round(teto, 3)
                    # aproximação CONTÍNUA (referência: ≈ +2 %/s o beat inteiro): se o teto cortaria a deriva no meio, a
                    # câmera começa um pouco mais aberta (até 0,6 de zoom) para o movimento durar o beat todo
                    if k['deriva'] > 0:
                        t_ini = 0.0 if i == 0 else t          # o 1º beat começa no quadro 0 (o clipe do gancho fica por cima)
                        falta = k['camera']['zoom'] + k['deriva'] * max(0, fim - t_ini - (k['dur_camera'] if i else 0)) - teto
                        if falta > 0:
                            k['camera'] = {**k['camera'], 'zoom': round(k['camera']['zoom'] - min(.6, falta), 3)}
                if mov == 'recua':
                    k['dur_deriva'] = round(max(.1, fim - t - k['dur_camera']), 3)   # recuo SUAVIZADO (referência: acelera e assenta)
                if mov == 'recua':           # termina no enquadramento: começa |deriva|·duração mais perto
                    k['camera'] = {**k['camera'], 'zoom': round(k['camera']['zoom'] - k['deriva'] * max(0, fim - t - k['dur_camera']), 3)}
                if c.get('quadro'):
                    k['roi'] = b['roi']
                prot = next((L for L in b.get('camadas') or [] if L.get('componente') == 'atlas.geoPin'
                             and (L.get('p') or {}).get('papel') == 'protagonista'), None)
                if mov == 'aproxima' and prot:
                    cam0 = _cam(k['camera'])
                    px, py = projetar({'fx': merc(*cam0['foco'])[0], 'fy': merc(*cam0['foco'])[1], 'ancora': cam0['ancora'], 'zoom': cam0['zoom']}, *prot['p']['lonlat'])
                    k['ponto_fixo'] = [round((cam0['ancora'][0] + px) / 2, 1), round((cam0['ancora'][1] + py) / 2, 1)]
            elif ultima:
                k['camera'] = ultima
            k.setdefault('dur_camera', duracao_transicao(ultima, k.get('camera')))
            ultima = k.get('camera', ultima)
        out.append(k)
    if out:
        out[0]['t'] = 0.0
    return out


# ---------------------------------------------------------------- pinos geográficos (atlas.geoPin)
def zonas(formato: str) -> dict:
    z = {k: v for k, v in CFG.get('zonas_identidade', {}).items()}
    zf = CFG.get('zonas_por_formato', {}).get(formato) or {}
    if zf.get('dinamico'):
        from src.v4.formatos import layout
        fi = layout.faixa_inferior()
        z.update(legenda=fi['legenda'], creditos=fi['creditos'])
        if formato == 'atlas':
            x, _, w, h = fi['creditos']
            z['creditos'] = [x, layout.H - layout.CFG['faixa_inferior']['atlas_creditos_margem_base'] - h, w, h]
        if zf.get('marca'):
            z['marca'] = zf['marca']
    else:
        z.update({k: v for k, v in zf.items() if not k.startswith('_')})
    if formato == 'atlas' and not layout.CFG['faixa_inferior'].get('marca_atlas', True):
        z.pop('marca', None)   # ATLAS: sem marca fixa para não bloquear abertura/cartões
    return z


def projetar(cam: dict, lon: float, lat: float) -> tuple[float, float]:
    ws = 512 * 2 ** cam['zoom']
    x, y = merc(lon, lat)
    dx = (x - cam['fx'] + .5) % 1 - .5          # cópia do mundo mais perto da câmera (vista centrada no Pacífico)
    return cam['ancora'][0] + dx * ws, cam['ancora'][1] + (y - cam['fy']) * ws


def papel_pino(q: dict) -> dict:
    return {**{'raio': 118, 'rotulo_px': 30, 'anel': 6}, **((canal().get('pino') or {}).get(q.get('papel') or 'secundario') or {})}


def caixa_pino(q: dict, ax: float, ay: float, desloc=None) -> dict:
    """caixa ocupada por um pino ancorado em (ax, ay) — MESMA geometria de Primitivas.GeoPin"""
    if q.get('tipo') == 'foto' and (canal().get('pino') or {}).get('estilo') == 'referencia':
        PP = papel_pino(q)
        r = q.get('raio') or PP['raio']
        dx, dy = desloc or (q['desloc'] if isinstance(q.get('desloc'), list) else [r, -(r + 55)])
        cx = ax + dx
        hl = PP['rotulo_px'] + 32
        lw = max(2 * r + 2 * PP['anel'], _largura(q.get('rotulo', ''), PP['rotulo_px'], .6) + 44)
        topo = ay + dy - r - PP['anel']
        return {'x': cx - lw / 2, 'y': topo, 'w': lw, 'h': (ay + hl / 2) - topo}
    if q.get('tipo') == 'foto':
        PP = papel_pino(q)
        r = q.get('raio') or PP['raio']
        dx, dy = desloc or (q['desloc'] if isinstance(q.get('desloc'), list) else [0, -(r + 80)])
        cx, cy = ax + dx, ay + dy
        foto = 2 * r + 2 * PP['anel']
        rot = _largura(q.get('rotulo', ''), PP['rotulo_px'], .66) + 40
        teto = max(300, foto + 40)                          # rótulo quebra em linhas, nunca mais largo que a foto + 40
        nl = 1 if rot <= teto else 2
        lw = max(foto, min(rot, teto))
        return {'x': cx - lw / 2, 'y': cy - r - PP['anel'] - 4, 'w': lw,
                'h': foto + 12 + nl * (PP['rotulo_px'] + 2) + 22 + (26 if q.get('meta') else 0), 'linhas_rotulo': nl}
    lw = _largura(q.get('rotulo', ''), 30, .66) + 44
    lado = q.get('lado_auto') or q.get('lado', 'direita')
    if lado in ('acima', 'abaixo'):
        return {'x': ax - lw / 2, 'y': ay - 84 if lado == 'acima' else ay + 28, 'w': lw, 'h': 56}
    return {'x': ax + 26 if lado == 'direita' else ax - 26 - lw, 'y': ay - 28, 'w': lw, 'h': 56}


def partes_pino(q: dict, ax: float, ay: float, desloc=None) -> list[dict]:
    """foto e rótulo do pino no estilo da referência, como caixas separadas (mesma geometria de PinoReferencia)"""
    PP = papel_pino(q)
    r = q.get('raio') or PP['raio']
    dx, dy = desloc or (q['desloc'] if isinstance(q.get('desloc'), list) else [r, -(r + 55)])
    a = PP['anel']
    hl = PP['rotulo_px'] + 32
    lw = _largura(q.get('rotulo', ''), PP['rotulo_px'], .62) + 44
    # rótulo centrado sob a foto, mas recuado para dentro da área segura se a coluna de ícones o alcançaria (= Primitivas)
    lx = min(ax + dx, layout.limite_direito(ay - hl / 2 + 8, ay + hl / 2 - 8) - lw / 2 - 4)
    return [{'x': ax + dx - r - a, 'y': ay + dy - r - a, 'w': 2 * (r + a), 'h': 2 * (r + a)},
            {'x': lx - lw / 2, 'y': ay - hl / 2, 'w': lw, 'h': hl}]      # crédito da foto vai para a faixa de créditos


def posicionar_pinos(plano: dict) -> None:
    """desloc 'auto' (ou ausente) num pino de foto: escolhe a direção em que a foto cabe na área segura e no quadro, sem
    cobrir camadas nem outros pinos, durante toda a vida do pino (protagonista primeiro). Regra do motor, não do episódio."""
    from src.v4.formatos import layout
    ks = plano.get('palco') or []
    Ls = camadas(plano)
    fi = layout.faixa_inferior()
    estat = [L for L in Ls if not L.get('dinamica')]
    fotos = sorted([L for L in Ls if L.get('dinamica') and (L.get('p') or {}).get('tipo') == 'foto' and not isinstance(L['p'].get('desloc'), list)],
                   key=lambda L: 0 if L['p'].get('papel') == 'protagonista' else 1)
    def custo_de(q, dx, dy, ts):
        custo = 0
        for t in ts:
            cam = camera_em(ks, t)
            if not cam:
                continue
            ax, ay = projetar(cam, *q['lonlat'])
            bx = caixa_pino(q, ax, ay, [dx, dy])
            xd = layout.limite_direito(bx['y'], bx['y'] + bx['h'])
            # estilo da referência: a foto e o rótulo são caixas SEPARADAS (a união cobriria a coluna de ícones sem tocar nela)
            caixas = partes_pino(q, ax, ay, [dx, dy]) if (canal().get('pino') or {}).get('estilo') == 'referencia' and q.get('tipo') == 'foto' else [bx]
            fora = sum(max(0, xe - b_['x']) + max(0, b_['x'] + b_['w'] - layout.limite_direito(b_['y'] + 8, b_['y'] + b_['h'] - 8)) +
                       max(0, fi['conteudo_topo'] - b_['y']) + max(0, b_['y'] + b_['h'] - fi['conteudo_base']) for b_ in caixas)
            custo += fora * 10
            for M in estat:
                if M['t0'] <= t <= M['t1'] + SAI and any(_cruza({'x': c_['x'] + 6, 'y': c_['y'] + 6, 'w': c_['w'] - 12, 'h': c_['h'] - 12}, M['caixa']) for c_ in caixas):
                    custo += 5000
        return custo

    xe = layout.uniao()['esquerda']
    # pinos de texto: o lado pedido é preferência; se o rótulo sair da área segura ou cruzar outro pino, troca de lado
    textos = [L for L in Ls if L.get('dinamica') and (L.get('p') or {}).get('tipo') != 'foto' and L['p'].get('lonlat')]
    for L in textos:
        q = L['p']
        pref = q.get('lado', 'direita')
        ts = list(_passos(L['t0'], L['t1'] + SAI, .25))     # MESMA amostragem do validador
        melhor, pior = pref, 1e9
        for lado in [pref] + [x for x in ('direita', 'esquerda', 'acima', 'abaixo') if x != pref]:
            q['lado_auto'] = lado
            custo = custo_de(q, 0, 0, ts)
            for t in ts:
                outros = {k: b for k, b in pinos_em(plano, [M for M in textos if M is not L and 'lado_auto' in M['p'] and M['t0'] <= t <= M['t1']], t).items()}
                mine = pinos_em(plano, [L], t).get(L['id'])
                if mine and any(_cruza(mine, b) for b in outros.values()):
                    custo += 5000
            if custo < pior:
                melhor, pior = lado, custo
            if custo == 0:
                break
        q['lado_auto'] = melhor
    for L in fotos:
        q = L['p']
        PP = papel_pino(q)
        r0 = q.get('raio') or PP['raio']
        ts = list(_passos(L['t0'], L['t1'] + SAI, .25))     # MESMA amostragem do validador
        melhor, pior, raio = None, 1e9, r0
        # escala do papel primeiro; se nenhuma direção couber na área segura, a foto encolhe (até 75 % do papel)
        for f in (1.0, .92, .84, .75):
            r = round(r0 * f)
            q['raio'] = r
            d = r + 70
            cands = ([(r, -(r + 55)), (-r, -(r + 55))] if (canal().get('pino') or {}).get('estilo') == 'referencia' else []) + [(0, -d), (d * .8, -d * .8), (-d * .8, -d * .8), (d, 0), (-d, 0), (d * .8, d * .8), (-d * .8, d * .8), (0, d),
                     (d * .5, -d * .87), (-d * .5, -d * .87), (d * .87, -d * .5), (-d * .87, -d * .5), (d * .87, d * .5), (-d * .87, d * .5)]
            for dx, dy in cands:
                custo = custo_de(q, dx, dy, ts)
                if custo < pior:
                    melhor, pior, raio = [round(dx), round(dy)], custo, r
                if custo == 0:
                    break
            if pior == 0:
                break
        q['raio'] = raio
        q['desloc'] = melhor
        q['desloc_auto'] = True
        q['escala_auto'] = round(raio / r0, 2)


def pinos_em(plano: dict, Ls: list[dict], t: float) -> dict[str, dict]:
    cam = camera_em(plano.get('palco') or [], t)
    out = {}
    if not cam:
        return out
    for L in Ls:
        if L['componente'] == 'atlas.geoPin' and L['t0'] <= t <= L['t1'] + SAI:
            q = L.get('p') or {}
            ax, ay = projetar(cam, *q['lonlat'])
            out[L['id']] = {**caixa_pino(q, ax, ay), 'ancora': (ax, ay)}
    return out


def camadas(plano: dict) -> list[dict]:
    out = []
    for b in plano['beats']:
        for L in b['camadas']:
            if L.get('componente') == 'atlas.geoPin':     # ancorado no território: caixa calculada pela câmera (pinos_em)
                out.append({**L, 'beat': b['id'], 'composicao': b.get('composicao'), 'caixa': {'x': -9e3, 'y': -9e3, 'w': 0, 'h': 0}, 'dinamica': True})
                continue
            out.append({**L, 'beat': b['id'], 'composicao': b.get('composicao'), 'caixa': caixa(L, b.get('composicao'))})
    return out


def caixa(L: dict, comp: str | None = None) -> dict:
    if isinstance(L.get('caixa'), dict):
        return L['caixa']
    if L.get('caixa'):
        x, y, w, h = L['caixa']
    elif comp and L.get('slot') in (COMP.get(comp) or {}).get('slots', {}):
        x, y, w, h = COMP[comp]['slots'][L['slot']]
    else:
        x, y, w, h = SLOTS[L['slot']]
    return {'x': x, 'y': y, 'w': w, 'h': h}


def _cruza(a: dict, b: dict) -> bool:
    return a['x'] < b['x'] + b['w'] and b['x'] < a['x'] + a['w'] and a['y'] < b['y'] + b['h'] and b['y'] < a['y'] + a['h']


def _largura(txt: str, px: float, peso: float = .72) -> float:
    return len(str(txt)) * px * peso


def fonte_nivel(w: float) -> int:
    """mesma regra do componente Hierarchy (Primitivas.tsx)"""
    return 26 if w > 150 else (22 if w > 110 else 20)


def _cabe(L: dict) -> list[str]:
    """estimativa conservadora de largura (Montserrat 900 em caixa alta ≈ 0,72 em; JetBrains Mono ≈ 0,6 em)"""
    p, b, c, out = L.get('p') or {}, caixa(L), L['componente'], []
    if c == 'editorial.titleOrPayoff':
        if len(p.get('linhas') or []) > REGRAS['titulo_max_linhas']:
            out.append(f"título com {len(p['linhas'])} linhas (máx. {REGRAS['titulo_max_linhas']}): vira slide")
        for l in p.get('linhas') or []:
            if _largura(l['texto'], l.get('tamanho', 104)) > b['w']:
                out.append(f"título {l['texto']!r} não cabe em {b['w']} px a {l.get('tamanho', 104)} px")
    elif c == 'editorial.statCard':
        txt = f"{p.get('prefixo', '')}{p.get('valor')}"
        K = {**{'pad_x': 40, 'numero_px': 112, 'numero_min_px': 60, 'unidade_razao': .46}, **(canal().get('cartao') or {})}
        util = b['w'] - 2 * K['pad_x']
        if p.get('estilo') == 'dial':        # mostrador à esquerda, número + legenda na metade direita (Primitivas.Dial)
            col = util * .5
            if _largura(f"{p.get('prefixo', '')}{p.get('valor')}", K['numero_min_px'], .7) > col or _largura(p.get('unidade', ''), 30, .7) > col:
                out.append(f'número {txt!r} {p.get("unidade", "")!r} não cabe ao lado do mostrador ({col:.0f} px)')
            for x in p.get('partes') or []:
                if _largura(x['rotulo'], 26, .62) + 24 > col:
                    out.append(f"legenda {x['rotulo']!r} não cabe ao lado do mostrador")
        elif p.get('estilo') in ('calendario', 'ficha', 'cedula'):
            pass
        elif p.get('estilo') == 'selo':
            if _largura(str(p.get('valor', '')), 30, .9) + 52 > b['w']:
                out.append(f"selo {p.get('valor')!r} não cabe em {b['w']} px")
        elif p.get('estilo') == 'pilula':
            tot = _largura(txt, 40, .62) + _largura(f" {p.get('unidade', '')}" if p.get('unidade') else '', 40) + _largura(f" · {p.get('rotulo', '')}" if p.get('rotulo') else '', 40, .66)
            if tot * 30 / 40 + 60 > b['w']:               # corpo encolhe até 30 px (Primitivas.StatCard pílula)
                out.append(f'pílula {txt} {p.get("rotulo", "")!r} não cabe nem a 30 px ({tot * .75 + 60:.0f} > {b["w"]} px)')
        else:                                 # cartão: o número encolhe até numero_min_px (Primitivas.StatCard)
            px = K['numero_min_px']
            if _largura(txt, px, .7) + _largura(' ' + p.get('unidade', ''), px * K['unidade_razao'], .7) > util:
                out.append(f'número {txt!r} não cabe no cartão nem no corpo mínimo ({px} px)')
            if p.get('rotulo') and _largura(p['rotulo'], 34) > 2 * (b['w'] - 90):
                out.append(f"rótulo {p['rotulo']!r} longo demais (> 2 linhas)")
    elif c == 'editorial.hierarchy':
        n = len(p.get('niveis') or [])
        w = (b['w'] - 10 * (n - 1)) / max(1, n)
        if p.get('rotulos_abaixo') is not False and n > 5:     # nomes embaixo em 2 fileiras, corpo 26 (Primitivas.Hierarchy)
            for nv in p.get('niveis') or []:
                if _largura(nv['rotulo'], 26, .62) > 220:
                    out.append(f"nível {nv['rotulo']!r} não cabe em 220 px a 26 px")
            return out
        for nv in p.get('niveis') or []:
            if max((_largura(x, fonte_nivel(w), .62) for x in str(nv['rotulo']).split()), default=0) > w - 8:
                out.append(f"nível {nv['rotulo']!r} não cabe em {w:.0f} px")
    elif c == 'editorial.timeline':
        for m in p.get('marcos') or []:
            if _largura(m['texto'], 28) > 2 * 300:
                out.append(f"marco {m['texto']!r} longo demais")
    elif c == 'editorial.flowConnections':
        for no in p.get('nos') or []:
            if _largura(no['rotulo'], 38) > (p.get('largura') or 640) - 30:
                out.append(f"nó {no['rotulo']!r} não cabe")
    return out


def _passos(a: float, b: float, d: float):
    x = a
    while x < b:
        yield round(x, 3)
        x += d


def eventos(plano: dict) -> list[float]:
    """instantes em que surge informação NOVA no conteúdo (nunca legenda/marca)"""
    ev = [k['t'] for k in plano.get('palco') or []]
    ev += [x['t0'] for x in plano.get('destaques') or []] + [x['t0'] for x in plano.get('rotulos') or []]
    for r in plano.get('rotas') or []:
        ev += [r['t0'], (r['t0'] + r['t1']) / 2, r['t1']]
    for c in plano.get('clipes') or []:
        # clipe aprovado com ação/filme verificado (o portão CONGELADO confere no render): progride o tempo todo
        ev += [c['t0'] + x for x in c['params'].get('tempos') or []] + [c['t0']] + list(_passos(c['t0'], c['t1'], 1.0))
    for L in camadas(plano):
        ev.append(L['t0'])
        q = L.get('p') or {}
        for lista in ('marcos', 'nos', 'niveis', 'linhas', 'itens'):
            ev += [x['t'] for x in q.get(lista) or [] if isinstance(x, dict) and x.get('t') is not None]
        ev += [a['t0'] for a in q.get('ativo') or []]
        if q.get('zoom'):
            ev.append(q['zoom']['t0'])
        if q.get('legenda_base') and q.get('legenda_t') is not None:
            ev.append(q['legenda_t'])
        if L['componente'] == 'atlas.provaVisual':
            for nome in ('rotulo_t', 'rotulo2_t'):
                if isinstance(q.get(nome), (int, float)) and q.get('rotulo' if nome == 'rotulo_t' else 'rotulo2'):
                    ev.append(q[nome])
        if q.get('contagem'):
            ev.append(L['t0'] + (q.get('dur_contagem') or 1.2))
        ev += [q[k] for k in ('t_marca', 't_total', 't_carimbo', 't_abre') if isinstance(q.get(k), (int, float))]
        if isinstance(q.get('carimbo'), dict) and isinstance(q['carimbo'].get('t'), (int, float)):
            ev.append(q['carimbo']['t'])
        for lista in ('campos', 'ativos', 'partes'):
            ev += [x['t'] for x in q.get(lista) or [] if isinstance(x, dict) and isinstance(x.get('t'), (int, float))]
    return sorted(ev)


def validar(plano: dict, imagens: dict | None = None) -> list[dict]:
    """plano com tempos JÁ resolvidos → [{gravidade, regra, onde, texto}]"""
    out = []
    v = lambda g, r, o, t: out.append({'gravidade': g, 'regra': r, 'onde': o, 'texto': t})
    F = CFG['formatos'].get(plano.get('formato'))
    if not F:
        return [{'gravidade': 'erro', 'regra': 'F-FORMATO', 'onde': '-', 'texto': f"formato desconhecido {plano.get('formato')!r}"}]
    dur = float(plano['duracao'])
    for k in plano.get('palco') or []:
        if k['tipo'] not in F['palcos']:
            v('erro', 'F-PALCO', f"t={k['t']}", f"palco {k['tipo']} fora do formato {plano['formato']}")
    if not plano.get('palco') or plano['palco'][0]['t'] > 0:
        v('erro', 'F-PALCO', 't=0', 'o palco precisa existir desde o primeiro quadro')
    Ls = camadas(plano)
    if imagens:
        _mirar(Ls, imagens)
    for L in Ls:
        onde = f"{L['beat']}/{L['id']}"
        if L['componente'] not in F['componentes']:
            v('erro', 'F-COMPONENTE', onde, f"{L['componente']} não é do formato {plano['formato']}")
        comp = COMP.get(L.get('composicao') or '')
        if L.get('composicao') and not comp:
            v('erro', 'F-COMPOSICAO', onde, f"composição {L['composicao']!r} desconhecida")
        elif L.get('dinamica'):
            if comp and not comp.get('pinos'):
                v('erro', 'F-COMPOSICAO', onde, f"{L['composicao']} não aceita pinos geográficos")
            if not (L.get('p') or {}).get('lonlat'):
                v('erro', 'F-PINO', onde, 'pino sem coordenada (lonlat)')
        elif comp and not (L.get('slot') in comp['slots'] or L.get('caixa_livre')):
            v('erro', 'F-SLOT', onde, f"slot {L.get('slot')!r} não existe na composição {L['composicao']} ({', '.join(comp['slots'])})")
        elif not comp and L.get('slot') not in SLOTS and not isinstance(L.get('caixa'), (list, dict)):
            v('erro', 'F-SLOT', onde, f"slot {L.get('slot')!r} desconhecido")
        if not (0 <= L['t0'] < L['t1'] <= dur + .01):
            v('erro', 'F-TEMPO', onde, f"tempo {L['t0']}–{L['t1']} fora de 0–{dur}")
        for f in _cabe(L):
            v('erro', 'F-TEXTO-NAO-CABE', onde, f)
        a = (L.get('p') or {}).get('asset')
        if a and imagens is not None and a not in imagens:
            v('erro', 'F-ASSET', onde, f'mídia {a!r} indisponível')
        if L['componente'] == 'atlas.provaVisual':
            if not a or not (L.get('p') or {}).get('meta'):
                v('erro', 'F-PROVA-CREDITO', onde, 'fotografia principal exige asset e crédito visível')
            if imagens is not None and a in imagens and imagens[a].get('tipo') == 'video':
                v('erro', 'F-PROVA-TIPO', onde, 'vídeo deve usar registro.video, não componente fotográfico')
    for c in plano.get('clipes') or []:
        if c['componente'] not in F['clipes']:
            v('erro', 'F-CLIPE', f"{c['t0']}", f"clipe {c['componente']} não aprovado no formato")
        if c.get('componente') == 'registro.video':
            a = (c.get('params') or {}).get('asset')
            inicio = (c.get('params') or {}).get('inicio', 0)
            if not a or not isinstance(inicio, (int, float)) or isinstance(inicio, bool) or inicio < 0 or c.get('fonte'):
                v('erro', 'F-VIDEO-PARAMS', str(c.get('t0')), 'vídeo exige asset verificado e início ≥0, sem campo fonte de mecanismo')
            if imagens is not None and a not in imagens:
                v('erro', 'F-ASSET', str(c.get('t0')), 'vídeo real ausente do acervo')
            if imagens is not None and a in imagens and imagens[a].get('tipo') != 'video':
                v('erro', 'F-VIDEO-TIPO', str(c.get('t0')), 'registro.video exige mídia de natureza vídeo')
            if imagens is not None and a in imagens and isinstance(inicio, (int, float)) and c['t1'] - c['t0'] + inicio > imagens[a].get('duracao', 0) + .01:
                v('erro', 'F-VIDEO-DURACAO', str(c.get('t0')), 'o trecho pedido excede a duração original; não congelar quadro')
            for L in Ls:
                if L['t0'] < c['t1'] and L['t1'] > c['t0']:
                    v('erro', 'F-VIDEO-SOBREPOE-CAMADA', L['id'], 'clipe real substitui o palco: camada nesse intervalo ficaria invisível')
    if plano.get('formato') == 'atlas':
        # Contrato global de clareza: limites vêm do canal e dos recursos
        # aprovados, nunca das cenas ou números do episódio do Panamá.
        direcao = canal(plano.get('canal', 'coringa')).get('direcao_visual') or {}
        max_editoriais = int(direcao.get('max_camadas_editoriais', 2))
        editoriais = [L for L in Ls if L['componente'] not in (
            'atlas.geoPin', 'dossie.evidenceHighlight', 'editorial.cta')]
        limites = sorted({x for L in editoriais for x in (L['t0'], L['t1'])})
        for a, b in zip(limites, limites[1:]):
            meio = (a + b) / 2
            ativos = [L['id'] for L in editoriais if L['t0'] <= meio < L['t1']]
            if len(ativos) > max_editoriais:
                v('erro', 'F-POLUICAO-VISUAL', f'{a:.2f}–{b:.2f}s',
                  f'{len(ativos)} informações editoriais simultâneas (máx. {max_editoriais}): {", ".join(ativos[:8])}')
                break
        catalogo = F.get('alvos_componentes') or {}
        ciclos = F.get('contratos_movimento') or {}
        for c in plano.get('clipes') or []:
            params = c.get('params') or {}
            ciclo = ciclos.get(c.get('componente'))
            if ciclo:
                tempos_c = params.get('tempos') or []
                indice = int(ciclo['marco_acao_final'])
                duracao_c = c['t1'] - c['t0']
                janela_min = float(ciclo['janela_final_min_s'])
                if len(tempos_c) <= indice or not isinstance(tempos_c[indice], (int, float)):
                    v('erro', 'F-ACAO-FINAL-SEM-MARCO', c['componente'],
                      f'marco final ausente; precisa demonstrar {ciclo["acao_final"]}')
                elif duracao_c - tempos_c[indice] < janela_min - .01:
                    v('erro', 'F-ACAO-FINAL-TRUNCADA', c['componente'],
                      f'mecanismo termina antes de demonstrar {ciclo["acao_final"]}: '
                      f'restam {duracao_c-tempos_c[indice]:.2f}s depois do marco final, '
                      f'mínimo {janela_min:.2f}s; replanejar a etapa ou reservar mais tempo, '
                      'sem acelerar artificialmente ou cortar a narração')
            marcacoes = params.get('focos') or params.get('destaques_fluxo') or []
            if not marcacoes:
                continue
            alvos = catalogo.get(c.get('componente'))
            dur_clipe = c['t1'] - c['t0']
            anterior = None
            for idx, marco in enumerate(marcacoes):
                onde = f"{c['componente']}/foco-{idx}"
                t, alvo, rotulo = marco.get('t'), marco.get('alvo'), str(marco.get('rotulo') or '')
                if alvos is None or alvo not in alvos:
                    v('erro', 'F-FOCO-SEM-ALVO', onde, f'alvo {alvo!r} não consta no catálogo do mecanismo')
                if not isinstance(t, (int, float)) or not (0 <= t <= dur_clipe + .01):
                    v('erro', 'F-FOCO-TEMPO', onde, 'foco deve ocorrer dentro do clipe, em tempo local da fala')
                    continue
                if not rotulo.strip() or len(rotulo.strip()) > direcao.get('max_caracteres_rotulo', 22):
                    v('erro', 'F-ROTULO-ILEGIVEL', onde, f'rótulo precisa ter 1–{direcao.get("max_caracteres_rotulo", 22)} caracteres')
                if anterior is not None and t - anterior < direcao.get('intervalo_min_foco_s', .8):
                    v('erro', 'F-FOCO-RAPIDO', onde, 'foco troca antes do intervalo mínimo de compreensão visual')
                anterior = t
    # composições: formato, palco, máximo de camadas simultâneas, reconstrução identificada
    for b in plano['beats']:
        comp = COMP.get(b.get('composicao') or '')
        if not comp:
            if plano.get('camera') == 'roi':
                v('erro', 'F-COMPOSICAO', b['id'], 'beat sem composição num plano de câmera automática')
            continue
        if comp['formato'] != plano['formato']:
            v('erro', 'F-COMPOSICAO', b['id'], f"{b['composicao']} é do formato {comp['formato']}")
        if comp['palco'] == 'mapa' and comp.get('quadro') and not b.get('roi'):
            v('erro', 'F-COMPOSICAO', b['id'], f"{b['composicao']} enquadra um território: falta roi (oeste, sul, leste, norte)")
        Lb = [L for L in Ls if L['beat'] == b['id'] and L['componente'] not in ('dossie.evidenceHighlight', 'atlas.geoPin')]
        for L in Lb:
            junto = sum(1 for M in Lb if M['t0'] < L['t1'] and L['t0'] < M['t1'])
            if junto > comp.get('max_camadas', 9):
                v('erro', 'F-COMPOSICAO', f"{b['id']}/{L['id']}", f"{junto} camadas ao mesmo tempo (máx. {comp['max_camadas']} em {b['composicao']}): vira slide")
                break
    for L in Ls:
        q = L.get('p') or {}
        if q.get('estilo') in ('calendario', 'ficha', 'regua') and not str(q.get('reconstrucao') or '').strip():
            v('erro', 'F-RECONSTRUCAO', f"{L['beat']}/{L['id']}", f"{q['estilo']} é reconstrução editorial: precisa do rótulo 'reconstrucao' visível (nunca passa por arquivo histórico)")
    # território: a câmera enquadra o roi no quadro e NENHUMA camada do beat o cobre (início e fim do beat, com a deriva)
    if plano.get('camera') == 'roi':
        ks = plano.get('palco') or []
        tempos_b = {}
        for k, b in zip([k for k in ks], [b for b in plano['beats'] if COMP.get(b.get('composicao') or '')]):
            tempos_b[b['id']] = k['t']
        fins = {}
        ids = list(tempos_b)
        for i, bid in enumerate(ids):
            fins[bid] = tempos_b[ids[i + 1]] if i + 1 < len(ids) else dur
        rasters = [raster_info(r['nome']) for r in plano.get('rasters') or []]
        for b in plano['beats']:
            comp = COMP.get(b.get('composicao') or '')
            if not comp or comp['palco'] != 'mapa' or not b.get('roi') or not comp.get('quadro'):
                continue
            t0 = tempos_b[b['id']] + next((k.get('dur_camera', 0) for k in ks if k['t'] == tempos_b[b['id']]), 0)
            qx, qy, qw, qh = comp['quadro']
            recua = next((k.get('movimento') for k in ks if k['t'] == tempos_b[b['id']]), None) == 'recua'
            # camada que ENTRA com a câmera ainda a caminho: o território em movimento não pode passar por baixo dela
            # (validação nos quadros, reuso China × EUA: cartão entrando 0,15 s depois do início do voo da câmera)
            for L in Ls:
                if L['beat'] == b['id'] and not L.get('dinamica') and L['t0'] + .35 < t0 and not recua:
                    tl = L['t0'] + .35
                    if _cruza(L['caixa'], roi_tela(camera_em(ks, tl), b['roi'])):
                        v('erro', 'F-COBRE-TERRITORIO', f"{b['id']}/{L['id']}", f"entra em {L['t0']:.1f}s com a câmera ainda em voo e cobre o território (espere a câmera)")
            # recuo: começa por dentro do território e TERMINA nele inteiro — confere o fim
            for t in ((fins[b['id']] - .05,) if recua else (min(t0, fins[b['id']]), fins[b['id']] - .05)):
                cam = camera_em(ks, t)
                r = roi_tela(cam, b['roi'])
                if r['x'] < qx - 8 or r['y'] < qy - 8 or r['x'] + r['w'] > qx + qw + 8 or r['y'] + r['h'] > qy + qh + 8:
                    v('erro', 'F-COBRE-TERRITORIO', b['id'], f"território sai do quadro livre em {t:.1f}s ({r['x']:.0f},{r['y']:.0f},{r['w']:.0f}×{r['h']:.0f})")
                for L in Ls:
                    if L['beat'] == b['id'] and not L.get('dinamica') and L['t0'] <= t <= L['t1'] + SAI and _cruza(L['caixa'], r):
                        v('erro', 'F-COBRE-TERRITORIO', f"{b['id']}/{L['id']}", f"camada cobre o território explicado em {t:.1f}s")
                # mapa GEOGRÁFICO exige base cartográfica licenciada (relevo/satélite) que cubra o território e seja
                # nítida no zoom usado — SEMPRE (antes, sem rasters a checagem era pulada e saía mapa vetorial chapado)
                cob = [ri for ri in rasters if cobre(ri, b['roi'])]
                ativos = [(r, ri) for r, ri in zip(plano.get('rasters') or [], rasters)
                          if cobre(ri, b['roi']) and opacidade_raster(cam['zoom'], r.get('de'), r.get('ate')) > .02]
                # a base cobre a TELA inteira (não só o território): sem isso aparece a borda do recorte (reuso mundo, 17/11)
                tela = tela_lonlat(cam)
                if cob and not any(cobre(ri, tela) for ri in rasters) and (fins[b['id']] - .05 == t or recua):
                    v('erro', 'F-MAPA-BORDA-DA-BASE', b['id'], f"a tela mostra além da base cartográfica ({', '.join(f'{x:.0f}' for x in tela)})")
                if not cob:
                    v('erro', 'F-MAPA-SEM-BASE', b['id'], 'mapa geográfico sem base cartográfica licenciada cobrindo o território (contorno vetorial chapado não é mapa ATLAS)')
                elif not ativos:
                    v('erro', 'F-MAPA-BASE-INVISIVEL', b['id'], f"há rasters no plano, mas todos têm opacidade zero no zoom {cam['zoom']:.2f} (limites de/ate); a tela ficaria chapada")
                elif not any(ri['nitido_ate'] >= cam['zoom'] - 1e-6 for _, ri in ativos):
                    v('erro', 'F-MAPA-BAIXA-RESOLUCAO', b['id'], f"zoom {cam['zoom']:.2f} além da nitidez das bases VISÍVEIS (até {max(ri['nitido_ate'] for _, ri in ativos):.2f})")
    # A marca é parte da identidade e precisa sobreviver ao recorte 4:5 do feed, antes do render.
    # Regressao 44221167260: 40/40 frames tinham a marca em y=232, acima do recorte do Reels (y=285).
    if plano.get('formato') == 'atlas' and layout.CFG['faixa_inferior'].get('marca_atlas', True):
        my = layout.faixa_inferior().get('marca_y')
        zona_marca = zonas('atlas').get('marca')
        if my is not None:
            if zona_marca and not (zona_marca[1] <= my <= zona_marca[1] + zona_marca[3]):
                v('erro', 'F-MARCA-ZONA-DESALINHADA', 'identidade', f'marca_y={my} fora da zona declarada {zona_marca}')
            for nome, perfil in layout.perfis().items():
                rec = perfil.get('recorte_feed')
                if rec and (my < rec['topo'] + 3 or my + 36 > 1920 - rec['base'] - 3):
                    v('erro', 'F-MARCA-RECORTE-FEED', 'identidade',
                      f'marca y={my} cortada no feed {nome} (faixa {rec["topo"]}–{1920 - rec["base"]})')
    # zonas fixas da identidade (marca no topo, faixa de legenda): nenhuma caixa entra nelas (colisão de 17/11)
    ZN = zonas(plano['formato'])
    for L in Ls:
        for nome, (x, y, w, h) in ZN.items():
            if _cruza(L['caixa'], {'x': x, 'y': y, 'w': w, 'h': h}):
                v('erro', 'F-ZONA-IDENTIDADE', f"{L['beat']}/{L['id']}", f'caixa cruza a zona da {nome}')
    # colisão: caixas de camadas simultâneas
    for i, a in enumerate(Ls):
        for b in Ls[i + 1:]:
            # mesma cena: conta a saída (0,3 s); troca de beat: a saída de um sob a entrada do outro é o dissolve da transição
            folga = SAI if a['beat'] == b['beat'] else -.02
            junto = a['t0'] < b['t1'] + folga and b['t0'] < a['t1'] + folga
            ev_a, ev_b = a['componente'] == 'dossie.evidenceHighlight', b['componente'] == 'dossie.evidenceHighlight'
            alvo_a, alvo_b = (a.get('p') or {}).get('alvo'), (b.get('p') or {}).get('alvo')
            ok = (ev_a and alvo_a == b['id']) or (ev_b and alvo_b == a['id']) or (ev_a and ev_b and alvo_a == alvo_b)
            if junto and not ok and not (a.get('dinamica') or b.get('dinamica')) and _cruza(a['caixa'], b['caixa']):
                v('erro', 'F-COLISAO', f"{a['id']}×{b['id']}", f"{a['slot'] or 'caixa'} e {b['slot'] or 'caixa'} ao mesmo tempo ({max(a['t0'], b['t0']):.1f}s)")
            if junto and (a.get('p') or {}).get('asset') and (a.get('p') or {}).get('asset') == (b.get('p') or {}).get('asset'):
                v('erro', 'F-MIDIA-DUPLICADA', f"{a['id']}×{b['id']}", 'a mesma mídia duas vezes no mesmo plano (ERR-055)')
    # pinos geográficos: seguem a câmera; a cada 0,25 s conferem âncora no quadro, colisão e zonas
    if any(L.get('dinamica') for L in Ls) and plano.get('palco'):
        vistos = set()
        ks = plano['palco']
        for i in range(int(dur / .25) + 1):
            t = i * .25
            pins = pinos_em(plano, Ls, t)
            if not pins:
                continue
            k = ks[0]
            for kk in ks:
                if t >= kk['t']:
                    k = kk
            qd = (COMP.get(k.get('composicao') or '') or {}).get('quadro')
            ativos = [L for L in Ls if not L.get('dinamica') and L['t0'] <= t <= L['t1'] + SAI]
            for pid, bx in pins.items():
                ax, ay = bx['ancora']
                if qd and not (qd[0] - 40 <= ax <= qd[0] + qd[2] + 40 and qd[1] - 40 <= ay <= qd[1] + qd[3] + 40) and (pid, 'fora') not in vistos:
                    vistos.add((pid, 'fora'))
                    v('erro', 'F-PINO-FORA', pid, f'âncora fora do território enquadrado em {t:.2f}s ({ax:.0f},{ay:.0f})')
                # pino da referência: foto e rótulo são caixas separadas (mesmas tolerâncias de posicionar_pinos)
                Lp = next((M for M in Ls if M['id'] == pid), None)
                partes = partes_pino(Lp['p'], ax, ay) if Lp and (canal().get('pino') or {}).get('estilo') == 'referencia' and Lp['p'].get('tipo') == 'foto' else None
                for b_ in partes or [bx]:
                    xd = layout.limite_direito(b_['y'] + (8 if partes else 0), b_['y'] + b_['h'] - (8 if partes else 0))
                    if (b_['x'] < layout.uniao()['esquerda'] - 2 or b_['x'] + b_['w'] > xd + 2 or b_['y'] < layout.faixa_inferior()['conteudo_topo'] - 4
                            or b_['y'] + b_['h'] > layout.faixa_inferior()['conteudo_base'] + 2) and (pid, 'tela') not in vistos:
                        vistos.add((pid, 'tela'))
                        v('erro', 'F-PINO-FORA', pid, f'pino sai da área segura das plataformas em {t:.2f}s')
                for L in ativos:
                    if any(_cruza({'x': c_['x'] + 6, 'y': c_['y'] + 6, 'w': c_['w'] - 12, 'h': c_['h'] - 12} if partes else c_, L['caixa']) for c_ in (partes or [bx])) and (pid, L['id']) not in vistos:
                        vistos.add((pid, L['id']))
                        v('erro', 'F-COLISAO', f"{pid}×{L['id']}", f'pino sob/sobre camada em {t:.2f}s')
                for nome, (x, y, w, h) in ZN.items():
                    if _cruza(bx, {'x': x, 'y': y, 'w': w, 'h': h}) and (pid, nome) not in vistos:
                        vistos.add((pid, nome))
                        v('erro', 'F-ZONA-IDENTIDADE', pid, f'pino invade a {nome} em {t:.2f}s')
                for qid, by in pins.items():
                    if qid > pid and _cruza(bx, by) and (pid, qid) not in vistos:
                        vistos.add((pid, qid))
                        v('erro', 'F-COLISAO', f'{pid}×{qid}', f'pinos sobrepostos em {t:.2f}s')
    usos = {}
    for L in Ls:
        a = (L.get('p') or {}).get('asset')
        if a:
            usos[a] = usos.get(a, 0) + 1
    for a, n in usos.items():
        if n > REGRAS['asset_max_usos']:
            v('erro', 'F-MIDIA-REPETIDA', a, f'mídia usada {n}× (máx. {REGRAS["asset_max_usos"]})')
    distintos = {L['componente'] for L in Ls if L['componente'] != 'editorial.cta'} | {c['componente'] for c in plano.get('clipes') or []}
    if len(distintos) > F['max_componentes_distintos']:
        v('erro', 'F-EXCESSO-MODALIDADES', '-', f"{len(distintos)} componentes distintos (máx. {F['max_componentes_distintos']}): vitrine de ferramentas")
    # progressão informativa: furos (clipes) contam com os próprios eventos
    ev = [e for e in eventos(plano) if 0 <= e <= dur] + [dur]
    ev = sorted(set([0.0] + ev))
    for x, y in zip(ev, ev[1:]):
        if y - x > REGRAS['progressao_max_s']:
            v('erro', 'F-SEM-PROGRESSAO', f'{x:.1f}–{y:.1f}s', f'{y - x:.1f} s sem informação nova no conteúdo')
    # palco técnico (diagrama) só para explicar mecanismo/estrutura — mapa geográfico é o padrão do ATLAS
    for b in plano.get('beats') or []:
        comp = COMP.get(b.get('composicao') or '') or {}
        if comp.get('exige_funcao') and b.get('funcao') not in comp['exige_funcao']:
            v('erro', 'F-TECNICO-SEM-MECANISMO', b.get('id', '-'), f"{b.get('composicao')} só com funcao {comp['exige_funcao']} (diagrama não substitui mapa)")
    if plano.get('formato') == 'atlas':
        for c in plano.get('clipes') or []:
            if not (str(c.get('componente', '')).startswith('mecanismo.') or c.get('componente') == 'registro.video'):
                v('erro', 'F-TECNICO-SEM-MECANISMO', c.get('componente', '-'), 'clipe ATLAS só para mecanismo aprovado ou registro de vídeo real')
        # ATLAS V1 fica EXATAMENTE como era por padrão. A direção V2 pode optar
        # EXPLICITAMENTE por prova fotográfica ou vídeo documental verificado.
        # Nunca liberar um mecanismo ou mapa genérico como gancho "real".
        bs = plano.get('beats') or []
        primeiro = bs[0] if bs else {}
        modo = plano.get('abertura_tipo', 'mapa')
        clips = plano.get('clipes') or []
        comeco_ok = (primeiro.get('t') or 0) <= .05
        if modo == 'mapa':
            if (primeiro.get('composicao') != 'atlas.abertura' or not comeco_ok
                    or any(c['t0'] < 3.0 for c in clips)):
                v('erro', 'F-GANCHO-MAPA-PRIMEIRO', '0–3s',
                  'ATLAS V1: abrir com mapa hero e pergunta/prova forte, sem clipe de mecanismo nos primeiros 3 segundos')
        elif modo == 'prova_real':
            fotos = [L for L in Ls if L['componente'] == 'atlas.provaVisual' and L['beat'] == primeiro.get('id')
                     and L['t0'] <= .05 and L['t1'] >= 2.5
                     and (L.get('p') or {}).get('asset') and (L.get('p') or {}).get('meta')]
            filmes = [c for c in clips if c.get('componente') == 'registro.video'
                      and isinstance(c.get('t0'), (int, float)) and c['t0'] <= .05
                      and isinstance(c.get('t1'), (int, float)) and c['t1'] >= 2.5
                      and (c.get('params') or {}).get('asset')]
            validado = (comeco_ok and (
                (primeiro.get('composicao') == 'atlas.prova' and bool(fotos) and not filmes)
                or (primeiro.get('composicao') == 'atlas.abertura' and bool(filmes) and not fotos)))
            if not validado or any(c['t0'] < 3.0 and c.get('componente') != 'registro.video' for c in clips):
                v('erro', 'F-GANCHO-PROVA-REAL', '0–3s',
                  'abertura física exige foto principal por 2,5 s OU registro.video original cobrindo a abertura; mecanismo não é prova real')
            if imagens is not None and validado:
                # A triagem do storyboard não é prova de procedência. No preflight
                # o arquivo da abertura deve ter origem binária conferida.
                referencias = [((f.get('p') or {}).get('asset')) for f in fotos] if fotos else [
                    ((f.get('params') or {}).get('asset')) for f in filmes
                ]
                for ref in referencias:
                    registro = imagens.get(ref) or {}
                    natureza = 'foto' if fotos else 'video'
                    if (registro.get('tipo') != natureza or registro.get('origem_conferida') is not True
                            or not registro.get('credito') or not registro.get('licenca')
                            or not registro.get('sha256_origem')):
                        v('erro', 'F-GANCHO-ORIGEM', '0–3s',
                          'registro inicial exige mídia correta, hash de origem conferido, licença e crédito')
        else:
            v('erro', 'F-GANCHO-TIPO', '0–3s', 'abertura_tipo só aceita mapa (V1) ou prova_real (V2)')
        if plano.get('cta') is True and not any(L['componente'] == 'editorial.cta' for L in Ls):
            v('erro', 'F-CTA-FINAL-AUSENTE', 'fecho',
              'storyboard pediu CTA final, mas não reservou slot: corrigir antes do render')
    if plano.get('formato') == 'atlas':
        # Toda demonstração técnica precisa de contrato explícito. Sem esse
        # metadado o teste de continuidade passaria silenciosamente; esta
        # obrigação vale para QUALQUER mecanismo ATLAS, nunca para DOSSIÊ/NTC.
        tecnicos = [c for c in plano.get('clipes') or []
                    if str(c.get('componente', '')).startswith('mecanismo.')]
        contratos = [e for e in plano.get('explicacoes') or []
                     if e.get('tipo') == 'mecanismo']
        for c in tecnicos:
            if not any(e.get('recurso') == c['componente']
                       and isinstance(e.get('t0'), (float, int))
                       and isinstance(e.get('t1'), (float, int))
                       and c['t0'] - .05 <= e['t0'] < e['t1'] <= c['t1'] + .05
                       for e in contratos):
                v('erro', 'F-EXPLICACAO-SEM-CONTRATO', c['componente'],
                  'demonstração técnica sem contrato explicativo com tempo e recurso compatíveis')
        # A narração ainda explica o MESMO mecanismo: não trocar o desenho por
        # caixas enquanto a peça ou o fluxo continua sendo descrito.
        # O diretor declara o intervalo; a checagem é determinística e reutilizável.
        for e in plano.get('explicacoes') or []:
            if e.get('tipo') != 'mecanismo':
                continue
            a, b, recurso = e.get('t0'), e.get('t1'), e.get('recurso')
            onde = e.get('id', 'explicacao')
            if not isinstance(a, (int, float)) or not isinstance(b, (int, float)) or not (0 <= a < b <= dur):
                v('erro', 'F-EXPLICACAO-TEMPO', onde, 'intervalo do mecanismo deve estar dentro do vídeo')
                continue
            if not recurso or not any(c.get('componente') == recurso and c['t0'] <= a + .05
                                      and c['t1'] >= b - .05 for c in plano.get('clipes') or []):
                v('erro', 'F-MECANISMO-SEM-CONTINUIDADE', onde,
                  f'a narração explica {recurso or "mecanismo desconhecido"} em {a:.2f}–{b:.2f}s; '
                  'o mesmo mecanismo precisa permanecer demonstrável até o fim (não substituir por cards)')
    for x in plano.get('_estilo_no_episodio') or []:
        v('erro', 'F-ESTILO-NO-EPISODIO', x, 'identidade visual é do canal (tokens/presets), não do episódio')
    # gancho: nos primeiros segundos, algo VISUALMENTE relevante (não só mapa e legenda)
    g = REGRAS.get('gancho_s', 3.0)
    fortes = [c for c in plano.get('clipes') or [] if c['t0'] <= .5] + \
             [L for L in Ls if L['t0'] <= g * .5 and (L['componente'] in ('dossie.documentCard', 'editorial.titleOrPayoff', 'atlas.provaVisual')
                                                   or (L['componente'] == 'atlas.geoPin' and (L.get('p') or {}).get('papel') == 'protagonista'))]
    mudanca = [e for e in eventos(plano) if .2 < e < g]
    if plano.get('formato') == 'atlas' and (not fortes or not mudanca):
        v('erro', 'F-GANCHO', f'0–{g:.0f}s', 'sem prova visual forte no início (clipe, foto protagonista, documento ou pergunta) ou sem mudança antes de 3 s')
    # rota prometida exige geometria
    if any(not r.get('arco') for r in plano.get('rotas') or []) and not plano.get('geo'):
        v('erro', 'F-ROTA-SEM-GEOMETRIA', '-', 'rota sem arquivo de geometria')
    return out


def geom_documento(L: dict, im: dict) -> dict:
    """mesmas contas do DocumentCard (Primitivas.tsx): retângulos do cartão, da foto e do texto à direita do cabeçalho"""
    b, p = caixa(L), L.get('p') or {}
    cab, rod = (52 if p.get('cabecalho') else 0), 22 + len(p.get('meta') or []) * 36
    esc = min((b['w'] - 36) / im['w'], (b['h'] - cab - rod - 36) / im['h'])
    fw, fh = im['w'] * esc, im['h'] * esc
    x0, y0 = b['x'] + (b['w'] - fw - 36) / 2, b['y'] + (b['h'] - fh - cab - rod - 36) / 2
    dw = len(str(p.get('cabecalho_dir') or '')) * 22 * .62 + 8
    return {'cartao': {'x': x0, 'y': y0, 'w': fw + 36, 'h': fh + cab + rod + 36},
            'foto': {'x': x0 + 18, 'y': y0 + 18 + cab + (12 if cab else 0), 'w': fw, 'h': fh},
            'cabecalho_dir': {'x': x0 + 18 + fw - dw, 'y': y0 + 18 + 6, 'w': dw, 'h': cab - 12}}


def _mirar(Ls: list[dict], imagens: dict) -> None:
    por = {L['id']: L for L in Ls}
    for L in Ls:
        q = L.get('p') or {}
        if L['componente'] == 'dossie.evidenceHighlight' and (q.get('parte') or q.get('regiao')) and q.get('alvo') in por:
            alvo = por[q['alvo']]
            im = imagens.get((alvo.get('p') or {}).get('asset'))
            if im:
                g = geom_documento(alvo, im)
                if q.get('regiao'):              # região da PRÓPRIA imagem (frações 0–1): marca exatamente o trecho citado
                    f, (a0, b0, a1, b1) = g['foto'], q['regiao']
                    L['caixa'] = {'x': round(f['x'] + a0 * f['w'], 1), 'y': round(f['y'] + b0 * f['h'], 1),
                                  'w': round((a1 - a0) * f['w'], 1), 'h': round((b1 - b0) * f['h'], 1)}
                else:
                    L['caixa'] = {k: round(v, 1) for k, v in g[q['parte']].items()}


def props(plano: dict, tokens: dict, geo: dict | None, imagens: dict) -> dict:
    furos = [{'t0': c['t0'], 't1': c['t1']} for c in plano.get('clipes') or []]
    Ls = camadas(plano)
    _mirar(Ls, imagens)
    # fonte factual por cartão (componente independente dos créditos do mapa): fato → domínios das fontes
    fatos = {f['id']: f for f in (plano.get('narracao') or {}).get('fatos', []) if isinstance(f, dict) and f.get('id')}
    for L in Ls:
        q = L.get('p') or {}
        if q.get('fato') in fatos and not q.get('fonte'):
            dom = [re.sub(r'^www\.', '', re.sub(r'^https?://([^/]+).*$', r'\1', u)) for u in fatos[q['fato']].get('fontes', [])]
            q['fonte'] = ' · '.join(dict.fromkeys(d.upper() for d in dom))
    rasters = []
    for r in plano.get('rasters') or []:
        m = raster_info(r['nome'])
        rasters.append({'dataset': m.get('dataset'), 'nome': r['nome'], 'src': f"_formato/raster/{m.get('arquivo') or r['nome'] + '.jpg'}", 'cantos': m['cantos'], 'de': r.get('de'), 'ate': r.get('ate'),
                        'atribuicao': m['atribuicao'], 'tipo': m.get('tipo', 'fisico'), 'ajuste': m.get('ajuste') or {}})
    return {'duracao': plano['duracao'], 'formato': plano['formato'], 'tokens': tokens, 'geo': geo, 'palco': plano['palco'], 'rasters': rasters,
            'composicoes': {k: {'quadro': v.get('quadro'), 'veu': v.get('veu')} for k, v in COMP.items()},
            'creditos': _creditos(plano), 'tecnico': plano.get('tecnico') or {}, 'seguro': seguro(plano.get('formato')),
            'destaques': plano.get('destaques') or [], 'rotas': plano.get('rotas') or [], 'rotulos': plano.get('rotulos') or [],
            'camadas': [{'id': L['id'], 'componente': L['componente'], 't0': L['t0'], 't1': L['t1'], 'caixa': L['caixa'], 'p': L.get('p') or {}}
                        for L in Ls], 'imagens': imagens, 'furos': furos}
