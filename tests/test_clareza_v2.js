/* Contrato visual genérico dos mecanismos V2, sem render e sem dados do Panamá. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.resolve(__dirname, '../src/render/v2/nucleo.js'), 'utf8');
const sandbox = {window: {}};
vm.runInNewContext(source, sandbox, {filename: 'nucleo.js'});
const {cameraDidatica, planejarRotulos} = sandbox.window.V2.U;
assert.equal(typeof cameraDidatica, 'function');
assert.equal(typeof planejarRotulos, 'function');

const aspecto = 1080 / 675, base = [0, 300, 1480];
const esquerda = cameraDidatica(base, [430, 740], [720, 700], aspecto, 1);
const direita = cameraDidatica(base, [1180, 740], [720, 700], aspecto, 1);
assert(direita[0] > esquerda[0], 'a câmera não segue o alvo narrado');
assert(esquerda[2] < base[2], 'sem foco adequado no alvo');
for (const alvo of [[430, 740], [1180, 740]]) {
  const cam = cameraDidatica(base, alvo, [720, 700], aspecto, 1);
  assert(alvo[0] >= cam[0] && alvo[0] <= cam[0] + cam[2], 'alvo cortado');
  assert(alvo[1] >= cam[1] && alvo[1] <= cam[1] + cam[2] / aspecto, 'alvo cortado na vertical');
  assert(720 >= cam[0] && 720 <= cam[0] + cam[2], 'contexto causal cortado');
}
assert.equal(cameraDidatica(base, null, [720,700], aspecto, 1), base, 'sem alvo deve conservar quadro');

const zona = {esq: 76, dir: 930, topo: 550, base: 1160};
const r = planejarRotulos([
  {id:'secundario', prioridade:10, x:400, y:600, w:240, h:65, visivel:true, ordem:0},
  {id:'assunto', prioridade:100, x:400, y:600, w:270, h:65, visivel:true, ordem:1},
  {id:'estado', prioridade:55, x:400, y:600, w:210, h:65, visivel:true, ordem:2},
  {id:'ruido', prioridade:1, x:300, y:1000, w:200, h:60, visivel:true, ordem:3},
], zona, 2);
assert.equal(r.length, 2, 'mais rótulos que o limite didático');
assert.equal(r[0].id, 'assunto', 'título narrado deve permanecer');
for(const item of r) {
  assert(item.x >= zona.esq && item.y >= zona.topo);
  const w = item.id==='assunto' ? 270 : 210, h = 65;
  assert(item.x+w <= zona.dir && item.y+h <= zona.base, 'rótulo fora da tela');
}
const seSobrepoe = (a,b,aw,bw) => a.x < b.x+bw+8 && b.x < a.x+aw+8 && a.y < b.y+73 && b.y < a.y+73;
assert(!seSobrepoe(r[0],r[1],270,210), 'rótulos sobrepostos');
const grandes = planejarRotulos([{id:'texto_inviavel',prioridade:10,x:100,y:600,w:1000,h:60,visivel:true}],zona,3);
assert.equal(grandes.length,0,'não deve exibir caixa larga cortada');
console.log('Direção visual V2: foco, contexto, hierarquia, densidade e zona segura aprovados');
