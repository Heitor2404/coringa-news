import React from 'react';
import {AbsoluteFill} from 'remotion';
// E349: owner superseded model B. Pure black, no decorative texture or lines.
// Keep the historical component name for compatible callers.
export const SignatureBackground:React.FC=()=>(
  <AbsoluteFill aria-hidden="true" data-documentary-background="BLACK_SOLID_V1"
    style={{pointerEvents:'none',overflow:'hidden',background:'#000000'}}/>
);
export const signatureHasVisibleArea=(media:readonly number[])=>media[0]>.5||media[1]>.5||media[2]<1079.5||media[3]<1919.5;
