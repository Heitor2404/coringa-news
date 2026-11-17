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
const MESES = ['JANEIRO', 'FEVEREIRO', 'MARÇO', 'ABRIL', 'MAIO', 'JUNHO', 'JULHO', 'AGOSTO', 'SETEMBRO', 'OUTUBRO', 'NOVEMBRO', 'DEZEMBRO'];
// rótulo obrigatório de reconstrução editorial (F-RECONSTRUCAO): o objeto é do Coringa, não um arquivo histórico
export const Reconstrucao: React.FC<{ c: Ctx; txt: string; cor?: string }> = ({ c, txt, cor }) => (
  <div data-meta="reconstrucao" style={{ fontFamily: FD(c), fontWeight: 700, fontSize: 19, letterSpacing: 1.5, color: cor || 'rgba(11,15,23,.62)', textTransform: 'uppercase', whiteSpace: 'nowrap' }}>{txt}</div>);

// calendário REAL do mês (dia da semana calculado), o dia citado é circulado na palavra que o pede
export const Calendario: React.FC<{ c: Ctx }> = ({ c }) => {
  const p = c.L.p, C = cores(c), b = c.L.caixa;
  const ini = new Date(Date.UTC(p.ano, p.mes - 1, 1)).getUTCDay(), dias = new Date(Date.UTC(p.ano, p.mes, 0)).getUTCDate();
  const w = Math.min(b.w, b.h * .98), x0 = b.x + (b.w - w) / 2, cel = (w - 80) / 7;
  const km = p.t_marca != null ? easeOut((c.t - p.t_marca) / .45) : 0;
  const L = 2 * Math.PI * cel * .58;
  return (
    <div style={{ position: 'absolute', left: x0, top: b.y, width: w, background: '#F3EEE2', boxShadow: '0 34px 80px rgba(0,0,0,.7)',
      transform: `translateY(${(1 - c.k) * 40}px) rotate(${p.inclina ?? -1.5}deg)`, padding: '0 40px 26px' }}>
      <div style={{ height: 34, margin: '0 -40px', background: '#2A2A2E', display: 'flex', justifyContent: 'space-around', alignItems: 'center' }}>
        {Array.from({ length: 9 }).map((_, i) => <div key={i} style={{ width: 16, height: 16, borderRadius: 8, background: '#0A0A0C', boxShadow: 'inset 0 2px 3px #000' }} />)}</div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', padding: '22px 0 10px', borderBottom: `3px solid ${C.tinta}` }}>
        <div style={{ fontFamily: FT(c), fontWeight: 900, fontSize: 64, color: C.tinta }}>{MESES[p.mes - 1]}</div>
        <div style={{ fontFamily: FD(c), fontWeight: 700, fontSize: 56, color: C.alerta }}>{p.ano}</div></div>
      <div style={{ display: 'grid', gridTemplateColumns: `repeat(7, ${cel}px)`, marginTop: 10 }}>
        {['D', 'S', 'T', 'Q', 'Q', 'S', 'S'].map((d, i) => <div key={i} style={{ textAlign: 'center', fontFamily: FD(c), fontWeight: 700, fontSize: 26, color: i === 0 ? C.alerta : 'rgba(11,15,23,.6)', padding: '6px 0' }}>{d}</div>)}
        {Array.from({ length: ini }).map((_, i) => <div key={'v' + i} />)}
        {Array.from({ length: dias }).map((_, i) => {
          const d = i + 1, alvo = d === p.dia;
          return <div key={d} style={{ position: 'relative', height: cel * .82, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FT(c), fontWeight: alvo ? 900 : 700,
            fontSize: alvo ? 44 : 34, color: alvo ? C.tinta : 'rgba(11,15,23,.55)', borderTop: '1px solid rgba(11,15,23,.12)' }}>{d}
            {alvo && km > 0 && <svg style={{ position: 'absolute', left: -12, top: -14, overflow: 'visible' }} width={cel + 24} height={cel * .82 + 28}>
              <ellipse cx={(cel + 24) / 2} cy={(cel * .82 + 28) / 2} rx={cel * .5} ry={cel * .44} fill="none" stroke={C.alerta} strokeWidth={7} strokeLinecap="round"
                strokeDasharray={L} strokeDashoffset={L * (1 - km)} transform={`rotate(-8 ${(cel + 24) / 2} ${(cel * .82 + 28) / 2})`} /></svg>}
          </div>;
        })}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 16 }}>
        <div style={{ fontFamily: FD(c), fontWeight: 700, fontSize: 28, color: C.tinta, opacity: km }}>{p.nota || ''}</div>
        <Reconstrucao c={c} txt={p.reconstrucao} /></div>
    </div>);
};

// ficha de arquivo (index card): campos que entram na palavra, prova fotográfica REAL presa com clipe e carimbo de
// conclusão. A ficha é reconstrução editorial (rótulo visível); a foto presa é arquivo real com crédito.
export const Ficha: React.FC<{ c: Ctx }> = ({ c }) => {
  const p = c.L.p, C = cores(c), b = c.L.caixa, im = p.asset ? c.P.imagens?.[p.asset] : null;
  const ny = 96 + 18 + (p.campos || []).length * 98;
  const fw = Math.min(340, b.w * .38), fh = im ? fw * im.h / im.w : 0;
  const kc = p.carimbo ? easeOut((c.t - p.carimbo.t) / .3) : 0;
  return (
    <div style={{ position: 'absolute', left: b.x, top: b.y, width: b.w, height: b.h, background: '#F5F1E6', boxShadow: '0 30px 70px rgba(0,0,0,.65)',
      transform: `translateY(${(1 - c.k) * 36}px) rotate(${p.inclina ?? 1.0}deg)`,
      backgroundImage: 'repeating-linear-gradient(180deg, rgba(0,0,0,0) 0 97px, rgba(63,120,200,.22) 97px 99px)', backgroundPosition: '0 114px' }}>
      <div style={{ height: 96, borderBottom: `4px solid ${C.alerta}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 40px' }}>
        <div style={{ fontFamily: FT(c), fontWeight: 900, fontSize: 46, color: C.tinta, textTransform: 'uppercase', whiteSpace: 'nowrap' }}>{p.titulo}</div>
        <div style={{ fontFamily: FD(c), fontWeight: 700, fontSize: 30, color: C.alerta, whiteSpace: 'nowrap' }}>{p.numero || ''}</div></div>
      <div style={{ padding: '18px 40px 0' }}>
        {(p.campos || []).map((f: any, i: number) => {
          const v = f.t != null ? easeOut((c.t - f.t) / .35) : 1;
          return <div key={i} style={{ height: 98, opacity: v, transform: `translateX(${(1 - v) * 14}px)` }}>
            <div style={{ fontFamily: FD(c), fontWeight: 700, fontSize: 26, color: 'rgba(11,15,23,.58)', textTransform: 'uppercase', whiteSpace: 'nowrap' }}>{f.rotulo}</div>
            <div style={{ fontFamily: FT(c), fontWeight: 800, fontSize: 42, lineHeight: 1.15, color: f.destaque ? C.alerta : C.tinta, textTransform: 'uppercase', whiteSpace: 'nowrap' }}>{f.valor}</div></div>;
        })}
      </div>
      {im && <div style={{ position: 'absolute', right: 34, top: ny + 4, width: fw + 20, padding: 10, background: '#F6F3EC', boxShadow: '0 16px 36px rgba(0,0,0,.5)', transform: 'rotate(2.2deg)' }}>
        <Img src={staticFile(im.src)} style={{ width: fw, height: fh, display: 'block', filter: 'contrast(1.05)' }} />
        {(p.meta || []).map((m: string, i: number) => <div key={i} data-meta="credito" style={{ fontFamily: FD(c), fontSize: 19, lineHeight: '24px', color: 'rgba(11,15,23,.8)', marginTop: i ? 0 : 6, width: fw }}>{m}</div>)}
        <div style={{ position: 'absolute', left: 30, top: -18, width: 28, height: 74, border: '5px solid #B9BEC6', borderRadius: 14, borderBottomColor: 'transparent' }} /></div>}
      {p.carimbo && kc > 0 && <div style={{ position: 'absolute', left: 44, top: ny + 60, padding: '10px 26px', border: `8px solid ${C.alerta}`, color: C.alerta, fontFamily: FT(c), fontWeight: 900,
        fontSize: 70, letterSpacing: 4, transform: `rotate(-9deg) scale(${lerp(1.6, 1, kc)})`, opacity: kc, whiteSpace: 'nowrap', mixBlendMode: 'multiply' }}>{p.carimbo.texto}</div>}
      <div style={{ position: 'absolute', left: 40, bottom: 18 }}><Reconstrucao c={c} txt={p.reconstrucao} /></div>
    </div>);
};

export const StatCard: React.FC<{ c: Ctx }> = ({ c }) => {
  const p = c.L.p, C = cores(c), b = c.L.caixa;
  if (p.estilo === 'calendario') return <Calendario c={c} />;
  if (p.estilo === 'ficha') return <Ficha c={c} />;
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
  const embaixo = p.rotulos_abaixo !== false && n > 5;          // muitos níveis: nomes embaixo, em 2 fileiras (≥ 26 px)
  const hb = (p.legenda_base ? b.h - 46 : b.h) - (embaixo ? 84 : 0);   // a legenda da base fica DENTRO da caixa
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
            {!embaixo && <div style={{ fontFamily: FD(c), fontWeight: 700, fontSize: w > 150 ? 26 : w > 110 ? 22 : 20, textTransform: 'uppercase', textAlign: 'center', marginTop: 6, padding: '0 6px', lineHeight: 1.15 }}>{nv.rotulo}</div>}
          </div>);
      })}
      {embaixo && p.niveis.map((nv: any, i: number) => {
        const ent = aparece(c, c.L.t0 + i * (p.cadencia ?? .18));
        const ativo = (nv.t != null && c.t >= nv.t) || (p.ativo || []).some((a: any) => c.t >= a.t0 && (a.t1 == null || c.t < a.t1) && a.i === i);
        const cx = i * (w + gap) + w / 2, fila = i % 2;
        return <React.Fragment key={'r' + i}>
          <div style={{ position: 'absolute', left: cx - 1.5, top: hb, width: 3, height: 8 + fila * 38, background: ativo ? C.destaque : 'rgba(255,255,255,.45)', opacity: ent }} />
          <div style={{ position: 'absolute', left: cx - 110, width: 220, top: hb + 8 + fila * 38, textAlign: 'center', fontFamily: FD(c), fontWeight: 700, fontSize: 26,
            color: ativo ? C.destaque : '#F4F1EA', textTransform: 'uppercase', whiteSpace: 'nowrap', textShadow: '0 2px 8px #000', opacity: ent }}>{nv.rotulo}</div>
        </React.Fragment>;
      })}
      {p.legenda_base && <div style={{ position: 'absolute', left: 0, right: 0, top: hb + (embaixo ? 92 : 12), textAlign: 'center', fontFamily: FD(c), fontWeight: 700, fontSize: 26,
        color: '#fff', letterSpacing: 2, textTransform: 'uppercase', textShadow: '0 2px 8px #000', opacity: aparece(c, p.legenda_t ?? c.L.t0 + .6) }}>{p.legenda_base}</div>}
    </div>);
};

// 7. editorial.timeline — linha com marcos que aparecem na ordem; o marco atual fica em destaque
// régua PROPORCIONAL: a distância entre marcos é a distância real em anos; evidências presas no ano por um fio.
export const Regua: React.FC<{ c: Ctx }> = ({ c }) => {
  const p = c.L.p, C = cores(c), b = c.L.caixa;
  const a0 = p.inicio, a1 = p.fim, x0 = 50, x1 = b.w - 50, yL = b.h * .5;
  const X = (a: number) => x0 + (x1 - x0) * (a - a0) / (a1 - a0);
  const kL = easeOut((c.t - c.L.t0) / 1.0);
  const kt = p.t_total != null ? easeOut((c.t - p.t_total) / .6) : 0;
  const foto = 196;
  return (
    <div style={{ position: 'absolute', left: b.x, top: b.y, width: b.w, height: b.h }}>
      {/* régua de madeira clara com marcas de ano (a cada 1; rótulo a cada 5) */}
      <div style={{ position: 'absolute', left: x0 - 30, top: yL - 6, width: (x1 - x0 + 60) * kL, height: 92, background: 'linear-gradient(180deg,#E7D6AE,#CDB685)', boxShadow: '0 18px 40px rgba(0,0,0,.6)', borderRadius: 4 }} />
      {Array.from({ length: a1 - a0 + 1 }).map((_, i) => {
        const a = a0 + i, x = X(a), v = clamp((kL * (x1 - x0 + 60) - (x - x0 + 30)) / 40);
        return <React.Fragment key={a}>
          <div style={{ position: 'absolute', left: x - 1.5, top: yL - 6, width: 3, height: a % 5 === 0 ? 38 : 20, background: '#3A2C18', opacity: v }} />
          {(a % 5 === 0 && a1 - a >= 3) || a === a1 || a === a0 ? <div style={{ position: 'absolute', left: x - 60, width: 120, top: yL + 40, textAlign: 'center', fontFamily: FD(c), fontWeight: 700, fontSize: 26, color: '#3A2C18', opacity: v }}>{a}</div> : null}
        </React.Fragment>;
      })}
      {p.marcos.map((m: any, i: number) => {
        const v = easeOut((c.t - (m.t ?? c.L.t0)) / .45), x = X(m.ano), im = m.asset ? c.P.imagens?.[m.asset] : null;
        const lin = m.linha ?? 0, topo = 10 + lin * 12, cx = clamp(x + (m.desloca || 0), foto / 2 + 6, b.w - foto / 2 - 6);
        const ativo = (p.ativos || []).some((a: any) => a.i === i && c.t >= a.t);
        return <React.Fragment key={i}>
          <svg style={{ position: 'absolute', left: 0, top: 0, overflow: 'visible', opacity: v }} width={b.w} height={b.h}>
            <line x1={cx} y1={topo + foto + 40} x2={x} y2={yL - 6} stroke={ativo ? C.destaque : '#D9D2C2'} strokeWidth={ativo ? 6 : 4} />
            <circle cx={x} cy={yL - 6} r={ativo ? 13 : 10} fill={ativo ? C.destaque : C.alerta} stroke="#1E160C" strokeWidth={4} /></svg>
          <div style={{ position: 'absolute', left: cx - foto / 2, top: topo + (1 - v) * 30, width: foto, opacity: v, background: '#F6F3EC', padding: 10,
            boxShadow: ativo ? `0 0 0 6px ${C.destaque}, 0 20px 40px rgba(0,0,0,.6)` : '0 20px 40px rgba(0,0,0,.6)', transform: `rotate(${(i % 2 ? 2 : -2)}deg)` }}>
            {im && <Img src={staticFile(im.src)} style={{ width: foto - 20, height: (foto - 20) * .74, objectFit: 'cover', display: 'block' }} />}
            <div style={{ fontFamily: FT(c), fontWeight: 900, fontSize: 38, color: C.tinta, marginTop: 6, lineHeight: 1 }}>{m.ano}</div>
            <div style={{ fontFamily: FD(c), fontWeight: 700, fontSize: 21, color: 'rgba(11,15,23,.75)', textTransform: 'uppercase', marginTop: 4, lineHeight: 1.15 }}>{m.texto}</div>
          </div>
        </React.Fragment>;
      })}
      {/* chave do intervalo total: o número com contexto (34 anos = a régua inteira) */}
      <div style={{ position: 'absolute', left: x0, top: yL + 104, width: (x1 - x0) * kt, height: 26, borderLeft: `5px solid ${C.destaque}`, borderRight: kt > .98 ? `5px solid ${C.destaque}` : undefined,
        borderBottom: `5px solid ${C.destaque}`, opacity: kt }} />
      <div style={{ position: 'absolute', left: 0, width: b.w, top: yL + 142, textAlign: 'center', opacity: kt, transform: `scale(${lerp(1.15, 1, kt)})` }}>
        <span style={{ fontFamily: FT(c), fontWeight: 900, fontSize: 120, color: C.destaque, lineHeight: 1, textShadow: '0 8px 30px rgba(0,0,0,.7)' }}>{p.total}</span>
        {p.total_rotulo && <div style={{ fontFamily: FT(c), fontWeight: 800, fontSize: 36, color: '#F4F1EA', textTransform: 'uppercase', marginTop: 6, textShadow: '0 4px 14px #000' }}>{p.total_rotulo}</div>}
      </div>
      <div style={{ position: 'absolute', left: 0, width: b.w, textAlign: 'center', top: b.h - 28 }}><Reconstrucao c={c} txt={p.reconstrucao} cor="rgba(244,241,234,.55)" /></div>
    </div>);
};

export const Timeline: React.FC<{ c: Ctx }> = ({ c }) => {
  if (c.L.p.estilo === 'regua') return <Regua c={c} />;
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

// 8. dossie.documentCard — registro/documento/foto REAL com proveniência; recorte (zoom) só se ampliar ≥ 1,5× (ERR-055).
// estilos: 'registro' (papel claro), 'foto' (cópia fotográfica com fita e carimbo de data), 'documento' (o papel é a
// própria imagem: sombra e clipe), 'pasta' (capa do dossiê com a primeira evidência aparecendo). A geometria (borda 18,
// cabeçalho 52, rodapé 22 + 36/linha) é a MESMA de plano.geom_documento: marcações miram o trecho certo da imagem.
const Fita: React.FC<{ x: number; y: number; r: number }> = ({ x, y, r }) => (
  <div style={{ position: 'absolute', left: x, top: y, width: 150, height: 40, background: 'rgba(232,222,196,.72)', transform: `rotate(${r}deg)`,
    boxShadow: '0 2px 6px rgba(0,0,0,.25)', mixBlendMode: 'normal' }} />);

export const Pasta: React.FC<{ c: Ctx }> = ({ c }) => {
  const p = c.L.p, C = cores(c), b = c.L.caixa, im = c.P.imagens?.[p.asset];
  const abre = easeOut((c.t - (p.t_abre ?? c.L.t0 + .5)) / .9);
  const fw = b.w * .78, fh = im ? Math.min(b.h * .62, fw * im.h / im.w) : b.h * .5;
  return (
    <div style={{ position: 'absolute', left: b.x, top: b.y, width: b.w, height: b.h, transform: `translateY(${(1 - c.k) * 40}px) rotate(${p.inclina ?? -2}deg)` }}>
      <div style={{ position: 'absolute', left: 0, top: 70, width: b.w, height: b.h - 70, background: '#B8955A', borderRadius: 10, boxShadow: '0 40px 80px rgba(0,0,0,.7)' }} />
      <div style={{ position: 'absolute', left: b.w - 380, top: 22, width: 330, height: 70, background: '#B8955A', borderRadius: '12px 12px 0 0', padding: '14px 24px',
        fontFamily: FD(c), fontWeight: 700, fontSize: 26, color: '#2B2113', letterSpacing: 2, textTransform: 'uppercase' }}>{p.aba || 'DOSSIÊ'}</div>
      {im && <div style={{ position: 'absolute', left: (b.w - fw) / 2 - 60, top: Math.max(18, 120 - abre * (fh * .55)), width: fw, height: fh, padding: 14, background: '#F4F1EA',
        boxShadow: '0 16px 40px rgba(0,0,0,.55)', transform: `rotate(${2.5 - abre * 1.5}deg)` }}>
        <Img src={staticFile(im.src)} style={{ width: '100%', height: '100%', objectFit: 'cover', filter: 'sepia(.2) contrast(1.05)' }} /></div>}
      <div style={{ position: 'absolute', left: 0, top: b.h * .44, width: b.w, height: b.h * .56, background: 'linear-gradient(180deg, #C9A66A 0%, #BD9A5F 100%)', borderRadius: '6px 6px 10px 10px',
        boxShadow: '0 -10px 30px rgba(0,0,0,.35)', padding: '40px 56px' }}>
        <div style={{ display: 'inline-block', padding: '8px 18px', border: `4px solid ${C.alerta}`, color: C.alerta, fontFamily: FD(c), fontWeight: 700, fontSize: 26, letterSpacing: 3,
          transform: 'rotate(-3deg)', opacity: .9 }}>{p.selo || 'ARQUIVO'}</div>
        <div style={{ marginTop: 26, fontFamily: FT(c), fontWeight: 900, fontSize: 64, lineHeight: 1, color: '#1E160C', textTransform: 'uppercase' }}>{p.titulo}</div>
        {p.sub && <div style={{ marginTop: 12, fontFamily: FD(c), fontWeight: 700, fontSize: 30, color: '#3A2C18', letterSpacing: 2 }}>{p.sub}</div>}
      </div>
      {im && p.meta && <div data-meta="credito" style={{ position: 'absolute', left: 56, right: 40, top: b.h - 34 - 26 * p.meta.length, fontFamily: FD(c), fontSize: 20, lineHeight: '26px', color: '#3A2C18' }}>
        {p.meta.map((m: string, i: number) => <div key={i}>{m}</div>)}</div>}
    </div>);
};

export const DocumentCard: React.FC<{ c: Ctx }> = ({ c }) => {
  const p = c.L.p, C = cores(c), b = c.L.caixa, im = c.P.imagens?.[p.asset];
  if (!im) return null;
  if (p.estilo === 'pasta') return <Pasta c={c} />;
  const meta = p.meta || [];
  const cab = p.cabecalho ? 52 : 0, rod = 22 + meta.length * 36;
  const maxW = b.w - 36, maxH = b.h - cab - rod - 36;
  const esc = Math.min(maxW / im.w, maxH / im.h);
  const fw = im.w * esc, fh = im.h * esc;
  const z = p.zoom && c.t >= p.zoom.t0 ? lerp(1, p.zoom.escala, easeOut((c.t - p.zoom.t0) / (p.zoom.dur || 1.4))) : 1;
  const foco = p.zoom?.foco || [.5, .5];
  const est = p.estilo || 'registro';
  const fundo = est === 'documento' ? 'rgba(244,239,228,.0)' : est === 'foto' ? '#F6F3EC' : C.papel;
  const inc = p.inclina ?? (est === 'foto' ? -1.2 : est === 'documento' ? .6 : -1.2);
  const carimbo = p.data_carimbo && c.t >= (p.t_carimbo ?? c.L.t0 + .5) ? easeOut((c.t - (p.t_carimbo ?? c.L.t0 + .5)) / .3) : 0;
  return (
    <div style={{ position: 'absolute', left: b.x + (b.w - fw - 36) / 2, top: b.y + (b.h - fh - cab - rod - 36) / 2, width: fw + 36, padding: 18,
      background: fundo, boxShadow: est === 'documento' ? 'none' : '0 30px 70px rgba(0,0,0,.65), 0 2px 0 rgba(255,255,255,.4) inset',
      transform: `translateY(${(1 - c.k) * 36}px) rotate(${inc}deg)` }}>
      {cab > 0 && <div style={{ height: cab, display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontFamily: FD(c), fontWeight: 700, fontSize: 24,
        color: C.tinta, letterSpacing: 2, textTransform: 'uppercase', borderBottom: `2px solid ${C.tinta}`, marginBottom: 12 }}>
        <span>{p.cabecalho}</span><span style={{ color: C.alerta }}>{p.cabecalho_dir || ''}</span></div>}
      <div style={{ width: fw, height: fh, overflow: 'hidden', position: 'relative', background: '#111',
        boxShadow: est === 'documento' ? '0 34px 80px rgba(0,0,0,.7), 0 8px 18px rgba(0,0,0,.45)' : 'none' }}>
        <Img src={staticFile(im.src)} style={{ width: fw, height: fh, transform: `scale(${z})`, transformOrigin: `${foco[0] * 100}% ${foco[1] * 100}%`,
          filter: p.sepia ? 'sepia(.25) contrast(1.05)' : 'contrast(1.04)' }} />
        {/* luz da luminária sobre o papel (mesma direção da mesa) */}
        <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(160deg, rgba(255,236,200,.10) 0%, rgba(0,0,0,0) 45%, rgba(0,0,0,.16) 100%)' }} />
      </div>
      {est === 'foto' && <><Fita x={-18} y={20} r={-22} /><Fita x={fw - 96} y={20} r={20} /></>}
      {est === 'documento' && <div style={{ position: 'absolute', left: 60, top: -10, width: 34, height: 96, border: '5px solid #B9BEC6', borderRadius: 18, borderBottomColor: 'transparent',
        boxShadow: '0 3px 6px rgba(0,0,0,.4)' }} />}
      <div style={{ paddingTop: 14, ...(est === 'documento' ? { marginTop: 14, padding: '10px 16px', background: C.papel, display: 'inline-block', boxShadow: '0 10px 24px rgba(0,0,0,.5)' } : {}) }}>
        {meta.map((m: string, i: number) => <div key={i} data-linha={i} data-meta={i === meta.length - 1 ? 'credito' : undefined} style={{ fontFamily: FD(c), fontSize: 24, lineHeight: '36px', color: C.tinta,
          whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', fontWeight: i === 0 ? 700 : 400 }}>{m}</div>)}
      </div>
      {carimbo > 0 && <div style={{ position: 'absolute', right: 30, top: cab + 40, padding: '8px 18px', border: `5px solid ${C.alerta}`, color: C.alerta, fontFamily: FD(c), fontWeight: 700,
        fontSize: 34, letterSpacing: 2, transform: `rotate(-7deg) scale(${lerp(1.5, 1, carimbo)})`, opacity: carimbo, background: 'rgba(246,243,236,.82)' }}>{p.data_carimbo}</div>}
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
          {no.sub && <div style={{ fontFamily: FD(c), fontWeight: 700, fontSize: 26, marginTop: 6, textTransform: 'uppercase' }}>{no.sub}</div>}
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
