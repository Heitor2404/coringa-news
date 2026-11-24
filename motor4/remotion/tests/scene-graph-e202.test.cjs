// E202: contrato v2 gerado pelo compilador Python (arquivo gerado pelo workflow a partir da fixture de teste).
const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');
const C=require('/tmp/e202-test/SceneGraphCoreE201.js');
const sg=JSON.parse(fs.readFileSync(process.env.E202_FIXTURE||'/tmp/e202_fixture_sg.json','utf8'));
const dur=sg.camera[sg.camera.length-1].t;
test('v2 válido, v1 intacto e interpolação determinística',()=>{
  assert.equal(C.validateSceneV2(sg,dur),true);
  for(const a of sg.actors){const k=a.states[Math.min(1,a.states.length-1)];assert.deepEqual(C.stateAtV2(a,k.t),C.stateAtV2(a,k.t));}
  const c=C.cameraAt(sg.camera,dur/2);assert.ok(c.zoom>0);
  const [x,y]=C.worldToScreen({t:0,x:0,y:0,zoom:1},0,0);assert.deepEqual([x,y],[(C.BOX_V2[0]+C.BOX_V2[2])/2,(C.BOX_V2[1]+C.BOX_V2[3])/2]);
});
test('recusa publicação, script e estados inválidos',()=>{
  const d=structuredClone(sg);d.publish=true;assert.throws(()=>C.validateSceneV2(d,dur),/E202-CONTRACT/);
  const e=structuredClone(sg);e.actors[0].shapes[0].d='<script>';assert.throws(()=>C.validateSceneV2(e,dur),/E202-SHAPE/);
  const f=structuredClone(sg);f.actors[0].states[0].sat=3;assert.throws(()=>C.validateSceneV2(f,dur),/E202-STATE/);
  const g=structuredClone(sg);g.camera[0].zoom=0;assert.throws(()=>C.validateSceneV2(g,dur),/E202-CAMERA/);
});
