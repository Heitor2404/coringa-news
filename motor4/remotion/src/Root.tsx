import React from 'react';
import { AbsoluteFill, Composition } from 'remotion';
import { MapaRota } from './MapaRota';
import { Camara3D } from './Camara3D';
import { Camada } from './Camada';
import { TipoLottie } from './TipoLottie';
import { Formato } from './formatos/Formato';
import { FilmeEditorial } from './formatos/FilmeEditorial';

// Amostra ATLAS: palco + legendas em UMA renderizacao, com o tempo GLOBAL do episodio.
const AtlasAmostra: React.FC<{ visual: any; legenda: any; duracao: number }> = ({ visual, legenda }) => (
  <AbsoluteFill>
    <Formato {...visual} />
    <Camada {...legenda} />
  </AbsoluteFill>
);

const meta = ({ props }: { props: any }) => ({ durationInFrames: Math.max(1, Math.round((props.duracao ?? 3) * 30)) });
const base = { width: 1080, height: 1920, fps: 30, durationInFrames: 90, calculateMetadata: meta as any };
export const Root: React.FC = () => (
  <>
    <Composition id="MapaRota" component={MapaRota as any} {...base} defaultProps={{ duracao: 3, geo: { topo: { type: 'Topology', objects: {}, arcs: [] }, meta: {} }, camera: [{ t: 0, centro: [-79.7, 9.1], zoom: 8 }], pontos: [] } as any} />
    <Composition id="Camara3D" component={Camara3D as any} {...base} defaultProps={{ duracao: 3, nivel_baixo_m: 0, nivel_alto_m: 9, encher: { de: .5, ate: 2.5 }, rotulos: [] } as any} />
    <Composition id="Camada" component={Camada as any} {...base} defaultProps={{ duracao: 3, palavras: [], cenas: [] } as any} />
    <Composition id="Formato" component={Formato as any} {...base} defaultProps={{ duracao: 3, formato: 'atlas', tokens: {} as any, palco: [{ t: 0, tipo: 'mesa' }], camadas: [] } as any} />
    <Composition id="FilmeEditorial" component={FilmeEditorial as any} {...base} defaultProps={{ duracao: 3, shots: [], preview: true } as any} />
    <Composition id="AtlasAmostra" component={AtlasAmostra as any} {...base} defaultProps={{ duracao: 3, visual: {}, legenda: {} } as any} />
    <Composition id="TipoLottie" component={TipoLottie as any} {...base} defaultProps={{ duracao: 3, lottie: 'lottie/gota.json', linhas: [] } as any} />
  </>
);
