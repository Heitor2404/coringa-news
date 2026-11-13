// Mede o render do protótipo Remotion (tempo de parede e pico de memória do processo + navegadores).
import {bundle} from '@remotion/bundler';
import {renderMedia, selectComposition} from '@remotion/renderer';
import {execSync} from 'node:child_process';
import path from 'node:path';

const browserExecutable = process.env.CHROME || '/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell';
let pico = 0;
const amostra = setInterval(() => {
  try {
    const kb = execSync("ps -eo rss,comm | grep -Ei 'chrome|node|remotion|compositor' | awk '{s+=$1} END {print s}'").toString().trim();
    pico = Math.max(pico, Number(kb) || 0);
  } catch {}
}, 250);
const t0 = Date.now();
const serveUrl = await bundle({entryPoint: path.resolve('src/index.jsx')});
const t1 = Date.now();
const composition = await selectComposition({serveUrl, id: 'Numero', browserExecutable});
await renderMedia({composition, serveUrl, codec: 'h264', outputLocation: process.argv[2] || 'saida/numero_remotion.mp4', browserExecutable,
  concurrency: Number(process.env.CONC || 2), chromiumOptions: {gl: 'swiftshader'}, logLevel: 'error'});
const t2 = Date.now();
clearInterval(amostra);
console.log(JSON.stringify({bundle_s: (t1 - t0) / 1000, render_s: (t2 - t1) / 1000, quadros: 150, pico_rss_mb: Math.round(pico / 1024)}));
