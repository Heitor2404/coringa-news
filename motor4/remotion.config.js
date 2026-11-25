// Remotion 4.0.544 — render headless determinístico (Coringa). WebGL por ANGLE em CPU (SwiftShader no Actions).
// JavaScript (não .ts) porque o CLI exige tsconfig.json na raiz para configs TypeScript, e motor4/ não tem um.
// LOCAL OBRIGATÓRIO: o CLI só carrega `remotion.config.{ts,js}` da "remotion root", que é a pasta do package.json mais
// próximo do cwd (= motor4/). Antes de 25/11 este arquivo ficava em motor4/remotion/ e NUNCA era carregado
// ("No config file loaded"): REMOTION_CHROME era ignorado e o Remotion tentava baixar o Chrome Headless Shell
// (falha da prova geográfica de Corinto). Regressão: tests/test_remotion_config_raiz.py.
import { Config } from '@remotion/cli/config';
import { existsSync } from 'node:fs';

Config.setChromiumOpenGlRenderer(process.env.REMOTION_GL || 'swangle');   // swangle = SwiftShader via ANGLE (CPU); 'angle' quando houver GPU
Config.setConcurrency(1);            // MapLibre/Three em WebGL: 1 aba por vez (exemplo oficial Remotion+MapLibre); flag --concurrency prevalece
Config.setVideoImageFormat('jpeg');
Config.setJpegQuality(92);

// Navegador local: variável explícita primeiro; depois o mesmo Chrome do sistema que src/v4/util.py usa. Sem nenhum,
// o Remotion mantém o comportamento padrão (download), que só funciona com rede liberada.
const candidatos = [process.env.REMOTION_CHROME, process.env.CORINGA_CHROME, '/usr/bin/google-chrome',
  '/usr/bin/chromium', '/usr/bin/chromium-browser'];
const navegador = candidatos.find((c) => !!c && existsSync(c));
if (navegador) Config.setBrowserExecutable(navegador);
