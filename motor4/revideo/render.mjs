// uso: node revideo/render.mjs <params.json> <saida.mp4>  — render headless (puppeteer + ffmpeg), sem editor.
// Execução 43972774128: o Chrome fechou na partida no runner ("Target closed") sem dizer por quê. Agora: stderr do Chrome
// no log (dumpio) e uma segunda tentativa com flags mínimas e, se houver, o chrome-headless-shell do Playwright.
process.env.DISABLE_TELEMETRY = 'true';   // @revideo/telemetry só desliga com a string 'true' (PostHog)
import fs from 'node:fs'; import path from 'node:path'; import { renderVideo } from '@revideo/renderer';
const [, , arq, saida] = process.argv;
const params = JSON.parse(fs.readFileSync(arq, 'utf8'));

function shellPlaywright() {
  const raiz = process.env.PLAYWRIGHT_BROWSERS_PATH || path.join(process.env.HOME || '', '.cache/ms-playwright');
  for (const base of [raiz, '/opt/pw-browsers']) {
    try {
      for (const d of fs.readdirSync(base).filter(n => n.startsWith('chromium_headless_shell')).sort().reverse()) {
        const exe = path.join(base, d, 'chrome-headless-shell-linux64', 'chrome-headless-shell');
        if (fs.existsSync(exe)) return exe;
      }
    } catch { /* sem pasta */ }
  }
  return null;
}

const tentativas = [
  { executablePath: process.env.REVIDEO_CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] },
  { executablePath: process.env.REVIDEO_CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu'] },
];
const shell = shellPlaywright();
if (shell) tentativas.push({ executablePath: shell, headless: 'shell', args: ['--no-sandbox', '--disable-dev-shm-usage'] });

let erro = null;
for (const [i, pup] of tentativas.entries()) {
  try {
    const out = await renderVideo({
      projectFile: path.resolve(path.dirname(new URL(import.meta.url).pathname), 'src/project.ts'),
      variables: { params },
      settings: { outFile: path.basename(saida), outDir: path.dirname(path.resolve(saida)), workers: 1, logProgress: false,
        puppeteer: { ...pup, dumpio: true, protocolTimeout: 240000 },
        projectSettings: { size: { x: 1080, y: 1920 }, background: '#0C2A33', range: [0, params.duracao || 12] } },
    });
    console.log(JSON.stringify({ ok: true, arquivo: out, tentativa: i + 1, chrome: pup.executablePath }));
    process.exit(0);
  } catch (e) {
    erro = e;
    console.error(`[revideo] tentativa ${i + 1} (${pup.executablePath}) falhou: ${String(e && e.message).slice(0, 300)}`);
  }
}
throw erro;
