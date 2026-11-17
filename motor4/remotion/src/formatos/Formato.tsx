// Composição única dos FORMATOS. Palco persistente + camadas (primitivas) em slots fixos. Marca e legendas NÃO são
// desenhadas aqui: vêm da camada global (Camada.tsx), como em todo o V4.
import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from 'remotion';
import { Fontes, clamp } from '../ident';
import { PalcoMapa, PalcoMesa, PalcoTecnico, palcoEm } from './Palco';
import { PRIMITIVAS, easeOut } from './Primitivas';
import type { FormatoProps } from './tipos';

export const Formato: React.FC<FormatoProps> = (P) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const { entra, sai } = P.tokens.tempo;
  // opacidade de cada tipo de palco: dissolve de 0,5 s na troca
  const i = palcoEm(P.palco, t);
  const op = (tipo: string) => {
    const atual = P.palco[i];
    const ant = i > 0 ? P.palco[i - 1] : null;
    const k = clamp((t - atual.t) / .5);
    if (atual.tipo === tipo) return ant && ant.tipo !== tipo ? k : 1;
    if (ant && ant.tipo === tipo) return 1 - k;
    return 0;
  };
  const temMapa = P.palco.some(p => p.tipo === 'mapa');
  return (
    <AbsoluteFill style={{ background: P.tokens.palco.mesa.fundo }}>
      <Fontes />
      {temMapa && <PalcoMapa P={P} opac={op('mapa')} />}
      {op('tecnico') > 0 && <PalcoTecnico P={P} opac={op('tecnico')} />}
      {op('mesa') > 0 && <PalcoMesa P={P} opac={op('mesa')} />}
      {P.camadas.map(L => {
        const Comp = PRIMITIVAS[L.componente];
        if (!Comp || t < L.t0 || t > L.t1 + sai) return null;
        const k = easeOut((t - L.t0) / entra);
        const v = clamp((t - L.t0) / entra) * clamp((L.t1 + sai - t) / sai);
        return <div key={L.id} data-camada={L.id} data-componente={L.componente} style={{ position: 'absolute', inset: 0, opacity: v }}>
          <Comp c={{ t, P, L, v, k }} /></div>;
      })}
    </AbsoluteFill>
  );
};
