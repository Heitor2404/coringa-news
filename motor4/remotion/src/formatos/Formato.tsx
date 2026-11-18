// Composição única dos FORMATOS. Palco persistente + camadas (primitivas) nos slots da COMPOSIÇÃO do beat. Marca e
// legendas NÃO são desenhadas aqui: vêm da camada global (Camada.tsx), como em todo o V4.
// Com props.medir, o quadro registra no console a geometria REAL depois de pronto (mapa ocioso, fontes carregadas):
// caixas visíveis de cada camada, território do beat, rótulos, menor corpo de texto e textos cortados → scripts/formatos_validar.py.
import React, { useEffect } from 'react';
import { AbsoluteFill, continueRender, delayRender, useCurrentFrame, useVideoConfig } from 'remotion';
import { Fontes, clamp } from '../ident';
import { PalcoMapa, PalcoMesa, PalcoTecnico, palcoEm } from './Palco';
import { PRIMITIVAS, easeOut } from './Primitivas';
import type { FormatoProps } from './tipos';

type R = { x: number; y: number; w: number; h: number };
const uniao = (rs: R[]) => {
  if (!rs.length) return null;
  const x0 = Math.min(...rs.map(r => r.x)), y0 = Math.min(...rs.map(r => r.y));
  const x1 = Math.max(...rs.map(r => r.x + r.w)), y1 = Math.max(...rs.map(r => r.y + r.h));
  return { x: x0, y: y0, w: x1 - x0, h: y1 - y0 };
};
const opacidade = (el: Element | null) => { let o = 1; for (let e = el as HTMLElement | null; e && e !== document.body; e = e.parentElement) o *= parseFloat(getComputedStyle(e).opacity || '1'); return o; };
const ret = (d: DOMRect): R => ({ x: d.left, y: d.top, w: d.width, h: d.height });

function medir(frame: number) {
  const out: any = { frame, camadas: [], textos: [], cortados: [], rotulos: [], roi: null };
  document.querySelectorAll('[data-camada]').forEach(c => {
    if (opacidade(c) < .05) return;
    const rs: R[] = [];
    c.querySelectorAll('*').forEach(el => {
      const s = getComputedStyle(el), r = el.getBoundingClientRect();
      if (r.width < 1 || r.height < 1 || opacidade(el) < .05) return;
      const fundo = s.backgroundColor && !/rgba\(.*, 0\)$/.test(s.backgroundColor) && s.backgroundColor !== 'transparent';
      // SVG: conta o DESENHO (linha, círculo, caminho), não a tela inteira do <svg> que o contém
      const forma = (el as any).ownerSVGElement && !['defs', 'pattern', 'filter', 'svg'].includes(el.tagName) && !el.closest('defs');
      const caixaHtml = !(el as any).ownerSVGElement && el.tagName !== 'svg' && (el.tagName === 'IMG' || fundo || s.backgroundImage !== 'none' || parseFloat(s.borderTopWidth) > 0 || parseFloat(s.borderLeftWidth) > 0);
      if (forma || caixaHtml) rs.push(ret(r));
    });
    const tw = document.createTreeWalker(c, NodeFilter.SHOW_TEXT);
    for (let n = tw.nextNode(); n; n = tw.nextNode()) {
      if (!n.textContent?.trim()) continue;
      const el = n.parentElement!, rg = document.createRange(); rg.selectNodeContents(n);
      const r = rg.getBoundingClientRect();
      if (r.width < 1 || opacidade(el) < .3) continue;
      rs.push(ret(r));
      // escala real (transform) = caixa desenhada ÷ altura de layout SEM arredondamento (offsetHeight arredonda: 25,9 px falsos)
      const hl = parseFloat(getComputedStyle(el).height) || (el as HTMLElement).offsetHeight || 1;
      const esc = el.getBoundingClientRect().height / Math.max(1, hl);
      out.textos.push({ camada: c.getAttribute('data-camada'), txt: n.textContent.trim().slice(0, 40), px: Math.round(parseFloat(getComputedStyle(el).fontSize) * (esc || 1) * 10) / 10,
        meta: !!el.closest('[data-meta]') });
    }
    c.querySelectorAll('*').forEach(el => {
      const h = el as HTMLElement, s = getComputedStyle(h);
      if ((s.overflow === 'hidden' || s.textOverflow === 'ellipsis') && h.scrollWidth > h.clientWidth + 2 && h.textContent?.trim() && opacidade(h) > .3 && !h.querySelector('img'))
        out.cortados.push({ camada: c.getAttribute('data-camada'), txt: h.textContent.trim().slice(0, 50) });
    });
    const u = uniao(rs);
    // pino = partes separadas (ponto, haste, foto, rótulo): colisão entre pinos confere PARTE × PARTE, não a caixa que as une
    if (u) out.camadas.push({ id: c.getAttribute('data-camada'), componente: c.getAttribute('data-componente'), caixa: u,
      ...(c.getAttribute('data-componente') === 'atlas.geoPin' ? { partes: rs.filter(r => r.w * r.h < 400000).slice(0, 12) } : {}) });
  });
  document.querySelectorAll('[data-rotulo]').forEach(el => { if (opacidade(el) > .3) out.rotulos.push({ tipo: el.getAttribute('data-rotulo'), txt: el.textContent, caixa: ret(el.getBoundingClientRect()) }); });
  document.querySelectorAll('[data-meta]').forEach(el => {
    if (opacidade(el) < .3 || el.closest('[data-camada]') || !el.textContent?.trim()) return;
    const tw = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    for (let n = tw.nextNode(); n; n = tw.nextNode()) if (n.textContent?.trim())
      out.textos.push({ camada: null, txt: n.textContent.trim().slice(0, 40), px: parseFloat(getComputedStyle(n.parentElement!).fontSize), meta: true });
    const h = el as HTMLElement, s = getComputedStyle(h);
    if ((s.overflow === 'hidden' || s.textOverflow === 'ellipsis') && h.scrollWidth > h.clientWidth + 2) out.cortados.push({ camada: el.getAttribute('data-meta'), txt: h.textContent!.trim().slice(0, 50) });
    const r = h.getBoundingClientRect();
    // A caixa pode ter 66px enquanto o TEXTO REAL quebra em 4+ linhas e invade a legenda.
    // Medir o filho visível impede que a atribuição pareça "dentro da faixa" só pela moldura.
    const textoReal = el.getAttribute('data-meta') === 'atribuicao' ? el.querySelector('span')?.getBoundingClientRect() : null;
    out.metas = (out.metas || []).concat([{ tipo: el.getAttribute('data-meta'), caixa: ret(r),
      ...(textoReal ? { texto_caixa: ret(textoReal) } : {}),
      txt: h.textContent!.trim().slice(0, 400), datasets: (el.getAttribute('data-atribuicao') || '').split(',').filter(Boolean) }]);
  });
  // cartões (sistema único): centro desenhado × centro do slot declarado, e rotação (nunca inclinado)
  out.cartoes = [];
  document.querySelectorAll('[data-cartao]').forEach(el => {
    if (opacidade(el) < .5) return;
    const alvo = JSON.parse(el.getAttribute('data-cartao')!), r = el.getBoundingClientRect();
    const tf = getComputedStyle(el).transform; let rot = 0;
    if (tf && tf !== 'none') { const m = tf.match(/matrix\(([^)]+)\)/); if (m) { const [a, b] = m[1].split(',').map(Number); rot = Math.atan2(b, a) * 180 / Math.PI; } }
    const camada = el.closest('[data-camada]')?.getAttribute('data-camada');
    out.cartoes.push({ camada, alvo, centro: [r.left + r.width / 2, r.top + r.height / 2], caixa: ret(r), rot });
  });
  // pinos ancorados: o centro desenhado precisa bater com o MapLibre (map.project) neste quadro — não descolam no pan/zoom
  const mapa = (window as any).__mapa;
  out.pinos = [];
  document.querySelectorAll('[data-ancora-geo]').forEach(el => {
    if (opacidade(el) < .3 || !mapa) return;
    const ll = JSON.parse(el.getAttribute('data-ancora-geo')!), r = el.getBoundingClientRect(), lc = mapa.getCenter().lng, pj = mapa.project([ll[0] + 360 * Math.round((lc - ll[0]) / 360), ll[1]]);
    const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    out.pinos.push({ lonlat: ll, centro: [cx, cy], mapa: [pj.x, pj.y], desvio: Math.hypot(cx - pj.x, cy - pj.y) });
  });
  const roi = document.querySelector('[data-roi]');
  if (roi && opacidade(roi) > .3) out.roi = ret(roi.getBoundingClientRect());
  console.log('MEDIDA ' + JSON.stringify(out));
}

export const Formato: React.FC<FormatoProps> = (P) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const { entra, sai } = P.tokens.tempo;
  const i = palcoEm(P.palco, t);
  const op = (tipo: string) => {
    const atual = P.palco[i];
    const ant = i > 0 ? P.palco[i - 1] : null;
    const k = clamp((t - atual.t) / .5);
    if (atual.tipo === tipo) return ant && ant.tipo !== tipo ? k : 1;
    if (ant && ant.tipo === tipo) return 1 - k;
    return 0;
  };
  const temMapa = P.palco.some(p => p.tipo === 'mapa');
  // "respiração" lenta dos objetos de papel (documento, foto, ficha, calendário): +1,5 % ao longo da vida da camada, em
  // torno do centro da caixa; a marcação sobre um documento herda a do alvo (continua no trecho certo).
  const porId = Object.fromEntries(P.camadas.map(L => [L.id, L]));
  const respira = (L: any) => {
    // ATLAS: os slots já respeitam as máscaras de Shorts/Reels/TikTok. Escalar a
    // evidência fora do slot provoca colisão com os ícones (chips, wafer, 20,88 s).
    // Movimento do mapa e entrada de cada componente continuam; DOSSIÊ mantém a
    // respiração de papel que pertence à sua identidade visual.
    if (P.formato === 'atlas') return undefined;
    const A = L.componente === 'dossie.evidenceHighlight' && L.p?.alvo ? porId[L.p.alvo] : L;
    if (!A || !(A.componente === 'dossie.documentCard' || ['ficha', 'calendario'].includes(A.p?.estilo))) return undefined;
    const s = 1 + .015 * clamp((t - A.t0) / Math.max(1, A.t1 - A.t0));
    return { transform: `scale(${s})`, transformOrigin: `${A.caixa.x + A.caixa.w / 2}px ${A.caixa.y + A.caixa.h / 2}px` };
  };
  useEffect(() => {
    if (!P.medir) return;
    const h = delayRender(`medir ${frame}`);
    let n = 0;
    const tenta = () => {
      const w = window as any;
      const mapaPronto = !temMapa || op('mapa') <= 0 || w.__mapaQuadro === frame;
      if ((mapaPronto && (document as any).fonts?.status === 'loaded') || n++ > 200) { medir(frame); continueRender(h); } else setTimeout(tenta, 40);
    };
    setTimeout(tenta, 60);
  }, [frame]);
  return (
    <AbsoluteFill style={{ background: P.tokens.palco.mesa.fundo }}>
      <Fontes />
      {temMapa && <PalcoMapa P={P} opac={op('mapa')} />}
      {op('tecnico') > 0 && <PalcoTecnico P={P} opac={op('tecnico')} />}
      {op('mesa') > 0 && <PalcoMesa P={P} opac={op('mesa')} />}
      {P.camadas.map(L => {
        const Comp = PRIMITIVAS[L.componente];
        if (!Comp || t < L.t0 || t > L.t1 + sai) return null;
        const k = easeOut((t - L.t0) / entra);
        const v = clamp((t - L.t0) / entra) * clamp((L.t1 + sai - t) / sai);
        return <div key={L.id} data-camada={L.id} data-componente={L.componente} style={{ position: 'absolute', inset: 0, opacity: v, ...respira(L) }}>
          <Comp c={{ t, P, L, v, k }} /></div>;
      })}
    </AbsoluteFill>
  );
};
