"""Medidor geométrico do Ninguém Te Contou (Fase 1 da auditoria, 11/11/2026) — SÓ DIAGNÓSTICO.

Abre o motor vetorial de verdade (canais/ntc/vetor/fabula.html) no Chrome do Playwright, chama seek(t) em vários
instantes de cada cena e mede o que o Chrome DESENHOU:
  - caixa na tela de cada elemento (Val, cabeça, mão, objetos, figurantes, peças do cenário, legenda, balão, painel);
  - quem está na frente de quem, ponto a ponto, usando document.elementsFromPoint (que testa a forma pintada, não a
    caixa) numa grade sobre a tela.
Não usa IA, não gera vídeo, não manda nada ao Telegram e não muda nenhum arquivo do motor (só lê e chama seek).

Uso:  python -m tests.ntc_geometria [saida.md]      → mede os casos fixos e escreve o relatório.
"""
import copy, json, math, sys, tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CASOS_JSON = RAIZ / 'tests' / 'ntc_casos_geometria.json'
BARATAS = RAIZ / 'tests' / 'ntc_roteiro_baratas.json'

PASSO_MOV = 1 / 15          # amostragem em cena com movimento (s)
PASSO_PARADO = 0.5          # amostragem extra em cena sem movimento (além dos 4 momentos e dos cortes de câmera)
GRADE = 18                  # px entre pontos da grade de elementsFromPoint
MOVEM = {'corre', 'foge', 'cai', 'pula', 'some'}
ASTROS_E_NUVEM = {'nuvem', 'sol', 'lua', 'terra'}

# ───────────────────────── parte que roda no Chrome ─────────────────────────
JS = r"""
window.__MED = (() => {
 const W = 1080, H = 1920;
 const camDe = S => { const m = /translate\(([-\d.e]+) ([-\d.e]+)\) scale\(([-\d.e]+)\)/.exec(S.cam.getAttribute('transform') || '');
   return m ? { x: +m[1], y: +m[2], z: +m[3] } : { x: 0, y: 0, z: 1 } };
 const op = el => { for (let e = el; e && e !== document.body; e = e.parentElement) {
     const a = e.getAttribute && e.getAttribute('opacity'); if (a !== null && a !== undefined && +a <= 0.02) return 0;
     const cs = getComputedStyle(e); if (+cs.opacity <= 0.02 || cs.display === 'none' || cs.visibility === 'hidden') return 0 }
   return 1 };
 // peças do cenário: filhos de .cam antes de .atras (grupo sem transform com vários filhos é aberto 1 nível)
 const pecasCenario = (S, cam) => {
   const out = []; const kids = [...S.cam.children]; const fim = kids.findIndex(e => e.classList.contains('atras'));
   const lista = [];
   kids.slice(0, fim < 0 ? kids.length : fim).forEach(e => {
     if (e.tagName === 'g' && !e.getAttribute('transform') && e.children.length > 1 && !e.getAttribute('class')) [...e.children].forEach(f => lista.push(f));
     else lista.push(e) });
   lista.forEach((e, k) => {
     const r = e.getBoundingClientRect(); if (!r.width || !r.height) return;
     const wx0 = (r.left - cam.x) / cam.z, wx1 = (r.right - cam.x) / cam.z, wy0 = (r.top - cam.y) / cam.z, wy1 = (r.bottom - cam.y) / cam.z;
     const html = e.outerHTML.slice(0, 400), fill = e.getAttribute('fill') || '';
     const circ = [...(e.tagName === 'circle' ? [e] : e.querySelectorAll('circle'))].map(c => +c.getAttribute('r') || 0);
     let tipo;
     if (/gCeu/.test(fill)) tipo = 'ceu';
     else if (/gSol|gGlobo|#FFF6D8|#FFF3C4/.test(fill + (e.tagName === 'g' ? html : '')) && Math.max(0, ...circ) >= 60 && wy1 - wy0 < 700) {
       tipo = 'astro'; var qual = /gGlobo/.test(fill + html) ? 'terra' : /gSol|#FFF3C4/.test(fill) ? 'sol' : 'lua' }
     else if ((e.tagName === 'circle' && (+e.getAttribute('r') || 0) < 8) || (e.tagName === 'g' && e.getAttribute('opacity') === '.9' && e.children.length === 1 && /fill="#fff"/.test(html))) tipo = 'decor_ceu';
     else if (e.getAttribute('fill') === 'none' || (e.tagName === 'path' && !e.getAttribute('fill'))) tipo = 'linha';   // fio, risco, rachadura
     else if (wx1 - wx0 >= 1000 && wy0 <= 5 && wy1 - wy0 >= 1000) tipo = 'pano';                  // pano de fundo liso (céu da floresta, parede)
     else if (wx1 - wx0 >= 1000) tipo = 'fundo';
     else tipo = 'estrutura';
     out.push({ el: e, id: 'cen' + k, tipo, qual: tipo === 'astro' ? qual : undefined, w: [wx0, wy0, wx1, wy1] }) });
   return out };
 const medir = (i, t, grade) => {
   seek(t);
   // só a cena medida participa do teste de clique (as outras já estão com opacidade 0; isso não muda a imagem)
   cenas.forEach((x, j) => x.el.style.pointerEvents = j === i ? '' : 'none');
   const S = cenas[i], cam = camDe(S), root = S.el, atores = [];
   const add = (id, el, info) => { if (el) atores.push({ id, el, ...info }) };
   if (S.V) { add('val', root.querySelector('.val'), { k: 'val' }); add('cabeca', root.querySelector('.cabeca'), { k: 'cabeca' });
     add('mao', root.querySelector('.mD'), { k: 'mao' }); add('olhos', root.querySelector('.olhos'), { k: 'olhos' }) }
   S.objs.forEach(({ p, g }, k) => add('obj' + k, g, { k: 'obj', t: p.t, anim: p.anim, ceu: !!p.ceu, atras: !!p.atras, voa: !!p.voa, de: p.de || 0, vel: p.vel || 0 }));
   S.povo.forEach((q, k) => add('povo' + k, q.p.g, { k: 'povo' }));
   ['cap', 'balao', 'hud', 'titulo', 'fim'].forEach(n => add(n, document.getElementById(n), { k: 'txt' }));
   const cen = pecasCenario(S, cam);
   // quem é dono de cada elemento pintado (o mais específico ganha: cabeça/mão/olhos antes de val)
   const dono = new Map(); const vis = {};
   cen.forEach(c => dono.set(c.el, c.id));
   atores.forEach(a => { vis[a.id] = op(a.el); if (!['cabeca', 'mao', 'olhos'].includes(a.id)) dono.set(a.el, a.id) });
   const sub = new Map(); ['cabeca', 'mao', 'olhos'].forEach(n => { const a = atores.find(x => x.id === n); if (a) sub.set(a.el, n) });
   const quem = el => { let s = null; for (let e = el; e && e !== document.body; e = e.parentNode) {
       if (!s && sub.has(e)) s = sub.get(e); if (dono.has(e)) { const d = dono.get(e); return d === 'val' && s ? [d, s] : [d] } } return null };
   // grade: lista de donos (de cima para baixo) em cada ponto
   const pontos = [], usados = new Set();
   const caixas = atores.filter(a => vis[a.id] && !['mao', 'olhos', 'fim'].includes(a.id)).map(a => a.el.getBoundingClientRect());
   const grid = [];
   caixas.forEach(r => { for (let y = Math.max(0, Math.floor(r.top / grade)); y * grade < Math.min(H, r.bottom); y++)
     for (let x = Math.max(0, Math.floor(r.left / grade)); x * grade < Math.min(W, r.right); x++) { const k = y * 1000 + x; if (!usados.has(k)) { usados.add(k); grid.push([x * grade + grade / 2, y * grade + grade / 2]) } } });
   for (const [x, y] of grid) {
     const ids = []; for (const el of document.elementsFromPoint(x, y)) { if (!root.contains(el) && !document.getElementById('st').contains(el)) continue;
       if (root !== el && !root.contains(el) && el.closest('.cena')) continue;          // outra cena (invisível)
       const q = quem(el); if (!q) continue; q.forEach(d => { if (!ids.includes(d) && (d.startsWith('cen') || vis[d])) ids.push(d) }) }
     if (ids.length) pontos.push([x, y, ids]) }
   const pl = [...S.pl].reverse().find(p => t >= p.t0) || S.pl[0];
   const res = { i, t, d: t - S.c.a, cam, plano: pl.tipo, fimOn: !!(S.c.fim && t - S.c.a > S.c.fim.de - 0.4),
     anda: !!(S.V && S.V.anda && t - S.c.a < 0.8), atores: {}, cenario: cen.map(c => ({ id: c.id, tipo: c.tipo, qual: c.qual, w: c.w })), pontos };
   const caixaVis = el => { if (el.tagName === 'DIV') return el.getBoundingClientRect(); let r = null;
     const anda = (e, ok) => { if (!ok) return; const o = e.getAttribute('opacity'), cs = getComputedStyle(e);
       if ((o !== null && +o <= 0.02) || +cs.opacity <= 0.02 || cs.display === 'none') return;
       if (e !== el && o !== null && +o < 0.3 && !e.children.length) return;          // halo/brilho quase transparente não define o contorno
       if (!e.children.length || ['path', 'rect', 'circle', 'ellipse', 'line', 'polygon', 'polyline', 'text'].includes(e.tagName)) { const q = e.getBoundingClientRect();
         if (q.width || q.height) r = r ? { left: Math.min(r.left, q.left), top: Math.min(r.top, q.top), right: Math.max(r.right, q.right), bottom: Math.max(r.bottom, q.bottom) } : { left: q.left, top: q.top, right: q.right, bottom: q.bottom } }
       else [...e.children].forEach(f => anda(f, true)) };
     anda(el, true); return r || el.getBoundingClientRect() };
   const cap = document.getElementById('cap'); const rg = document.createRange(); rg.selectNodeContents(cap);
   res.linhas_cap = [...rg.getClientRects()].map(q => [q.left, q.top, q.right, q.bottom]);
   atores.forEach(a => { const r = caixaVis(a.el); const { el, ...info } = a;
     res.atores[a.id] = { ...info, vis: vis[a.id], s: [r.left, r.top, r.right, r.bottom],
       w: [(r.left - cam.x) / cam.z, (r.top - cam.y) / cam.z, (r.right - cam.x) / cam.z, (r.bottom - cam.y) / cam.z] } });
   return res };
 const info = () => cenas.map((S, i) => ({ i, a: S.c.a, b: S.c.b, cen: S.c.cen, val: !!S.V, anda: !!(S.V && S.V.anda), povo: S.povo.length,
   planos: S.pl.map(p => ({ t0: p.t0, tipo: p.tipo })), props: (S.c.props || []).map(p => ({ t: p.t, anim: p.anim, de: p.de || 0, ceu: !!p.ceu, voa: !!p.voa, atras: !!p.atras })) }));
 return { medir, info };
})();
"""


# ───────────────────────── montar a página com o próprio motor ─────────────────────────
def _tempos(r: dict) -> list:
    """Duração estimada de cada cena pela narração (~3 palavras/s, como a voz do NTC a 1,12x)."""
    out, t = [], 0.0
    for c in r['cenas']:
        dur = max(3.0, len(str(c.get('narracao', '')).split()) / 3.0)
        out.append((round(t, 3), round(t + dur, 3))); t += dur
    return out


def _legendas(r: dict, tempos: list) -> list:
    """Legenda como a do vídeo: blocos de 3 palavras ao longo da cena."""
    caps = []
    for c, (a, b) in zip(r['cenas'], tempos):
        pal = [w.upper() for w in str(c.get('narracao', '')).split()]
        blocos = [pal[k:k + 3] for k in range(0, len(pal), 3)] or [[]]
        dt = (b - a) / len(blocos)
        for k, bl in enumerate(blocos):
            if bl:
                caps.append({'start': round(a + k * dt, 3), 'end': round(a + (k + 1) * dt - 0.02, 3), 'words': [{'w': w, 'hl': False} for w in bl]})
    return caps


def dados_do_roteiro(r: dict) -> dict:
    from src import fabula
    r = fabula.validar(copy.deepcopy(r))
    tempos = _tempos(r)
    return fabula.dados_template(r, tempos, _legendas(r, tempos), tempos[-1][1] + 2.5)


def instantes(cena: dict, passo_mov=PASSO_MOV, passo_parado=PASSO_PARADO) -> list:
    """4 momentos (início, desenvolvimento, ação principal, final) + cada corte de câmera + amostragem densa se houver movimento."""
    a, b = cena['a'], cena['b']
    dur = b - a
    acao = max([p['de'] for p in cena['props']] + [0]) + 0.5
    ts = {a + 0.05, a + dur * 0.4, a + min(dur - 0.1, max(0.6, acao)), b - 0.05}
    ts |= {p['t0'] + 0.03 for p in cena['planos']} | {p['t0'] + 0.3 for p in cena['planos']}
    mov = cena['anda'] or cena['povo'] or any(p['anim'] in MOVEM or p['voa'] for p in cena['props'])
    passo = passo_mov if mov else passo_parado
    ts |= {a + k * passo for k in range(int(dur / passo) + 1)}
    return sorted(x for x in {round(t, 3) for t in ts} if a <= x < b - 0.005)


def medir_dados(dados: dict, passo_mov=PASSO_MOV, passo_parado=PASSO_PARADO, grade=GRADE, so_cenas=None) -> dict:
    from playwright.sync_api import sync_playwright
    from src import fabula
    with tempfile.TemporaryDirectory() as tmp:
        pag = fabula._pagina(dados, Path(tmp) / 'medidor')
        with sync_playwright() as p:
            nav = p.chromium.launch(args=['--allow-file-access-from-files'])
            pg = nav.new_page(viewport={'width': 1080, 'height': 1920})
            erros = []
            pg.on('pageerror', lambda e: erros.append(str(e)))
            pg.goto(pag.as_uri()); pg.wait_for_function('window.READY===true', timeout=60000)
            pg.evaluate(JS)
            info = pg.evaluate('__MED.info()')
            amostras = []
            for c in info:
                if so_cenas is not None and c['i'] not in so_cenas:
                    continue
                for t in instantes(c, passo_mov, passo_parado):
                    amostras.append(pg.evaluate(f'__MED.medir({c["i"]}, {t}, {grade})'))
            nav.close()
    return {'info': info, 'amostras': amostras, 'erros_js': erros, 'grade': grade}


# ───────────────────────── análise (regras) ─────────────────────────
def _area(r):
    return max(0, r[2] - r[0]) * max(0, r[3] - r[1])


def _inter(a, b):
    return [max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])]


def _fora(r):
    """Fração da caixa (tela) fora do quadro 1080×1920."""
    tot = _area(r)
    return 0 if not tot else 1 - _area(_inter(r, [0, 0, 1080, 1920])) / tot


def _r(v):
    return [round(x) for x in v]


def analisar(med: dict, nome_caso: str) -> list:
    info = {c['i']: c for c in med['info']}
    achados = []

    def achou(a, ator, tipo, nivel, regiao, detalhe, valor):
        c = info[a['i']]
        achados.append({'caso': nome_caso, 'cena': a['i'], 'cenario': c['cen'], 't': round(a['t'], 2), 'd': round(a['d'], 2),
                        'plano': a['plano'], 'ator': ator, 'tipo': tipo, 'nivel': nivel, 'regiao': regiao, 'detalhe': detalhe, 'valor': valor})

    def nome(a, id_):
        x = a['atores'].get(id_, {})
        if x.get('k') == 'obj':
            return f"{x['t']} ({id_}, {x['anim']})"
        return id_

    for a in med['amostras']:
        A = a['atores']
        cen = {c['id']: c for c in a['cenario']}
        visiveis = {k for k, v in A.items() if v['vis']}
        # pontos pintados por ator, quem está logo atrás, e pares
        pint, atras_de, cobre = {}, {}, {}
        for x, y, ids in a['pontos']:
            for j, idd in enumerate(ids):
                pint[idd] = pint.get(idd, 0) + 1
                if not idd.startswith('cen'):
                    baixo = next((q for q in ids[j + 1:] if q.startswith('cen')), None)
                    if baixo:
                        atras_de.setdefault(idd, {}).setdefault(cen[baixo]['tipo'], {}).setdefault(baixo, 0)
                        atras_de[idd][cen[baixo]['tipo']][baixo] += 1
                    for q in ids[j + 1:]:
                        if not q.startswith('cen'):
                            cobre[(idd, q)] = cobre.get((idd, q), 0) + 1      # idd está NA FRENTE de q nesse ponto
        geral = a['cam']['z'] <= 1.12 and a['plano'] == 'geral'
        chao_top = min([c['w'][1] for c in a['cenario'] if c['tipo'] == 'fundo' and c['w'][3] >= 1900 and c['w'][1] > 1000] or [1340])
        astros = [c for c in a['cenario'] if c['tipo'] == 'astro']

        for idd in visiveis:
            x = A[idd]
            n = pint.get(idd, 0)
            if x['k'] == 'obj':
                dd = a['d'] - x['de']
                if dd < 0:
                    continue
                if x['ceu'] and n:
                    tipos = atras_de.get(idd, {})
                    # nuvem/astro na frente de casa ou árvore é sempre erro (estão longe). Bicho voando, gota ou nota caindo
                    # na frente de casa é profundidade normal → só entram na regra do horizonte.
                    regras = [('fundo', 'objeto do céu abaixo do horizonte (sobre morro, chão ou calçada)')]
                    if x['t'] in ASTROS_E_NUVEM:
                        regras.insert(0, ('estrutura', 'objeto do céu desenhado na frente de construção/árvore'))
                    for tp, rot in regras:
                        q = sum(tipos.get(tp, {}).values())
                        if q / n >= 0.10 or q / n > 0.02:
                            maior = max(tipos[tp], key=tipos[tp].get)
                            achou(a, nome(a, idd), 'ceu_sobre_estrutura' if tp == 'estrutura' else 'ceu_abaixo_horizonte',
                                  'comprovado' if q / n >= 0.10 else 'possível', f"{maior} ({cen[maior]['tipo']}) x{_r(cen[maior]['w'][::2])} y{_r(cen[maior]['w'][1::2])}",
                                  f"{rot}; caixa no mundo {_r(x['w'])}", round(q / n, 2))
                if x['t'] in ('sol', 'lua', 'terra'):
                    for s in astros:
                        encosta = _area(_inter(x['w'], s['w'])) > 0
                        igual = s.get('qual') == x['t']
                        achou(a, nome(a, idd), 'astro_duplicado', 'comprovado' if igual or encosta else 'possível',
                              f"{s['id']} ({s.get('qual')} do cenário) {_r(s['w'])}",
                              f"o cenário já desenha {s.get('qual')}; objeto {x['t']} em {_r(x['w'])}" + (' e encosta nele' if encosta else ''), 1)
                # flutuando / fora da bancada
                girando = x['anim'] == 'some' and dd > 1.3           # 'some' = gira e encolhe de propósito
                if not x['ceu'] and not x['voa'] and not (x['anim'] == 'cai' and dd < 0.5) and x['anim'] != 'pula' and not girando:
                    fundo_y = x['w'][3]
                    if x['atras']:
                        c = info[a['i']]['cen']
                        from src import fabula
                        banc = fabula.BANCADA.get(c)
                        if banc and (abs(fundo_y - banc[0]) > 40 or (x['w'][0] + x['w'][2]) / 2 < banc[1] - 20 or (x['w'][0] + x['w'][2]) / 2 > banc[2] + 20) and x['anim'] not in ('corre', 'foge'):
                            achou(a, nome(a, idd), 'fora_da_bancada', 'comprovado', f'bancada y={banc[0]} x={banc[1]}–{banc[2]}', f'base do objeto em y={round(fundo_y)}, centro x={round((x["w"][0] + x["w"][2]) / 2)}', round(abs(fundo_y - banc[0])))
                    elif fundo_y < chao_top - 25:
                        from src import fabula
                        if x['t'] not in fabula.VOAM:
                            achou(a, nome(a, idd), 'flutuando', 'comprovado', f'chão começa em y={round(chao_top)}', f'base do objeto em y={round(fundo_y)} (objeto que não voa)', round(chao_top - fundo_y))
                        elif x['anim'] == 'cai' and dd > 0.7:
                            achou(a, nome(a, idd), 'cai_e_para_no_ar', 'comprovado', f'chão começa em y={round(chao_top)}', f'terminou a queda em y={round(fundo_y)}, no meio do ar', round(chao_top - fundo_y))
                        elif x['anim'] != 'cai':
                            achou(a, nome(a, idd), 'parado_no_ar', 'possível', f'chão começa em y={round(chao_top)}', f'{x["t"]} parado no ar em y={round(fundo_y)} (o motor permite; ver se faz sentido)', round(chao_top - fundo_y))
                # fora da tela (só no plano geral; quem entra/sai correndo e quem está caindo é intencional)
                if geral and x['anim'] not in ('corre', 'foge') and not (x['anim'] == 'cai' and dd < 0.5) and not girando:
                    f = _fora(x['s'])
                    if f > 0.03:
                        so_baixo = x['s'][0] >= 0 and x['s'][2] <= 1080 and x['s'][1] >= 0      # cortado só embaixo: comum em coisa no chão perto da câmera
                        nivel = 'comprovado' if f >= (0.40 if so_baixo else 0.15) else 'possível'
                        if x['voa'] or x['t'] == 'fogo':
                            nivel = 'possível'                        # bicho voando ou fogo cortado na borda: enquadramento comum
                        achou(a, nome(a, idd), 'fora_da_tela', nivel, 'borda de baixo' if so_baixo else 'borda do quadro', f'caixa na tela {_r(x["s"])}', round(f, 2))
            elif idd == 'val' and geral and not a['anda'] and _fora(x['s']) > 0.03:
                f = _fora(x['s'])
                achou(a, 'Val', 'fora_da_tela', 'comprovado' if f >= 0.15 else 'possível', 'borda do quadro', f'caixa na tela {_r(x["s"])}', round(f, 2))
            elif x['k'] == 'txt' and _fora(x['s']) > 0.01:
                achou(a, idd, 'texto_fora_da_tela', 'comprovado', 'borda do quadro', f'caixa {_r(x["s"])}', round(_fora(x['s']), 2))

        # o que cobre a Val (só quem está NA FRENTE dela)
        nv, nc = pint.get('val', 0), pint.get('cabeca', 0)
        for (fr, tr), q in cobre.items():
            if fr not in visiveis or A[fr]['k'] != 'obj' or a['d'] < A[fr]['de']:
                continue
            o = A[fr]
            caindo = o['anim'] == 'cai' and a['d'] - o['de'] < 0.6     # passa na frente durante a queda
            if tr == 'val' and nv and not a['anda']:
                f = q / nv
                if ((o['t'] == 'fogo' and f >= 0.02) or f >= 0.15) and not caindo:
                    achou(a, nome(a, fr), 'cobre_val', 'comprovado', 'corpo da Val', f'{round(100 * f)}% do corpo da Val atrás do objeto', round(f, 2))
                elif f >= 0.05:
                    achou(a, nome(a, fr), 'cobre_val', 'possível', 'corpo da Val', f'{round(100 * f)}% do corpo (pode ser profundidade)', round(f, 2))
            if tr == 'cabeca' and nc and q / nc >= 0.05:
                achou(a, nome(a, fr), 'cobre_rosto', 'comprovado' if q / nc >= 0.15 and not caindo else 'possível', 'cabeça da Val', f'{round(100 * q / nc)}% da cabeça atrás do objeto', round(q / nc, 2))
            if A.get(tr, {}).get('k') == 'povo' and o['voa'] and pint.get(fr):
                f = q / pint[fr]
                if f >= 0.10:
                    achou(a, nome(a, fr), 'voador_na_frente_de_pessoa', 'possível', tr, f'{round(100 * f)}% do bicho voando sobre o figurante', round(f, 2))
            if A.get(tr, {}).get('k') == 'obj' and tr in visiveis and a['d'] >= A[tr]['de']:
                m = min(pint.get(fr, 0), pint.get(tr, 0))
                if m and q / m >= 0.35:
                    achou(a, f"{nome(a, fr)} × {nome(a, tr)}", 'objetos_amontoados', 'possível', nome(a, tr), f'{round(100 * q / m)}% do menor coberto', round(q / m, 2))
        # textos: legenda × balão × painel × título; balão/legenda em cima do rosto
        txt = {k: A[k] for k in ('cap', 'balao', 'hud', 'titulo', 'fim') if k in visiveis}
        lin = a.get('linhas_cap') or []
        if 'cap' in txt and lin:                                 # a caixa da legenda vai de margem a margem; o que conta são as linhas de texto
            txt['cap'] = {**txt['cap'], 's': [min(q[0] for q in lin), min(q[1] for q in lin), max(q[2] for q in lin), max(q[3] for q in lin)]}
        ks = list(txt)
        for m in range(len(ks)):
            for n_ in range(m + 1, len(ks)):
                ar = _area(_inter(txt[ks[m]]['s'], txt[ks[n_]]['s']))
                if ar > 0:
                    achou(a, f'{ks[m]} × {ks[n_]}', 'texto_sobre_texto', 'comprovado', ks[n_], f'{round(ar)} px² de sobreposição', round(ar))
        for k in ('balao', 'cap'):
            if k in txt and nc:
                q = cobre.get((k, 'cabeca'), 0) if k == 'balao' else sum(1 for x_, y_, ids in a['pontos'] if 'cabeca' in ids and any(r[0] <= x_ <= r[2] and r[1] <= y_ <= r[3] for r in lin))
                if q / nc >= 0.05:
                    achou(a, k, 'texto_cobre_rosto', 'comprovado' if q / nc >= 0.2 else 'possível', 'cabeça da Val', f'{round(100 * q / nc)}% da cabeça coberta', round(q / nc, 2))
        # foco do close cortado / close em coisa invisível
        if a['plano'] in ('rosto', 'mao', 'olho', 'objeto') and not a['fimOn']:
            alvo = {'rosto': 'cabeca', 'mao': 'mao', 'olho': 'olhos'}.get(a['plano'])
            if a['plano'] == 'objeto':
                c = info[a['i']]
                k = next((j for j, p in enumerate(c['props']) if p['anim'] not in ('corre', 'foge', 'some')), None)
                alvo = f'obj{k}' if k is not None else None
            if alvo and alvo in A:
                x = A[alvo]
                if not x['vis'] or (x.get('k') == 'obj' and a['d'] < x['de']):
                    achou(a, nome(a, alvo), 'close_no_vazio', 'comprovado', f"plano '{a['plano']}'", 'a câmera fecha num elemento que não está visível', 1)
                elif _fora(x['s']) >= 0.10:
                    achou(a, nome(a, alvo), 'foco_cortado', 'comprovado' if _fora(x['s']) >= 0.25 else 'possível', f"plano '{a['plano']}'", f'caixa na tela {_r(x["s"])}', round(_fora(x['s']), 2))

    # ── temporais: saltos e sumiços (coordenadas do mundo, então corte de câmera não conta)
    por = {}
    for a in med['amostras']:
        for idd, x in a['atores'].items():
            if x['k'] in ('obj', 'val'):
                por.setdefault((a['i'], idd), []).append((a, x))
    for (i, idd), seq in por.items():
        for (a0, x0), (a1, x1) in zip(seq, seq[1:]):
            dt = a1['t'] - a0['t']
            if dt <= 0 or dt > 0.11:
                continue
            if x0['vis'] and not x1['vis'] and x0.get('anim') not in ('some', 'corre', 'foge') and x0['k'] == 'obj':
                achou(a1, nome(a1, idd), 'sumiu_sem_motivo', 'comprovado', 'tempo', f'visível em t={a0["t"]:.2f}, invisível em t={a1["t"]:.2f}', 1)
            if not (x0['vis'] and x1['vis']) or _fora(x0['s']) > 0.5 or _fora(x1['s']) > 0.5:
                continue
            if x0['k'] == 'obj' and a0['d'] - x0['de'] < 0.35:
                continue                                         # ainda aparecendo (pulo de escala)
            if x0['k'] == 'val':                                 # a caixa da Val muda com os braços: segue a cabeça (x) e os pés (y)
                c0, c1 = a0['atores'].get('cabeca'), a1['atores'].get('cabeca')
                bx0, bx1 = (c0['w'][0] + c0['w'][2]) / 2, (c1['w'][0] + c1['w'][2]) / 2
            else:
                bx0, bx1 = (x0['w'][0] + x0['w'][2]) / 2, (x1['w'][0] + x1['w'][2]) / 2
            v = math.hypot(bx1 - bx0, x1['w'][3] - x0['w'][3]) / dt
            if x0['k'] == 'val':
                lim = 2500 if a0['anda'] else 700
            elif x0['anim'] in ('corre', 'foge'):
                lim = 1.6 * abs(x0['vel']) + 300
            elif x0['anim'] == 'cai':
                lim = 4200                                        # queda de 900 px em 0,5 s chega a 3600 px/s no fim
            elif x0['anim'] == 'some':
                lim = 1800
            else:
                lim = 600
            if v > lim:
                achou(a1, nome(a1, idd), 'salto', 'comprovado' if v > 2 * lim else 'possível', 'tempo',
                      f'andou {round(v * dt)} px em {dt:.2f} s ({round(v)} px/s; limite {round(lim)})', round(v))
    return achados


def agrupar(achados: list) -> list:
    """Junta o mesmo problema em instantes seguidos numa linha só (intervalo + pior valor)."""
    out = {}
    for f in achados:
        k = (f['caso'], f['cena'], f['ator'], f['tipo'], f['nivel'], f['regiao'].split(' ')[0])
        g = out.get(k)
        if not g:
            out[k] = {**f, 't_ini': f['t'], 't_fim': f['t'], 'n': 1, 'pior': f['valor']}
        else:
            g['t_fim'] = f['t']; g['n'] += 1
            if f['valor'] > g['pior']:
                g['pior'], g['detalhe'], g['t'], g['d'], g['plano'] = f['valor'], f['detalhe'], f['t'], f['d'], f['plano']
    return sorted(out.values(), key=lambda g: (g['caso'], g['nivel'] != 'comprovado', g['cena'], g['t_ini']))


# ───────────────────────── casos e relatório ─────────────────────────
def casos() -> list:
    out = [('baratas', json.loads(BARATAS.read_text(encoding='utf-8')))]
    out += [(c['nome'], c['roteiro']) for c in json.loads(CASOS_JSON.read_text(encoding='utf-8'))['casos']]
    return out


def relatorio(resultados: list) -> str:
    L = ['# Relatório geométrico — Ninguém Te Contou (Fase 1)', '',
         'Gerado por `python -m tests.ntc_geometria`. Medido no Chrome do Playwright sobre o motor real (`canais/ntc/vetor/fabula.html`), '
         f'grade de {GRADE} px com `elementsFromPoint` (forma pintada), amostras a cada {PASSO_MOV:.3f} s em cena com movimento e a cada {PASSO_PARADO} s nas paradas, '
         'mais início/desenvolvimento/ação/final e cada corte de câmera. Tempo de cada cena estimado pela narração (3 palavras/s).', '',
         '**comprovado** = a medida mostra o erro sem depender de gosto. **possível** = a medida acusa, mas pode ser intencional (profundidade, encostar de leve) — precisa de olho.', '']
    tot_c = tot_p = 0
    for nome, med, grupos in resultados:
        c = sum(g['nivel'] == 'comprovado' for g in grupos); p = len(grupos) - c
        tot_c += c; tot_p += p
        L += [f'## Caso `{nome}` — {len(med["info"])} cenas, {len(med["amostras"])} instantes medidos, {c} comprovados, {p} possíveis', '']
        if med['erros_js']:
            L += ['Erros de JavaScript na página: ' + '; '.join(med['erros_js'][:5]), '']
        L += ['| nível | cena | cenário | quando (s na cena) | plano | elemento | problema | região invadida | medida |', '|---|---|---|---|---|---|---|---|---|']
        for g in grupos:
            a0 = round(g['t_ini'] - (g['t'] - g['d']), 2); a1 = round(g['t_fim'] - (g['t'] - g['d']), 2)
            quando = f'{a0}' if g['n'] == 1 else f'{a0}–{a1} ({g["n"]} amostras)'
            L.append(f"| {g['nivel']} | {g['cena']} | {g['cenario']} | {quando} | {g['plano']} | {g['ator']} | {g['tipo']} | {g['regiao']} | {g['detalhe']} |")
        L.append('')
    L.insert(6, f'**Total: {tot_c} comprovados, {tot_p} possíveis.**\n')
    return '\n'.join(L)


def rodar(saida: Path | None = None, **kw) -> list:
    res = []
    for nome, r in casos():
        med = medir_dados(dados_do_roteiro(r), **kw)
        res.append((nome, med, agrupar(analisar(med, nome))))
    if saida:
        saida.write_text(relatorio(res), encoding='utf-8')
    return res


if __name__ == '__main__':
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / 'docs' / 'RELATORIO_GEOMETRIA_NTC.md'
    for nome, med, g in rodar(out):
        print(nome, len(med['amostras']), 'instantes', sum(x['nivel'] == 'comprovado' for x in g), 'comprovados', len(g), 'no total')
    print('relatório:', out)
