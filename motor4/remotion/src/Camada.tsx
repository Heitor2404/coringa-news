// camada.identidade — camada ÚNICA (fundo transparente) aplicada sobre TODA a linha do tempo, qualquer que seja o backend
// de cada cena: marca, selo honesto por cena (REGISTRO/ESQUEMA/RECONSTRUÇÃO…), crédito do asset da cena e legendas por
// palavra com @remotion/captions (destaque ativo, poucas palavras por grupo, área segura dos apps).
import React, { useMemo } from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from 'remotion';
import { createTikTokStyleCaptions, type Caption } from '@remotion/captions';
import { C, FD, FT, Fontes, IDT, clamp } from './ident';

export type CamadaProps = {
  duracao: number;
  palavras: { w: string; s: number; e: number; hl?: boolean }[];
  cenas: { ini: number; fim: number; selo?: string | null; credito?: string | null; legenda_tom?: 'escuro' | 'claro' }[];
  combinar_ms?: number;
};

export const Camada: React.FC<CamadaProps> = (P) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps, ms = t * 1000;
  const L = IDT.legenda;
  const pages = useMemo(() => {
    const caps: Caption[] = P.palavras.map((p, i) => ({ text: (i ? ' ' : '') + p.w, startMs: p.s * 1000, endMs: p.e * 1000, timestampMs: p.s * 1000, confidence: 1 }));
    return createTikTokStyleCaptions({ captions: caps, combineTokensWithinMilliseconds: P.combinar_ms ?? 900 }).pages;
  }, [P.palavras]);
  // grupos com no máximo L.max_palavras palavras (quebra páginas longas mantendo a sincronia real)
  const grupos = useMemo(() => pages.flatMap(pg => {
    const out: typeof pg.tokens[] = [];
    for (let i = 0; i < pg.tokens.length; i += L.max_palavras) out.push(pg.tokens.slice(i, i + L.max_palavras));
    return out;
  }), [pages]);
  const hl = new Set(P.palavras.filter(p => p.hl).map(p => p.s.toFixed(3)));
  const g = grupos.find(gr => ms >= gr[0].fromMs - 60 && ms < gr[gr.length - 1].toMs + 120);
  const cena = P.cenas.find(c => t >= c.ini && t < c.fim);
  const sv = cena ? clamp((t - cena.ini) / .25) * clamp((cena.fim - t) / .2) : 0;
  return (
    <AbsoluteFill style={{ backgroundColor: 'transparent' }}>
      <Fontes />
      <div style={{ position: 'absolute', left: IDT.marca.x, top: IDT.marca.y, display: 'flex', alignItems: 'center', gap: 12, fontFamily: FD,
        fontWeight: 700, fontSize: IDT.marca.tamanho, letterSpacing: 4, color: IDT.marca.cor, textShadow: '0 1px 8px rgba(0,0,0,.8)' }}>
        <i style={{ width: 14, height: 14, background: C.amarelo, transform: 'rotate(45deg)', display: 'inline-block' }} />{IDT.marca.texto}</div>
      {cena && cena.selo && <div style={{ position: 'absolute', left: 72, top: IDT.selo.y, opacity: sv, fontFamily: FD, fontWeight: 700, fontSize: IDT.selo.tamanho,
        letterSpacing: 3, color: '#fff', padding: '4px 12px', border: '2px solid rgba(255,255,255,.75)', background: 'rgba(0,0,0,.35)', textTransform: 'uppercase' }}>{cena.selo}</div>}
      {cena && cena.credito && <div style={{ position: 'absolute', right: 160, top: IDT.credito.y, maxWidth: 760, textAlign: 'right', opacity: sv,
        fontFamily: FD, fontSize: IDT.credito.tamanho, lineHeight: 1.2, color: IDT.credito.cor, textShadow: '0 1px 6px #000' }}>{cena.credito}</div>}
      {g && <div style={{ position: 'absolute', left: 150, right: 150, top: IDT.areas_seguras.legenda_topo, display: 'flex', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center', fontFamily: FT, fontWeight: L.peso, fontSize: L.tamanho, lineHeight: 1.08, letterSpacing: -1, textTransform: 'uppercase',
          color: L.cor, textShadow: L.sombra, background: cena?.legenda_tom === 'claro' ? L.placa : 'transparent', padding: '6px 20px', borderRadius: 14 }}>
          {g.map((tk, i) => {
            const ativo = ms >= tk.fromMs && ms < tk.toMs, fut = ms < tk.fromMs;
            return <span key={i} style={{ color: (ativo || hl.has((tk.fromMs / 1000).toFixed(3))) && !fut ? L.cor_ativa : fut ? L.cor_futura : L.cor }}>{tk.text}</span>;
          })}
        </div></div>}
    </AbsoluteFill>
  );
};
