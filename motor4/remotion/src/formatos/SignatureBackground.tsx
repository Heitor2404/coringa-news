import React from 'react';
import {AbsoluteFill} from 'remotion';

// Coringa Explica — approved universal model B, E293.
// Decorative only. No map, subject-specific texture, labels, media duplicate,
// external assets, glow filters, or stochastic work per frame.
export const SignatureBackground:React.FC=()=>(
  <AbsoluteFill aria-hidden="true" data-documentary-background="SIGNATURE_B_V1"
    style={{pointerEvents:'none',overflow:'hidden',background:'radial-gradient(ellipse at 68% 13%,#232426 0%,#151618 39%,#0B0C0E 76%,#090A0C 100%)'}}>
    <svg viewBox="0 0 1080 1920" width="100%" height="100%" style={{position:'absolute',inset:0}}>
      <defs>
        <linearGradient id="signature-b-panel" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#252628"/><stop offset="1" stopColor="#090A0B"/>
        </linearGradient>
        <pattern id="signature-b-grain" width="17" height="19" patternUnits="userSpaceOnUse">
          <path d="M2 4h1 M9 12h2 M14 3h1 M4 16h1" stroke="#C2C2C2" strokeWidth=".55" opacity=".13"/>
          <path d="M5 7h1 M13 15h1" stroke="#000" strokeWidth=".7" opacity=".20"/>
        </pattern>
      </defs>
      <rect width="1080" height="1920" fill="url(#signature-b-grain)" opacity=".75"/>
      <path d="M620 0H1080V420L530 970L420 860L1080 200V0Z" fill="#08090A" opacity=".44"/>
      <path d="M890 0H1080V175L728 527L641 440Z" fill="url(#signature-b-panel)" opacity=".7"/>
      <path d="M1054 0L850 204" stroke="#D4AD39" strokeWidth="2" opacity=".74"/>
      <path d="M1080 102L724 458" stroke="#626367" strokeWidth="1" opacity=".23"/>
      <path d="M1080 1390V1920H550Z" fill="url(#signature-b-panel)" opacity=".56"/>
      <path d="M1080 1512V1920H672Z" fill="#08090B" opacity=".65"/>
      <path d="M1080 1624L784 1920" stroke="#D4AD39" strokeWidth="2" opacity=".64"/>
      <path d="M1080 1440L600 1920" stroke="#58595D" strokeWidth="1" opacity=".25"/>
    </svg>
  </AbsoluteFill>
);
export const signatureHasVisibleArea=(media:readonly number[])=>media[0]>.5||media[1]>.5||media[2]<1079.5||media[3]<1919.5;
