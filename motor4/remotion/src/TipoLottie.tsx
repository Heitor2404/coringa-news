// tipo.lottie — afirmação tipográfica curta com ícone Lottie (@remotion/lottie, quadro a quadro determinístico).
// Usada com moderação (Kurzgesagt pontual): uma ideia por tela, frase curta, ícone que reforça a ação física.
import React, { useEffect, useState } from 'react';
import { AbsoluteFill, continueRender, delayRender, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { Lottie, type LottieAnimationData } from '@remotion/lottie';
import { C, FT, Fontes, clamp } from './ident';

export type TipoLottieProps = { duracao: number; lottie: string; linhas: { texto: string; t: number; destaque?: boolean }[]; laco?: boolean };

export const TipoLottie: React.FC<TipoLottieProps> = (P) => {
  const frame = useCurrentFrame(); const { fps } = useVideoConfig(); const t = frame / fps;
  const [anim, setAnim] = useState<LottieAnimationData | null>(null);
  const [h] = useState(() => delayRender('lottie'));
  useEffect(() => { fetch(staticFile(P.lottie)).then(r => r.json()).then(j => { setAnim(j); continueRender(h); }); }, []);
  return (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse 80% 60% at 50% 40%, ${C.grafite}, ${C.noite})` }}>
      <Fontes />
      {anim && <div style={{ position: 'absolute', left: 290, top: 380, width: 500, height: 500 }}><Lottie animationData={anim} loop={P.laco ?? true} /></div>}
      <div style={{ position: 'absolute', left: 90, right: 90, top: 900 }}>
        {P.linhas.map((l, i) => { const v = clamp((t - l.t) / .3); return (
          <div key={i} style={{ fontFamily: FT, fontWeight: 900, fontSize: 96, lineHeight: 1.0, letterSpacing: -2, textTransform: 'uppercase', textAlign: 'center',
            color: l.destaque ? C.amarelo : '#fff', opacity: v, transform: `translateY(${(1 - v) * 24}px)`, marginBottom: 14 }}>{l.texto}</div>); })}
      </div>
    </AbsoluteFill>
  );
};
