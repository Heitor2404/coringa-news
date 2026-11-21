import React from 'react';
import { AbsoluteFill, Composition } from 'remotion';
import { MapaRota } from './MapaRota';
import { Camara3D } from './Camara3D';
import { Camada } from './Camada';
import { TipoLottie } from './TipoLottie';
import { Formato } from './formatos/Formato';
import { FilmeEditorial } from './formatos/FilmeEditorial';
import { LeverMechanism2D } from './formatos/LeverMechanism2D';
import leverContract from './formatos/lever2d-contract.json';
import { Mechanism2DOtherModels } from './formatos/Mechanism2DOtherModels';
import probes2d from './formatos/mechanisms2d-probes.json';
import { AtlasAProof } from './formatos/AtlasAProof';
import { SliderCrankProof } from './formatos/SliderCrankProof';
import { CinematicCutaway3D } from './formatos/CinematicCutaway3D';
import atlasAProof from './formatos/atlas-a-proof.json';
import sliderProof from './formatos/slider-crank-proofs.json';

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
    {/* Laboratório isolado: não entra no catálogo nem na produção. */}
    <Composition id="ProvaMecanismo2D" component={LeverMechanism2D as any}
      {...base} defaultProps={{
        duracao:leverContract.duration,variant:'paper',private_review_only:true,
        cues:leverContract.cues,geometry:leverContract.geometry,
      } as any}/>
    {/* Duas famílias novas: mesma identidade clara, física diferente.
        Somente laboratório privado, sem alterar o catálogo de produção. */}
    <Composition id="ProvaPolia2D" component={Mechanism2DOtherModels as any}
      {...base} defaultProps={{duracao:probes2d.demo.pulley.duration,
        kind:'pulley',private_review_only:true} as any}/>
    <Composition id="ProvaEngrenagens2D" component={Mechanism2DOtherModels as any}
      {...base} defaultProps={{duracao:probes2d.demo.gears.duration,
        kind:'gears',private_review_only:true} as any}/>
    {/* A — arte ilustrada 2.5D autoral, amplitude de tela.
        Provas eclusa/EUV PRIVADAS, nunca no pipeline de episódios. */}
    <Composition id="ProvaA-Eclusa" component={AtlasAProof as any}
      {...base} defaultProps={{kind:'lock',duracao:atlasAProof.duration,
        private_review_only:true} as any}/>
    <Composition id="ProvaA-EUV" component={AtlasAProof as any}
      {...base} defaultProps={{kind:'euv',duracao:atlasAProof.duration,
        private_review_only:true} as any}/>
    {/* Prova privada: MESMO rig slider-crank em dois temas, sem renderer por episodio. */}
    <Composition id="ProvaA-Pistao" component={SliderCrankProof as any}
      {...base} defaultProps={{kind:'motor',duracao:sliderProof.duration,
        private_review_only:true} as any}/>
    <Composition id="ProvaA-Compressor" component={SliderCrankProof as any}
      {...base} defaultProps={{kind:'compressor',duracao:sliderProof.duration,
        private_review_only:true} as any}/>
    {/* Alternativa visual: cutaway 3D full-bleed. Mesma geometria slider-crank,
        dois dados, nao usar no filme editorial sem revisao. */}
    <Composition id="Prova3D-Pistao" component={CinematicCutaway3D as any}
      {...base} defaultProps={{kind:'motor',duracao:sliderProof.duration,
        private_review_only:true} as any}/>
    <Composition id="Prova3D-Compressor" component={CinematicCutaway3D as any}
      {...base} defaultProps={{kind:'compressor',duracao:sliderProof.duration,
        private_review_only:true} as any}/>
    <Composition id="AtlasAmostra" component={AtlasAmostra as any} {...base} defaultProps={{ duracao: 3, visual: {}, legenda: {} } as any} />
    <Composition id="TipoLottie" component={TipoLottie as any} {...base} defaultProps={{ duracao: 3, lottie: 'lottie/gota.json', linhas: [] } as any} />
  </>
);
