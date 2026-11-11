// Ninguém Te Contou — kit vetorial: utilidades e definições comuns (cores, degradês, padrões).
const L = '#2a1d17';                     // contorno
const SK = '#F0BC94', SK2 = '#D99A74';   // pele
const cl = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x)), lerp = (a, b, k) => a + (b - a) * k;
const eo = k => 1 - Math.pow(1 - cl(k), 3), eio = k => { k = cl(k); return k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2 };
const back = k => { k = cl(k); const c = 1.7; return 1 + (c + 1) * Math.pow(k - 1, 3) + c * Math.pow(k - 1, 2) };
const rnd = s => { const x = Math.sin(s * 9301 + 49297) * 233280; return x - Math.floor(x) };
const NS = 'http://www.w3.org/2000/svg';
// "tubo" = linha com contorno (braço, perna, dedo, cabo)
const tubo = (cls, cor, w) => `<line class="${cls}c" stroke="${L}" stroke-width="${w + 9}" stroke-linecap="round"/><line class="${cls}" stroke="${cor}" stroke-width="${w}" stroke-linecap="round"/>`;
const tuboFixo = (x1, y1, x2, y2, cor, w) => `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${L}" stroke-width="${w + 9}" stroke-linecap="round"/><line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${cor}" stroke-width="${w}" stroke-linecap="round"/>`;
function linha(root, cls, x1, y1, x2, y2) {
  for (const s of [cls, cls + 'c']) { const e = root.querySelector('.' + s); if (!e) continue; e.setAttribute('x1', x1); e.setAttribute('y1', y1); e.setAttribute('x2', x2); e.setAttribute('y2', y2) }
}
// degradês e padrões usados pelos cenários, pela Val e pelos objetos (ficam num <svg> escondido da página)
const DEFS = `<defs>
 <linearGradient id="gParede" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#E6C9A0"/><stop offset="1" stop-color="#D2AB80"/></linearGradient>
 <linearGradient id="gParedeVerde" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#CFE3D6"/><stop offset="1" stop-color="#B3CFBF"/></linearGradient>
 <linearGradient id="gParedeAzul" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#BFD0E0"/><stop offset="1" stop-color="#A3B8CC"/></linearGradient>
 <linearGradient id="gChaoSombra" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000" stop-opacity=".05"/><stop offset="1" stop-color="#000" stop-opacity=".35"/></linearGradient>
 <pattern id="pLadrilho" width="120" height="120" patternUnits="userSpaceOnUse"><rect width="120" height="120" fill="#C98A7C"/><rect width="60" height="60" fill="#E7C7B4"/><rect x="60" y="60" width="60" height="60" fill="#E7C7B4"/></pattern>
 <pattern id="pPiso" width="140" height="140" patternUnits="userSpaceOnUse"><rect width="140" height="140" fill="#E8E2D6"/><path d="M0 0H140V140" fill="none" stroke="#CFC6B6" stroke-width="4"/></pattern>
 <pattern id="pMadeira" width="200" height="60" patternUnits="userSpaceOnUse"><rect width="200" height="60" fill="#B98455"/><path d="M0 58H200M120 0V60" stroke="#94643C" stroke-width="4"/><path d="M20 28 Q60 22 100 30" stroke="#A8744A" stroke-width="3" fill="none"/></pattern>
 <pattern id="pAzulejo" width="70" height="70" patternUnits="userSpaceOnUse"><rect width="70" height="70" fill="#F1E6D4"/><path d="M0 0H70V70" fill="none" stroke="#CBB89E" stroke-width="3"/></pattern>
 <pattern id="pXadrez" width="36" height="36" patternUnits="userSpaceOnUse"><rect width="36" height="36" fill="#F7B8C8"/><rect width="18" height="36" fill="#EE93AC" opacity=".7"/><rect width="36" height="18" fill="#EE93AC" opacity=".7"/></pattern>
 <pattern id="pTapete" width="60" height="60" patternUnits="userSpaceOnUse"><rect width="60" height="60" fill="#B5574A"/><path d="M0 30H60M30 0V60" stroke="#C9745F" stroke-width="6"/></pattern>
 <linearGradient id="gArmario" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#C97E86"/><stop offset="1" stop-color="#DE97A0"/></linearGradient>
 <linearGradient id="gCeuNoite" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#131B3D"/><stop offset="1" stop-color="#3A4683"/></linearGradient>
 <linearGradient id="gCeuDia" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6FB3E6"/><stop offset="1" stop-color="#CDE8F5"/></linearGradient>
 <linearGradient id="gCeuTarde" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5A6FB0"/><stop offset=".6" stop-color="#F0A47A"/><stop offset="1" stop-color="#F8D29A"/></linearGradient>
 <linearGradient id="gCeuCinza" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5B5550"/><stop offset="1" stop-color="#A8907A"/></linearGradient>
 <linearGradient id="gAsfalto" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6B6560"/><stop offset="1" stop-color="#3E3A37"/></linearGradient>
 <linearGradient id="gTerra" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#A9784C"/><stop offset="1" stop-color="#6E4A2E"/></linearGradient>
 <linearGradient id="gGrama" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8CC063"/><stop offset="1" stop-color="#4E8A3A"/></linearGradient>
 <linearGradient id="gAreia" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#F3D9A0"/><stop offset="1" stop-color="#D9B26C"/></linearGradient>
 <linearGradient id="gMar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3FA4C9"/><stop offset="1" stop-color="#2A7BA8"/></linearGradient>
 <linearGradient id="gLua" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#9A9AA6"/><stop offset="1" stop-color="#5E5E6A"/></linearGradient>
 <linearGradient id="gBolo" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8A4B2E"/><stop offset="1" stop-color="#5E2F1C"/></linearGradient>
 <radialGradient id="gLuz" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#FFE3A6" stop-opacity=".7"/><stop offset=".45" stop-color="#FFC56B" stop-opacity=".25"/><stop offset="1" stop-color="#FFB050" stop-opacity="0"/></radialGradient>
 <radialGradient id="gSol" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#FFF4C8" stop-opacity=".9"/><stop offset="1" stop-color="#FFE08A" stop-opacity="0"/></radialGradient>
 <radialGradient id="gSom" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#2a140c" stop-opacity=".45"/><stop offset="1" stop-color="#2a140c" stop-opacity="0"/></radialGradient>
 <radialGradient id="gVin" cx=".5" cy=".46" r=".75"><stop offset=".55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#1a0d06" stop-opacity=".55"/></radialGradient>
 <radialGradient id="gGlobo" cx=".35" cy=".3" r=".75"><stop offset="0" stop-color="#7CC7EE"/><stop offset="1" stop-color="#2D6FA8"/></radialGradient>
</defs>`;
