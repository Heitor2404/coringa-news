// Protótipo Remotion (Módulo F): a MESMA composição numero.animado da V2, reescrita em React/Remotion,
// para comparar facilidade, sincronização, desempenho e licença com o palco atual (HTML + seek(t) + Playwright).
import React from 'react';
import {AbsoluteFill, Composition, interpolate, registerRoot, staticFile, useCurrentFrame, useVideoConfig, Easing} from 'remotion';

const PAPEL = '#F2EDE3', TINTA = '#141414', AMARELO = '#FFD21F';
const fmt = (n) => Math.round(n).toLocaleString('pt-BR');

const Numero = ({rotulo, valor, unidade, natureza, contexto, n, texto, fonte}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = f / fps;
  const k = interpolate(t, [0.25, 1.55], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  const ap = (t0, d = 0.45) => interpolate(t, [t0, t0 + d], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  return (
    <AbsoluteFill style={{background: PAPEL, fontFamily: 'Montserrat, sans-serif', color: TINTA}}>
      <div style={{position: 'absolute', left: 72, top: 352, fontFamily: 'monospace', fontWeight: 700, fontSize: 28, letterSpacing: 5}}>◆ {rotulo.toUpperCase()}</div>
      <div style={{position: 'absolute', left: 72, top: 418, opacity: ap(0.15), border: `2px solid ${TINTA}`, padding: '6px 12px', fontFamily: 'monospace', fontWeight: 700, fontSize: 24, letterSpacing: 3}}>{natureza}</div>
      <div style={{position: 'absolute', left: 66, top: 470, display: 'flex', alignItems: 'baseline', gap: 22, opacity: ap(0.1), transform: `translateY(${(1 - ap(0.1)) * 20}px)`}}>
        <span style={{fontWeight: 900, fontSize: 200, letterSpacing: -8}}>{fmt(valor * k)}</span>
        <span style={{fontWeight: 800, fontSize: 56, maxWidth: 420}}>{unidade}</span>
      </div>
      <div style={{position: 'absolute', left: 72, top: 690, height: 10, width: 260 * ap(0.4, 1.1), background: AMARELO}} />
      <div style={{position: 'absolute', left: 72, right: 150, top: 724, fontFamily: 'Georgia, serif', fontSize: 44, opacity: ap(1.0)}}>{contexto}</div>
      <div style={{position: 'absolute', left: 72, top: 820, display: 'grid', gridTemplateColumns: 'repeat(10, 64px)'}}>
        {Array.from({length: n}, (_, i) => (
          <div key={i} style={{width: 56, height: 56, margin: 4, border: `3px solid ${TINTA}`, borderRadius: 8, opacity: 0.12 + 0.88 * interpolate(t, [1.4 + i * 0.022, 1.6 + i * 0.022], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}} />
        ))}
      </div>
      <div style={{position: 'absolute', left: 72, top: 1360, fontWeight: 800, fontSize: 38, opacity: ap(2.0)}}>{texto}</div>
      <div style={{position: 'absolute', left: 72, top: 1120, fontFamily: 'monospace', fontSize: 24, opacity: ap(0.8)}}>FONTE · {fonte}</div>
    </AbsoluteFill>
  );
};

const Raiz = () => (
  <Composition id="Numero" component={Numero} durationInFrames={150} fps={30} width={1080} height={1920}
    defaultProps={{rotulo: 'Água doce por travessia', valor: 200, unidade: 'milhões de litros', natureza: 'MÉDIA POR TRAVESSIA',
      contexto: 'Sai do lago Gatún e vai para o mar.', n: 80, texto: '≈ 80 piscinas olímpicas', fonte: 'WIKIPÉDIA'}} />
);
registerRoot(Raiz);
