// Identidade única (motor4/identidade/identidade.json) aplicada às composições Remotion.
import React from 'react';
import { staticFile } from 'remotion';
import ID from '../../identidade/identidade.json';
export const C = ID.cores;
export const IDT = ID;
const face = (fam: string, peso: string, arq: string) =>
  `@font-face{font-family:${fam};font-weight:${peso};font-style:normal;font-display:block;src:url(${staticFile('fontes/' + arq)}) format('woff2');}`;
export const Fontes: React.FC = () => {
  const f = ID.fontes;
  const css = [
    ...Object.entries(f.titulo.arquivos).map(([p, a]) => face(f.titulo.familia, p, a as string)),
    ...Object.entries(f.titulo.ext).map(([p, a]) => face(f.titulo.familia, p, a as string)),
    ...Object.entries(f.dado.arquivos).map(([p, a]) => face(f.dado.familia, p, a as string)),
  ].join('\n');
  return <style>{css}</style>;
};
export const FT = 'Mont, sans-serif';
export const FD = 'JBM, monospace';
export const W = ID.quadro.w, H = ID.quadro.h;
export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
export const clamp = (x: number, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const easeIO = (t: number) => (t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
