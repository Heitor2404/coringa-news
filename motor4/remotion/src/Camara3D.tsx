// tresd.camara — Three.js + React Three Fiber via @remotion/three. Corte 3D simples de uma câmara (paredes, comportas,
// água que sobe e objeto flutuante que sobe COM a água). Câmera fixa. Física coerente: o casco fica sempre na superfície.
// Sem fotorrealismo; render por SwiftShader/ANGLE em CPU.
import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from 'remotion';
import { ThreeCanvas } from '@remotion/three';
import { PerspectiveCamera, Vector3 } from 'three';
import { C, FD, FT, Fontes, W, H, clamp, easeIO, lerp } from './ident';

export type Camara3DProps = {
  duracao: number;
  nivel_baixo_m: number; nivel_alto_m: number;     // nível da água no começo e no fim do enchimento (escala real em metros)
  encher: { de: number; ate: number };
  comprimento_m?: number; largura_m?: number; altura_parede_m?: number;
  rotulos: { texto: string; t: number; ancora: 'agua' | 'lago' | 'comporta' | 'navio' }[];
  rotulo_selo?: string;
};

const Casco: React.FC<{ y: number }> = ({ y }) => (
  <group position={[0, y, 0]}>
    <mesh position={[0, 1.2, 0]}><boxGeometry args={[20, 4.2, 5.4]} /><meshStandardMaterial color="#B23A2E" roughness={.7} /></mesh>
    <mesh position={[0, 3.9, 0]}><boxGeometry args={[19, 1.4, 5.0]} /><meshStandardMaterial color="#1F2833" roughness={.6} /></mesh>
    <mesh position={[-5.5, 6.2, 0]}><boxGeometry args={[5, 3.4, 4.2]} /><meshStandardMaterial color="#E9ECEF" roughness={.5} /></mesh>
    {[ -1, 2, 5 ].map((x, i) => <mesh key={i} position={[x, 5.6, 0]}><boxGeometry args={[2.6, 2.2, 4.4]} /><meshStandardMaterial color={['#3A7BD5', '#E0A100', '#3DDC84'][i]} roughness={.6} /></mesh>)}
  </group>
);

export const Camara3D: React.FC<Camara3DProps> = (P) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const L = P.comprimento_m ?? 60, Wd = P.largura_m ?? 12, Hp = P.altura_parede_m ?? Math.max(P.nivel_alto_m + 4, 14);
  // escala de cena: 1 unidade = 1 m na horizontal; altura comprimida igual (sem exagero vertical: proporção honesta)
  const k = easeIO(clamp((t - P.encher.de) / Math.max(.01, P.encher.ate - P.encher.de)));
  const nivel = lerp(P.nivel_baixo_m, P.nivel_alto_m, k);
  const vis = (t0: number) => clamp((t - t0) / .35);
  // rótulos ancorados por PROJEÇÃO dos pontos 3D com a mesma câmera da cena (nada de posição chutada)
  const CAM = { pos: [-(L * 1.05), Hp * 2.1 + 18, L * 1.25] as [number, number, number], fov: 34 };
  const cam = new PerspectiveCamera(CAM.fov, W / H, .5, 900); cam.position.set(...CAM.pos); cam.lookAt(0, 0, 0); cam.updateMatrixWorld();
  const rot = .18, base = -Hp / 2;
  const tela = (x: number, y: number, z: number) => { const c = Math.cos(rot), s2 = Math.sin(rot);
    const v = new Vector3(x * c + z * s2, y + base, -x * s2 + z * c).project(cam); return { x: (v.x + 1) / 2 * W, y: (1 - v.y) / 2 * H }; };
  const ANC = { agua: () => tela(-L / 2 + 4, nivel, Wd / 2), lago: () => tela(L / 2 + 22, P.nivel_alto_m, Wd / 2 + 3),
                comporta: () => tela(L / 2 + 1, Hp, 0), navio: () => tela(0, nivel + 8, 0) };
  return (
    <AbsoluteFill style={{ background: `linear-gradient(${C.noite}, ${C.grafite})` }}>
      <Fontes />
      <ThreeCanvas width={W} height={H} camera={{ position: CAM.pos, fov: CAM.fov, near: .5, far: 900 }} onCreated={({ camera }) => camera.lookAt(0, 0, 0)}>
        <ambientLight intensity={.55} />
        <directionalLight position={[-30, 60, 40]} intensity={1.4} />
        <directionalLight position={[40, 20, -30]} intensity={.35} />
        <group position={[0, -Hp / 2, 0]} rotation={[0, .18, 0]}>
          {/* piso e paredes (corte: parede frontal omitida para mostrar o interior) */}
          <mesh position={[0, -.5, 0]}><boxGeometry args={[L + 8, 1, Wd + 8]} /><meshStandardMaterial color={C.concreto} roughness={.95} /></mesh>
          <mesh position={[0, Hp / 2, -Wd / 2 - 1.5]}><boxGeometry args={[L + 8, Hp, 3]} /><meshStandardMaterial color="#9AA2AD" roughness={.95} /></mesh>
          {/* comportas: montante (lado do lago, mais alta) e jusante */}
          <mesh position={[L / 2 + 1, Hp / 2, 0]}><boxGeometry args={[2, Hp, Wd]} /><meshStandardMaterial color="#4B5563" roughness={.8} /></mesh>
          <mesh position={[-L / 2 - 1, Hp / 2, 0]}><boxGeometry args={[2, Hp, Wd]} /><meshStandardMaterial color="#4B5563" roughness={.8} /></mesh>
          {/* lago a montante: nível alto constante */}
          <mesh position={[L / 2 + 22, P.nivel_alto_m / 2, 0]}><boxGeometry args={[40, P.nivel_alto_m, Wd + 6]} /><meshStandardMaterial color={C.agua} transparent opacity={.85} /></mesh>
          {/* água da câmara: sobe */}
          <mesh position={[0, nivel / 2, 0]}><boxGeometry args={[L, Math.max(.05, nivel), Wd]} /><meshStandardMaterial color={C.agua} transparent opacity={.78} /></mesh>
          {/* navio: flutua na superfície (calado ≈ 2,5 m) */}
          <Casco y={nivel - 2.5} />
        </group>
      </ThreeCanvas>
      {P.rotulo_selo && <div style={{ position: 'absolute', left: 72, top: 400, fontFamily: FD, fontWeight: 700, fontSize: 30, letterSpacing: 4, color: C.tecnico_linha }}>{P.rotulo_selo}</div>}
      {P.rotulos.map((r, i) => {
        const a = ANC[r.ancora](); const x = Math.min(W - 420, Math.max(72, a.x - 40)), y = Math.min(1150, Math.max(420, a.y - 70));
        return <div key={i} data-ancora={r.ancora} style={{ position: 'absolute', left: x, top: y, opacity: vis(r.t), padding: '8px 16px', background: 'rgba(8,10,14,.82)',
          borderLeft: `6px solid ${C.amarelo}`, fontFamily: FT, fontWeight: 900, fontSize: 34, color: '#fff', textTransform: 'uppercase', whiteSpace: 'nowrap' }}>
          {r.texto.replace('{nivel}', nivel.toFixed(0))}</div>;
      })}
    </AbsoluteFill>
  );
};
