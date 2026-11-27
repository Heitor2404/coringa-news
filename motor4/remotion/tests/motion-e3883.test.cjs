const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const C=require('/tmp/e3883-test/MotionChartCoreE3883.js');
const claims=JSON.parse(fs.readFileSync('benchmarks/e3883/props.json')).shots.map(s=>s.documentary_chart_trial);
test('selects six chart families by structure',()=>assert.deepEqual(claims.map(C.selectChart),['range','area','proportion','bars','timeline','number']));
test('preserves reported limits and units',()=>{assert.equal(C.valueText(claims[0]),'≈ 21–26 km/h');assert.equal(C.valueText(claims[1]),'≈ 3,54 km²');assert.equal(C.valueText(claims[2]),'> 80%');});
for(const [idx,mut] of [[0,c=>c.values.reverse()],[0,c=>c.source=null],[1,c=>c.unit='m'],[2,c=>c.denominator=0],[2,c=>c.values[0].value=101],[3,c=>delete c.comparable],[4,c=>c.events.reverse()],[5,c=>c.publish=true],[5,c=>c.values[0].value=Infinity],[5,c=>c.fixture=false]])test('rejects malformed claim '+idx+' '+mut.toString(),()=>{const c=structuredClone(claims[idx]);mut(c);assert.throws(()=>C.selectChart(c),/E3883/);});

test('shared area preserves scale and rejects unrelated claims',()=>{
 const total=structuredClone(claims[1]);total.values[0].value=35.5;
 const part=structuredClone(claims[1]);const r={schema:'coringa.motion.area_relation.private.v1',publish:false,kind:'included_area',group:'test',role:'part',total,part,inclusion_statement:'Source explicitly includes part in total'};
 const a=C.areaRelation(part,r);assert.ok(Math.abs(a.sideRatio*a.sideRatio-3.54/35.5)<1e-12);
 assert.equal(C.areaSideLabel(3.54),'≈ 1,9 km');
 assert.equal(C.areaSideLabel(35.5),'≈ 6 km');
 assert.throws(()=>C.areaRelation(total,r),/E3883/);
 const wrong=structuredClone(r);wrong.total.values[0].value=2;assert.throws(()=>C.areaRelation(part,wrong),/E3883/);
 const different=structuredClone(r);different.total.source.url='https://example.org';assert.throws(()=>C.areaRelation(part,different),/E3883/);
});
