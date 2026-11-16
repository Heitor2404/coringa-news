// Revideo 0.11 (fork MIT do Motion Canvas com render headless). Projeto paramétrico: a cena é escolhida pela variável
// 'cena' e lê os parâmetros do contrato do Coringa (variables). Mesma API de cena do Motion Canvas (@motion-canvas/2d).
import { makeProject } from '@revideo/core';
import nivelVasos from './cenas/nivel_vasos';
export default makeProject({
  name: 'coringa-mecanismos',
  scenes: [nivelVasos],
  settings: { shared: { size: { x: 1080, y: 1920 }, background: '#0C2A33' }, rendering: { fps: 30 } } as any,
});
