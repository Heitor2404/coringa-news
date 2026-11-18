// PRIMITIVAS EDITORIAIS (12 com o palco). Cada uma desenha DENTRO da caixa recebida (slot calculado no Python), com
// entrada/saída determinísticas (tokens.tempo) e tamanhos mínimos para celular. Nada de efeito decorativo: cada
// primitiva revela uma informação (número, nível, data, documento, relação, comparação).
import React from 'react';
import { Img, staticFile } from 'remotion';
import { FS, clamp, lerp } from '../ident';
import type { Camada, FormatoProps } from './tipos';
import { cameraEm, mercX, mercY } from './Palco';

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

// CARTÃO DE DADO — design system único (tokens canal.cartao): sem inclinação, centralizado no slot, largura pelo conteúdo
// (entre largura_min e o slot), número que encolhe para caber (≥ numero_min_px), hierarquia título → número → rótulo →
// fonte factual (independente dos créditos do mapa). data-cartao = centro do slot (alinhamento conferido no quadro).
const KT = (c: Ctx) => ({ pad_x: 40, pad_y: 26, borda_topo: 10, titulo_px: 26, numero_px: 112, numero_min_px: 60, unidade_razao: .46, rotulo_px: 32, fonte_px: 18,
  largura_min: 520, entra_px: 24, sombra: '0 18px 50px rgba(0,0,0,.5)', borda_px: 0, borda_cor: 'transparent', raio_px: 0,
  titulo_cor: '', numero_cor: '', rotulo_cor: '',
  ...((c.P.tokens as any).cartao || {}), ...(c.P.formato === 'atlas' ? ((c.P.tokens as any).cartao_atlas || {}) : {}) });
export const larguraTxt = (s: string, px: number, k = .7) => s.length * px * k;
export const Cartao: React.FC<{ c: Ctx; largura: number; children: React.ReactNode }> = ({ c, largura, children }) => {
  const b = c.L.caixa, T = KT(c), C = cores(c);
  const w = Math.max(Math.min(T.largura_min, b.w), Math.min(b.w, largura));
  return (
    <div style={{ position: 'absolute', left: b.x, top: b.y, width: b.w, height: b.h, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
      <div data-cartao={JSON.stringify([b.x + b.w / 2, b.y + b.h / 2])} style={{ width: w, padding: `${T.pad_y}px ${T.pad_x}px`, background: C.papel, color: C.tinta,
        boxShadow: T.sombra, borderTop: `${T.borda_topo}px solid ${C.destaque}`, borderLeft: `${T.borda_px}px solid ${T.borda_cor}`,
        borderRight: `${T.borda_px}px solid ${T.borda_cor}`, borderBottom: `${T.borda_px}px solid ${T.borda_cor}`,
        borderRadius: T.raio_px, transform: `translateY(${(1 - c.k) * T.entra_px}px)`, boxSizing: 'border-box' }}>{children}</div>
    </div>);
};
const Fonte: React.FC<{ c: Ctx }> = ({ c }) => c.L.p.fonte ? <div data-meta="fonte" style={{ fontFamily: FD(c), fontSize: KT(c).fonte_px, marginTop: 12, color: 'rgba(11,15,23,.62)',
  textTransform: 'uppercase', letterSpacing: 1 }}>FONTE: {c.L.p.fonte}</div> : null;

export const StatCard: React.FC<{ c: Ctx }> = ({ c }) => {
  const p = c.L.p, C = cores(c), b = c.L.caixa, T = KT(c);
  if (p.estilo === 'calendario') return <Calendario c={c} />;
  if (p.estilo === 'ficha') return <Ficha c={c} />;
  if (p.estilo === 'dial') return <Dial c={c} />;
  if (p.estilo === 'cedula') return <Cedula c={c} />;
  if (p.estilo === 'selo') return <Selo c={c} />;
  const conta = p.contagem && typeof p.valor === 'number' ? p.valor * easeOut((c.t - c.L.t0) / (p.dur_contagem || 1.2)) : p.valor;
  const txt = typeof conta === 'number' ? num(conta, p.casas || 0) : String(p.valor);
  if (p.estilo === 'pilula') return (
    <div style={{ position: 'absolute', left: b.x, top: b.y, width: b.w, height: b.h, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
      <div data-cartao={JSON.stringify([b.x + b.w / 2, b.y + b.h / 2])} style={{ padding: '14px 30px', background: C.papel, color: C.tinta, fontFamily: FT(c), fontWeight: 900, textTransform: 'uppercase',
        // corpo encolhe 40 → 30 px para caber na faixa (MESMA conta de plano._cabe)
        fontSize: Math.max(30, Math.min(40, 40 * (b.w - 60) / Math.max(1, larguraTxt(`${p.prefixo || ''}${txt}`, 40, .62) + larguraTxt(p.unidade ? ` ${p.unidade}` : '', 40, .72) + larguraTxt(p.rotulo ? ` · ${p.rotulo}` : '', 40, .66)))),
        boxShadow: '0 10px 30px rgba(0,0,0,.45)', transform: `translateY(${(1 - c.k) * 18}px)`, whiteSpace: 'nowrap', maxWidth: b.w, overflow: 'hidden', textOverflow: 'ellipsis' }}>
        <span style={{ fontFamily: FD(c), fontWeight: 700 }}>{p.prefixo || ''}{txt}</span>{p.unidade ? ` ${p.unidade}` : ''}{p.rotulo ? <span style={{ fontWeight: 700, opacity: .75 }}> · {p.rotulo}</span> : null}
      </div>
    </div>);
  // número final (não o da contagem) define o tamanho: o cartão não "respira" enquanto conta
  const fim = `${p.prefixo || ''}${typeof p.valor === 'number' ? num(p.valor, p.casas || 0) : p.valor}`;
  const util = b.w - 2 * T.pad_x;
  const npx = Math.max(T.numero_min_px, Math.min(T.numero_px, util / (larguraTxt(fim, 1, .7) + larguraTxt(` ${p.unidade || ''}`, T.unidade_razao, .7))));
  const larg = 2 * T.pad_x + Math.max(larguraTxt(fim, npx, .7) + larguraTxt(` ${p.unidade || ''}`, npx * T.unidade_razao, .7),
    larguraTxt(p.titulo || '', T.titulo_px, .62), Math.min(util, larguraTxt(p.rotulo || '', T.rotulo_px, .66)));
  return (
    <Cartao c={c} largura={larg}>
      {p.titulo && <div style={{ fontFamily: FD(c), fontWeight: 700, fontSize: T.titulo_px, letterSpacing: 3, textTransform: 'uppercase', color: T.titulo_cor || C.alerta, marginBottom: 6 }}>{p.titulo}</div>}
      <div style={{ fontFamily: FT(c), fontWeight: 900, fontSize: npx, lineHeight: .95, whiteSpace: 'nowrap', color: T.numero_cor || C.tinta }}>
        {p.prefixo || ''}{txt}<span style={{ fontSize: npx * T.unidade_razao, fontWeight: 800, marginLeft: 12 }}>{p.unidade || ''}</span></div>
      {p.rotulo && <div style={{ fontFamily: FT(c), fontWeight: 800, fontSize: T.rotulo_px, textTransform: 'uppercase', marginTop: 10, lineHeight: 1.1, color: T.rotulo_cor || C.tinta }}>{p.rotulo}</div>}
      <Fonte c={c} />
    </Cartao>);
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
  const n = p.niveis.length, gap = 14, prof = 12, w = (b.w - prof - gap * (n - 1)) / n;
  const embaixo = p.rotulos_abaixo !== false && n > 5;          // muitos níveis: nomes embaixo, em 2 fileiras (≥ 26 px)
  const hb = (p.legenda_base ? b.h - 46 : b.h) - (embaixo ? 84 : 0);   // a legenda da base fica DENTRO da caixa
  // altura mínima do bloco: a da escada baixa na faixa superior, mas NUNCA menor que o conteúdo (valor + nome dentro do bloco)
  const wb = (b.w - prof - gap * (n - 1)) / n;
  const conteudo = embaixo ? 0 : 14 + (p.niveis.some((x: any) => x.valor != null) ? (wb > 150 ? 54 : 40) + 6 : 0) + 2 * (wb > 150 ? 26 : 22) * 1.15 + 10;
  const base = Math.min(Math.max(Math.min(120, hb * .25), conteudo), hb - prof - 10);
  const passo = (hb - base - prof - 40) / Math.max(1, n - 1) * (p.escada === false ? 0 : 1);
  const ativoEm = (i: number) => {
    const nv = p.niveis[i];
    const ts = [nv.t, ...(p.ativo || []).filter((a: any) => a.i === i && c.t >= a.t0 && (a.t1 == null || c.t < a.t1)).map((a: any) => a.t0)].filter((x: any) => x != null && c.t >= x);
    return ts.length ? Math.max(...ts) : null;
  };
  const alt = (i: number) => (p.alturas ? base + p.alturas[i] * (hb - base - prof - 40) : base + i * passo);
  const xs = (i: number) => i * (w + gap);
  // salto (referência: seta que pula para o nível que acende): do último nível aceso ao novo, por 1,2 s
  const acesos = p.niveis.map((_: any, i: number) => ({ i, t: ativoEm(i) })).filter((a: any) => a.t != null).sort((a: any, z: any) => a.t - z.t);
  const novo = acesos[acesos.length - 1], ant = acesos[acesos.length - 2];
  const ks = novo && ant && novo.i !== ant.i ? clamp((c.t - novo.t) / .55) * clamp((novo.t + 1.6 - c.t) / .4) : 0;
  return (
    <div style={{ position: 'absolute', left: b.x, top: b.y, width: b.w, height: b.h }}>
      {p.niveis.map((nv: any, i: number) => {
        const ent = aparece(c, c.L.t0 + i * (p.cadencia ?? .18));
        const ativo = ativoEm(i) != null;
        const altura = alt(i), topo = hb - altura;
        const face = ativo ? C.destaque : C.papel, lado = ativo ? C.destaque_escuro : '#BDB6A6', cima = ativo ? '#FFE680' : '#FFFDF6';
        return (
          <div key={i} style={{ position: 'absolute', left: xs(i), top: topo + (1 - ent) * 40, width: w + prof, height: altura + prof, opacity: ent,
            filter: 'drop-shadow(0 16px 22px rgba(0,0,0,.5))' }}>
            <div style={{ position: 'absolute', left: prof / 2, top: 0, width: w, height: prof, background: cima, transform: 'skewX(-45deg)', transformOrigin: '0 100%' }} />
            <div style={{ position: 'absolute', left: w, top: prof / 2, width: prof, height: altura, background: lado, transform: 'skewY(-45deg)', transformOrigin: '0 0' }} />
            <div style={{ position: 'absolute', left: 0, top: prof, width: w, height: altura, background: face, color: C.tinta,
              display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: 14 }}>
              {nv.valor != null && <div style={{ fontFamily: FT(c), fontWeight: 900, fontSize: w > 150 ? 54 : 40, lineHeight: 1 }}>{nv.valor}</div>}
              {!embaixo && <div style={{ fontFamily: FD(c), fontWeight: 700, fontSize: w > 150 ? 26 : w > 110 ? 22 : 20, textTransform: 'uppercase', textAlign: 'center', marginTop: 6, padding: '0 6px', lineHeight: 1.15 }}>{nv.rotulo}</div>}
            </div>
          </div>);
      })}
      {ks > 0 && (() => {
        const x0 = xs(ant.i) + w / 2, y0 = hb - alt(ant.i) - 8, x1 = xs(novo.i) + w / 2, y1 = hb - alt(novo.i) - 8;
        const yc = Math.min(y0, y1) - 70, d = `M${x0} ${y0} Q${(x0 + x1) / 2} ${yc} ${x1} ${y1}`, L = Math.hypot(x1 - x0, y1 - y0) * 1.3 + 60;
        return <svg style={{ position: 'absolute', left: 0, top: 0, overflow: 'visible', opacity: Math.min(1, ks * 2) }} width={b.w} height={b.h}>
          <path d={d} fill="none" stroke="#fff" strokeWidth={5} strokeLinecap="round" strokeDasharray={L} strokeDashoffset={L * (1 - clamp((c.t - novo.t) / .55))} />
          <circle cx={x1} cy={y1} r={9} fill={C.destaque} stroke="#0B0F17" strokeWidth={3} opacity={clamp((c.t - novo.t - .4) / .2)} /></svg>;
      })()}
      {embaixo && p.niveis.map((nv: any, i: number) => {
        const ent = aparece(c, c.L.t0 + i * (p.cadencia ?? .18));
        const ativo = ativoEm(i) != null;
        const cx = xs(i) + w / 2, fila = i % 2;
        // nome centrado no bloco, mas PRESO dentro da caixa da camada (o primeiro/último nível não vaza pela margem)
        const tw = Math.min(220, larguraTxt(String(nv.rotulo), 26, .66) + 8), lx = Math.max(0, Math.min(b.w - tw, cx - tw / 2));
        return <React.Fragment key={'r' + i}>
          <div style={{ position: 'absolute', left: cx - 1.5, top: hb + prof, width: 3, height: 8 + fila * 38, background: ativo ? C.destaque : 'rgba(255,255,255,.45)', opacity: ent }} />
          <div style={{ position: 'absolute', left: lx, width: tw, top: hb + prof + 8 + fila * 38, textAlign: 'center', fontFamily: FD(c), fontWeight: 700, fontSize: 26,
            color: ativo ? C.destaque : '#F4F1EA', textTransform: 'uppercase', whiteSpace: 'nowrap', textShadow: '0 2px 8px #000', opacity: ent }}>{nv.rotulo}</div>
        </React.Fragment>;
      })}
      {p.legenda_base && <div style={{ position: 'absolute', left: 0, right: 0, top: hb + prof + (embaixo ? 92 : 12), textAlign: 'center', fontFamily: FD(c), fontWeight: 700, fontSize: 26,
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
  // ATLAS: documentação/registro sempre reto e alinhado; DOSSIÊ preserva estilo de arquivo original.
  const inc = c.P.formato === 'atlas' ? 0 : (p.inclina ?? (est === 'foto' ? -1.2 : est === 'documento' ? .6 : -1.2));
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

// atlas.geoPin — objeto ANCORADO no território: a posição sai da MESMA câmera do palco (cameraEm), então o pino segue
// pan/zoom quadro a quadro. 'local' = ponto + nome; 'foto' = prova fotográfica circular ligada ao ponto por um fio
// (gramática da referência: retrato circular preso ao lugar; aqui só fotos reais com crédito). Geometria = plano.caixa_pino.
export const GeoPin: React.FC<{ c: Ctx }> = ({ c }) => {
  const p = c.L.p, C = cores(c);
  const cam = cameraEm(c.P.palco, c.t), ws = 512 * 2 ** cam.zoom;
  const dxw = ((mercX(p.lonlat[0]) - cam.fx + .5) % 1 + 1) % 1 - .5;          // cópia do mundo mais perto da câmera
  const ax = cam.ancora[0] + dxw * ws, ay = cam.ancora[1] + (mercY(p.lonlat[1]) - cam.fy) * ws;
  const k = c.k, pulso = p.t_ativo != null && c.t >= p.t_ativo ? clamp((c.t - p.t_ativo) / .5) : 0;
  const ponto = <div data-ancora-geo={JSON.stringify(p.lonlat)} style={{ position: 'absolute', left: ax - 12, top: ay - 12, width: 24, height: 24, borderRadius: 12,
    background: C.destaque, border: '4px solid #0B0F17', boxShadow: `0 0 0 3px #fff, 0 0 0 ${3 + 14 * pulso * (1 - pulso) * 4}px rgba(255,210,31,.35), 0 4px 14px rgba(0,0,0,.6)`,
    transform: `scale(${.4 + .6 * k})` }} />;
  if (p.tipo !== 'foto') {
    // lado resolvido pelo motor (plano.posicionar_pinos → lado_auto): direita, esquerda, acima ou abaixo
    const lado = p.lado_auto || p.lado || 'direita', dir = lado !== 'esquerda', vert = lado === 'acima' || lado === 'abaixo';
    const lw = larguraTxt(String(p.rotulo || ''), 30, .66) + 44;
    return <>{ponto}<div style={{ position: 'absolute', ...(vert ? { left: ax - lw / 2, width: lw, justifyContent: 'center' } : dir ? { left: ax + 26 } : { right: 1080 - (ax - 26) }),
      top: lado === 'acima' ? ay - 84 : lado === 'abaixo' ? ay + 28 : ay - 28, height: 56, display: 'flex', alignItems: 'center',
      padding: '0 16px', background: '#0B0F17', borderLeft: `6px solid ${pulso > 0 ? C.destaque : '#F4F1EA'}`, fontFamily: FT(c), fontWeight: 900, fontSize: 30, color: '#fff',
      textTransform: 'uppercase', whiteSpace: 'nowrap', boxShadow: '0 6px 18px rgba(0,0,0,.5)', opacity: k, transform: `translateX(${(1 - k) * (dir ? -12 : 12)}px)` }}>{p.rotulo}</div></>;
  }
  // papel narrativo → escala (tokens canal.pino): protagonista domina o quadro; secundário acompanha
  const PP = ((c.P.tokens as any).pino || {})[p.papel || 'secundario'] || { raio: 118, rotulo_px: 30, anel: 6 };
  const TK = ((c.P.tokens as any).pino || {});
  if (TK.estilo === 'referencia') return <PinoReferencia c={c} ax={ax} ay={ay} PP={PP} TK={TK} />;
  const im = c.P.imagens?.[p.asset], r = p.raio ?? PP.raio, [dx, dy] = Array.isArray(p.desloc) ? p.desloc : [0, -(r + 80)];
  const cx = ax + dx, cy = ay + dy, d = Math.hypot(dx, dy) || 1;
  const ex = cx - dx / d * (r + 6), ey = cy - dy / d * (r + 6);
  return <>
    <svg style={{ position: 'absolute', left: 0, top: 0, overflow: 'visible', opacity: k }} width={1080} height={1920}>
      <line x1={ax} y1={ay} x2={lerp(ax, ex, k)} y2={lerp(ay, ey, k)} stroke="#fff" strokeWidth={4} /></svg>
    {ponto}
    <div style={{ position: 'absolute', left: cx - r, top: cy - r, width: 2 * r, height: 2 * r, borderRadius: r, overflow: 'hidden', background: '#111',
      boxShadow: `0 0 0 ${PP.anel}px ${C.destaque}, 0 0 0 ${PP.anel + 3}px #0B0F17, 0 18px 40px rgba(0,0,0,.6)`, transform: `scale(${.55 + .45 * k})`, opacity: k }}>
      {im && <Img src={staticFile(im.src)} style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: `${(p.foco || [.5, .5])[0] * 100}% ${(p.foco || [.5, .5])[1] * 100}%` }} />}
    </div>
    <div style={{ position: 'absolute', left: cx - 300, width: 600, top: cy + r + 12, display: 'flex', flexDirection: 'column', alignItems: 'center', opacity: aparece(c, c.L.t0 + .25) }}>
      {/* rótulo nunca mais largo que a foto (+40): quebra em até 2 linhas — MESMA regra de plano.caixa_pino */}
      <div style={{ padding: '10px 20px', background: C.papel, color: C.tinta, fontFamily: FT(c), fontWeight: 800, fontSize: PP.rotulo_px, lineHeight: `${PP.rotulo_px + 2}px`, textTransform: 'uppercase',
        maxWidth: Math.max(300, 2 * r + 2 * PP.anel + 40), textAlign: 'center', boxShadow: '0 8px 20px rgba(0,0,0,.5)' }}>{p.rotulo}</div>
      {p.meta && <div data-meta="credito" style={{ marginTop: 4, fontFamily: FD(c), fontSize: 18, lineHeight: '22px', color: 'rgba(255,255,255,.88)', textShadow: '0 1px 4px #000', whiteSpace: 'nowrap' }}>{p.meta}</div>}
    </div>
  </>;
};

// pino de foto na gramática da REFERÊNCIA A (medida quadro a quadro): anel de pulso no lugar; a foto circular com anel
// quente nasce pequena sobre o lugar e cresce (40 % → 100 %, 0,2 s) para cima; o rótulo em serifa desdobra na horizontal
// logo abaixo da foto. Geometria = plano.caixa_pino (estilo 'referencia').
const rotuloX = (c: Ctx, cx: number, ay: number, rpx: number, txt: string) => {
  const S = (c.P as any).seguro; if (!S) return cx;
  const hl = rpx + 32, y0 = ay - hl / 2 + 8, y1 = ay + hl / 2 - 8, lw = txt.length * rpx * .62 + 44;
  const xd = Math.min(S.dir_max, ...S.direita.filter((d: any) => y1 > d.de_y && y0 < d.ate_y).map((d: any) => d.x));
  return Math.min(cx, xd - lw / 2 - 4);
};
const PinoReferencia: React.FC<{ c: Ctx; ax: number; ay: number; PP: any; TK: any }> = ({ c, ax, ay, PP, TK }) => {
  const p = c.L.p, im = c.P.imagens?.[p.asset], r = p.raio ?? PP.raio;
  // medido na referência A (1,0 s): foto com a borda esquerda sobre o lugar e a base ~55 px acima dele; rótulo centrado
  // sob a foto, com o MEIO na altura do lugar; anel de pulso no lugar (até ~47 px)
  const [dx, dy] = Array.isArray(p.desloc) ? p.desloc : [r, -(r + 55)];
  const te = c.t - c.L.t0, sai = clamp((c.L.t1 + .3 - c.t) / .3);
  const kf = easeOut(clamp(te / (TK.entrada_s ?? .22)));
  const kr = easeOut(clamp((te - (TK.rotulo_atraso_s ?? .2)) / (TK.rotulo_entrada_s ?? .16)));
  const kp = clamp(te / (TK.pulso_s ?? .7));
  const cx = ax + dx * (.25 + .75 * kf), cy = ay + dy * (.25 + .75 * kf);
  const anel = PP.anel ?? 6, corAnel = TK.cor_anel || '#D8A64A';
  const rpx = PP.rotulo_px ?? 30;
  return <div style={{ opacity: sai }}>
    {/* Âncora permanente e invisível (sem opacity:0): o fiscal mede o pino durante TODO o pan/zoom, não só nos primeiros 0,7 s. */}
    <div data-ancora-geo={JSON.stringify(p.lonlat)} style={{ position: 'absolute', left: ax - 1, top: ay - 1, width: 2, height: 2, pointerEvents: 'none' }} />
    {kp < 1 && <div style={{ position: 'absolute', left: ax - 14 - 33 * kp, top: ay - 14 - 33 * kp, width: 28 + 66 * kp, height: 28 + 66 * kp,
      borderRadius: '50%', border: '2.5px solid rgba(255,240,235,.85)', opacity: 1 - kp * .7 }} />}
    {kp < 1 && <div style={{ position: 'absolute', left: ax - 8, top: ay - 8, width: 16, height: 16, borderRadius: '50%', border: '2px solid rgba(255,240,235,.8)', opacity: 1 - kp }} />}
    <div style={{ position: 'absolute', left: cx - r, top: cy - r, width: 2 * r, height: 2 * r, borderRadius: r, overflow: 'hidden', background: '#222',
      boxShadow: `0 0 0 ${anel}px ${corAnel}, 0 10px 26px rgba(0,0,0,.55)`, transform: `scale(${.4 + .6 * kf})`, opacity: Math.min(1, kf * 1.6) }}>
      {im && <Img src={staticFile(im.src)} style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: `${(p.foco || [.5, .5])[0] * 100}% ${(p.foco || [.5, .5])[1] * 100}%` }} />}
    </div>
    {/* rótulo centrado sob a foto; recua para dentro da área segura (coluna de ícones) — MESMA conta de plano.partes_pino */}
    <div style={{ position: 'absolute', left: rotuloX(c, ax + dx, ay, rpx, String(p.rotulo || '')) - 300, width: 600, top: ay - (rpx + 32) / 2, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <div style={{ height: rpx + 32, padding: '0 22px', display: 'flex', alignItems: 'center', background: '#F4F0E8', color: '#1D1A16', fontFamily: FS, fontWeight: 700, fontSize: rpx,
        borderRadius: 5, boxShadow: '0 6px 16px rgba(0,0,0,.4)', transform: `scaleX(${kr})`, opacity: kr > 0 ? 1 : 0, whiteSpace: 'nowrap' }}>{p.rotulo}</div>
    </div>
  </div>;
};

// statCard estilo 'cedula' — papel de votação/lista sobre o mapa (referência A): papel com borda picotada, inclinação e
// entrada que DESDOBRA na vertical (0,2 s); cabeçalho vermelho em serifa, linha de rubrica espaçada, linhas com caixa de
// marcar (marcada no instante da fala) e coluna à direita. Tokens: canal.papel.
export const Cedula: React.FC<{ c: Ctx }> = ({ c }) => {
  const p = c.L.p, b0 = c.L.caixa, K0 = (c.P.tokens as any).papel || {};
  const wc = Math.min(b0.w, K0.largura || b0.w), b = { ...b0, x: b0.x + (b0.w - wc) / 2, w: wc };     // largura da referência, centrada no slot
  const K = { inclina: -2.2, entrada_s: .2, fundo: '#F3EEE3', tinta: '#1D1A16', vermelho: '#B4262B', fio: 'rgba(29,26,22,.55)', sombra: '0 14px 34px rgba(0,0,0,.45)', ...((c.P.tokens as any).papel || {}) };
  const ke = easeOut(clamp((c.t - c.L.t0) / K.entrada_s));
  const linhas = p.linhas || [], hL = Math.min(78, (b.h - 120) / Math.max(1, linhas.length));
  const col = b.w * .7;
  return (
    <div style={{ position: 'absolute', left: b.x, top: b.y, width: b.w, height: b.h, transform: `rotate(${K.inclina}deg) scaleY(${Math.max(.02, ke)})`, transformOrigin: '50% 50%',
      filter: 'drop-shadow(0 12px 18px rgba(0,0,0,.45))' }}>
      {/* borda picotada: papel com furos em grade (máscara) + miolo liso recuado 7 px → só a borda fica picotada */}
      <div style={{ position: 'absolute', inset: 0, background: K.fundo, WebkitMaskImage: 'radial-gradient(circle 4px, transparent 97%, #000 100%)',
        WebkitMaskSize: '12px 12px', WebkitMaskPosition: '-6px -6px' }} />
      <div style={{ position: 'absolute', inset: 7, background: K.fundo }} />
      <div style={{ position: 'absolute', left: 0, top: 0, width: col, height: 106, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ fontFamily: FS, fontWeight: 700, fontSize: 40, color: K.vermelho, letterSpacing: 6, lineHeight: 1 }}>{p.cabecalho}</div>
        <div data-meta="rubrica" style={{ fontFamily: FT(c), fontWeight: 700, fontSize: 18, color: K.fio, letterSpacing: 5, marginTop: 8, textTransform: 'uppercase' }}>{p.rubrica}</div>
      </div>
      <div data-meta="rubrica" style={{ position: 'absolute', left: col, top: 0, width: b.w - col, height: 106, display: 'flex', alignItems: 'flex-end', paddingLeft: 14, paddingBottom: 22,
        fontFamily: FT(c), fontWeight: 700, fontSize: 18, color: K.fio, letterSpacing: 4 }}>{p.rubrica_dir || ''}</div>
      <div style={{ position: 'absolute', left: 18, right: 18, top: 106, height: 2, background: K.fio }} />
      <div style={{ position: 'absolute', left: col, top: 18, bottom: 18, width: 2, background: K.fio }} />
      {linhas.map((l: any, i: number) => {
        const v = l.t != null ? clamp((c.t - l.t) / .35) : 1, mk = l.marca_t != null ? easeOut(clamp((c.t - l.marca_t) / .25)) : 0;
        const y = 122 + i * hL;
        return <React.Fragment key={i}>
          <div style={{ position: 'absolute', left: 30, top: y + hL / 2 - 14, width: 28, height: 28, border: `3px solid ${K.tinta}`, borderRadius: 3, background: '#fff', opacity: .85 }} />
          {mk > 0 && <svg style={{ position: 'absolute', left: 28, top: y + hL / 2 - 22, overflow: 'visible' }} width={40} height={40}>
            <path d="M6 20 L15 30 L34 4" fill="none" stroke="#2E8A73" strokeWidth={6} strokeLinecap="round" strokeLinejoin="round"
              strokeDasharray={60} strokeDashoffset={60 * (1 - mk)} /></svg>}
          <div style={{ position: 'absolute', left: 76, top: y, height: hL, width: col - 96, display: 'flex', alignItems: 'center', fontFamily: FS,
            fontWeight: l.italico ? 600 : 700, fontStyle: l.italico ? 'italic' : 'normal', fontSize: l.italico ? 30 : 38, color: l.italico ? 'rgba(29,26,22,.7)' : K.tinta,
            opacity: v, whiteSpace: 'nowrap', borderBottom: l.pontilhado ? `2px dashed ${K.fio}` : 'none' }}>{l.texto}</div>
          {l.dir && <div style={{ position: 'absolute', left: col + 20, top: y, height: hL, display: 'flex', alignItems: 'center', fontFamily: FS, fontSize: 26, color: K.fio, opacity: v }}>{l.dir}</div>}
        </React.Fragment>;
      })}
    </div>);
};

// statCard estilo 'selo' — estado (ELEITO…): retângulo arredondado verde, letras espaçadas, entra em 0,3 s (canal.selo)
export const Selo: React.FC<{ c: Ctx }> = ({ c }) => {
  const p = c.L.p, b = c.L.caixa, K = { fundo: '#2E8A73', texto: '#F4F1EA', px: 30, entrada_s: .3, ...((c.P.tokens as any).selo || {}) };
  const k = easeOut(clamp((c.t - c.L.t0) / K.entrada_s));
  return <div style={{ position: 'absolute', left: b.x, top: b.y, width: b.w, height: b.h, display: 'flex', alignItems: 'center', justifyContent: p.alinha === 'esquerda' ? 'flex-start' : 'center' }}>
    <div data-cartao={JSON.stringify([b.x + b.w / 2, b.y + b.h / 2])} style={{ padding: '10px 26px', background: K.fundo, color: K.texto, fontFamily: FT(c), fontWeight: 800, fontSize: K.px,
      letterSpacing: 5, borderRadius: 8, boxShadow: '0 8px 20px rgba(0,0,0,.4)', transform: `scale(${.6 + .4 * k})`, opacity: k, textTransform: 'uppercase' }}>{p.valor}</div>
  </div>;
};

// editorial.statCard estilo 'dial' — número com CONTEXTO proporcional: meio-círculo de pontos dividido pelas partes
// (gramática do cartão de dados da referência; aqui, por exemplo, metade da água sobe e metade desce)
export const Dial: React.FC<{ c: Ctx }> = ({ c }) => {
  const p = c.L.p, C = cores(c), b = c.L.caixa, T = KT(c);
  const partes = p.partes || [], tot = partes.reduce((s: number, x: any) => s + x.fracao, 0) || 1;
  const util = b.w - 2 * T.pad_x;
  const R = Math.max(90, Math.min(util * .3, b.h - 2 * T.pad_y - T.titulo_px - 120));
  const fileiras = 6, pts: { x: number; y: number; a: number }[] = [];
  for (let f = 0; f < fileiras; f++) {
    const rr = R * (.46 + .54 * f / (fileiras - 1)), n = Math.round(12 + f * 3.6);
    for (let j = 0; j < n; j++) { const a = Math.PI * (j / (n - 1)); pts.push({ x: R - Math.cos(a) * rr, y: R - Math.sin(a) * rr, a }); }
  }
  pts.sort((u, v) => u.a - v.a);
  const kv = p.contagem ? easeOut((c.t - c.L.t0 - .2) / (p.dur_contagem || 1.2)) : 1;
  const lim: number[] = []; let acc = 0; partes.forEach((x: any) => { acc += x.fracao / tot; lim.push(acc); });
  const corDe = (u: number) => { const i = lim.findIndex(l => u <= l + 1e-6); const k = partes[Math.max(0, i)]?.cor; return k === 'agua' ? C.agua : k === 'alerta' ? C.alerta : k === 'cinza' ? '#9AA0A6' : C.destaque_escuro; };
  const val = typeof p.valor === 'number' ? Math.round(p.valor * kv) : p.valor;
  const fim = `${p.prefixo || ''}${typeof p.valor === 'number' ? num(p.valor, 0) : p.valor}`;
  const colN = util * .5, npx = Math.max(T.numero_min_px, Math.min(92, colN / larguraTxt(fim, 1, .7)));
  return (
    <Cartao c={c} largura={b.w}>
      {p.titulo && <div style={{ fontFamily: FD(c), fontWeight: 700, fontSize: T.titulo_px, letterSpacing: 3, textTransform: 'uppercase', color: C.alerta }}>{p.titulo}</div>}
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', marginTop: 8 }}>
        <svg width={2 * R + 12} height={R + 10} style={{ overflow: 'visible', flex: 'none' }}>
          {pts.map((q, i) => {
            const u = i / (pts.length - 1), pi = Math.max(0, lim.findIndex(l => u <= l + 1e-6)), ini = pi ? lim[pi - 1] : 0;
            const tp = partes[pi]?.t, cheio = tp != null ? c.t >= tp + (u - ini) / Math.max(1e-3, lim[pi] - ini) * .6 : u <= kv;
            return <circle key={i} cx={q.x + 6} cy={q.y + 4} r={R / 25} fill={cheio ? corDe(u) : 'rgba(11,15,23,.12)'} />;
          })}
        </svg>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', minWidth: 0 }}>
          <div style={{ fontFamily: FT(c), fontWeight: 900, fontSize: npx, lineHeight: 1, whiteSpace: 'nowrap' }}>{p.prefixo || ''}{typeof val === 'number' ? val.toLocaleString('pt-BR') : val}</div>
          {p.unidade && <div style={{ fontFamily: FT(c), fontWeight: 800, fontSize: 30, marginTop: 4, whiteSpace: 'nowrap' }}>{p.unidade}</div>}
          <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 4, alignItems: 'flex-end' }}>
            {partes.map((x: any, i: number) => <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, fontFamily: FD(c), fontWeight: 700, fontSize: 26, textTransform: 'uppercase',
              whiteSpace: 'nowrap', opacity: aparece(c, (x.t ?? c.L.t0 + .6)) }}><i style={{ width: 16, height: 16, borderRadius: 8, background: corDe(lim[i] - 1e-3), display: 'inline-block' }} />{x.rotulo}</div>)}
          </div>
        </div>
      </div>
      <Fonte c={c} />
    </Cartao>);
};

// editorial.cta — encerramento curto e reutilizável (canal.cta): entra só quando a revelação final já terminou
export const CTA: React.FC<{ c: Ctx }> = ({ c }) => {
  const p = c.L.p, b = c.L.caixa, C = cores(c), K = (c.P.tokens as any).cta || {};
  return (
    <div style={{ position: 'absolute', left: b.x, top: b.y, width: b.w, height: b.h, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
      <div data-cartao={JSON.stringify([b.x + b.w / 2, b.y + b.h / 2])} style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '12px 26px', background: '#0B0F17',
        border: `3px solid ${C.destaque}`, boxShadow: '0 10px 30px rgba(0,0,0,.5)', transform: `translateY(${(1 - c.k) * 16}px)`, whiteSpace: 'nowrap' }}>
        <i style={{ width: 16, height: 16, background: C.destaque, transform: 'rotate(45deg)', display: 'inline-block' }} />
        <span style={{ fontFamily: FT(c), fontWeight: 900, fontSize: 36, color: C.destaque, textTransform: 'uppercase' }}>{p.texto || K.texto || 'SIGA'}</span>
        <span style={{ fontFamily: FD(c), fontWeight: 700, fontSize: 34, color: '#F4F1EA' }}>{p.handle || K.handle}</span>
      </div>
    </div>);
};

export const PRIMITIVAS: Record<string, React.FC<{ c: Ctx }>> = {
  'editorial.cta': CTA,
  'atlas.geoPin': GeoPin,
  'editorial.statCard': StatCard, 'editorial.peopleCard': PeopleCard, 'editorial.hierarchy': Hierarchy, 'editorial.timeline': Timeline,
  'dossie.documentCard': DocumentCard, 'dossie.evidenceHighlight': Evidence, 'editorial.comparison': Comparison,
  'editorial.flowConnections': Flow, 'editorial.titleOrPayoff': Title,
};
