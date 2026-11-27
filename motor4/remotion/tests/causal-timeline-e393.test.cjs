const test=require('node:test'),assert=require('node:assert/strict');
const {causalAt}=require('/tmp/e393/CausalTimelineE393.js');
const events=[{acao:'a',tempo_s:2,depois:{a:'changed'}},{acao:'b',tempo_s:5,depois:{b:'changed'}}],init={a:'initial',b:'initial'};
test('no anticipation; continuous progress and ordered states',()=>{assert.deepEqual(causalAt(events,[2,1],init,1).progress,[0,0]);assert.deepEqual(causalAt(events,[2,1],init,3).progress,[.5,0]);assert.deepEqual(causalAt(events,[2,1],init,6).state,{a:'changed',b:'changed'});assert.deepEqual(init,{a:'initial',b:'initial'});});
test('reject overlapping events',()=>assert.throws(()=>causalAt(events,[4,1],init,3)));
