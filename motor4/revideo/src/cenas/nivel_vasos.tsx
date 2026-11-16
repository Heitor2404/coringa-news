/** @jsxImportSource @revideo/2d/lib */
// mecanismo nivel.vasos — corte lateral: reservatório baixo | câmara entre comportas | reservatório alto, aqueduto sob o
// piso com válvula; o objeto flutua SEMPRE na superfície. Sequência física: entra → comporta fecha → válvula abre →
// água desce do alto pelo aqueduto (gravidade) → nível e objeto sobem → níveis iguais → comporta abre → objeto segue.
// Tempos e textos vêm do contrato (variables); nada é específico de um vídeo.
import { Circle, Line, Node, Rect, Txt, makeScene2D } from '@revideo/2d';
// fontes da identidade (motor4/identidade/fontes), servidas pelo vite como assets
import mont800 from '../../../identidade/fontes/montserrat-latin-800-normal.woff2?url';
import mont900 from '../../../identidade/fontes/montserrat-latin-900-normal.woff2?url';
import montx800 from '../../../identidade/fontes/montserrat-latin-ext-800-normal.woff2?url';
import montx900 from '../../../identidade/fontes/montserrat-latin-ext-900-normal.woff2?url';
import jbm700 from '../../../identidade/fontes/jetbrains-mono-latin-700-normal.woff2?url';
const FONTES: [string, string, string][] = [['Mont', mont800, '800'], ['Mont', mont900, '900'], ['Mont', montx800, '800'], ['Mont', montx900, '900'], ['JBM', jbm700, '700']];
import { all, createRef, createSignal, easeInOutCubic, linear, map, tween, useScene, waitFor } from '@revideo/core';

const AM = '#FFD21F', AG = '#2F8FD8', AGC = '#7CC7F2', CONC = '#8A929E', LIN = '#7FE3F0', BR = '#FFFFFF';
const FT = 'Mont, Montserrat, sans-serif', FD = 'JBM, JetBrains Mono, monospace';

export default makeScene2D('nivel_vasos', function* (view) {
  yield Promise.all(FONTES.map(([f, u, w]) => new FontFace(f, `url(${u})`, { weight: w }).load().then(ff => (document as any).fonts.add(ff))));
  const V = useScene().variables;
  const p: any = V.get('params', {})();
  const T = { entra: 1.2, fecha: .6, valvula: .7, enche: 4.0, abre: .8, sai: 1.4, ...(p.tempos || {}) };
  const total: number = p.duracao || 12;
  const nomes = { baixo: 'nível do mar', alto: 'nível do lago', objeto: 'navio', ...(p.nomes || {}) };
  const passos: string[] = p.passos || ['O navio entra na câmara', 'A comporta se fecha', 'A válvula abre: a água desce do lago', 'A água sobe — e o navio sobe junto', 'Níveis iguais: a comporta abre'];
  const desnivel_m: number = p.desnivel_m ?? 9;
  // geometria (px, origem no centro do quadro 1080×1920)
  const yFundo = 260, yBaixo = 120, yAlto = -160;            // superfícies (y cresce para baixo)
  const xC0 = -250, xC1 = 250;                                // câmara
  const nivel = createSignal(yBaixo);                         // superfície da água na câmara
  const fluxo = createSignal(0), valv = createSignal(0), gateL = createSignal(1), gateR = createSignal(1), xObj = createSignal(-470);
  const passo = createSignal(-1);
  const titulo = createRef<Txt>(), medida = createRef<Txt>(), passoTxt = createRef<Txt>();
  const m = () => Math.round(((yBaixo - nivel()) / (yBaixo - yAlto)) * desnivel_m);

  view.add(<Node>
    {/* grade técnica discreta */}
    {Array.from({ length: 13 }, (_, i) => <Line points={[[-540, -960 + i * 160], [540, -960 + i * 160]]} stroke={'rgba(120,220,235,.08)'} lineWidth={2} />)}
    {/* título do esquema e selo */}
    <Txt ref={titulo} text={p.titulo || 'COMO A ECLUSA LEVANTA O NAVIO'} x={0} y={-520} fontFamily={FT} fontWeight={900} fontSize={58} fill={BR} textWrap textAlign={'center'} width={900} />
    {/* terreno/concreto */}
    <Rect x={0} y={yFundo + 120} width={1080} height={240} fill={'#3B4350'} />
    <Rect x={(xC1 + 540) / 2} y={(yAlto + yFundo) / 2 + 60} width={540 - xC1} height={0} />
    {/* reservatório baixo (esquerda) */}
    <Rect x={(-540 + xC0) / 2} y={(yBaixo + yFundo) / 2} width={xC0 + 540} height={yFundo - yBaixo} fill={AG} opacity={.9} />
    {/* reservatório alto (direita): degrau de terreno + água */}
    <Rect x={(xC1 + 540) / 2} y={(yFundo + 40 + yFundo) / 2 + 40} width={540 - xC1} height={80} fill={'#3B4350'} />
    <Rect x={(xC1 + 540) / 2} y={(yAlto + yFundo) / 2} width={540 - xC1} height={yFundo - yAlto} fill={AG} opacity={.9} />
    {/* câmara: água com nível variável */}
    <Rect x={0} y={() => (nivel() + yFundo) / 2} width={xC1 - xC0} height={() => yFundo - nivel()} fill={AG} opacity={.92} />
    <Line points={() => [[xC0, nivel()], [xC1, nivel()]]} stroke={AGC} lineWidth={5} />
    {/* paredes e piso da câmara */}
    <Rect x={0} y={yFundo + 20} width={xC1 - xC0 + 60} height={40} fill={CONC} />
    {/* aqueduto sob o piso: do fundo do lago até aberturas no piso da câmara */}
    <Line points={[[400, yFundo - 10], [400, yFundo + 90], [-180, yFundo + 90], [-180, yFundo + 40]]} stroke={CONC} lineWidth={46} lineJoin={'round'} />
    <Line points={[[400, yFundo - 10], [400, yFundo + 90], [-180, yFundo + 90], [-180, yFundo + 40]]} stroke={() => fluxo() > 0 ? AGC : '#1C2430'} lineWidth={26} lineJoin={'round'}
      lineDash={[28, 22]} lineDashOffset={() => -fluxo() * 900} />
    {/* válvula: roda que gira ao abrir */}
    <Circle x={400} y={yFundo + 90} size={74} fill={'#1C2430'} stroke={AM} lineWidth={8} rotation={() => valv() * 120}>
      <Line points={[[-30, 0], [30, 0]]} stroke={AM} lineWidth={8} />
    </Circle>
    {/* comportas (sobem para abrir) */}
    <Rect x={xC0} y={() => (yAlto - 40) / 2 + (yFundo) / 2 - (1 - gateL()) * 420} width={26} height={yFundo - yAlto + 40} fill={'#4B5563'} stroke={BR} lineWidth={3} />
    <Rect x={xC1} y={() => (yAlto - 40) / 2 + (yFundo) / 2 - (1 - gateR()) * 420} width={26} height={yFundo - yAlto + 40} fill={'#4B5563'} stroke={BR} lineWidth={3} />
    {/* objeto flutuante: casco sempre na superfície (calado fixo) */}
    <Node x={xObj} y={() => (xObj() > xC1 + 20 ? yAlto : xObj() < xC0 - 20 ? yBaixo : nivel()) - 18}>
      <Line points={[[-150, -10], [150, -10], [118, 42], [-130, 42]]} closed fill={'#B23A2E'} stroke={'#1A0E0C'} lineWidth={4} />
      <Rect x={-70} y={-48} width={70} height={70} fill={'#E9ECEF'} />
      <Rect x={30} y={-36} width={56} height={46} fill={'#3A7BD5'} /><Rect x={92} y={-36} width={46} height={46} fill={'#E0A100'} />
    </Node>
    {/* setas de gravidade no aqueduto */}
    <Txt text={'↓'} x={455} y={yFundo + 20} fontSize={70} fill={AM} opacity={() => fluxo() > 0 ? 1 : 0} />
    {/* rótulos dos níveis */}
    <Txt text={nomes.baixo.toUpperCase()} x={-400} y={yBaixo - 46} fontFamily={FD} fontWeight={700} fontSize={30} fill={BR} />
    <Txt text={nomes.alto.toUpperCase()} x={400} y={yAlto - 46} fontFamily={FD} fontWeight={700} fontSize={30} fill={BR} />
    {/* régua de altura */}
    <Line points={[[xC1 + 60, yBaixo], [xC1 + 60, yAlto]]} stroke={LIN} lineWidth={3} lineDash={[10, 10]} opacity={.7} />
    <Txt ref={medida} text={'+0 m'} x={xC0 + 110} y={() => nivel() - 50} fontFamily={FD} fontWeight={700} fontSize={44} fill={AM} />
    {/* legenda do passo (dentro da área segura, acima da faixa de legendas) */}
    <Rect x={0} y={-370} width={940} height={130} radius={10} fill={'rgba(6,8,12,.72)'} opacity={() => passo() >= 0 ? 1 : 0} />
    <Txt ref={passoTxt} text={' '} x={0} y={-370} width={880} textWrap textAlign={'center'}
      fontFamily={FT} fontWeight={800} fontSize={44} fill={BR} />
  </Node>);

  const P = (k: number) => { passo(k); passoTxt().text(`${k + 1}. ${passos[Math.min(k, passos.length - 1)]}`); };
  let gasto = 0;
  const fase = function* (d: number, g: any) { gasto += d; yield* g; };
  P(0); yield* fase(T.entra, xObj(-20, T.entra, easeInOutCubic));
  P(1); yield* fase(T.fecha, gateL(1, T.fecha));                 // comporta já baixa: confirma fechada (sem "pulo")
  P(2); yield* fase(T.valvula, all(valv(1, T.valvula, easeInOutCubic), fluxo(.15, T.valvula, linear)));
  P(3); gasto += T.enche;
  yield* tween(T.enche, v => { const e = easeInOutCubic(v); nivel(map(yBaixo, yAlto, e)); fluxo(.15 + v * T.enche * .9); medida().text(`+${m()} m`); });
  fluxo(0); P(4); yield* fase(T.abre, gateR(0, T.abre, easeInOutCubic));
  yield* fase(T.sai, xObj(420, T.sai, easeInOutCubic));
  yield* waitFor(Math.max(0, total - gasto));
});
