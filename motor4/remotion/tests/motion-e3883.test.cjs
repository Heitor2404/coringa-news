const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const C=require('/tmp/e3883-test/MotionChartCoreE3883.js');
const claims=JSON.parse(fs.readFileSync('benchmarks/e3883/props.json')).shots.map(s=>s.documentary_chart_trial);
test('selects six chart families by structure',()=>assert.deepEqual(claims.map(C.selectChart),['range','area','proportion','bars','timeline','number']));
test('preserves reported limits and units',()=>{assert.equal(C.valueText(claims[0]),'≈ 21–26 km/h');assert.equal(C.valueText(claims[1]),'≈ 3,54 km²');assert.equal(C.valueText(claims[2]),'> 80%');});
for(const [idx,mut] of [[0,c=>c.values.reverse()],[0,c=>c.source=null],[1,c=>c.unit='m'],[2,c=>c.denominator=0],[2,c=>c.values[0].value=101],[3,c=>delete c.comparable],[4,c=>c.events.reverse()],[5,c=>c.publish=true],[5,c=>c.values[0].value=Infinity],[5,c=>c.fixture=false]])test('rejects malformed claim '+idx+' '+mut.toString(),()=>{const c=structuredClone(claims[idx]);mut(c);assert.throws(()=>C.selectChart(c),/E3883/);});
