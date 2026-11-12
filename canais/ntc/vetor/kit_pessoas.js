// Figurantes genéricos no mesmo estilo da Val (boneco de tubo). Origem = entre os pés (0,0); altura ~ 600 em escala 1.
const PELES = ['#F0BC94', '#D99A74', '#B9784F', '#8A5A3C', '#F6D2B4'];
const CAMISAS = ['#3F7FA8', '#6E8B3D', '#D9A13B', '#C0563C', '#8A5A9E', '#2E9C8A', '#E07A6B'];
const CALCAS = ['#2F3A56', '#5A4A3A', '#3E4A55', '#6B5E4E'];
const CABELOS = ['#2A1D17', '#6B3E26', '#A8743A', '#9AA0A6', '#1A1A1A'];
function pessoaSVG(k) {
  const pele = PELES[k % PELES.length], cam = CAMISAS[(k * 3) % CAMISAS.length], calca = CALCAS[(k * 5) % CALCAS.length],
    cab = CABELOS[(k * 7) % CABELOS.length], tipo = k % 4;   // 0 curto, 1 careca, 2 rabo de cavalo, 3 boné
  const cabelo = tipo === 0 ? `<path d="M-62 -470 Q-60 -540 0 -542 Q60 -540 62 -470 Q40 -500 0 -500 Q-40 -500 -62 -470Z" fill="${cab}" stroke="${L}" stroke-width="5"/>`
    : tipo === 1 ? '' : tipo === 2 ? `<path d="M-62 -470 Q-60 -540 0 -542 Q60 -540 62 -470 Q40 -505 0 -505 Q-40 -505 -62 -470Z" fill="${cab}" stroke="${L}" stroke-width="5"/><path d="M58 -500 Q100 -480 86 -420 Q76 -450 56 -470Z" fill="${cab}" stroke="${L}" stroke-width="5"/>`
    : `<path d="M-64 -478 Q-60 -548 0 -548 Q60 -548 64 -478Z" fill="${CAMISAS[(k + 2) % CAMISAS.length]}" stroke="${L}" stroke-width="5"/><path d="M40 -480 L110 -470 Q112 -458 40 -462Z" fill="${CAMISAS[(k + 2) % CAMISAS.length]}" stroke="${L}" stroke-width="5"/>`;
  return `<ellipse class="psom" cx="0" cy="2" rx="80" ry="14" fill="url(#gSom)"/>
   ${tubo('pp1', calca, 26)}${tubo('pp2', calca, 26)}<ellipse class="pz1" rx="24" ry="9" fill="${L}"/><ellipse class="pz2" rx="24" ry="9" fill="${L}"/>
   <g class="pt">
    ${tubo('pa1', cam, 24)}<circle class="pm1" r="15" fill="${pele}" stroke="${L}" stroke-width="4"/>
    <rect x="-56" y="-330" width="112" height="200" rx="40" fill="${cam}" stroke="${L}" stroke-width="5"/>
    <rect x="-14" y="-370" width="28" height="44" fill="${pele}" stroke="${L}" stroke-width="5"/>
    <g class="pc"><circle cx="0" cy="-440" r="72" fill="${pele}" stroke="${L}" stroke-width="5"/>${cabelo}
     <circle class="po1" cx="-24" cy="-444" r="7" fill="${L}"/><circle class="po2" cx="24" cy="-444" r="7" fill="${L}"/>
     <path class="pb" stroke="${L}" stroke-width="5" fill="#7A2430" stroke-linecap="round"/></g>
    ${tubo('pa2', cam, 24)}<circle class="pm2" r="15" fill="${pele}" stroke="${L}" stroke-width="4"/>
   </g>`;
}
class Pessoa {
  constructor(g, k) { this.g = g; this.k = k; g.innerHTML = pessoaSVG(k); }
  // e = {x, y (pés), s (escala), t, modo: 'anda'|'corre'|'parado', dir: 1|-1}
  desenha(e) {
    const g = this.g, t = e.t + this.k * .37, modo = e.modo, dir = e.dir || 1;
    const vel = modo === 'corre' ? 15 : modo === 'anda' ? 7 : 0, ph = t * vel;
    const f = modo === 'parado' ? 0 : Math.sin(ph) * (modo === 'corre' ? 46 : 28), lev = modo === 'parado' ? 0 : Math.abs(Math.cos(ph)) * (modo === 'corre' ? 26 : 12);
    linha(g, 'pp1', -20, -140, -20 + f, 0 - Math.max(0, Math.cos(ph)) * 18); linha(g, 'pp2', 20, -140, 20 - f, 0 - Math.max(0, -Math.cos(ph)) * 18);
    const z1 = g.querySelector('.pz1'), z2 = g.querySelector('.pz2');
    z1.setAttribute('cx', -20 + f + 8); z1.setAttribute('cy', 4 - Math.max(0, Math.cos(ph)) * 18); z2.setAttribute('cx', 20 - f + 8); z2.setAttribute('cy', 4 - Math.max(0, -Math.cos(ph)) * 18);
    // braços: andando balançam; correndo de pânico vão para cima
    const r = Math.PI / 180, br = (cls, m, sx, sy, a) => { const hx = sx + Math.sin(a * r) * 150, hy = sy + Math.cos(a * r) * 150; linha(g, cls, sx, sy, hx, hy); const c = g.querySelector(m); c.setAttribute('cx', hx); c.setAttribute('cy', hy) };
    if (modo === 'corre') { br('pa1', '.pm1', -50, -310, -160 + Math.sin(ph * 2) * 12); br('pa2', '.pm2', 50, -310, 160 + Math.sin(ph * 2 + 1) * 12) }
    else { br('pa1', '.pm1', -50, -310, -12 - f * .5); br('pa2', '.pm2', 50, -310, 12 + f * .5) }
    g.querySelector('.pb').setAttribute('d', modo === 'corre' ? 'M-14 -404 Q0 -416 14 -404 Q12 -384 0 -382 Q-12 -384 -14 -404Z' : 'M-14 -404 Q0 -394 14 -404');
    const pisca = (t % 3.1) < .1; ['.po1', '.po2'].forEach(o => g.querySelector(o).setAttribute('r', pisca ? 1.5 : 7));
    g.querySelector('.pc').setAttribute('transform', `rotate(${Math.sin(t * 1.3) * 3 + (modo === 'corre' ? Math.sin(ph * 2) * 4 : 0)} 0 -370)`);
    g.querySelector('.pt').setAttribute('transform', `translate(0 ${-lev}) rotate(${modo === 'corre' ? 6 : 0} 0 -140)`);
    g.setAttribute('transform', `translate(${e.x} ${e.y}) scale(${e.s * dir} ${e.s})`);
  }
}
// cenários públicos ganham figurantes; quantidade e profundidade
const MULTIDAO = { rua: 4, rua_destruida: 3, mercado: 4, praia: 3, fazenda: 2, hospital: 3 };
