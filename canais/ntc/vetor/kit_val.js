// Valdirene no estilo "boneco de tubo": tudo articulado. Origem = quadril (0,0); pés em y≈186; topo do coque em y≈-514.
const VAL_PES = 186, VAL_TOPO = -514, VAL_ESC = 1.3;
const OMBRO_D = [-118, -238], OMBRO_E = [118, -238];   // D = lado esquerdo da tela (braço do chinelo), E = lado direito
// pose = ângulos dos braços (graus a partir de "para baixo"; D para fora = negativo, E para fora = positivo), mãos e rosto
const POSES = {
  neutra:      { D: [-14, -10], E: [14, 10], mD: 'aberta', mE: 'aberta', olhos: 'normal', sob: 'normal', boca: 'sorriso' },
  pensa:       { D: [25, 150], E: [16, 12], mD: 'punho', mE: 'aberta', olhos: 'cima', sob: 'surpresa', boca: 'reta' },
  comemora:    { D: [-158, -14], E: [158, 14], mD: 'punho', mE: 'punho', olhos: 'feliz', sob: 'surpresa', boca: 'aberto', pula: 1, confete: 1 },
  comemora2:   { D: [-160, -10], E: [40, -100], mD: 'punho', mE: 'punho', olhos: 'feliz', sob: 'surpresa', boca: 'aberto' },
  explica:     { D: [-48, -112], E: [16, 12], mD: 'aponta', mE: 'aberta', olhos: 'normal', sob: 'surpresa', boca: 'fala' },
  explica2:    { D: [-16, -12], E: [62, 70], mD: 'aberta', mE: 'aberta', olhos: 'normal', sob: 'surpresa', boca: 'fala' },
  susto:       { D: [-142, -34], E: [142, 34], mD: 'aberta', mE: 'aberta', olhos: 'arregalado', sob: 'surpresa', boca: 'o', suor: 1, pulo: 1 },
  brava:       { D: [-42, 98], E: [42, -98], mD: 'punho', mE: 'punho', olhos: 'normal', sob: 'raiva', boca: 'raiva', vermelha: 1 },
  brava2:      { D: [-92, -16], E: [42, -98], mD: 'aponta', mE: 'punho', olhos: 'normal', sob: 'raiva', boca: 'grita', vermelha: 1 },
  tchau:       { D: [-14, -10], E: [155, 10], mD: 'aberta', mE: 'aberta', olhos: 'feliz', sob: 'surpresa', boca: 'aberto' },
  chora:       { D: [-18, -40], E: [18, 40], mD: 'aberta', mE: 'aberta', olhos: 'normal', sob: 'triste', boca: 'choro' },
  desesperada: { D: [-160, -150], E: [160, 150], mD: 'aberta', mE: 'aberta', olhos: 'arregalado', sob: 'triste', boca: 'choro', suor: 1, treme: 1 },
};
const ALTERNATIVA = { neutra: 'pensa', comemora: 'comemora2', explica: 'explica2', susto: 'pensa', brava: 'brava2', desesperada: 'chora' };
const maoAberta = `<g class="hAberta"><g>${[[-13, 26, -17, 58], [-4, 28, -5, 64], [5, 28, 6, 63], [13, 26, 18, 55]].map(([a, b, c, d]) => tuboFixo(a, b, c, d, SK, 11)).join('')}</g>
  <ellipse cx="0" cy="18" rx="21" ry="20" fill="${SK}" stroke="${L}" stroke-width="5"/>${tuboFixo(-16, 12, -30, 34, SK, 11)}<ellipse cx="-2" cy="18" rx="15" ry="14" fill="${SK}"/></g>`;
const maoPunho = `<g class="hPunho"><rect x="-22" y="-2" width="44" height="54" rx="20" fill="${SK}" stroke="${L}" stroke-width="5"/>
  ${[4, 16, 28, 40].map(y => `<ellipse cx="-20" cy="${y + 3}" rx="13" ry="7.5" fill="${SK}" stroke="${L}" stroke-width="4"/>`).join('')}
  <path d="M12 2 Q22 14 6 26" stroke="${L}" stroke-width="19" fill="none" stroke-linecap="round"/><path d="M12 2 Q22 14 6 26" stroke="${SK}" stroke-width="10" fill="none" stroke-linecap="round"/></g>`;
const maoAponta = `<g class="hAponta">${tuboFixo(-2, 40, -2, 92, SK, 12)}<rect x="-22" y="-2" width="44" height="50" rx="20" fill="${SK}" stroke="${L}" stroke-width="5"/>
  ${[18, 30, 42].map(y => `<ellipse cx="-20" cy="${y}" rx="12" ry="7" fill="${SK}" stroke="${L}" stroke-width="4"/>`).join('')}
  <path d="M12 2 Q22 14 6 26" stroke="${L}" stroke-width="19" fill="none" stroke-linecap="round"/><path d="M12 2 Q22 14 6 26" stroke="${SK}" stroke-width="10" fill="none" stroke-linecap="round"/></g>`;
const VAL_SVG = `
 <ellipse class="vsom" cx="0" cy="${VAL_PES}" rx="150" ry="22" fill="url(#gSom)"/>
 <g class="pernas">${tubo('pa1', SK, 34)}${tubo('pa2', SK, 34)}${tubo('pe1', SK, 34)}${tubo('pe2', SK, 34)}
  <ellipse class="ch1" rx="34" ry="11" fill="#F4C431" stroke="${L}" stroke-width="5"/><ellipse class="ch2" rx="34" ry="11" fill="#F4C431" stroke="${L}" stroke-width="5"/></g>
 <g class="tronco">
  <g class="bracoE">${tubo('bE1', '#7E2B3E', 36)}${tubo('bE2', SK, 30)}<g class="mE">${maoAberta}${maoPunho}${maoAponta}</g></g>
  <path d="M-128 -40 Q-140 -230 -95 -262 Q0 -292 95 -262 Q140 -230 128 -40 Q130 40 120 110 L-120 110 Q-130 40 -128 -40Z" fill="#7E2B3E" stroke="${L}" stroke-width="6"/>
  <path d="M-128 -40 Q-140 -230 -95 -262 Q-60 -275 -40 -278 Q-90 -150 -100 105 L-120 110 Q-130 40 -128 -40Z" fill="#5E1E2D" opacity=".35"/>
  <path d="M-62 -232 L62 -232 L66 -110 L118 -95 Q128 30 112 118 Q0 140 -112 118 Q-128 30 -118 -95 L-66 -110Z" fill="url(#pXadrez)" stroke="${L}" stroke-width="5"/>
  <path d="M-62 -232 L-85 -270 M62 -232 L85 -270" stroke="#EE93AC" stroke-width="14"/><path d="M-118 -95 Q0 -80 118 -95" stroke="#EE93AC" stroke-width="12" fill="none"/>
  <g transform="translate(-20 -20)"><rect x="-36" y="-30" width="72" height="62" rx="8" fill="#FBE3EA" stroke="${L}" stroke-width="4"/><path d="M-14 20 L-18 0 L18 0 L14 20Z" fill="#E9A7C0" stroke="${L}" stroke-width="3"/><circle cy="-8" r="13" fill="#7A3D2B" stroke="${L}" stroke-width="3"/></g>
  <g class="cabeca">
   <rect x="-22" y="-300" width="44" height="40" fill="${SK}" stroke="${L}" stroke-width="5"/>
   <circle cx="0" cy="-470" r="44" fill="#6B3E26" stroke="${L}" stroke-width="5"/>
   <g transform="rotate(-18 0 -478)"><rect x="-70" y="-484" width="140" height="13" rx="6" fill="#F2C230" stroke="${L}" stroke-width="4"/><path d="M68 -500 L88 -490 L68 -478Z" fill="#E8B88A" stroke="${L}" stroke-width="3"/><path d="M82 -493 L88 -490 L82 -487Z" fill="#3A2A20"/><rect x="-78" y="-484" width="12" height="13" fill="#E98AA0" stroke="${L}" stroke-width="3"/></g>
   <circle cx="0" cy="-375" r="104" fill="${SK}" stroke="${L}" stroke-width="6"/>
   <path d="M-104 -380 Q-104 -480 0 -482 Q104 -480 104 -380 Q90 -440 40 -440 Q0 -400 -50 -440 Q-95 -435 -104 -380Z" fill="#6B3E26" stroke="${L}" stroke-width="5"/>
   <circle cx="-96" cy="-360" r="16" fill="${SK}" stroke="${L}" stroke-width="5"/><circle cx="96" cy="-360" r="16" fill="${SK}" stroke="${L}" stroke-width="5"/>
   <ellipse class="boch" cx="-62" cy="-325" rx="20" ry="12" fill="#E98A86" opacity=".55"/><ellipse class="boch" cx="62" cy="-325" rx="20" ry="12" fill="#E98A86" opacity=".55"/>
   <ellipse cx="-58" cy="-312" rx="12" ry="8" fill="#fff" opacity=".85"/>
   <path class="sbE" stroke="${L}" stroke-width="7" fill="none" stroke-linecap="round"/><path class="sbD" stroke="${L}" stroke-width="7" fill="none" stroke-linecap="round"/>
   <g class="olhos"></g>
   <circle cx="-40" cy="-378" r="29" fill="#fff" fill-opacity=".18" stroke="${L}" stroke-width="5"/><circle cx="40" cy="-378" r="29" fill="#fff" fill-opacity=".18" stroke="${L}" stroke-width="5"/><path d="M-11 -380 H11" stroke="${L}" stroke-width="5"/>
   <path d="M-6 -350 Q0 -340 6 -350" stroke="${SK2}" stroke-width="5" fill="none"/>
   <path class="boca" fill="#7A2430" stroke="${L}" stroke-width="5" stroke-linejoin="round"/>
   <path class="lagr" d="M-40 -350 Q-46 -330 -40 -318 Q-34 -330 -40 -350Z M40 -350 Q34 -330 40 -318 Q46 -330 40 -350Z" fill="#9FD3F2" stroke="${L}" stroke-width="3" opacity="0"/>
   <path class="suor" d="M92 -440 Q104 -415 92 -408 Q80 -415 92 -440Z" fill="#9FD3F2" stroke="${L}" stroke-width="4" opacity="0"/>
  </g>
  <g class="bracoD">${tubo('bD1', '#7E2B3E', 36)}${tubo('bD2', SK, 30)}<g class="mD">${maoAberta}${maoPunho}${maoAponta}</g></g>
 </g>`;
const SOB = { normal: ['M-62 -408 Q-40 -420 -18 -410', 'M18 -410 Q40 -420 62 -408'], raiva: ['M-64 -420 Q-40 -404 -16 -396', 'M16 -396 Q40 -404 64 -420'],
  surpresa: ['M-62 -424 Q-40 -440 -18 -428', 'M18 -428 Q40 -440 62 -424'], triste: ['M-64 -404 Q-40 -412 -18 -426', 'M18 -426 Q40 -412 64 -404'] };
function bocaD(tipo, ab) {   // ab = abertura 0..1 (fala/grito)
  switch (tipo) {
    case 'sorriso': return 'M-26 -330 Q0 -306 26 -330 Q0 -318 -26 -330Z';
    case 'reta': return 'M-18 -326 Q0 -322 18 -326 Q0 -320 -18 -326Z';
    case 'aberto': return `M-34 -334 Q0 -330 34 -334 Q30 ${-300 + ab * 8} 0 ${-294 + ab * 8} Q-30 ${-300 + ab * 8} -34 -334Z`;
    case 'o': return `M0 ${-338 - ab * 4} Q22 -338 20 -318 Q18 ${-298 + ab * 6} 0 ${-298 + ab * 6} Q-18 ${-298 + ab * 6} -20 -318 Q-22 -338 0 ${-338 - ab * 4}Z`;
    case 'fala': { const a = 6 + ab * 18; return `M-24 -328 Q0 -332 24 -328 Q20 ${-328 + a} 0 ${-326 + a} Q-20 ${-328 + a} -24 -328Z` }
    case 'raiva': return 'M-24 -320 Q0 -332 24 -320 Q0 -326 -24 -320Z';
    case 'grita': { const a = 18 + ab * 14; return `M-30 -325 Q0 -335 30 -325 Q26 ${-325 + a} 0 ${-322 + a} Q-26 ${-325 + a} -30 -325Z` }
    case 'choro': { const a = 14 + ab * 10; return `M-30 -318 Q0 -334 30 -318 Q26 ${-318 + a} 0 ${-314 + a} Q-26 ${-318 + a} -30 -318Z` }
  }
  return bocaD('sorriso', 0);
}
function olhosSVG(tipo, ox, oy, pisca) {
  if (pisca) return `<path d="M-52 -378 H-28 M28 -378 H52" stroke="${L}" stroke-width="6" stroke-linecap="round"/>`;
  if (tipo === 'feliz') return `<path d="M-54 -372 Q-40 -392 -26 -372 M26 -372 Q40 -392 54 -372" stroke="${L}" stroke-width="7" fill="none" stroke-linecap="round"/>`;
  if (tipo === 'arregalado') return `<circle cx="-40" cy="-378" r="20" fill="#fff" stroke="${L}" stroke-width="4"/><circle cx="40" cy="-378" r="20" fill="#fff" stroke="${L}" stroke-width="4"/><circle cx="${-40 + ox * .6}" cy="${-378 + oy * .6}" r="6" fill="${L}"/><circle cx="${40 + ox * .6}" cy="${-378 + oy * .6}" r="6" fill="${L}"/>`;
  if (tipo === 'cima') { ox = 6; oy = -10 }
  return `<circle cx="${-40 + ox}" cy="${-378 + oy}" r="9" fill="${L}"/><circle cx="${40 + ox}" cy="${-378 + oy}" r="9" fill="${L}"/>`;
}
function braco(g, p, sx, sy, a1, a2, l1 = 125, l2 = 112) {
  const r = Math.PI / 180, ex = sx + Math.sin(a1 * r) * l1, ey = sy + Math.cos(a1 * r) * l1, hx = ex + Math.sin((a1 + a2) * r) * l2, hy = ey + Math.cos((a1 + a2) * r) * l2;
  linha(g, p + '1', sx, sy, ex, ey); linha(g, p + '2', ex, ey, hx, hy); return [hx, hy, a1 + a2];
}
class Val {
  constructor(g) { this.g = g; g.innerHTML = VAL_SVG; this.q = s => g.querySelector(s); this._olhos = ''; }
  // e = {x, chao, s, pose, poseAnt, kTroca (0..1 da troca), t, anda (0..1 ou null), olhaX, olhaY, pisca, fala (0..1), aceno, inclina, agacha, pulo, treme}
  desenha(e) {
    const P = POSES[e.pose] || POSES.neutra, A = POSES[e.poseAnt] || P, k = back(cl(e.kTroca ?? 1));
    const mix = (a, b) => [lerp(a[0], b[0], k), lerp(a[1], b[1], k)];
    const S = VAL_ESC * (e.s || 1), t = e.t;
    // pernas: andar / agachar
    const ag = e.agacha || 0;
    let f1 = 0, f2 = 0, l1 = 0, l2 = 0;
    if (e.anda != null) { const ph = e.anda * Math.PI * 2; f1 = Math.sin(ph) * 34; f2 = -f1; l1 = Math.max(0, Math.cos(ph)) * 22; l2 = Math.max(0, -Math.cos(ph)) * 22 }
    const kx = ag * .9;
    linha(this.g, 'pa1', -50, 100 + ag, -50 - kx + f1 * .5, 140 + ag * .3 - l1 * .5); linha(this.g, 'pa2', 50, 100 + ag, 50 + kx + f2 * .5, 140 + ag * .3 - l2 * .5);
    linha(this.g, 'pe1', -50 - kx + f1 * .5, 140 + ag * .3 - l1 * .5, -58 + f1, 178 - l1); linha(this.g, 'pe2', 50 + kx + f2 * .5, 140 + ag * .3 - l2 * .5, 58 + f2, 178 - l2);
    const c1 = this.q('.ch1'), c2 = this.q('.ch2'); c1.setAttribute('cx', -62 + f1); c1.setAttribute('cy', 186 - l1); c2.setAttribute('cx', 62 + f2); c2.setAttribute('cy', 186 - l2);
    // tronco: respira, inclina, mola na troca de pose
    const resp = Math.sin(t * 2.6) * 0.012;
    let sy = 1 + resp, sx = 1 - resp * .6, inc = (e.inclina || 0) + Math.sin(t * 0.9) * 1.2;
    if ((e.kTroca ?? 1) < 1) { sy += 0.07 * (1 - back(cl(e.kTroca))); sx -= 0.04 * (1 - back(cl(e.kTroca))) }
    if (e.treme) sx *= 1 + Math.sin(t * 40) * 0.008;
    this.q('.tronco').setAttribute('transform', `translate(0 ${100 + ag}) rotate(${inc}) scale(${sx} ${sy}) translate(0 -100)`);
    // braços (com balanço leve) e mãos
    const bal = Math.sin(t * 1.6) * 4, bal2 = Math.sin(t * 1.4 + 1) * 4;
    let [d1, d2] = mix(A.D, P.D), [e1, e2] = mix(A.E, P.E);
    if (e.anda != null) { d1 = -14 - f1 * .5; d2 = -10; e1 = 14 - f2 * .5; e2 = 10 }
    if (e.bracoD) [d1, d2] = e.bracoD;
    if (e.bracoE) [e1, e2] = e.bracoE;
    d1 += bal * (P.D[0] > -60 ? 1 : .4); e1 += bal2 * (P.E[0] < 60 ? 1 : .4);
    if (e.treme) { d1 += Math.sin(t * 33) * 4; e1 += Math.sin(t * 29) * 4 }
    const hD = braco(this.g, 'bD', ...OMBRO_D, d1, d2), hE = braco(this.g, 'bE', ...OMBRO_E, e1, e2);
    for (const [cls, h, tipo] of [['.mD', hD, (k > .5 ? P : A).mD], ['.mE', hE, (k > .5 ? P : A).mE]]) {
      const m = this.q(cls); m.setAttribute('transform', `translate(${h[0]} ${h[1]}) rotate(${-h[2]}) translate(0 -16)`);
      m.querySelector('.hAberta').style.display = tipo === 'aberta' ? '' : 'none'; m.querySelector('.hPunho').style.display = tipo === 'punho' ? '' : 'none'; m.querySelector('.hAponta').style.display = tipo === 'aponta' ? '' : 'none';
    }
    this.maoD = hD;
    // cabeça: balança, acena com a narração, treme
    const R = k > .5 ? P : A;
    let hr = Math.sin(t * 1.3) * 2.5 + (e.aceno || 0);
    if (e.treme) hr += Math.sin(t * 31) * 1.5;
    this.q('.cabeca').setAttribute('transform', `rotate(${hr} 0 -280)`);
    const ot = olhosSVG(R.olhos, e.olhaX || 0, e.olhaY || 0, e.pisca && R.olhos !== 'feliz');
    if (ot !== this._olhos) { this.q('.olhos').innerHTML = ot; this._olhos = ot }
    const sb = SOB[R.sob] || SOB.normal; this.q('.sbE').setAttribute('d', sb[0]); this.q('.sbD').setAttribute('d', sb[1]);
    const ab = R.boca === 'fala' || R.boca === 'grita' || R.boca === 'choro' ? Math.abs(Math.sin(t * 11)) * (e.fala ?? 1) : Math.abs(Math.sin(t * 6)) * .5;
    this.q('.boca').setAttribute('d', bocaD(R.boca, ab));
    this.g.querySelectorAll('.boch').forEach(b => { b.setAttribute('fill', R.vermelha ? '#E2544E' : '#E98A86'); b.setAttribute('opacity', R.vermelha ? .8 : .55) });
    this.q('.suor').setAttribute('opacity', R.suor ? 1 : 0); this.q('.suor').setAttribute('transform', `translate(0 ${R.suor ? (t * 30) % 25 : 0})`);
    this.q('.lagr').setAttribute('opacity', R.boca === 'choro' ? 1 : 0); this.q('.lagr').setAttribute('transform', `translate(0 ${(t * 60) % 40})`);
    // posição no mundo
    const pulo = e.pulo || 0;
    this.g.setAttribute('transform', `translate(${e.x} ${e.chao - VAL_PES * S - pulo}) scale(${S})`);
    const so = this.q('.vsom'); so.setAttribute('transform', `translate(0 ${pulo / S}) scale(${lerp(1, .6, cl(pulo / 140))} 1)`);
  }
}
