// PRIMITIVAS EDITORIAIS (12 com o palco). Cada uma desenha DENTRO da caixa recebida (slot calculado no Python), com
// entrada/saída determinísticas (tokens.tempo) e tamanhos mínimos para celular. Nada de efeito decorativo: cada
// primitiva revela uma informação (número, nível, data, documento, relação, comparação).
import React from 'react';
import { Img, staticFile } from 'remotion';
import { clamp, lerp } from '../ident';
import type { Camada, FormatoProps } from './tipos';

export const easeOut = (x: number) => 1 - Math.pow(1 - clamp(x), 3);
export type Ctx = { t: number; P: FormatoProps; L: Camada; v: number; k: number };   // v = visibilidade 0–1, k = progresso de entrada
const cores = (c: Ctx) => c.P.tokens.cores;
const FT = (c: Ctx) => c.P.tokens.fontes.titulo;
const FD = (c: Ctx) => c.P.tokens.fontes.dado;
const aparece = (c: Ctx, t0: number, d = .4) => easeOut((c.t - t0) / d);
const num = (x: number, casas = 0) => x.toLocaleString('pt-BR', { minimumFractionDigits: casas, maximumFractionDigits: casas });

// 4. editorial.statCard — número com unidade e referência; 'pilula' (rótulo de mapa) ou 'cartao' (papel)
export const StatCard: React.FC<{ c: Ctx }> = ({ c }) => {
  const p = c.L.p, C = cores(c), b = c.L.caixa;
  const conta = p.contagem && typeof p.valor === 'number' ? p.valor * easeOut((c.t - c.L.t0) / (p.dur_contagem || 1.2)) : p.valor;
  const txt = typeof conta === 'number' ? num(conta, p.casas || 0) : String(p.valor);
  if (p.estilo === 'pilula') return (
    <div style={{ position: 'absolute', left: b.x, top: b.y, width: b.w, height: b.h, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
      <div style={{ padding: '14px 30px', background: C.papel, color: C.tinta, fontFamily: FT(c), fontWeight: 900, fontSize: 40, textTransform: 'uppercase',
        boxShadow: '0 10px 30px rgba(0,0,0,.45)', transform: `translateY(${(1 - c.k) * 18}px)`, whiteSpace: 'nowrap' }}>
        <span style={{ fontFamily: FD(c), fontWeight: 700 }}>{p.prefixo || ''}{txt}</span>{p.unidade ? ` ${p.unidade}` : ''}{p.rotulo ? <span style={{ fontWeight: 700, opacity: .75 }}> · {p.rotulo}</span> : null}
      </div>
    </div>);
  return (
    <div style={{ position: 'absolute', left: b.x, top: b.y, width: b.w, height: b.h, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
      <div style={{ minWidth: Math.min(b.w, 620), maxWidth: b.w, padding: '34px 44px 28px', background: C.papel, color: C.tinta, boxShadow: '0 18px 50px rgba(0,0,0,.5)',
        transform: `translateY(${(1 - c.k) * 26}px) rotate(${p.inclina ?? -1}deg)`, borderTop: `10px solid ${C.destaque}` }}>
        {p.titulo && <div style={{ fontFamily: FD(c), fontWeight: 700, fontSize: 26, letterSpacing: 3, textTransform: 'uppercase', color: C.alerta, marginBottom: 6 }}>{p.titulo}</div>}
        <div style={{ fontFamily: FT(c), fontWeight: 900, fontSize: p.grande ? 150 : 112, lineHeight: .95, whiteSpace: 'nowrap' }}>
          {p.prefixo || ''}{txt}<span style={{ fontSize: p.grande ? 64 : 52, fontWeight: 800, marginLeft: 12 }}>{p.unidade || ''}</span></div>
        {p.rotulo && <div style={{ fontFamily: FT(c), fontWeight: 800, fontSize: 34, textTransform: 'uppercase', marginTop: 10, lineHeight: 1.1 }}>{p.rotulo}</div>}
        {p.referencia && <div style={{ fontFamily: FD(c), fontSize: 24, marginTop: 14, opacity: .7 }}>{p.referencia}</div>}
      </div>
    </div>);
};

// 5. editorial.peopleCard — retrato real licenciado em círculo + identidade curta
export const PeopleCard: React.FC<{ c: Ctx }> = ({ c }) => {
  const p = c.L.p, C = cores(c), b = c.L.caixa, im = c.P.imagens?.[p.asset];
  const R = Math.min(b.w, b.h - 90) / 2;
  return (
    <div style={{ position: 'absolute', left: b.x, top: b.y, width: b.w, height: b.h, display: 'flex', flexDirection: 'column', alignItems: 'center', transform: `scale(${.9 + .1 * c.k})` }}>
      <div style={{ width: 2 * R, height: 2 * R, borderRadius: R, overflow: 'hidden', border: `8px solid ${C.destaque}`, boxShadow: '0 12px 40px rgba(0,0,0,.55)', background: C.tinta }}>
        {im && <Img src={staticFile(im.src)} style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: p.foco || '50% 30%' }} />}
      </div>
      <div style={{ marginTop: -18, padding: '8px 22px', background: C.papel, color: C.tinta, fontFamily: FT(c), fontWeight: 900, fontSize: 32, whiteSpace: 'nowrap' }}>{p.nome}</div>
      {p.papel && <div style={{ marginTop: 8, fontFamily: FD(c), fontSize: 24, color: '#fff', textShadow: '0 2px 8px #000' }}>{p.papel}</div>}
    </div>);
};

// 6. editorial.hierarchy — degraus/níveis; o nível ativo acende em sequência (t por nível)
export const Hierarchy: React.FC<{ c: Ctx }> = ({ c }) => {
  const p = c.L.p, C = cores(c), b = c.L.caixa;
  const n = p.niveis.length, gap = 10, w = (b.w - gap * (n - 1)) / n;
  const hb = p.legenda_base ? b.h - 46 : b.h;                    // a legenda da base fica DENTRO da caixa
  const passo = (hb - 120) / Math.max(1, n - 1) * (p.escada === false ? 0 : 1);
  return (
    <div style={{ position: 'absolute', left: b.x, top: b.y, width: b.w, height: b.h }}>
      {p.niveis.map((nv: any, i: number) => {
        const ent = aparece(c, c.L.t0 + i * (p.cadencia ?? .18));
        const ativo = (nv.t != null && c.t >= nv.t) || (p.ativo || []).some((a: any) => c.t >= a.t0 && (a.t1 == null || c.t < a.t1) && a.i === i);
        const altura = p.alturas ? 120 + p.alturas[i] * (hb - 160) : 120 + i * passo;   // escada ou perfil (alturas 0–1)
        const topo = hb - altura;
        return (
          <div key={i} style={{ position: 'absolute', left: i * (w + gap), top: topo + (1 - ent) * 40, width: w, height: altura, opacity: ent,
            background: ativo ? C.destaque : C.papel, color: C.tinta, boxShadow: `0 -6px 0 ${ativo ? C.destaque_escuro : 'rgba(0,0,0,.18)'} inset, 0 14px 30px rgba(0,0,0,.45)`,
            display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: 14 }}>
            {nv.valor != null && <div style={{ fontFamily: FT(c), fontWeight: 900, fontSize: w > 150 ? 54 : 44, lineHeight: 1 }}>{nv.valor}</div>}
            <div style={{ fontFamily: FD(c), fontWeight: 700, fontSize: w > 150 ? 22 : w > 110 ? 18 : 16, textTransform: 'uppercase', textAlign: 'center', marginTop: 6, padding: '0 6px', lineHeight: 1.15 }}>{nv.rotulo}</div>
          </div>);
      })}
      {p.legenda_base && <div style={{ position: 'absolute', left: 0, right: 0, top: hb + 12, textAlign: 'center', fontFamily: FD(c), fontWeight: 700, fontSize: 24,
        color: '#fff', letterSpacing: 2, textTransform: 'uppercase', textShadow: '0 2px 8px #000', opacity: aparece(c, p.legenda_t ?? c.L.t0 + .6) }}>{p.legenda_base}</div>}
    </div>);
};

// 7. editorial.timeline — linha com marcos que aparecem na ordem; o marco atual fica em destaque
export const Timeline: React.FC<{ c: Ctx }> = ({ c }) => {
  const p = c.L.p, C = cores(c), b = c.L.caixa, n = p.marcos.length;
  const yL = Math.min(84, b.h * .47), x0 = 40, x1 = b.w - 40;   // tudo DENTRO da caixa: data 0–58, linha 84, texto 110–173
  const atual = p.marcos.reduce((a: number, m: any, i: number) => (c.t >= m.t ? i : a), -1);
  const prog = atual < 0 ? 0 : (atual + Math.min(1, (c.t - p.marcos[atual].t) / .6)) / Math.max(1, n - 1);
  return (
    <div style={{ position: 'absolute', left: b.x, top: b.y, width: b.w, height: b.h }}>
      <div style={{ position: 'absolute', left: x0, top: yL - 3, width: x1 - x0, height: 6, background: 'rgba(255,255,255,.18)' }} />
      <div style={{ position: 'absolute', left: x0, top: yL - 3, width: (x1 - x0) * clamp(prog), height: 6, background: C.destaque }} />
      {p.marcos.map((m: any, i: number) => {
        const x = x0 + (x1 - x0) * (n === 1 ? .5 : i / (n - 1)), v = aparece(c, m.t), on = i === atual;
        return (<React.Fragment key={i}>
          <div style={{ position: 'absolute', left: x - 16, top: yL - 16, width: 32, height: 32, borderRadius: 16, background: on ? C.destaque : C.papel, opacity: v, border: `5px solid ${C.tinta}` }} />
          <div style={{ position: 'absolute', left: clamp(x - 140, 0, b.w - 280), width: 280, top: yL - 84, textAlign: 'center', opacity: v, fontFamily: FD(c), fontWeight: 700,
            fontSize: on ? 48 : 36, color: on ? C.destaque : '#fff', textShadow: '0 2px 10px #000' }}>{m.data}</div>
          <div style={{ position: 'absolute', left: clamp(x - 150, 0, b.w - 300), width: 300, top: yL + 26, textAlign: 'center', opacity: v * (on ? 1 : .75), fontFamily: FT(c), fontWeight: 800,
            fontSize: 28, lineHeight: 1.12, color: '#fff', textTransform: 'uppercase', textShadow: '0 2px 10px #000' }}>{m.texto}</div>
        </React.Fragment>);
      })}
    </div>);
};

// 8. dossie.documentCard — registro/documento real com proveniência; recorte (zoom) só se ampliar ≥ 1,5× (ERR-055)
export const DocumentCard: React.FC<{ c: Ctx }> = ({ c }) => {
  const p = c.L.p, C = cores(c), b = c.L.caixa, im = c.P.imagens?.[p.asset];
  if (!im) return null;
  const meta = p.meta || [];
  const cab = p.cabecalho ? 52 : 0, rod = 22 + meta.length * 36;
  const maxW = b.w - 36, maxH = b.h - cab - rod - 36;
  const esc = Math.min(maxW / im.w, maxH / im.h);
  const fw = im.w * esc, fh = im.h * esc;
  const z = p.zoom && c.t >= p.zoom.t0 ? lerp(1, p.zoom.escala, easeOut((c.t - p.zoom.t0) / (p.zoom.dur || 1.4))) : 1;
  const foco = p.zoom?.foco || [.5, .5];
  const reg = p.estilo === 'registro';
  return (
    <div style={{ position: 'absolute', left: b.x + (b.w - fw - 36) / 2, top: b.y + (b.h - fh - cab - rod - 36) / 2, width: fw + 36, padding: 18,
      background: reg ? '#F7F5F0' : C.papel, boxShadow: '0 22px 60px rgba(0,0,0,.6)', transform: `translateY(${(1 - c.k) * 30}px) rotate(${p.inclina ?? (reg ? 0 : -1.2)}deg)` }}>
      {cab > 0 && <div style={{ height: cab, display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontFamily: FD(c), fontWeight: 700, fontSize: 22,
        color: C.tinta, letterSpacing: 2, textTransform: 'uppercase', borderBottom: `2px solid ${C.tinta}`, marginBottom: 12 }}>
        <span>{p.cabecalho}</span><span style={{ color: C.alerta }}>{p.cabecalho_dir || ''}</span></div>}
      <div style={{ width: fw, height: fh, overflow: 'hidden', position: 'relative', background: '#111' }}>
        <Img src={staticFile(im.src)} style={{ width: fw, height: fh, transform: `scale(${z})`, transformOrigin: `${foco[0] * 100}% ${foco[1] * 100}%`, filter: p.sepia ? 'sepia(.25) contrast(1.05)' : undefined }} />
      </div>
      <div style={{ paddingTop: 14 }}>
        {meta.map((m: string, i: number) => <div key={i} data-linha={i} style={{ fontFamily: FD(c), fontSize: 24, lineHeight: '36px', color: C.tinta, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{m}</div>)}
      </div>
    </div>);
};

// 9. dossie.evidenceHighlight — carimbo / sublinhado / círculo sobre algo JÁ presente (coordenadas da caixa alvo)
export const Evidence: React.FC<{ c: Ctx }> = ({ c }) => {
  const p = c.L.p, C = cores(c), b = c.L.caixa, k = aparece(c, c.L.t0, .35);
  // carimbo na metade de baixo do alvo (sobre o rótulo, nunca sobre o número/rosto): ref. B "NÃO EXISTE" sobre a ficha
  if (p.tipo === 'carimbo') return (
    <div style={{ position: 'absolute', left: b.x + b.w * .22, top: b.y + b.h * .52, width: b.w * .7, height: b.h * .3, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ padding: '10px 26px', border: `7px solid ${C.alerta}`, color: C.alerta, fontFamily: FT(c), fontWeight: 900, fontSize: p.tamanho || 64,
        textTransform: 'uppercase', letterSpacing: 4, transform: `rotate(${p.inclina ?? -8}deg) scale(${lerp(1.6, 1, k)})`, opacity: k, background: 'rgba(242,237,227,.08)', whiteSpace: 'nowrap' }}>{p.texto}</div>
    </div>);
  if (p.tipo === 'sublinhado') return <div style={{ position: 'absolute', left: b.x, top: b.y + b.h - 10, width: b.w * k, height: 10, background: C.destaque, opacity: .95 }} />;
  const L = 2 * Math.PI * Math.sqrt((b.w * b.w + b.h * b.h) / 8);
  return (
    <svg style={{ position: 'absolute', left: b.x - 20, top: b.y - 20, overflow: 'visible' }} width={b.w + 40} height={b.h + 40}>
      <ellipse cx={b.w / 2 + 20} cy={b.h / 2 + 20} rx={b.w / 2 + 10} ry={b.h / 2 + 10} fill="none" stroke={C.destaque} strokeWidth={8}
        strokeDasharray={L} strokeDashoffset={L * (1 - k)} strokeLinecap="round" transform={`rotate(-4 ${b.w / 2 + 20} ${b.h / 2 + 20})`} />
    </svg>);
};

// 10. editorial.comparison — barras com unidade comum; o valor conta até o real
export const Comparison: React.FC<{ c: Ctx }> = ({ c }) => {
  const p = c.L.p, C = cores(c), b = c.L.caixa, n = p.itens.length;
  const max = Math.max(...p.itens.map((x: any) => x.valor)), gap = 40, w = Math.min(240, (b.w - gap * (n + 1)) / n), hMax = b.h - 170;
  const x0 = (b.w - (n * w + (n - 1) * gap)) / 2;
  return (
    <div style={{ position: 'absolute', left: b.x, top: b.y, width: b.w, height: b.h }}>
      <div style={{ position: 'absolute', left: 20, right: 20, top: b.h - 80, height: 4, background: 'rgba(255,255,255,.55)' }} />
      {p.itens.map((it: any, i: number) => {
        const k = easeOut((c.t - (it.t ?? c.L.t0 + i * .5)) / 1.1), h = hMax * (it.valor / max) * k;
        return (<React.Fragment key={i}>
          <div style={{ position: 'absolute', left: x0 + i * (w + gap), top: b.h - 80 - h, width: w, height: h, background: i === n - 1 ? C.destaque : C.papel,
            backgroundImage: it.andares ? `repeating-linear-gradient(0deg, rgba(0,0,0,.22) 0 3px, transparent 3px ${hMax * (it.valor / max) / it.andares}px)` : undefined }} />
          <div style={{ position: 'absolute', left: x0 + i * (w + gap) - 40, width: w + 80, top: b.h - 80 - h - 74, textAlign: 'center', fontFamily: FT(c), fontWeight: 900,
            fontSize: 58, color: '#fff', textShadow: '0 2px 12px #000', opacity: k }}>{num(it.valor * k, 0)}<span style={{ fontSize: 30 }}> {p.unidade}</span></div>
          <div style={{ position: 'absolute', left: x0 + i * (w + gap) - 50, width: w + 100, top: b.h - 64, textAlign: 'center', fontFamily: FD(c), fontWeight: 700,
            fontSize: 24, color: '#fff', textTransform: 'uppercase', lineHeight: 1.15, textShadow: '0 2px 8px #000' }}>{it.rotulo}</div>
        </React.Fragment>);
      })}
    </div>);
};

// 11. editorial.flowConnections — nós e setas; 'fluxo' anima o sentido (água, dinheiro, causa → efeito)
export const Flow: React.FC<{ c: Ctx }> = ({ c }) => {
  const p = c.L.p, C = cores(c), b = c.L.caixa, n = p.nos.length;
  const hN = 112, gap = (b.h - n * hN) / Math.max(1, n - 1);
  const yN = (i: number) => i * (hN + gap);
  return (
    <div style={{ position: 'absolute', left: b.x, top: b.y, width: b.w, height: b.h }}>
      <svg width={b.w} height={b.h} style={{ position: 'absolute', inset: 0, overflow: 'visible' }}>
        {p.nos.slice(0, -1).map((_: any, i: number) => {
          const v = aparece(c, p.nos[i + 1].t ?? c.L.t0), ya = yN(i) + hN, yb = yN(i + 1);
          return <g key={i} opacity={v}>
            <line x1={b.w / 2} y1={ya + 6} x2={b.w / 2} y2={ya + 6 + (yb - ya - 18) * v} stroke={C.destaque} strokeWidth={8}
              strokeDasharray={p.fluxo ? '22 14' : undefined} strokeDashoffset={p.fluxo ? -(c.t * 60) % 36 : undefined} />
            <path d={`M${b.w / 2 - 20} ${yb - 26} L${b.w / 2} ${yb - 4} L${b.w / 2 + 20} ${yb - 26}`} fill="none" stroke={C.destaque} strokeWidth={8} opacity={v > .95 ? 1 : 0} />
            {p.nos[i + 1].seta && <text x={b.w / 2 + 34} y={(ya + yb) / 2 + 10} fill="#fff" style={{ font: `700 26px ${FD(c)}`, textTransform: 'uppercase' } as any}>{p.nos[i + 1].seta}</text>}
          </g>;
        })}
      </svg>
      {p.nos.map((no: any, i: number) => {
        const v = aparece(c, no.t ?? c.L.t0);
        return <div key={i} style={{ position: 'absolute', left: (b.w - (p.largura || 640)) / 2, top: yN(i) + (1 - v) * 16, width: p.largura || 640, height: hN, opacity: v,
          background: no.destaque ? C.destaque : C.papel, color: C.tinta, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center',
          boxShadow: '0 12px 32px rgba(0,0,0,.45)' }}>
          <div style={{ fontFamily: FT(c), fontWeight: 900, fontSize: 38, textTransform: 'uppercase', lineHeight: 1 }}>{no.rotulo}</div>
          {no.sub && <div style={{ fontFamily: FD(c), fontWeight: 700, fontSize: 22, marginTop: 6, textTransform: 'uppercase' }}>{no.sub}</div>}
        </div>;
      })}
    </div>);
};

// 12. editorial.titleOrPayoff — pergunta/payoff curto (≤ 3 linhas, entra palavra a palavra); nunca slide longo
export const Title: React.FC<{ c: Ctx }> = ({ c }) => {
  const p = c.L.p, C = cores(c), b = c.L.caixa;
  return (
    <div style={{ position: 'absolute', left: b.x, top: b.y, width: b.w, height: b.h, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', gap: 6 }}>
      {p.linhas.map((l: any, i: number) => {
        const k = aparece(c, l.t ?? c.L.t0 + i * .35, .35);
        return <div key={i} style={{ fontFamily: FT(c), fontWeight: 900, fontSize: l.tamanho || 104, lineHeight: 1, textTransform: 'uppercase', textAlign: 'center',
          color: l.destaque ? C.destaque : '#fff', textShadow: '0 6px 26px rgba(0,0,0,.75)', opacity: k, transform: `translateY(${(1 - k) * 30}px) scale(${lerp(1.08, 1, k)})` }}>{l.texto}</div>;
      })}
    </div>);
};

export const PRIMITIVAS: Record<string, React.FC<{ c: Ctx }>> = {
  'editorial.statCard': StatCard, 'editorial.peopleCard': PeopleCard, 'editorial.hierarchy': Hierarchy, 'editorial.timeline': Timeline,
  'dossie.documentCard': DocumentCard, 'dossie.evidenceHighlight': Evidence, 'editorial.comparison': Comparison,
  'editorial.flowConnections': Flow, 'editorial.titleOrPayoff': Title,
};
