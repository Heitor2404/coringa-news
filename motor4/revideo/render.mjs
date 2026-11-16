// uso: node revideo/render.mjs <params.json> <saida.mp4>  — render headless (puppeteer + ffmpeg), sem editor.
process.env.DISABLE_TELEMETRY = 'true';   // @revideo/telemetry só desliga com a string 'true' (PostHog)
import fs from 'node:fs'; import path from 'node:path'; import { renderVideo } from '@revideo/renderer';
const [, , arq, saida] = process.argv;
const params = JSON.parse(fs.readFileSync(arq, 'utf8'));
const out = await renderVideo({
  projectFile: path.resolve(path.dirname(new URL(import.meta.url).pathname), 'src/project.ts'),
  variables: { params },
  settings: { outFile: path.basename(saida), outDir: path.dirname(path.resolve(saida)), workers: 1, logProgress: false,
    puppeteer: { executablePath: process.env.REVIDEO_CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] },
    projectSettings: { size: { x: 1080, y: 1920 }, background: '#0C2A33', range: [0, params.duracao || 12] } },
});
console.log(JSON.stringify({ ok: true, arquivo: out }));
