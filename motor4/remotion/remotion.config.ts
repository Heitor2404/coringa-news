// Remotion 4.0.544 — render headless determinístico (Coringa). WebGL por ANGLE em CPU (SwiftShader no Actions).
import { Config } from '@remotion/cli/config';
Config.setChromiumOpenGlRenderer((process.env.REMOTION_GL as any) || 'swangle');   // swangle = SwiftShader via ANGLE (CPU); 'angle' quando houver GPU
Config.setConcurrency(1);            // MapLibre/Three em WebGL: 1 aba por vez (exemplo oficial Remotion+MapLibre)
Config.setVideoImageFormat('jpeg');
Config.setJpegQuality(92);
if (process.env.REMOTION_CHROME) Config.setBrowserExecutable(process.env.REMOTION_CHROME);
