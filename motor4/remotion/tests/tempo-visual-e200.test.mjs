import test from 'node:test';
import assert from 'node:assert/strict';
import {progresso,progressoMarcos} from '../src/formatos/TempoVisualE200.ts';
const m=[{t:0,fracao:0,fonte:'fixture'},{t:2,fracao:.2,fonte:'fixture'},{t:5,fracao:1,fonte:'fixture'}];
test('legacy map and motion easing',()=>{
  for(let i=0;i<=100;i++){
    const x=i/100;
    assert.equal(progresso(x,0,1,'easeIO'),x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2);
    assert.equal(progresso(x,0,1,'easeOut'),1-Math.pow(1-x,3));
  }
});
test('same timeline for arbitrary phenomena',()=>{
  assert.equal(progressoMarcos(1,m,'degrau'),0);
  assert.equal(progressoMarcos(2,m,'degrau'),.2);
  assert.ok(Math.abs(progressoMarcos(3.5,m,'linear_ilustrativa')-.6)<1e-9);
  assert.equal(progressoMarcos(5,m,'degrau'),1);
  assert.equal(progressoMarcos(-1,m,'degrau'),0);
  assert.equal(progressoMarcos(100,m,'linear_ilustrativa'),1);
});
test('refuse chronology and missing source',()=>{
  assert.throws(()=>progressoMarcos(1,[m[0],{...m[1],t:0},m[2]],'degrau'));
  assert.throws(()=>progressoMarcos(1,[m[0],{...m[1],fonte:''},m[2]],'degrau'));
});
