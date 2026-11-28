const test=require('node:test');const assert=require('node:assert/strict');
const {fitCaptionLines}=require('/tmp/e392-caption/CaptionFitE392.js');
const words=s=>s.split(' ').map((w,i)=>({w,hl:i===1}));
const width=s=>[...s].reduce((n,c)=>n+(c==='W'?25:c==='I'?8:c===' '?8:17),0);
test('short character count can still overflow; preserve highlight and order',()=>{const w=words('APROFUNDANDO A CRATERA');const measured=s=>s==='APROFUNDANDO A CRATERA'?424.32:width(s);const lines=fitCaptionLines(w,measured,410);assert.equal(lines.length,2);assert.deepEqual(lines.flat(),w);assert.ok(lines.every(l=>measured(l.map(x=>x.w).join(' '))<=410));});
test('short group stays on one line',()=>{const w=words('TOPO DO KILAUEA');assert.deepEqual(fitCaptionLines(w,width,410),[w]);});
test('balance actual width and never lose a token on impossible input',()=>{const w=words('WWWWWW IIIIIII IIIIIII WWWWWW');const l=fitCaptionLines(w,width,240);assert.deepEqual(l.flat(),w);assert.ok(l.length<=2);const bad=words('WWWWWWWWWWWWWWWWWWWW');assert.deepEqual(fitCaptionLines(bad,width,100),[bad]);});
