// camada.identidade — camada ÚNICA (fundo transparente) aplicada sobre TODA a linha do tempo, qualquer que seja o backend
// de cada cena: marca, selo honesto por cena (REGISTRO/ESQUEMA/RECONSTRUÇÃO…), crédito do asset da cena e legendas por
// palavra com @remotion/captions (destaque ativo, poucas palavras por grupo, área segura dos apps).
import React, { useEffect, useMemo } from 'react';
import { AbsoluteFill, continueRender, delayRender, useCurrentFrame, useVideoConfig } from 'remotion';
import { C, FD, FT, Fontes, IDT, clamp } from './ident';

export type CamadaProps = {
  duracao: number;
  palavras: { w: string; s: number; e: number; hl?: boolean }[];
  cenas: { ini: number; fim: number; selo?: string | null; credito?: string | null; legenda_tom?: 'escuro' | 'claro'; legenda?: boolean }[];
  combinar_ms?: number;
  legenda_topo?: number;            // por formato (ATLAS: mais baixa, perto da referência, dentro da área segura)
  legenda_caixa?: [number, number, number, number];   // faixa PRÓPRIA da legenda (layout.faixa_inferior): ancorada pela BASE
  credito_caixa?: [number, number, number, number];   // faixa ATLAS de atribuição para registros MP4 (abaixo da legenda)
  marca_y?: number;                 // posição da marca quando ativa
  marca_visivel?: boolean;          // ATLAS: false para não competir com a geografia e documentos
  medir?: boolean;                  // registra a caixa real da legenda e da marca (validação nos quadros)
  estilo?: { max_palavras?: number; tamanho?: number; tamanho_min?: number; peso?: number; caixa?: string; linhas_max?: number; cor_ativa?: string; cor_futura?: string; destaque_palavra?: boolean; destaque_estatico?: boolean };
};

export const Camada: React.FC<CamadaProps> = (P) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps, ms = t * 1000;
  const L = { ...IDT.legenda, ...(P.estilo || {}) } as typeof IDT.legenda & NonNullable<CamadaProps['estilo']>;   // estilo do CANAL por formato
  // agrupamento = src/v4/formatos/legenda_sync.grupos (MESMA regra, conferida contra o áudio): quebra na pausa real,
  // em 4 palavras ou 1,6 s; grupo curto demais (< 0,35 s) funde com o vizinho — sem trocas bruscas
  const grupos = useMemo(() => {
    const W = P.palavras, max = L.max_palavras || 4;
    let gs: typeof W[] = [], cur: typeof W = [];
    for (const w of W) {
      if (cur.length && (w.s - cur[cur.length - 1].e >= .25 || cur.length >= max || w.e - cur[0].s > 1.6)) { gs.push(cur); cur = []; }
      cur.push(w);
    }
    if (cur.length) gs.push(cur);
    for (let mudou = true; mudou;) {
      mudou = false;
      for (let i = 0; i < gs.length && gs.length > 1; i++) {
        const g = gs[i];
        if (g[g.length - 1].e - g[0].s >= .35) continue;
        const viz = [i - 1, i + 1].filter(k => k >= 0 && k < gs.length && gs[k].length + g.length <= max + 1)
          .filter(k => {
            const left = gs[Math.min(i, k)], right = gs[Math.max(i, k)];
            return right[0].s - left[left.length - 1].e < .25 && right[right.length - 1].e - left[0].s <= 1.6;
          });
        if (!viz.length) continue;
        const k = viz.sort((x, y) => Math.abs((x > i ? gs[x][0].s - g[g.length - 1].e : g[0].s - gs[x][gs[x].length - 1].e)) - Math.abs((y > i ? gs[y][0].s - g[g.length - 1].e : g[0].s - gs[y][gs[y].length - 1].e)))[0];
        if (k > i) { gs[i] = [...g, ...gs[k]]; gs.splice(k, 1); } else { gs[k] = [...gs[k], ...g]; gs.splice(i, 1); }
        mudou = true; break;
      }
    }
    const out = gs.map(g => ({ ini: g[0].s - .06, fim: g[g.length - 1].e + .12, tokens: g.map((w, j) => ({ text: (j ? ' ' : '') + w.w, fromMs: w.s * 1000, toMs: w.e * 1000 })) }));
    for (let i = 0; i + 1 < out.length; i++) out[i].fim = Math.min(out[i].fim, out[i + 1].ini);
    return out;
  }, [P.palavras]);
  const hl = new Set(P.palavras.filter(p => p.hl).map(p => p.s.toFixed(3)));
  // corpo da legenda MEDIDO com a fonte real (canvas): maior corpo em que o grupo quebra em ≤ 2 linhas DENTRO da faixa
  const [fontes, setFontes] = React.useState(false);
  const [hF] = React.useState(() => (P.legenda_caixa ? delayRender('fontes da legenda') : null));
  useEffect(() => { (document as any).fonts.ready.then(() => setFontes(true)); }, []);
  useEffect(() => { if (fontes && hF != null) continueRender(hF); }, [fontes]);     // libera só DEPOIS do corpo medido aplicado
  const corpoQueCabe = (txt: string, larg: number, alt: number): number => {
    const cv = (corpoQueCabe as any).cv || ((corpoQueCabe as any).cv = document.createElement('canvas').getContext('2d'));
    for (let px = L.tamanho; px >= (L.tamanho_min || 40); px -= 2) {
      cv.font = `${L.peso} ${px}px ${FT}`;
      const w = (s: string) => cv.measureText(s).width - Math.max(0, s.length - 1);      // letterSpacing −1
      const pal = txt.split(' '); let linhas = 1, atual = '';
      for (const x of pal) { const tent = atual ? atual + ' ' + x : x; if (w(tent) <= larg) atual = tent; else { linhas++; atual = x; if (w(x) > larg) linhas = 99; } }
      if (linhas <= (L.linhas_max || 2) && linhas * px * 1.08 <= alt) return px;
    }
    return L.tamanho_min || 40;
  };
  const gg = grupos.find(gr => t >= gr.ini && t < gr.fim), g = gg ? gg.tokens : null;
  const cena = P.cenas.find(c => t >= c.ini && t < c.fim);
  const sv = cena ? clamp((t - cena.ini) / .25) * clamp((cena.fim - t) / .2) : 0;
  useEffect(() => {
    if (!P.medir || (P.legenda_caixa && !fontes)) return;          // mede DEPOIS do corpo da legenda aplicado
    const h = delayRender('medir camada');
    (document as any).fonts.ready.then(() => {
      const r = (sel: string) => { const e = document.querySelector(sel); if (!e) return null; const q = e.getBoundingClientRect(); return { x: q.left, y: q.top, w: q.width, h: q.height }; };
      console.log('MEDIDA_CAMADA ' + JSON.stringify({ frame, legenda: r('[data-legenda] > div'), marca: r('[data-marca]'), palavras: g ? g.map(tk => tk.text.trim()) : [] }));
      continueRender(h);
    });
  }, [frame, fontes]);
  const LC = P.legenda_caixa;
  return (
    <AbsoluteFill style={{ backgroundColor: 'transparent' }}>
      <Fontes />
      {P.marca_visivel !== false && <div data-marca="1" style={{ position: 'absolute', left: IDT.marca.x, top: P.marca_y ?? IDT.marca.y, display: 'flex', alignItems: 'center', gap: 12, fontFamily: FD,
        fontWeight: 700, fontSize: IDT.marca.tamanho, letterSpacing: 4, color: IDT.marca.cor, textShadow: '0 1px 8px rgba(0,0,0,.8)' }}>
        <i style={{ width: 14, height: 14, background: C.amarelo, transform: 'rotate(45deg)', display: 'inline-block' }} />{IDT.marca.texto}</div>}
      {cena && cena.selo && <div style={{ position: 'absolute', left: 72, top: IDT.selo.y, opacity: sv, fontFamily: FD, fontWeight: 700, fontSize: IDT.selo.tamanho,
        letterSpacing: 3, color: '#fff', padding: '4px 12px', border: '2px solid rgba(255,255,255,.75)', background: 'rgba(0,0,0,.35)', textTransform: 'uppercase' }}>{cena.selo}</div>}
      {cena && cena.credito && <div data-credito-video="1" style={P.credito_caixa ? { position: 'absolute', left: P.credito_caixa[0], top: P.credito_caixa[1], width: P.credito_caixa[2], height: P.credito_caixa[3],
        textAlign: 'center', opacity: sv, fontFamily: FD, fontSize: 18, lineHeight: '22px', color: '#F2EDE3',
        textShadow: '0 1px 6px #000', overflow: 'hidden' } : { position: 'absolute', right: 160, top: IDT.credito.y, maxWidth: 760, textAlign: 'right', opacity: sv,
        fontFamily: FD, fontSize: IDT.credito.tamanho, lineHeight: 1.2, color: IDT.credito.cor, textShadow: '0 1px 6px #000' }}>{cena.credito}</div>}
      {g && cena?.legenda !== false && <div data-legenda="1" style={LC ? { position: 'absolute', left: LC[0], width: LC[2], top: LC[1], height: LC[3], display: 'flex', justifyContent: 'center', alignItems: 'flex-end' }
        : { position: 'absolute', left: 150, right: 150, top: P.legenda_topo ?? IDT.areas_seguras.legenda_topo, display: 'flex', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center', fontFamily: FT, fontWeight: L.peso, lineHeight: 1.08,
          // faixa própria: corpo encolhe (mín. 50 px) para caber em 2 linhas na largura da área segura
          fontSize: LC && fontes ? corpoQueCabe(L.caixa === 'frase' ? g.map(tk => tk.text).join('').trim() : g.map(tk => tk.text).join('').trim().toUpperCase(), LC[2] - 44, LC[3] - 12) : L.tamanho, letterSpacing: -1, textTransform: L.caixa === 'frase' ? 'none' : 'uppercase',
          color: L.cor, textShadow: L.sombra, background: cena?.legenda_tom === 'claro' ? L.placa : 'transparent', padding: '6px 20px', borderRadius: 14 }}>
          {g.map((tk, i) => {
            const ativo = ms >= tk.fromMs && ms < tk.toMs, fut = ms < tk.fromMs;
            const chave = L.destaque_palavra !== false && hl.has((tk.fromMs / 1000).toFixed(3));
            // ATLAS: palavra-chave fica amarela durante todo o bloco; nunca animar palavra a palavra.
            // DOSSIÊ mantém comportamento anterior intacto.
            const cor = L.destaque_estatico ? (chave ? L.cor_ativa : L.cor)
              : ((ativo || chave) && !fut ? L.cor_ativa : fut ? L.cor_futura : L.cor);
            return <span key={i} style={{ color: cor }}>{tk.text}</span>;
          })}
        </div></div>}
    </AbsoluteFill>
  );
};
