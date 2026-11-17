// Styleframes + MEDIÇÃO sobre quadros efetivamente renderizados (formatos ATLAS/DOSSIÊ).
// Um bundle, N quadros: para cada quadro renderiza o Formato (com props.medir → a própria página registra a geometria
// real: caixas visíveis, território, rótulos, corpos de texto, textos cortados) e a Camada (marca + legenda, alfa).
// uso: node medir.mjs <props_formato.json> <props_camada.json> <quadros "30,120,..."> <saida_dir> <chrome>
import { bundle } from '@remotion/bundler';
import { renderStill, selectComposition } from '@remotion/renderer';
import fs from 'node:fs';
import path from 'node:path';

const [pf, pc, qs, out, chrome] = process.argv.slice(2);
const raiz = path.dirname(new URL(import.meta.url).pathname);
fs.mkdirSync(out, { recursive: true });
const serveUrl = await bundle({ entryPoint: path.join(raiz, 'src/index.ts'), publicDir: path.join(raiz, 'public') });
const propsF = { ...JSON.parse(fs.readFileSync(pf, 'utf8')), medir: true };
const propsC = { ...JSON.parse(fs.readFileSync(pc, 'utf8')), medir: true };   // medir JÁ na seleção: renderStill usa as props resolvidas da composição
const chromiumOptions = { gl: 'swangle' };
const compF = await selectComposition({ serveUrl, id: 'Formato', inputProps: propsF, browserExecutable: chrome, chromiumOptions });
const compC = await selectComposition({ serveUrl, id: 'Camada', inputProps: propsC, browserExecutable: chrome, chromiumOptions });
const medidas = {};
for (const q of qs.split(',').map(Number)) {
  let m = null;
  await renderStill({ serveUrl, composition: compF, inputProps: propsF, frame: q, output: path.join(out, `f_${q}.png`), imageFormat: 'png',
    browserExecutable: chrome, chromiumOptions, timeoutInMilliseconds: 120000,
    onBrowserLog: (l) => { if (l.text.startsWith('MEDIDA ')) m = JSON.parse(l.text.slice(7)); else if (/ERRO|Error/.test(l.text)) console.error(l.text.slice(0, 200)); } });
  let mc = null;
  await renderStill({ serveUrl, composition: compC, inputProps: propsC, frame: q, output: path.join(out, `c_${q}.png`), imageFormat: 'png',
    browserExecutable: chrome, chromiumOptions, timeoutInMilliseconds: 60000,
    onBrowserLog: (l) => { if (l.text.startsWith('MEDIDA_CAMADA ')) mc = JSON.parse(l.text.slice(14)); } });
  medidas[q] = m ? { ...m, camada: mc } : null;
  console.log('quadro', q, m ? `${m.camadas.length} camadas` : 'SEM MEDIDA');
}
fs.writeFileSync(path.join(out, 'medidas.json'), JSON.stringify(medidas));
